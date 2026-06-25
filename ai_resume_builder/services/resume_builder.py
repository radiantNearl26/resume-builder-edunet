from __future__ import annotations

from . import __init__  # noqa: F401
from ..core.schemas import ResumeData


def join_nonempty(parts: list[str]) -> str:
    return "\n".join(part for part in parts if part.strip())


def build_resume_text(resume: ResumeData) -> str:
    lines: list[str] = []
    personal = resume.personal_info
    lines.append(personal.full_name)
    lines.append(" | ".join([personal.title, personal.location, personal.email, personal.phone]).strip(" |"))
    if personal.linkedin:
        lines.append(personal.linkedin)
    if personal.portfolio:
        lines.append(personal.portfolio)

    if resume.summary.strip():
        lines.extend(["", "SUMMARY", resume.summary.strip()])

    if resume.experience:
        lines.extend(["", "EXPERIENCE"])
        for item in resume.experience:
            header = f"{item.title} - {item.company} ({item.start_date} to {item.end_date or 'Present'})"
            lines.append(header)
            for bullet in item.bullets:
                if bullet.strip():
                    lines.append(f"- {bullet.strip()}")
            for bullet in item.achievements:
                if bullet.strip():
                    lines.append(f"- {bullet.strip()}")

    if resume.education:
        lines.extend(["", "EDUCATION"])
        for item in resume.education:
            lines.append(f"{item.degree} - {item.institution} ({item.start_date} to {item.end_date or 'Present'})")
            if item.coursework:
                lines.append(f"Coursework: {item.coursework}")

    if any([resume.skills.technical, resume.skills.tools, resume.skills.soft_skills]):
        lines.extend(["", "SKILLS"])
        if resume.skills.technical:
            lines.append("Technical: " + ", ".join(resume.skills.technical))
        if resume.skills.tools:
            lines.append("Tools: " + ", ".join(resume.skills.tools))
        if resume.skills.soft_skills:
            lines.append("Soft Skills: " + ", ".join(resume.skills.soft_skills))

    if resume.projects:
        lines.extend(["", "PROJECTS"])
        for item in resume.projects:
            detail_parts = [item.tech_stack, item.description, item.impact]
            lines.append(item.name)
            for part in detail_parts:
                if part.strip():
                    lines.append(f"- {part.strip()}")
            if item.link:
                lines.append(f"Link: {item.link}")

    if resume.certifications:
        lines.extend(["", "CERTIFICATIONS"])
        for item in resume.certifications:
            line = f"{item.name} - {item.issuer}".strip(" -")
            if item.date_obtained:
                line = f"{line} ({item.date_obtained})"
            lines.append(line)

    if resume.languages:
        lines.extend(["", "LANGUAGES", ", ".join(resume.languages)])
    if resume.awards:
        lines.extend(["", "AWARDS"])
        lines.extend([f"- {award}" for award in resume.awards])
    if resume.publications:
        lines.extend(["", "PUBLICATIONS"])
        lines.extend([f"- {publication}" for publication in resume.publications])

    return join_nonempty(lines)
