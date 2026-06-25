from __future__ import annotations

from datetime import date
from pathlib import Path
import sys

import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ai_resume_builder.core.schemas import (
    CertificationEntry,
    EducationEntry,
    ExperienceEntry,
    PersonalInfo,
    ProjectEntry,
    ResumeData,
    Skills,
)
from ai_resume_builder.core.validators import validate_resume_dates
from ai_resume_builder.export.pdf_reportlab import generate_resume_pdf
from ai_resume_builder.services.llm_service import enhance_resume
from ai_resume_builder.services.resume_builder import build_resume_text
from ai_resume_builder.services.scoring_service import ats_quality_score
from ai_resume_builder.utils.text_cleaning import split_items


st.set_page_config(page_title="AI Resume Builder", page_icon="🧾", layout="wide")


def init_state() -> None:
    defaults = {
        "personal_info": {
            "full_name": "",
            "email": "",
            "phone": "",
            "location": "",
            "linkedin": "",
            "portfolio": "",
            "title": "",
        },
        "summary": "",
        "education": [
            {
                "degree": "",
                "institution": "",
                "location": "",
                "start_date": "",
                "end_date": "",
                "gpa": "",
                "coursework": "",
            }
        ],
        "experience": [
            {
                "title": "",
                "company": "",
                "location": "",
                "start_date": "",
                "end_date": "",
                "bullets": [""],
                "achievements": [""],
            }
        ],
        "skills": {
            "technical": [],
            "tools": [],
            "soft_skills": [],
        },
        "projects": [],
        "certifications": [],
        "languages": [],
        "awards": [],
        "publications": [],
        "target_role": "",
        "job_description": "",
        "template_name": "modern",
        "enhanced_summary": "",
        "enhanced_bullets": [],
        "last_score": {},
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def date_to_iso(value: date | None) -> str:
    return value.isoformat() if value else ""


def csv_to_list(value: str) -> list[str]:
    return split_items(value)


def render_personal_info() -> None:
    st.subheader("Personal Information")
    cols = st.columns(2)
    with cols[0]:
        st.session_state.personal_info["full_name"] = st.text_input("Full name", st.session_state.personal_info["full_name"])
        st.session_state.personal_info["title"] = st.text_input("Professional title", st.session_state.personal_info["title"])
        st.session_state.personal_info["location"] = st.text_input("Location", st.session_state.personal_info["location"])
    with cols[1]:
        st.session_state.personal_info["email"] = st.text_input("Email", st.session_state.personal_info["email"])
        st.session_state.personal_info["phone"] = st.text_input("Phone", st.session_state.personal_info["phone"])
        st.session_state.personal_info["linkedin"] = st.text_input("LinkedIn", st.session_state.personal_info["linkedin"])
        st.session_state.personal_info["portfolio"] = st.text_input("Portfolio", st.session_state.personal_info["portfolio"])


def render_summary() -> None:
    st.subheader("Summary")
    st.session_state.summary = st.text_area("Professional summary", st.session_state.summary, height=130)


def render_education() -> None:
    st.subheader("Education")
    for index, entry in enumerate(st.session_state.education):
        with st.expander(f"Education {index + 1}", expanded=index == 0):
            columns = st.columns(2)
            with columns[0]:
                entry["degree"] = st.text_input(f"Degree {index}", entry["degree"], key=f"edu_degree_{index}")
                entry["institution"] = st.text_input(f"Institution {index}", entry["institution"], key=f"edu_institution_{index}")
                entry["location"] = st.text_input(f"Education location {index}", entry["location"], key=f"edu_location_{index}")
            with columns[1]:
                start = st.date_input(f"Start date {index}", value=None, key=f"edu_start_{index}")
                end = st.date_input(f"End date {index}", value=None, key=f"edu_end_{index}")
                entry["start_date"] = date_to_iso(start)
                entry["end_date"] = date_to_iso(end)
                entry["gpa"] = st.text_input(f"GPA {index}", entry["gpa"], key=f"edu_gpa_{index}")
                entry["coursework"] = st.text_input(f"Coursework {index}", entry["coursework"], key=f"edu_coursework_{index}")
    if st.button("Add education entry"):
        st.session_state.education.append(
            {
                "degree": "",
                "institution": "",
                "location": "",
                "start_date": "",
                "end_date": "",
                "gpa": "",
                "coursework": "",
            }
        )
        st.rerun()


def render_experience() -> None:
    st.subheader("Experience")
    for index, entry in enumerate(st.session_state.experience):
        with st.expander(f"Experience {index + 1}", expanded=index == 0):
            columns = st.columns(2)
            with columns[0]:
                entry["title"] = st.text_input(f"Job title {index}", entry["title"], key=f"exp_title_{index}")
                entry["company"] = st.text_input(f"Company {index}", entry["company"], key=f"exp_company_{index}")
                entry["location"] = st.text_input(f"Experience location {index}", entry["location"], key=f"exp_location_{index}")
            with columns[1]:
                start = st.date_input(f"Experience start {index}", value=None, key=f"exp_start_{index}")
                end = st.date_input(f"Experience end {index}", value=None, key=f"exp_end_{index}")
                entry["start_date"] = date_to_iso(start)
                entry["end_date"] = date_to_iso(end)

            st.markdown("Bullets")
            bullets = entry.get("bullets", []) or [""]
            normalized_bullets: list[str] = []
            for bullet_index, bullet in enumerate(bullets):
                normalized_bullets.append(
                    st.text_area(
                        f"Bullet {index + 1}.{bullet_index + 1}",
                        bullet,
                        key=f"exp_bullet_{index}_{bullet_index}",
                        height=80,
                    )
                )
            if st.button(f"Add bullet to experience {index + 1}", key=f"add_exp_bullet_{index}"):
                normalized_bullets.append("")
                st.session_state.experience[index]["bullets"] = normalized_bullets
                st.rerun()
            entry["bullets"] = normalized_bullets

            st.markdown("Achievements")
            achievements = entry.get("achievements", []) or [""]
            normalized_achievements: list[str] = []
            for achievement_index, achievement in enumerate(achievements):
                normalized_achievements.append(
                    st.text_area(
                        f"Achievement {index + 1}.{achievement_index + 1}",
                        achievement,
                        key=f"exp_achievement_{index}_{achievement_index}",
                        height=80,
                    )
                )
            if st.button(f"Add achievement to experience {index + 1}", key=f"add_exp_achievement_{index}"):
                normalized_achievements.append("")
                st.session_state.experience[index]["achievements"] = normalized_achievements
                st.rerun()
            entry["achievements"] = normalized_achievements

    if st.button("Add experience entry"):
        st.session_state.experience.append(
            {
                "title": "",
                "company": "",
                "location": "",
                "start_date": "",
                "end_date": "",
                "bullets": [""],
                "achievements": [""],
            }
        )
        st.rerun()


def render_skills() -> None:
    st.subheader("Skills")
    cols = st.columns(3)
    with cols[0]:
        technical_value = st.text_area("Technical skills", ", ".join(st.session_state.skills["technical"]))
        st.session_state.skills["technical"] = csv_to_list(technical_value)
    with cols[1]:
        tool_value = st.text_area("Tools", ", ".join(st.session_state.skills["tools"]))
        st.session_state.skills["tools"] = csv_to_list(tool_value)
    with cols[2]:
        soft_value = st.text_area("Soft skills", ", ".join(st.session_state.skills["soft_skills"]))
        st.session_state.skills["soft_skills"] = csv_to_list(soft_value)


def render_projects() -> None:
    st.subheader("Projects")
    for index, entry in enumerate(st.session_state.projects):
        with st.expander(f"Project {index + 1}"):
            entry["name"] = st.text_input(f"Project name {index}", entry["name"], key=f"project_name_{index}")
            entry["tech_stack"] = st.text_input(f"Tech stack {index}", entry["tech_stack"], key=f"project_stack_{index}")
            entry["description"] = st.text_area(f"Description {index}", entry["description"], key=f"project_desc_{index}")
            entry["impact"] = st.text_area(f"Impact {index}", entry["impact"], key=f"project_impact_{index}")
            entry["link"] = st.text_input(f"Link {index}", entry.get("link", ""), key=f"project_link_{index}")
    if st.button("Add project"):
        st.session_state.projects.append({"name": "", "tech_stack": "", "description": "", "impact": "", "link": ""})
        st.rerun()


def render_certifications() -> None:
    st.subheader("Certifications")
    for index, entry in enumerate(st.session_state.certifications):
        with st.expander(f"Certification {index + 1}"):
            entry["name"] = st.text_input(f"Certification name {index}", entry["name"], key=f"cert_name_{index}")
            entry["issuer"] = st.text_input(f"Issuer {index}", entry["issuer"], key=f"cert_issuer_{index}")
            entry["date_obtained"] = st.text_input(f"Date {index}", entry["date_obtained"], key=f"cert_date_{index}")
            entry["credential_link"] = st.text_input(f"Credential link {index}", entry.get("credential_link", ""), key=f"cert_link_{index}")
    if st.button("Add certification"):
        st.session_state.certifications.append({"name": "", "issuer": "", "date_obtained": "", "credential_link": ""})
        st.rerun()


def build_resume() -> ResumeData:
    return ResumeData(
        personal_info=PersonalInfo(**st.session_state.personal_info),
        summary=st.session_state.summary,
        education=[EducationEntry(**entry) for entry in st.session_state.education],
        experience=[ExperienceEntry(**entry) for entry in st.session_state.experience],
        skills=Skills(**st.session_state.skills),
        projects=[ProjectEntry(**{**entry, "link": entry.get("link") or None}) for entry in st.session_state.projects if entry.get("name")],
        certifications=[CertificationEntry(**entry) for entry in st.session_state.certifications if entry.get("name")],
        languages=csv_to_list(st.session_state.get("languages", "")) if isinstance(st.session_state.get("languages"), str) else st.session_state.get("languages", []),
        awards=csv_to_list(st.session_state.get("awards", "")) if isinstance(st.session_state.get("awards"), str) else st.session_state.get("awards", []),
        publications=csv_to_list(st.session_state.get("publications", "")) if isinstance(st.session_state.get("publications"), str) else st.session_state.get("publications", []),
    )


def render_extra_sections() -> None:
    st.subheader("Additional Sections")
    cols = st.columns(3)
    with cols[0]:
        st.session_state["languages"] = st.text_area("Languages", ", ".join(st.session_state.get("languages", [])))
    with cols[1]:
        st.session_state["awards"] = st.text_area("Awards", ", ".join(st.session_state.get("awards", [])))
    with cols[2]:
        st.session_state["publications"] = st.text_area("Publications", ", ".join(st.session_state.get("publications", [])))


def normalize_entries() -> None:
    for section in ["education", "experience", "projects", "certifications"]:
        for entry in st.session_state[section]:
            for key, value in list(entry.items()):
                if isinstance(value, str):
                    entry[key] = value.strip()


def run_ai_assistant(resume: ResumeData) -> None:
    all_bullets = [bullet for exp in resume.experience for bullet in [*exp.bullets, *exp.achievements] if bullet.strip()]
    result = enhance_resume(
        summary=resume.summary,
        bullets=all_bullets,
        target_role=st.session_state.target_role,
        job_description=st.session_state.job_description,
    )
    st.session_state.enhanced_summary = result.summary
    st.session_state.enhanced_bullets = result.bullets


def apply_enhancements_to_resume(resume: ResumeData) -> ResumeData:
    if not st.session_state.enhanced_summary and not st.session_state.enhanced_bullets:
        return resume

    bullet_index = 0
    updated_experience = []
    for entry in resume.experience:
        updated_bullets = []
        for bullet in entry.bullets:
            if bullet_index < len(st.session_state.enhanced_bullets) and bullet.strip():
                updated_bullets.append(st.session_state.enhanced_bullets[bullet_index])
                bullet_index += 1
            else:
                updated_bullets.append(bullet)
        updated_achievements = []
        for bullet in entry.achievements:
            if bullet_index < len(st.session_state.enhanced_bullets) and bullet.strip():
                updated_achievements.append(st.session_state.enhanced_bullets[bullet_index])
                bullet_index += 1
            else:
                updated_achievements.append(bullet)
        updated_experience.append(entry.model_copy(update={"bullets": updated_bullets, "achievements": updated_achievements}))

    return resume.model_copy(
        update={
            "summary": st.session_state.enhanced_summary or resume.summary,
            "experience": updated_experience,
        }
    )


def main() -> None:
    init_state()
    st.title("AI Resume Builder")
    st.caption("Structured resume builder with AI enhancement, ATS scoring, preview, and PDF export.")

    with st.sidebar:
        st.header("Build Settings")
        st.session_state.target_role = st.text_input("Target role", st.session_state.target_role)
        st.session_state.job_description = st.text_area("Target job description", st.session_state.job_description, height=220)
        st.session_state.template_name = st.selectbox("Template", ["modern", "classic"], index=0 if st.session_state.template_name == "modern" else 1)
        if st.button("Run AI assistant"):
            try:
                normalize_entries()
                resume = build_resume()
                run_ai_assistant(resume)
                st.success("AI suggestions generated")
            except Exception as exc:
                st.error(f"AI assistant failed: {exc}")

    tabs = st.tabs(["Profile", "Resume Sections", "Scoring & Preview", "Export"])

    with tabs[0]:
        render_personal_info()
        render_summary()

    with tabs[1]:
        render_education()
        render_experience()
        render_skills()
        render_projects()
        render_certifications()
        render_extra_sections()

    with tabs[2]:
        try:
            normalize_entries()
            resume = build_resume()
            if st.session_state.enhanced_summary or st.session_state.enhanced_bullets:
                resume = apply_enhancements_to_resume(resume)
            score_report = ats_quality_score(resume, st.session_state.job_description)
            st.session_state.last_score = score_report
            score_cols = st.columns(4)
            score_cols[0].metric("ATS Score", f"{score_report['ats_score']}")
            score_cols[1].metric("Similarity", f"{score_report['similarity']}%")
            score_cols[2].metric("Action Bullets", score_report["action_bullets"])
            score_cols[3].metric("Quantified Bullets", score_report["quantified_bullets"])

            left, right = st.columns(2)
            with left:
                st.markdown("### Original Summary")
                st.write(resume.summary or "No summary yet.")
                if st.session_state.enhanced_summary:
                    st.markdown("### AI Suggested Summary")
                    st.info(st.session_state.enhanced_summary)
            with right:
                st.markdown("### Missing Keywords")
                missing = score_report.get("missing_keywords", [])
                st.write(", ".join(missing) if missing else "No major gaps detected.")

            st.markdown("### Preview")
            st.code(build_resume_text(resume), language="text")
        except Exception as exc:
            st.error(f"Unable to build preview: {exc}")

    with tabs[3]:
        try:
            normalize_entries()
            resume = build_resume()
            if st.session_state.enhanced_summary or st.session_state.enhanced_bullets:
                resume = apply_enhancements_to_resume(resume)
            score_report = ats_quality_score(resume, st.session_state.job_description)
            pdf_bytes = generate_resume_pdf(resume, score_report, st.session_state.template_name)
            st.download_button(
                label="Download PDF",
                data=pdf_bytes,
                file_name=f"{resume.personal_info.full_name or 'resume'}.pdf",
                mime="application/pdf",
            )
            st.success("PDF generated successfully")
        except Exception as exc:
            st.error(f"PDF export failed: {exc}")

        st.markdown("### Validation")
        try:
            resume = build_resume()
            errors = validate_resume_dates(resume)
            if errors:
                for error in errors:
                    st.warning(error)
            else:
                st.success("Date validation passed")
        except Exception as exc:
            st.error(f"Validation failed: {exc}")


if __name__ == "__main__":
    main()
