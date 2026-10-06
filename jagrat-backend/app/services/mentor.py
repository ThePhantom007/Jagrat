from datetime import datetime, timezone
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import AIRequestTrace, ActionItem, ChallengeRound, Conversation, InteractionRecord, Message, Profile, Teaching
from app.schemas import (
    ActionPayload,
    ChallengeGeneration,
    ChallengeResponse,
    MentorGeneration,
    MentorResponse,
    ProblemAnalysis,
    TextAssessment,
    TrustPanel,
)
from app.services.context import build_context
from app.services.gemini import GeminiService, compact_json
from app.services.prompts import CHALLENGE_SYSTEM, MASTER_SYSTEM, TEXT_ASSESSMENT_SYSTEM
from app.services.retrieval import terms_from_analysis


class SourceGuardError(RuntimeError):
    pass


def teaching_payload(t: Teaching | None):
    if not t:
        return None
    return {
        "id": t.id,
        # Exact text from the canonical organiser JSON/database record.
        "quote": t.quote,
        "source": {
            "type": t.source_type,
            "title": t.source_title,
            "volume": t.source_volume,
            "chapter": t.source_chapter,
            "page": t.source_page,
            "section": t.source_section,
            "url": t.source_url,
            "authority": "organizer_provided_json",
        },
    }


def trust_panel(selected: Teaching | None, candidate_count: int, candidate_ids: set[str]) -> TrustPanel:
    return TrustPanel(
        quote_verified=bool(selected and selected.id in candidate_ids),
        quote_id=selected.id if selected else None,
        candidate_count=candidate_count,
        quote_authority="organizer_provided_json",
        rendered_from_backend=bool(selected),
        ai_written_sections=["understanding", "interpretation", "reflection_question", "challenge", "action"],
    )


def validate_quote_id(quote_id: str | None, candidate_ids: set[str]) -> str | None:
    if quote_id is None:
        return None
    if quote_id not in candidate_ids:
        raise SourceGuardError("Gemini returned a teaching ID that was not in the supplied candidate set")
    return quote_id


def _history_for_challenge(rounds: list[ChallengeRound]) -> list[dict]:
    return [
        {
            "round": r.round_number,
            "assumption": r.assumption,
            "question": r.challenge_question,
            "user_response": r.user_response,
            "reflection": r.reflection,
        }
        for r in rounds
    ]


