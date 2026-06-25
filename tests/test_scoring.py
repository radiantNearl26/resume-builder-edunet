from ai_resume_builder.core.schemas import PersonalInfo, ResumeData, Skills, ExperienceEntry, EducationEntry
from ai_resume_builder.services.scoring_service import ats_quality_score


def build_sample_resume() -> ResumeData:
    return ResumeData(
        personal_info=PersonalInfo(full_name="Test User", email="a@b.com", phone="12345", location="Remote"),
        summary="Built scalable applications.",
        education=[EducationEntry(degree="BS", institution="University", start_date="2018-01", end_date="2022-01")],
        experience=[
            ExperienceEntry(
                title="Engineer",
                company="Acme",
                start_date="2022-01",
                end_date="2024-01",
                bullets=["Led a migration that reduced cost by 20%"],
                achievements=["Improved delivery by 15%"],
            )
        ],
        skills=Skills(technical=["Python", "SQL"], tools=["Docker"], soft_skills=["Leadership"]),
    )


def test_ats_quality_score_returns_expected_fields():
    result = ats_quality_score(build_sample_resume(), "Python SQL Docker")
    assert 0 <= result["ats_score"] <= 100
    assert "similarity" in result
    assert "missing_keywords" in result
