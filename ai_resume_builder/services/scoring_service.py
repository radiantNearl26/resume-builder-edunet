from __future__ import annotations

import re
from collections import Counter

import numpy as np
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from ..core.constants import ACTION_VERBS
from ..core.schemas import ResumeData
from .resume_builder import build_resume_text


def _tokenize(text: str) -> list[str]:
    return [token.lower() for token in re.findall(r"[A-Za-z][A-Za-z+.#-]{1,}", text)]


def _keyword_terms(text: str, top_n: int = 8) -> list[str]:
    tokens = [token for token in _tokenize(text) if token not in ENGLISH_STOP_WORDS]
    counts = Counter(tokens)
    return [term for term, _ in counts.most_common(top_n)]


def job_resume_similarity(resume_text: str, job_description: str) -> float:
    if not resume_text.strip() or not job_description.strip():
        return 0.0
    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform([resume_text, job_description])
    score = cosine_similarity(matrix[0], matrix[1])[0, 0]
    return float(np.clip(score, 0.0, 1.0))


def ats_quality_score(resume: ResumeData, job_description: str = "") -> dict[str, object]:
    resume_text = build_resume_text(resume)
    similarity = job_resume_similarity(resume_text, job_description)
    text_tokens = set(_tokenize(resume_text))
    quantified_bullets = 0
    action_bullets = 0

    for experience in resume.experience:
        for bullet in [*experience.bullets, *experience.achievements]:
            lowered = bullet.lower()
            if re.search(r"\d|%|\$", lowered):
                quantified_bullets += 1
            if any(lowered.startswith(verb) for verb in ACTION_VERBS):
                action_bullets += 1

    completeness = 0
    completeness += 1 if resume.summary.strip() else 0
    completeness += 1 if resume.education else 0
    completeness += 1 if resume.experience else 0
    completeness += 1 if any([resume.skills.technical, resume.skills.tools, resume.skills.soft_skills]) else 0
    completeness += 1 if resume.projects else 0
    completeness += 1 if resume.certifications else 0

    keyword_hits = 0
    missing_keywords: list[str] = []
    if job_description.strip():
        desired_terms = _keyword_terms(job_description)
        keyword_hits = sum(1 for term in desired_terms if term in text_tokens)
        missing_keywords = [term for term in desired_terms if term not in text_tokens]

    score = (
        similarity * 45
        + min(completeness, 6) * 8
        + min(action_bullets, 8) * 2.5
        + min(quantified_bullets, 8) * 2.5
        + min(keyword_hits, 8) * 2.5
    )
    score = float(np.clip(score, 0.0, 100.0))

    return {
        "ats_score": round(score, 1),
        "similarity": round(similarity * 100, 1),
        "completeness": completeness,
        "action_bullets": action_bullets,
        "quantified_bullets": quantified_bullets,
        "keyword_hits": keyword_hits,
        "missing_keywords": missing_keywords[:10],
    }
