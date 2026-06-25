from ai_resume_builder.core.schemas import EducationEntry, PersonalInfo, ResumeData, Skills
from ai_resume_builder.export.pdf_reportlab import generate_resume_pdf
from ai_resume_builder.services.scoring_service import ats_quality_score


def test_generate_resume_pdf_returns_pdf_bytes():
    resume = ResumeData(
        personal_info=PersonalInfo(full_name="Test User", email="a@b.com", phone="12345", location="Remote"),
        summary="Experienced engineer.",
        education=[EducationEntry(degree="BS", institution="University", start_date="2018-01", end_date="2022-01")],
        skills=Skills(technical=["Python"]),
    )
    pdf_bytes = generate_resume_pdf(resume, ats_quality_score(resume))
    assert pdf_bytes.startswith(b"%PDF")
