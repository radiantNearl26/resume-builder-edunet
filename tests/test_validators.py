from ai_resume_builder.core.schemas import EducationEntry, ExperienceEntry, PersonalInfo, ResumeData, Skills
from ai_resume_builder.core.validators import validate_date_order, validate_resume_dates


def test_validate_date_order_accepts_chronological_dates():
    assert validate_date_order("2020-01", "2024-01") is True


def test_validate_date_order_rejects_reverse_dates():
    assert validate_date_order("2024-01", "2020-01") is False


def test_validate_resume_dates_reports_invalid_entries():
    resume = ResumeData(
        personal_info=PersonalInfo(full_name="Test User", email="a@b.com", phone="12345", location="Remote"),
        summary="Experienced engineer.",
        education=[EducationEntry(degree="BS", institution="University", start_date="2024-01", end_date="2020-01")],
        experience=[ExperienceEntry(title="Engineer", company="Acme", start_date="2020-01", end_date="2021-01", bullets=["Built systems"], achievements=[])],
        skills=Skills(technical=["Python"]),
    )
    errors = validate_resume_dates(resume)
    assert errors
