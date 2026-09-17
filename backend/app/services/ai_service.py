"""
Core AI prompt pipelines. All prompts instruct the model to ground its
answer strictly in the BNS section context retrieved from the RAG
knowledge base (app.services.rag_service.knowledge_base), and to return
structured JSON that maps directly onto our Pydantic schemas.
"""
from __future__ import annotations

import json
from datetime import date

from openai import AsyncOpenAI

from app.core.config import settings
from app.schemas.case import BNSPredictionResult
from app.schemas.petition import PetitionScanResult
from app.services.rag_service import knowledge_base

_client = AsyncOpenAI(
    api_key=settings.OPENAI_API_KEY or "sk-placeholder",
    base_url=settings.OPENAI_BASE_URL or None,
)

SYSTEM_DISCLAIMER = (
    "You are an AI legal-research assistant specialised in the Bharatiya Nyaya "
    "Sanhita (BNS), 2023. You ONLY use the BNS section context provided to you "
    "in the prompt — never invent section numbers. You always clarify that your "
    "output is preliminary AI analysis, not a substitute for a licensed advocate."
)


def _format_context(sections: list[dict]) -> str:
    if not sections:
        return "No matching BNS sections were found in the knowledge base."
    lines = []
    for s in sections:
        punishment = s.get("punishment") or "not specified in source data"
        imprisonment = s.get("imprisonment_term") or "not specified in source data"
        bailable = s.get("bailable") or "not specified in source data"
        cognizable = s.get("cognizable") or "not specified in source data"
        lines.append(
            f"- {s.get('section_number')} | {s.get('section_title')}: {s.get('description')} "
            f"| Punishment: {punishment} | Imprisonment: {imprisonment} "
            f"| Bailable: {bailable} | Cognizable: {cognizable}"
        )
    return "\n".join(lines)


CONTEXT_GAP_INSTRUCTION = (
    "IMPORTANT: Some BNS sections in the context above only include the raw section "
    "text (title + description) without a source value for punishment, imprisonment "
    "term, bailable, or cognizable status — these are marked 'not specified in source "
    "data'. In those cases, use your own accurate knowledge of the Bharatiya Nyaya "
    "Sanhita, 2023 (including its First Schedule of offence classifications) to fill "
    "in the correct punishment, imprisonment term, bailable/non-bailable status, and "
    "cognizable/non-cognizable status for that exact section number. Never leave these "
    "fields blank or say 'not specified' in your JSON output — always give your best, "
    "legally accurate answer."
)


async def _chat_json(system: str, user: str) -> dict:
    response = await _client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        response_format={"type": "json_object"},
        temperature=0.2,
        extra_body={"reasoning_effort": "low"},  # minimize Gemini's internal "thinking" latency
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    if not response or not getattr(response, "choices", None):
        raise RuntimeError("The AI model returned an empty response. Please try again.")

    choice = response.choices[0]
    message = getattr(choice, "message", None)
    content = getattr(message, "content", None) if message else None

    if not content:
        finish_reason = getattr(choice, "finish_reason", "unknown")
        raise RuntimeError(
            f"The AI model did not return usable content (reason: {finish_reason}). "
            "Please try rephrasing your input and try again."
        )
    return json.loads(content)


async def predict_bns_sections(case_summary: str, case_category: str | None) -> BNSPredictionResult:
    context_sections = knowledge_base.retrieve(case_summary, k=5)
    context_text = _format_context(context_sections)

    user_prompt = f"""
Case summary provided by the user:
\"\"\"{case_summary}\"\"\"

Optional category hint: {case_category or "none provided"}

Relevant BNS sections retrieved from the knowledge base (use ONLY these,
do not invent section numbers not listed here):
{context_text}

{CONTEXT_GAP_INSTRUCTION}

Return a JSON object with this exact shape:
{{
  "applicable_sections": [
    {{
      "section_number": string,
      "section_title": string,
      "description": string,
      "punishment": string,
      "imprisonment_term": string,
      "bailable": "Bailable" | "Non-Bailable",
      "cognizable": "Cognizable" | "Non-Cognizable",
      "relevance_score": number between 0 and 1
    }}
  ],
  "overall_severity": "Low" | "Moderate" | "High" | "Severe",
  "severity_explanation": string,
  "recommended_next_steps": [string, ...]
}}
Only include sections that are genuinely relevant, ranked by relevance_score descending.
Do NOT include purely definitional, procedural, or general-explanation sections
(e.g. sections titled "Definitions", "General explanations", "Short title",
"Punishments" as a general chapter heading, etc.) — only include sections that
define an actual criminal offence applicable to these facts, along with its
punishment.
"""
    data = await _chat_json(SYSTEM_DISCLAIMER, user_prompt)
    data.setdefault("applicable_sections", [])
    data.setdefault("recommended_next_steps", [])
    return BNSPredictionResult(**data)


