from __future__ import annotations

from datetime import datetime, timezone
import re
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import AIRequestTrace, ActionItem, ChallengeRound, Conversation, InteractionRecord, Message, Profile, Teaching
from app.schemas import ActionPayload, ChallengeGeneration, ChallengeResponse, MentorGeneration, MentorResponse, ProblemAnalysis, TextAssessment, TrustPanel
from app.services.context import build_context
from app.services.gemini import GeminiService, compact_json
from app.services.prompts import CHALLENGE_SYSTEM, MASTER_SYSTEM, TEXT_ASSESSMENT_SYSTEM
from app.services.retrieval import looks_like_letter, terms_from_analysis


class SourceGuardError(RuntimeError):
    pass


class ChallengeLimitError(RuntimeError):
    pass


EXPECTED_ONBOARDING_KEYS = {
    "profession",
    "age",
    "matters_most",
    "troubling_most",
    "problem_approach",
    "improve",
}

# Canonical source material must never be silently fabricated inside AI-written fields.
ATTRIBUTION_PATTERNS = [
    r"\b(?:swami\s+)?vivekananda\s+(?:said|says|taught|wrote|writes|declared|explained|believed|once said)\b",
    r"\bas\s+(?:swami\s+)?vivekananda\s+(?:said|taught|wrote|explained|put it)\b",
    r"\baccording to\s+(?:swami\s+)?vivekananda\b",
    r"\bin the words of\s+(?:swami\s+)?vivekananda\b",
    r"\b(?:swami\s+)?vivekananda\s*:\s*",
    r"\bquote from\s+(?:swami\s+)?vivekananda\b",
]
ATTRIBUTION_RE = re.compile("|".join(ATTRIBUTION_PATTERNS), re.IGNORECASE)
MIN_QUOTED_CHARS = 20
_CURLY_QUOTE_RE = re.compile(r"\u201c([^\u201c\u201d\n]+)\u201d")


def _quoted_spans(text: str) -> list[str]:
    """Return properly paired quoted spans.

    Straight quotes are paired sequentially per line (1st with 2nd, 3rd with 4th, ...) so the text between
    one quotation's closing mark and the next quotation's opening mark is never mistaken for a quotation.
    """
    spans = [m.group(1) for m in _CURLY_QUOTE_RE.finditer(text)]
    for line in text.splitlines():
        parts = line.split('"')
        # parts[1], parts[3], ... are the inside of paired quotes (an unmatched trailing quote is ignored).
        for i in range(1, len(parts) - 1, 2):
            spans.append(parts[i])
    return spans


