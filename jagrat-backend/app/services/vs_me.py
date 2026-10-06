from __future__ import annotations

from datetime import datetime, timezone
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import AIRequestTrace, InteractionRecord, Profile, ReflectionGoal, VivekanandaComparison, Teaching
from app.schemas import TextAssessment, VivekanandaVsMeGeneration, VivekanandaVsMeResponse, TrustPanel
from app.services.context import build_retrieval_excerpt
from app.services.gemini import GeminiService, compact_json
from app.services.mentor import SourceGuardError, teaching_payload, validate_ai_written_text, validate_quote_id, trust_panel
from app.services.prompts import TEXT_ASSESSMENT_SYSTEM, VIVEKANANDA_VS_ME_SYSTEM
from app.services.retrieval import retrieve_journal_insights, retrieve_teachings, terms_from_analysis


class VivekanandaVsMeService:
    def __init__(self, gemini: GeminiService):
        self.gemini = gemini

    def assess_text(self, text: str) -> TextAssessment:
        return self.gemini.generate(
            system_instruction=TEXT_ASSESSMENT_SYSTEM,
            prompt=f"TEXT TO ASSESS:\n{text}",
            schema=TextAssessment,
            fast=True,
        )

    def _build_context(self, db: Session, profile_id: str, view: str, assessment: TextAssessment) -> dict:
        settings = get_settings()
        profile = db.get(Profile, profile_id)
        terms = terms_from_analysis(assessment.analysis)
        journals = retrieve_journal_insights(db, profile_id, terms, limit=settings.journal_memory_limit)
        teachings = retrieve_teachings(db, terms, limit=settings.teaching_candidate_limit)
        answers = (profile.answers if profile else {}) or {}
        goal = db.scalar(select(ReflectionGoal).where(ReflectionGoal.profile_id == profile_id))

        onboarding = {
            "profession": answers.get("profession"),
            "profession_other": answers.get("profession_other"),
            "age": answers.get("age"),
            "matters_most": answers.get("matters_most"),
            "troubling_most": answers.get("troubling_most"),
            "troubling_other": answers.get("troubling_other"),
            "problem_approach": answers.get("problem_approach"),
            "improve": answers.get("improve"),
            "improve_other": answers.get("improve_other"),
        }
        return {
            "profile": {
                "display_name": profile.display_name if profile else "Friend",
                "onboarding": onboarding,
                "active_reflection_goal": {
                    "goal_key": goal.goal_key,
                    "goal_text": goal.goal_text,
                } if goal else None,
            },
            "my_view": view,
            "analysis": assessment.analysis.model_dump(),
            "relevant_journal_memory": [
                {
                    "observation": j.observation,
                    "tags": j.tags,
                    "themes": j.themes,
                    "emotions": j.emotions,
                    "diary_excerpt": (j.entry.text[:1800] if j.entry else ""),
                }
                for j in journals
            ],
            "candidate_teachings": [
                {
                    "id": t.id,
                    "excerpt": build_retrieval_excerpt(t.quote, terms.terms, settings.max_candidate_excerpt_chars),
                    "themes": t.themes,
                    "emotions": t.emotions,
                    "challenges": t.challenges,
                    "keywords": t.keywords,
                    "context": t.context,
                    "source_title": t.source_title,
                    "source_type": t.source_type,
                }
                for t in teachings
            ],
        }

    def _generate(self, context: dict) -> VivekanandaVsMeGeneration:
        prompt = (
            "Return JSON only for the following Vivekananda-vs-Me comparison. "
            "The teaching field must contain only a candidate quote_id or null. "
            "Never write source text in any AI-generated field. If no candidate is sufficiently relevant, use null "
            "and make the comparison limitation explicit rather than inventing a teaching.\n"
            + compact_json(context)
        )
        last_error: Exception | None = None
        for correction in (False, True):
            try:
                current_prompt = prompt
                if correction:
                    current_prompt = (
                        "Regenerate the comparison. Do not include any quotation marks, source wording, or attribution "
                        "to Swami Vivekananda in AI-written fields. Return only a valid JSON comparison and a candidate "
                        "quote_id from the supplied list, or null.\n" + compact_json(context)
                    )
                generation = self.gemini.generate(
                    system_instruction=VIVEKANANDA_VS_ME_SYSTEM,
                    prompt=current_prompt,
                    schema=VivekanandaVsMeGeneration,
                )
                validate_ai_written_text(
                    generation.where_they_align,
                    generation.where_they_differ,
                    generation.what_to_examine,
                    *generation.questions_for_me,
                    generation.experiment,
                    generation.conclusion,
                )
                validate_quote_id(generation.teaching.quote_id, {c["id"] for c in context["candidate_teachings"]})
                return generation
            except SourceGuardError as exc:
                last_error = exc
        raise SourceGuardError(str(last_error or "Vivekananda-vs-Me output failed source-grounding validation"))

    def create(self, db: Session, profile_id: str, view: str, assessment: TextAssessment | None = None) -> VivekanandaVsMeResponse:
        profile = db.get(Profile, profile_id)
        if not profile:
            raise ValueError("Profile not found")

        assessment = assessment or self.assess_text(view)
        if assessment.risk.risk_level in {"high", "immediate"}:
            raise RuntimeError("SAFETY_TRIGGERED")

        context = self._build_context(db, profile_id, view, assessment)
        candidate_ids = {c["id"] for c in context["candidate_teachings"]}
        generation = self._generate(context)
        quote_id = validate_quote_id(generation.teaching.quote_id, candidate_ids)
        selected = db.get(Teaching, quote_id) if quote_id else None
        if quote_id and selected is None:
            raise SourceGuardError("Selected teaching ID does not exist in the canonical teaching database")

        record = VivekanandaComparison(
            profile_id=profile_id,
            user_view=view,
            problem_analysis=assessment.analysis.model_dump(),
            selected_teaching_id=selected.id if selected else None,
            result_json=generation.model_dump(),
            risk_flag=False,
        )
        db.add(record)
        db.add(InteractionRecord(profile_id=profile_id, themes=assessment.analysis.themes))
        db.add(
            AIRequestTrace(
                request_id=str(uuid.uuid4()),
                profile_id=profile_id,
                conversation_id=None,
                operation="vivekananda_vs_me",
                model=get_settings().gemini_model,
                candidate_ids=sorted(candidate_ids),
                selected_quote_id=selected.id if selected else None,
                safety_status="none",
                metadata_json={"analysis": assessment.analysis.model_dump()},
            )
        )
        db.commit()
        db.refresh(record)

        return VivekanandaVsMeResponse(
            comparison_id=record.id,
            my_view=view,
            teaching=teaching_payload(selected),
            where_they_align=generation.where_they_align,
            where_they_differ=generation.where_they_differ,
            what_to_examine=generation.what_to_examine,
            questions_for_me=generation.questions_for_me,
            experiment=generation.experiment,
            conclusion=generation.conclusion,
            trust=trust_panel(selected, len(context["candidate_teachings"]), candidate_ids),
        )

    def get(self, db: Session, profile_id: str, comparison_id: str) -> VivekanandaVsMeResponse:
        record = db.scalar(
            select(VivekanandaComparison).where(
                VivekanandaComparison.id == comparison_id,
                VivekanandaComparison.profile_id == profile_id,
            )
        )
        if not record:
            raise ValueError("Comparison not found")
        selected = db.get(Teaching, record.selected_teaching_id) if record.selected_teaching_id else None
        result = VivekanandaVsMeGeneration.model_validate(record.result_json or {})
        candidate_ids = {selected.id} if selected else set()
        return VivekanandaVsMeResponse(
            comparison_id=record.id,
            my_view=record.user_view,
            teaching=teaching_payload(selected),
            where_they_align=result.where_they_align,
            where_they_differ=result.where_they_differ,
            what_to_examine=result.what_to_examine,
            questions_for_me=result.questions_for_me,
            experiment=result.experiment,
            conclusion=result.conclusion,
            trust=trust_panel(selected, 1 if selected else 0, candidate_ids),
        )