class MentorService:
    def __init__(self, gemini: GeminiService):
        self.gemini = gemini

    def assess_text(self, text: str) -> TextAssessment:
        return self.gemini.generate(
            system_instruction=TEXT_ASSESSMENT_SYSTEM,
            prompt=f"TEXT TO ASSESS:\n{text}",
            schema=TextAssessment,
            fast=True,
        )

    def create_turn(self, db: Session, profile_id: str, message: str, assessment: TextAssessment | None = None) -> MentorResponse:
        profile = db.get(Profile, profile_id)
        if not profile:
            raise ValueError("Profile not found")

        assessment = assessment or self.assess_text(message)
        analysis: ProblemAnalysis = assessment.analysis
        conversation = Conversation(
            profile_id=profile_id,
            current_problem=message,
            problem_analysis=analysis.model_dump(),
        )
        db.add(conversation)
        db.flush()

        context = build_context(db, profile_id=profile_id, current_problem=message, analysis=analysis, conversation=conversation)
        if not context["candidate_teachings"]:
            db.rollback()
            raise LookupError("No sufficiently relevant organiser-provided teaching was found for this problem")

        generation = self.gemini.generate(
            system_instruction=MASTER_SYSTEM,
            prompt=(
                "Return JSON only for the following mentor context. Every one of the six onboarding fields must "
                "meaningfully influence the response; include each field exactly once in personalization_trace:\n"
                + compact_json(context)
            ),
            schema=MentorGeneration,
        )

        expected_profile_fields = {
            "profession",
            "age",
            "matters_most",
            "troubling_most",
            "problem_approach",
            "improve",
        }
        if set(generation.personalization_trace) != expected_profile_fields:
            raise RuntimeError("Gemini did not confirm use of all six onboarding dimensions")

        candidates = {item["id"] for item in context["candidate_teachings"]}
        quote_id = validate_quote_id(generation.teaching.quote_id, candidates)

        selected = None
        if quote_id is not None:
            selected = db.scalar(select(Teaching).where(Teaching.id == quote_id))
            if selected is None:
                raise SourceGuardError("Selected teaching ID does not exist in the canonical teaching database")

        conversation.selected_teaching_id = selected.id if selected else None
        db.add(Message(conversation_id=conversation.id, role="user", content=message, metadata_json={"analysis": analysis.model_dump()}))
        db.add(
            Message(
                conversation_id=conversation.id,
                role="assistant",
                content=generation.interpretation,
                metadata_json={"quote_id": selected.id if selected else None},
            )
        )
        db.add(InteractionRecord(profile_id=profile_id, conversation_id=conversation.id, themes=analysis.themes))
        db.add(
            ChallengeRound(
                conversation_id=conversation.id,
                round_number=1,
                belief=analysis.underlying_belief,
                assumption=generation.challenge.assumption,
                challenge_question=generation.challenge.question,
                teaching_id=selected.id if selected else None,
            )
        )
        db.add(
            ActionItem(
                profile_id=profile_id,
                conversation_id=conversation.id,
                text=generation.action.action,
                reason=generation.action.reason,
            )
        )
        db.add(AIRequestTrace(
            request_id=str(uuid.uuid4()), profile_id=profile_id, conversation_id=conversation.id, operation="mentor",
            model=get_settings().gemini_model, candidate_ids=sorted(candidates), selected_quote_id=selected.id if selected else None,
            safety_status="none", metadata_json={"analysis": analysis.model_dump(), "active_reflection_goal": context["profile"].get("active_reflection_goal")},
        ))
        db.commit()

        return MentorResponse(
            conversation_id=conversation.id,
            round=1,
            understanding=generation.understanding,
            teaching=teaching_payload(selected),
            interpretation=generation.interpretation,
            reflection_question=generation.reflection_question,
            challenge=generation.challenge,
            action=generation.action,
            trust=trust_panel(selected, len(context["candidate_teachings"]), candidates),
        )

    def continue_turn(self, db: Session, profile_id: str, conversation_id: str, message: str) -> MentorResponse:
        conversation = db.scalar(select(Conversation).where(Conversation.id == conversation_id, Conversation.profile_id == profile_id))
        if not conversation:
            raise ValueError("Conversation not found")
        if conversation.risk_flag:
            raise ValueError("Cannot continue a safety-flagged conversation")

        assessment = self.assess_text(message)
        if assessment.risk.risk_level in {"high", "immediate"}:
            raise RuntimeError("SAFETY_TRIGGERED")
        analysis = assessment.analysis
        context = build_context(db, profile_id=profile_id, current_problem=message, analysis=analysis, conversation=conversation)
        if not context["candidate_teachings"]:
            raise LookupError("No sufficiently relevant organiser-provided teaching was found for this problem")

        generation = self.gemini.generate(
            system_instruction=MASTER_SYSTEM,
            prompt=(
                "Return JSON only for the following mentor context. Every one of the six onboarding fields must "
                "meaningfully influence the response; include each field exactly once in personalization_trace:\n"
                + compact_json(context)
            ),
            schema=MentorGeneration,
        )
        expected = {"profession", "age", "matters_most", "troubling_most", "problem_approach", "improve"}
        if set(generation.personalization_trace) != expected:
            raise RuntimeError("Gemini did not confirm use of all six onboarding dimensions")
        candidates = {item["id"] for item in context["candidate_teachings"]}
        quote_id = validate_quote_id(generation.teaching.quote_id, candidates)
        selected = db.get(Teaching, quote_id) if quote_id else None
        if quote_id and selected is None:
            raise SourceGuardError("Selected teaching ID does not exist in the canonical teaching database")

        conversation.current_problem = message
        conversation.updated_at = datetime.now(timezone.utc)
        conversation.selected_teaching_id = selected.id if selected else None
        db.add(Message(conversation_id=conversation.id, role="user", content=message, metadata_json={"analysis": analysis.model_dump()}))
        db.add(Message(conversation_id=conversation.id, role="assistant", content=generation.interpretation, metadata_json={"quote_id": selected.id if selected else None}))
        db.add(InteractionRecord(profile_id=profile_id, conversation_id=conversation.id, themes=analysis.themes))
        db.add(ActionItem(profile_id=profile_id, conversation_id=conversation.id, text=generation.action.action, reason=generation.action.reason))
        db.add(AIRequestTrace(
            request_id=str(uuid.uuid4()), profile_id=profile_id, conversation_id=conversation.id, operation="mentor_continue",
            model=get_settings().gemini_model, candidate_ids=sorted(candidates), selected_quote_id=selected.id if selected else None,
            safety_status="none", metadata_json={"analysis": analysis.model_dump(), "active_reflection_goal": context["profile"].get("active_reflection_goal")},
        ))
        db.commit()
        return MentorResponse(
            conversation_id=conversation.id, round=max(1, conversation.rounds_used), understanding=generation.understanding,
            teaching=teaching_payload(selected), interpretation=generation.interpretation, reflection_question=generation.reflection_question,
            challenge=generation.challenge, action=generation.action, trust=trust_panel(selected, len(candidates), candidates),
        )

    def continue_challenge(self, db: Session, profile_id: str, conversation_id: str, user_response: str, assessment: TextAssessment | None = None) -> ChallengeResponse:
        conversation = db.scalar(select(Conversation).where(Conversation.id == conversation_id, Conversation.profile_id == profile_id))
        if not conversation:
            raise ValueError("Conversation not found")
        if conversation.risk_flag:
            raise ValueError("Challenge unavailable for a safety-flagged conversation")

        rounds = list(
            db.scalars(
                select(ChallengeRound)
                .where(ChallengeRound.conversation_id == conversation_id)
                .order_by(ChallengeRound.round_number)
            ).all()
        )
        if not rounds:
            raise RuntimeError("Challenge conversation has no starting round")
        if len(rounds) >= 3:
            raise RuntimeError("Challenge is limited to 3 rounds")

        assessment = assessment or self.assess_text(user_response)
        previous = rounds[-1]
        previous.user_response = user_response

        selected = None
        if conversation.selected_teaching_id:
            selected = db.scalar(select(Teaching).where(Teaching.id == conversation.selected_teaching_id))

        prompt = {
            "original_problem": conversation.current_problem,
            "belief": previous.belief,
            "round_history": _history_for_challenge(rounds),
            "latest_user_response": user_response,
            "relevant_teaching": {
                "id": selected.id,
                "themes": selected.themes,
                "context": selected.context,
            } if selected else None,
            "round_number": len(rounds) + 1,
        }

        # One Gemini call handles both safety assessment and Socratic generation at the API layer.
        if assessment.risk.risk_level in {"high", "immediate"}:
            raise RuntimeError("SAFETY_TRIGGERED")

        generated = self.gemini.generate(
            system_instruction=CHALLENGE_SYSTEM,
            prompt="Return JSON only:\n" + compact_json(prompt),
            schema=ChallengeGeneration,
        )

        round_no = len(rounds) + 1
        new_round = ChallengeRound(
            conversation_id=conversation_id,
            round_number=round_no,
            belief=previous.belief,
            assumption=generated.assumption,
            challenge_question=generated.question,
            user_response=None,
            reflection=generated.reflection,
            next_step=generated.next_step,
            teaching_id=selected.id if selected else None,
        )
        db.add(new_round)
        conversation.rounds_used = round_no
        conversation.updated_at = datetime.now(timezone.utc)
        if round_no == 3:
            conversation.completed_at = datetime.now(timezone.utc)
            db.add(
                ActionItem(
                    profile_id=profile_id,
                    conversation_id=conversation.id,
                    text=generated.next_step,
                    reason="Concrete next step from the completed reflection exercise.",
                )
            )
        db.commit()

        return ChallengeResponse(
            conversation_id=conversation_id,
            round=round_no,
            assumption=generated.assumption,
            question=generated.question,
            reflection=generated.reflection,
            next_step=generated.next_step,
            action=ActionPayload(action=generated.next_step, reason="Concrete next step from the reflection") if round_no == 3 else None,
            completed=round_no == 3,
            trust=trust_panel(selected, 1 if selected else 0, {selected.id} if selected else set()) if selected else None,
        )
