"""
AI Service — Multi-provider LLM integration supporting Groq (primary) and Google Gemini.

Default Groq model: `llama-3.3-70b-versatile`
Provides:
  1. parse_resume_text()   → structured JSON from raw resume text
  2. score_ats()           → ATS compatibility score + feedback
  3. tailor_resume()       → modified resume JSON targeted at a JD + changes summary
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, Tuple

from app.core.config import settings
from app.schemas.dto import ATSScoreResponse, ParsedResume

logger = logging.getLogger(__name__)


def _clean_job_description(jd: str, max_chars: int = 5000) -> str:
    """
    Strip HTML tags, decode common entities, and truncate excessive legal/boilerplate
    text so LLM prompts stay lean and strictly within model TPM limits.
    """
    if not jd:
        return ""
    # Strip HTML tags
    cleaned = re.sub(r"<[^>]+>", " ", jd)
    # Decode HTML entities
    cleaned = (
        cleaned.replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&#39;", "'")
        .replace("&nbsp;", " ")
    )
    # Collapse multiple whitespaces
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned[:max_chars]


def _extract_json(text: str) -> Dict[str, Any]:
    """
    Robustly extract the first JSON object from an LLM response,
    stripping markdown fences, trailing commas, etc.
    """
    # Strip markdown code fences
    cleaned = re.sub(r"```(?:json)?\s*", "", text)
    cleaned = re.sub(r"```", "", cleaned)
    cleaned = cleaned.strip()

    # Remove trailing commas before } or ] (common LLM mistake)
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)

    # Find the outermost { ... }
    start = cleaned.find("{")
    if start == -1:
        raise ValueError(f"No JSON object found in LLM response: {text[:200]}")

    depth = 0
    end = start
    for i in range(start, len(cleaned)):
        if cleaned[i] == "{":
            depth += 1
        elif cleaned[i] == "}":
            depth -= 1
        if depth == 0:
            end = i + 1
            break

    return json.loads(cleaned[start:end])


async def _call_llm_json(prompt: str, system_prompt: str = "You are a professional JSON-only career intelligence assistant.") -> Dict[str, Any]:
    """
    Dispatch request to Groq (default) or Gemini based on configuration.
    Guarantees returning a parsed JSON dictionary.
    """
    use_groq = (
        settings.LLM_PROVIDER.lower() == "groq"
        or (bool(settings.GROQ_API_KEY) and not settings.GEMINI_API_KEY)
    )

    if use_groq:
        if not settings.GROQ_API_KEY or settings.GROQ_API_KEY.startswith("your_"):
            raise ValueError(
                "GROQ_API_KEY is not configured or is using placeholder text. "
                "Please add your actual Groq API key in ai_job_platform/.env"
            )

        from groq import AsyncGroq

        groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        fallback_models = [settings.GROQ_MODEL, "openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]
        # Deduplicate while preserving order
        candidate_models = list(dict.fromkeys(fallback_models))

        last_error = None
        for model_name in candidate_models:
            try:
                logger.info("Calling Groq LLM using model: %s", model_name)
                response = await groq_client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_prompt + "\nCRITICAL: Respond ONLY with a valid JSON object."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.1,
                    response_format={"type": "json_object"},
                )
                raw_text = response.choices[0].message.content or "{}"
                return _extract_json(raw_text)
            except Exception as err:
                logger.warning("Groq model %s encountered issue (%s), attempting next candidate...", model_name, err)
                last_error = err
                continue

        if last_error:
            raise last_error

    # Fallback to Google Gemini
    if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY.startswith("your_"):
        raise ValueError(
            "Neither GROQ_API_KEY nor GEMINI_API_KEY is configured. "
            "Please provide a valid GROQ_API_KEY in ai_job_platform/.env"
        )

    from google import genai
    from google.genai.types import GenerateContentConfig

    logger.info("Calling Google Gemini LLM fallback")
    gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
    full_prompt = f"{system_prompt}\n\nCRITICAL: Respond ONLY with a valid JSON object.\n\n{prompt}"
    response = await gemini_client.aio.models.generate_content(
        model="gemini-2.0-flash",
        contents=full_prompt,
        config=GenerateContentConfig(
            temperature=0.1,
            top_p=0.95,
            max_output_tokens=8192,
        ),
    )
    return _extract_json(response.text or "{}")


# ─────────────────────────────────────────────────────────────────────────
#  1. Resume Parsing
# ─────────────────────────────────────────────────────────────────────────

_PARSE_PROMPT = """You are an expert resume parser. Given the raw text extracted
from a candidate's resume, produce a SINGLE valid JSON object matching the
schema below. Return ONLY the JSON — no commentary, no markdown fences.