def _norm_quote(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().strip(".,;:!?-\u2014 ").casefold()


def has_long_unsourced_quote(text: str, user_text: str = "") -> bool:
    """True when the AI text contains a long quotation that is not the user's own wording."""
    user_norm = _norm_quote(user_text)
    for span in _quoted_spans(text):
        if len(span.strip()) < MIN_QUOTED_CHARS:
            continue
        # Echoing the user's own words back to them is reflective listening, not a fabricated source quote.
        if user_norm and _norm_quote(span) in user_norm:
            continue
        return True
    return False


PREVIEW_WORDS = 90


def _preview(text: str, max_words: int = PREVIEW_WORDS) -> str:
    """First ~max_words words of the exact canonical text, cut at a sentence end where possible (display aid only)."""
    words = text.split()
    if len(words) <= max_words:
        return text
    cut = " ".join(words[:max_words])
    end = max(cut.rfind(". "), cut.rfind("? "), cut.rfind("! "))
    return (cut[: end + 1] if end > len(cut) // 2 else cut) + " …"


def teaching_payload(t: Teaching | None):
    if not t:
        return None
    return {
        "id": t.id,
        "quote": t.quote,
        "word_count": len(t.quote.split()),
        "preview": _preview(t.quote),
        "is_letter": looks_like_letter(t.quote),
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
        source_note=(
            None
            if selected
            else "No sufficiently relevant organiser-provided teaching was found for this situation; no teaching is attributed."
        ),
    )


def validate_quote_id(quote_id: str | None, candidate_ids: set[str]) -> str | None:
    if quote_id is None:
        return None
    if quote_id not in candidate_ids:
        raise SourceGuardError("Gemini returned a teaching ID that was not in the supplied candidate set")
    return quote_id


def validate_ai_written_text(*texts: str, user_text: str = "") -> None:
    combined = "\n".join(t or "" for t in texts)
    if ATTRIBUTION_RE.search(combined) or has_long_unsourced_quote(combined, user_text):
        raise SourceGuardError("AI-generated text attempted to present source material or an attribution as a quotation")


def _user_text_from_context(context: dict) -> str:
    """The user's own words in this request (current message and earlier user turns)."""
    parts = [context.get("current_problem") or ""]
    parts += [m.get("content") or "" for m in context.get("conversation_history", []) if m.get("role") == "user"]
    return "\n".join(parts)


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

    def _mentor_generation(self, context: dict, *, correction: bool = False) -> MentorGeneration:
        prompt = (
            "Return JSON only for the following mentor context. Use the six onboarding dimensions as real context, "
            "but do not return bookkeeping fields proving that you used them. If candidate_teachings is empty, "
            "set teaching.quote_id to null and do not mention or invent any Vivekananda quotation.\n"
            + compact_json(context)
        )
        if correction:
            prompt = (
                "Your previous draft violated source-grounding rules. Regenerate it. Do NOT include any quoted text "
                "or attribution to Swami Vivekananda in AI-written fields. Return only a candidate quote_id, or null "
                "when no candidate is relevant.\n" + compact_json(context)
            )
        return self.gemini.generate(
            system_instruction=MASTER_SYSTEM,
            prompt=prompt,
            schema=MentorGeneration,
        )

    def _generate_clean_mentor(self, context: dict, candidate_ids: set[str]) -> MentorGeneration:
        last_error: Exception | None = None
        for correction in (False, True):
            try:
                generation = self._mentor_generation(context, correction=correction)
                # Validate every AI-written field before allowing it into the persisted response.
                validate_ai_written_text(
                    generation.understanding,
                    generation.interpretation,
                    generation.reflection_question,
                    generation.challenge.assumption,
                    generation.challenge.question,
                    generation.action.action,
                    generation.action.reason,
                    user_text=_user_text_from_context(context),
                )
                validate_quote_id(generation.teaching.quote_id, candidate_ids)
                return generation
            except SourceGuardError as exc:
                last_error = exc
        raise SourceGuardError(str(last_error or "Gemini output failed source-grounding validation"))

    def _persist_generation(
        self,
        db: Session,
        *,
        conversation: Conversation,
        profile_id: str,
        message: str,
        analysis: ProblemAnalysis,
        generation: MentorGeneration,
        context: dict,
    ) -> MentorResponse:
        candidates = {item["id"] for item in context["candidate_teachings"]}
        quote_id = validate_quote_id(generation.teaching.quote_id, candidates)
        selected = db.get(Teaching, quote_id) if quote_id else None
        if quote_id and selected is None:
            raise SourceGuardError("Selected teaching ID does not exist in the canonical teaching database")

        conversation.problem_analysis = {**analysis.model_dump(), "status": "ready"}
        conversation.selected_teaching_id = selected.id if selected else None
        conversation.updated_at = datetime.now(timezone.utc)

        # Avoid duplicate user message if this is a retry of a persisted request.
        if not db.scalar(select(Message.id).where(Message.conversation_id == conversation.id, Message.role == "user", Message.content == message)):
            db.add(Message(conversation_id=conversation.id, role="user", content=message, metadata_json={"analysis": analysis.model_dump()}))
        db.add(
            Message(
                conversation_id=conversation.id,
                role="assistant",
                content=generation.interpretation,
                metadata_json={"quote_id": selected.id if selected else None, "mentor_generation": True},
            )
        )
        db.add(InteractionRecord(profile_id=profile_id, conversation_id=conversation.id, themes=analysis.themes))
        # Keep the initial round as the first Socratic challenge seed.
        existing_round = db.scalar(select(ChallengeRound.id).where(ChallengeRound.conversation_id == conversation.id, ChallengeRound.round_number == 1))
        if existing_round is None:
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
            conversation.rounds_used = 1
        db.add(
            ActionItem(
                profile_id=profile_id,
                conversation_id=conversation.id,
                text=generation.action.action,
                reason=generation.action.reason,
            )
        )
        db.add(
            AIRequestTrace(
                request_id=str(uuid.uuid4()),
                profile_id=profile_id,
                conversation_id=conversation.id,
                operation="mentor",
                model=get_settings().gemini_model,
                candidate_ids=sorted(candidates),
                selected_quote_id=selected.id if selected else None,
                safety_status="none",
                metadata_json={
                    "analysis": analysis.model_dump(),
                    "active_reflection_goal": context["profile"].get("active_reflection_goal"),
                    "personalization_fields": sorted(EXPECTED_ONBOARDING_KEYS),
                },
            )
        )
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

    def _prepare_conversation(self, db: Session, profile_id: str, message: str) -> Conversation:
        conversation = Conversation(
            profile_id=profile_id,
            current_problem=message,
            problem_analysis={"status": "pending"},
        )
        db.add(conversation)
        db.flush()
        db.add(Message(conversation_id=conversation.id, role="user", content=message, metadata_json={}))
        db.commit()
        db.refresh(conversation)
        return conversation

    def create_turn(self, db: Session, profile_id: str, message: str, assessment: TextAssessment | None = None) -> MentorResponse:
        profile = db.get(Profile, profile_id)
        if not profile:
            raise ValueError("Profile not found")

        conversation = self._prepare_conversation(db, profile_id, message)
        try:
            assessment = assessment or self.assess_text(message)
            if assessment.risk.risk_level in {"high", "immediate"}:
                conversation.risk_flag = True
                db.commit()
                raise RuntimeError("SAFETY_TRIGGERED")
            analysis: ProblemAnalysis = assessment.analysis
            conversation.problem_analysis = analysis.model_dump()
            db.commit()

            context = build_context(db, profile_id=profile_id, current_problem=message, analysis=analysis, conversation=conversation)
            candidates = {item["id"] for item in context["candidate_teachings"]}
            generation = self._generate_clean_mentor(context, candidates)
            return self._persist_generation(db, conversation=conversation, profile_id=profile_id, message=message, analysis=analysis, generation=generation, context=context)
        except RuntimeError as exc:
            if str(exc) == "SAFETY_TRIGGERED":
                raise  # conversation is already flagged; it must not be offered for retry
            db.rollback()
            existing = db.get(Conversation, conversation.id)
            if existing:
                existing.problem_analysis = {**(existing.problem_analysis or {}), "status": "pending"}
                db.commit()
            raise
        except Exception:
            # Keep the persisted conversation/message so the frontend can offer Retry Reflection.
            db.rollback()
            existing = db.get(Conversation, conversation.id)
            if existing:
                existing.problem_analysis = {**(existing.problem_analysis or {}), "status": "pending"}
                db.commit()
            raise

    def retry_turn(self, db: Session, profile_id: str, conversation_id: str) -> MentorResponse:
        conversation = db.scalar(select(Conversation).where(Conversation.id == conversation_id, Conversation.profile_id == profile_id))
        if not conversation:
            raise ValueError("Conversation not found")
        if conversation.risk_flag:
            raise ValueError("Cannot retry a safety-flagged reflection")
        if conversation.completed_at is not None:
            raise ValueError("This reflection is already completed")
        has_assistant = db.scalar(select(Message.id).where(Message.conversation_id == conversation.id, Message.role == "assistant").limit(1))
        if has_assistant:
            raise ValueError("This reflection already has a generated response")
        return self._generate_for_existing_conversation(db, profile_id, conversation, conversation.current_problem)

    def _generate_for_existing_conversation(self, db: Session, profile_id: str, conversation: Conversation, message: str) -> MentorResponse:
        assessment = self.assess_text(message)
        if assessment.risk.risk_level in {"high", "immediate"}:
            conversation.risk_flag = True
            db.commit()
            raise RuntimeError("SAFETY_TRIGGERED")
        analysis = assessment.analysis
        conversation.problem_analysis = analysis.model_dump()
        db.commit()
        context = build_context(db, profile_id=profile_id, current_problem=message, analysis=analysis, conversation=conversation)
        candidates = {item["id"] for item in context["candidate_teachings"]}
        generation = self._generate_clean_mentor(context, candidates)
        # Remove a previous failed user message duplicate is handled in _persist_generation.
        return self._persist_generation(db, conversation=conversation, profile_id=profile_id, message=message, analysis=analysis, generation=generation, context=context)

    def continue_turn(self, db: Session, profile_id: str, conversation_id: str, message: str) -> MentorResponse:
        conversation = db.scalar(select(Conversation).where(Conversation.id == conversation_id, Conversation.profile_id == profile_id))
        if not conversation:
            raise ValueError("Conversation not found")
        if conversation.risk_flag:
            raise ValueError("Cannot continue a safety-flagged conversation")
        if conversation.completed_at is not None:
            raise ValueError("This reflection is already completed")

        # Persist the user's continuation before any provider call.
        db.add(Message(conversation_id=conversation.id, role="user", content=message, metadata_json={"pending": True}))
        conversation.current_problem = message
        conversation.updated_at = datetime.now(timezone.utc)
        db.commit()

        assessment = self.assess_text(message)
        if assessment.risk.risk_level in {"high", "immediate"}:
            conversation.risk_flag = True
            db.commit()
            raise RuntimeError("SAFETY_TRIGGERED")
        analysis = assessment.analysis
        context = build_context(db, profile_id=profile_id, current_problem=message, analysis=analysis, conversation=conversation)
        candidates = {item["id"] for item in context["candidate_teachings"]}
        generation = self._generate_clean_mentor(context, candidates)

        conversation.current_problem = message
        conversation.updated_at = datetime.now(timezone.utc)
        response = self._persist_generation(db, conversation=conversation, profile_id=profile_id, message=message, analysis=analysis, generation=generation, context=context)
        response.round = max(1, conversation.rounds_used)
        return response

    def continue_challenge(self, db: Session, profile_id: str, conversation_id: str, user_response: str, assessment: TextAssessment | None = None) -> ChallengeResponse:
        conversation = db.scalar(select(Conversation).where(Conversation.id == conversation_id, Conversation.profile_id == profile_id))
        if not conversation:
            raise ValueError("Conversation not found")
        if conversation.risk_flag:
            raise ValueError("Challenge unavailable for a safety-flagged conversation")

        rounds = list(db.scalars(select(ChallengeRound).where(ChallengeRound.conversation_id == conversation_id).order_by(ChallengeRound.round_number)).all())
        if not rounds:
            raise RuntimeError("Challenge conversation has no starting round")
        if len(rounds) >= 3:
            raise ChallengeLimitError("Challenge is limited to 3 rounds")

        previous = rounds[-1]
        previous.user_response = user_response
        db.commit()  # Persist the user's response even if Gemini is unavailable.

        assessment = assessment or self.assess_text(user_response)
        if assessment.risk.risk_level in {"high", "immediate"}:
            conversation.risk_flag = True
            db.commit()
            raise RuntimeError("SAFETY_TRIGGERED")

        selected = db.get(Teaching, conversation.selected_teaching_id) if conversation.selected_teaching_id else None
        prompt = {
            "original_problem": conversation.current_problem,
            "belief": previous.belief,
            "round_history": _history_for_challenge(rounds),
            "latest_user_response": user_response,
            "relevant_teaching": {"id": selected.id, "themes": selected.themes, "context": selected.context} if selected else None,
            "round_number": len(rounds) + 1,
        }

        last_error: Exception | None = None
        generated = None
        for correction in (False, True):
            try:
                challenge_prompt = "Return JSON only:\n" + compact_json(prompt)
                if correction:
                    challenge_prompt = (
                        "Regenerate without any quotations or attribution to Swami Vivekananda in AI-written fields. "
                        "Use the supplied teaching only as a principle. Return JSON only:\n" + compact_json(prompt)
                    )
                candidate = self.gemini.generate(system_instruction=CHALLENGE_SYSTEM, prompt=challenge_prompt, schema=ChallengeGeneration)
                validate_ai_written_text(
                    candidate.assumption, candidate.question, candidate.reflection, candidate.next_step,
                    user_text="\n".join([conversation.current_problem or "", user_response, *[r.user_response or "" for r in rounds]]),
                )
                generated = candidate
                break
            except SourceGuardError as exc:
                last_error = exc
        if generated is None:
            raise SourceGuardError(str(last_error or "Challenge output failed source-grounding validation"))

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
            db.add(ActionItem(profile_id=profile_id, conversation_id=conversation.id, text=generated.next_step, reason="Concrete next step from the completed reflection exercise."))
        db.add(
            AIRequestTrace(
                request_id=str(uuid.uuid4()),
                profile_id=profile_id,
                conversation_id=conversation.id,
                operation="challenge",
                model=get_settings().gemini_model,
                candidate_ids=[selected.id] if selected else [],
                selected_quote_id=selected.id if selected else None,
                safety_status="none",
                metadata_json={"round": round_no},
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