async def scan_petition(petition_text: str) -> PetitionScanResult:
    context_sections = knowledge_base.retrieve(petition_text, k=5)
    context_text = _format_context(context_sections)

    user_prompt = f"""
Analyse the following legal petition/complaint draft for completeness,
argument strength, formatting, and correct use of BNS sections.

Petition text:
\"\"\"{petition_text[:12000]}\"\"\"

Relevant BNS sections for cross-checking citations:
{context_text}

{CONTEXT_GAP_INSTRUCTION}

Return a JSON object with this exact shape:
{{
  "validity_score": integer 0-100,
  "summary": string,
  "issues": [
    {{
      "category": "Missing Point" | "Weak Argument" | "Formatting" | "Legal Citation",
      "severity": "Low" | "Medium" | "High",
      "description": string,
      "suggestion": string
    }}
  ],
  "missing_sections_detected": [string, ...],
  "strengths": [string, ...]
}}
"""
    data = await _chat_json(SYSTEM_DISCLAIMER, user_prompt)
    data.setdefault("issues", [])
    data.setdefault("missing_sections_detected", [])
    data.setdefault("strengths", [])
    return PetitionScanResult(**data)


async def generate_petition_draft(
    petitioner_name: str,
    respondent_name: str,
    court_name: str,
    case_summary: str,
    relief_sought: str,
    applicable_sections: list[str] | None,
) -> str:
    context_sections = knowledge_base.retrieve(case_summary, k=4)
    context_text = _format_context(context_sections)
    sections_hint = ", ".join(applicable_sections) if applicable_sections else "auto-detect from context"
    today_str = date.today().strftime("%d %B %Y")  # e.g. "09 September 2026"
    current_year = date.today().year

    user_prompt = f"""
Draft a formal legal petition/complaint in professional Indian legal
drafting style (cause title, parties, facts, grounds, prayer, verification)
using the details below. Cite relevant BNS sections where appropriate.

Court: {court_name}
Petitioner: {petitioner_name}
Respondent: {respondent_name}
Relief sought: {relief_sought}
Applicable sections hint: {sections_hint}

Case facts:
\"\"\"{case_summary}\"\"\"

Relevant BNS sections for citation:
{context_text}

{CONTEXT_GAP_INSTRUCTION}

DATE AND FACTUAL ACCURACY — CRITICAL:
- Today's actual real-world date is {today_str} (year {current_year}). Use this
  exact date/year for the "PLACE / DATE" filing line, the "VERIFICATION ... this
  ___ day of ___, {current_year}" line, and the petition/complaint number's year
  (e.g. "NO. _____ OF {current_year}") — NEVER guess or default to any other
  year (do not write 2024 or any year other than {current_year} unless that
  year was explicitly given as the incident date in the case facts).
- Use ONLY the date(s), names, and factual details that are explicitly
  stated in the "Case facts" above for the INCIDENT date. Do NOT invent,
  guess, assume, or infer any incident date that was not explicitly given.
- If the incident date, address, or any other specific fact was NOT
  provided in the case facts, leave it as a clearly marked placeholder
  in square brackets, e.g. "[Insert Date of Incident]" — never fill it
  with a plausible-sounding but fabricated date.

Write the full petition as plain text (no markdown headers, use
traditional numbered paragraph legal formatting). End with a
verification clause and a clear note that this is an AI-generated
draft requiring review by a licensed advocate before filing.
"""
    response = await _client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        temperature=0.3,
        extra_body={"reasoning_effort": "low"},
        messages=[
            {"role": "system", "content": SYSTEM_DISCLAIMER},
            {"role": "user", "content": user_prompt},
        ],
    )
    return _extract_reply_text(response)


def _extract_reply_text(response) -> str:
    """
    Safely pulls the assistant's text out of a chat completion response.
    Some Gemini responses can come back with an empty/blocked choice
    (e.g. safety filtering, or a "thinking-only" turn with no visible
    content) — in that case `message` or `message.content` can be None,
    which would otherwise crash with an AttributeError.
    """
    if not response or not getattr(response, "choices", None):
        return "I couldn't generate a response for that. Could you please rephrase your question?"

    choice = response.choices[0]
    message = getattr(choice, "message", None)
    content = getattr(message, "content", None) if message else None

    if not content:
        finish_reason = getattr(choice, "finish_reason", "unknown")
        return (
            "I wasn't able to generate a response for that message "
            f"(reason: {finish_reason}). Please try rephrasing your question."
        )
    return content


async def chat_reply(history: list[dict], user_message: str) -> tuple[str, list[str]]:
    """
    Conversational BNS Q&A. `history` is a list of {"role": "user"/"assistant", "content": str}.
    Returns (reply_text, referenced_section_numbers).
    """
    context_sections = knowledge_base.retrieve(user_message, k=4)
    context_text = _format_context(context_sections)
    referenced = [s.get("section_number", "") for s in context_sections if s.get("section_number")]

    messages = [{"role": "system", "content": SYSTEM_DISCLAIMER + "\n\nRelevant BNS context:\n" + context_text}]
    messages.extend(history[-10:])  # keep last 10 turns for context window efficiency
    messages.append({"role": "user", "content": user_message})

    response = await _client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        temperature=0.3,
        extra_body={"reasoning_effort": "low"},
        messages=messages,
    )
    reply = _extract_reply_text(response)
    return reply, referenced