**Schema:**
{
  "personal_info": {
    "full_name": "string|null",
    "email": "string|null",
    "phone": "string|null",
    "location": "string|null",
    "linkedin": "string|null",
    "github": "string|null",
    "portfolio": "string|null",
    "summary": "string|null"
  },
  "career_preferences": {
    "desired_roles": ["string"],
    "desired_locations": ["string"],
    "job_type": "string|null",
    "expected_salary": "string|null",
    "notice_period": "string|null"
  },
  "education": [
    {
      "institution": "string|null",
      "degree": "string|null",
      "field_of_study": "string|null",
      "start_date": "string|null",
      "end_date": "string|null",
      "grade": "string|null",
      "description": "string|null"
    }
  ],
  "experience": [
    {
      "company": "string|null",
      "title": "string|null",
      "location": "string|null",
      "start_date": "string|null",
      "end_date": "string|null",
      "is_current": false,
      "bullet_points": ["string"]
    }
  ],
  "projects": [
    {
      "name": "string|null",
      "description": "string|null",
      "technologies": ["string"],
      "url": "string|null",
      "bullet_points": ["string"]
    }
  ],
  "skills": ["string"],
  "certifications": [
    {
      "name": "string|null",
      "issuer": "string|null",
      "date": "string|null",
      "url": "string|null"
    }
  ],
  "achievements": ["string"],
  "resume_meta": {
    "file_name": null,
    "file_type": null,
    "extraction_method": null,
    "parsed_at": null,
    "confidence": null
  }
}

**Instructions:**
- Extract ALL information you can find.
- If a field is not present in the text, set it to null or an empty list.
- For bullet_points, preserve original technical achievements.
- Do NOT invent or hallucinate data.

**Resume Text:**
"""


async def parse_resume_text(raw_text: str) -> ParsedResume:
    """Send raw resume text to Groq/Gemini and return a validated ParsedResume."""
    prompt = _PARSE_PROMPT + raw_text
    raw_json = await _call_llm_json(
        prompt=prompt,
        system_prompt="You are an expert resume parsing engine that returns strict JSON profiles."
    )
    return ParsedResume.model_validate(raw_json)


# ─────────────────────────────────────────────────────────────────────────
#  2. ATS Scoring
# ─────────────────────────────────────────────────────────────────────────

_ATS_PROMPT = """You are an expert ATS (Applicant Tracking System) evaluator.

Given a candidate's structured profile JSON and a job description, produce a
SINGLE valid JSON object with this exact schema — no commentary, no markdown:

{
  "ats_score": <number 0-100>,
  "missing_keywords": ["keyword1", "keyword2"],
  "strengths": ["strength1", "strength2"],
  "fixes": ["actionable fix 1", "actionable fix 2"]
}

**Scoring rubric:**
- Keyword match density (40%)
- Skills alignment (25%)
- Experience relevance (20%)
- Education fit (15%)

**Profile JSON:**
<<PROFILE>>

**Job Description:**
<<JD>>
"""


async def score_ats(
    profile_json: Dict[str, Any], job_description: str
) -> ATSScoreResponse:
    """Score a resume against a JD via Groq/Gemini."""
    cleaned_jd = _clean_job_description(job_description)
    prompt = (
        _ATS_PROMPT.replace("<<PROFILE>>", json.dumps(profile_json, indent=2))
        .replace("<<JD>>", cleaned_jd)
    )
    raw_json = await _call_llm_json(
        prompt=prompt,
        system_prompt="You are an advanced Applicant Tracking System (ATS) evaluation algorithm."
    )
    return ATSScoreResponse.model_validate(raw_json)


# ─────────────────────────────────────────────────────────────────────────
#  3. Resume Tailoring
# ─────────────────────────────────────────────────────────────────────────

_TAILOR_PROMPT = """You are a Senior Technical Resume Architect. Your goal is to maximize ATS compatibility while maintaining a high-density, professional technical profile.

**STRICT DIRECTIVES:**
1. **NO DELETION:** Do not remove any experience, project, or education entries. Every piece of history must remain.
2. **METRIC PRESERVATION:** Strictly preserve all quantitative data. These are your strongest selling points.
3. **ADVANCED TAILORING:** Rewrite bullet points to lead with strong action verbs. Integrate keywords from the JD naturally into existing descriptions.
4. **SKILL RANKING:** Move the most relevant skills to the front of the list, but do not delete the others.
5. **TONE:** Use a sophisticated, senior engineering tone. Avoid generic "fluff."

**OUTPUT SCHEMA:**
Produce a SINGLE valid JSON object with this exact schema:
{
  "tailored_profile": { ... the complete structured resume JSON following the original schema ... },
  "changes_summary": "A 2-3 sentence summary of the key modifications made to align with the job description."
}

**Original Profile JSON:**
<<PROFILE>>

**Target Job Description:**
<<JD>>
"""


async def tailor_resume(
    profile_json: Dict[str, Any], job_description: str
) -> Tuple[Dict[str, Any], str]:
    """Return a JD-tailored version of the resume JSON and a summary of changes."""
    cleaned_jd = _clean_job_description(job_description)
    prompt = (
        _TAILOR_PROMPT.replace("<<PROFILE>>", json.dumps(profile_json, indent=2))
        .replace("<<JD>>", cleaned_jd)
    )
    raw_json = await _call_llm_json(
        prompt=prompt,
        system_prompt="You are a Senior Resume Tailoring Specialist optimizing candidate profiles for job descriptions."
    )
    
    # Fallback in case the LLM doesn't wrap with tailored_profile
    tailored_profile = raw_json.get("tailored_profile", raw_json if "skills" in raw_json else profile_json)
    changes_summary = raw_json.get("changes_summary", "Optimized keywords and bullet points to match target job description.")
    
    return tailored_profile, changes_summary
