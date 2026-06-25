from __future__ import annotations

import json
from dataclasses import dataclass
from urllib import error, request

from ..core.config import settings
from ..core.constants import ACTION_VERBS
from ..utils.text_cleaning import normalize_spaces, split_items


@dataclass
class EnhancementResult:
    summary: str
    bullets: list[str]
    keywords: list[str]


def _extract_keywords(job_description: str, top_n: int = 8) -> list[str]:
    tokens = split_items(job_description.replace("/", ","))
    if not tokens:
        return []
    words: list[str] = []
    for item in tokens:
        words.extend([word.lower() for word in item.split() if len(word) > 2])
    seen: list[str] = []
    for word in words:
        if word not in seen:
            seen.append(word)
    return seen[:top_n]


def _prefix_with_action_verb(text: str, index: int) -> str:
    text = normalize_spaces(text)
    if not text:
        return ""
    lowered = text.lower()
    if any(lowered.startswith(verb) for verb in ACTION_VERBS):
        return text[0].upper() + text[1:]
    verb = ACTION_VERBS[index % len(ACTION_VERBS)].capitalize()
    return f"{verb} {text[0].lower() + text[1:] if len(text) > 1 else text.lower()}"


def local_enhance_summary(summary: str, target_role: str, job_description: str) -> str:
    summary = normalize_spaces(summary)
    keywords = ", ".join(_extract_keywords(job_description, 5))
    if summary:
        base = summary.rstrip(".")
        if target_role.strip():
            base = f"{base}. Targeting {target_role.strip()} roles"
        if keywords:
            base = f"{base} with strengths in {keywords}"
        return base + "."
    return f"Results-driven {target_role.strip() or 'professional'} with strengths in {keywords or 'delivery, collaboration, and quality'}."


def local_enhance_bullets(bullets: list[str], job_description: str = "") -> list[str]:
    keywords = _extract_keywords(job_description, 5)
    enhanced: list[str] = []
    for index, bullet in enumerate(bullets):
        if not bullet.strip():
            continue
        text = _prefix_with_action_verb(bullet, index)
        if keywords and not any(keyword in text.lower() for keyword in keywords):
            text = f"{text} while aligning with {keywords[0]} goals"
        enhanced.append(text)
    return enhanced


def _chat_completions(messages: list[dict[str, str]]) -> str:
    if not settings.openai_api_key:
        raise RuntimeError("Missing OPENAI_API_KEY")

    url = settings.openai_base_url.rstrip("/") + "/chat/completions"
    payload = json.dumps(
        {
            "model": settings.openai_model,
            "messages": messages,
            "temperature": 0.2,
        }
    ).encode("utf-8")
    req = request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.openai_api_key}",
        },
        method="POST",
    )
    with request.urlopen(req, timeout=45) as response:
        data = json.loads(response.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]


def enhance_resume(summary: str, bullets: list[str], target_role: str, job_description: str) -> EnhancementResult:
    if settings.openai_api_key:
        prompt = (
            "Return JSON with keys summary, bullets, keywords. "
            "Improve the resume summary and bullets for clarity, impact, and ATS relevance. "
            f"Target role: {target_role}. Job description: {job_description}. Current summary: {summary}. "
            f"Bullets: {bullets}"
        )
        try:
            content = _chat_completions(
                [
                    {"role": "system", "content": "You are a resume optimization assistant."},
                    {"role": "user", "content": prompt},
                ]
            )
            parsed = json.loads(content)
            return EnhancementResult(
                summary=parsed.get("summary", local_enhance_summary(summary, target_role, job_description)),
                bullets=parsed.get("bullets", local_enhance_bullets(bullets, job_description)),
                keywords=parsed.get("keywords", _extract_keywords(job_description)),
            )
        except Exception:
            pass

    return EnhancementResult(
        summary=local_enhance_summary(summary, target_role, job_description),
        bullets=local_enhance_bullets(bullets, job_description),
        keywords=_extract_keywords(job_description),
    )
