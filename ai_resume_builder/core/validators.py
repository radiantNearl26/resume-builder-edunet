from __future__ import annotations

from datetime import date, datetime

from .schemas import ResumeData


def parse_date_value(value: str | date | None) -> date | None:
    if value in (None, "", "Present"):
        return None
    if isinstance(value, date):
        return value
    for fmt in ("%Y-%m-%d", "%Y-%m"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def validate_date_order(start_value: str | date | None, end_value: str | date | None) -> bool:
    start_date = parse_date_value(start_value)
    end_date = parse_date_value(end_value)
    if start_date is None or end_date is None:
        return True
    return start_date <= end_date


def validate_resume_dates(resume: ResumeData) -> list[str]:
    errors: list[str] = []
    for item in resume.education:
        if not validate_date_order(item.start_date, item.end_date):
            errors.append(f"Education entry at {item.institution} has invalid dates")
    for item in resume.experience:
        if not validate_date_order(item.start_date, item.end_date):
            errors.append(f"Experience entry at {item.company} has invalid dates")
    return errors


def validate_bullets(bullets: list[str]) -> list[str]:
    return [bullet.strip() for bullet in bullets if bullet and bullet.strip()]
