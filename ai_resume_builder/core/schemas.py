from __future__ import annotations

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl, model_validator


class PersonalInfo(BaseModel):
    full_name: str = Field(min_length=1)
    email: str = Field(min_length=3)
    phone: str = Field(min_length=5)
    location: str = Field(min_length=1)
    linkedin: Optional[str] = None
    portfolio: Optional[str] = None
    title: str = Field(default="")


class EducationEntry(BaseModel):
    degree: str = Field(min_length=1)
    institution: str = Field(min_length=1)
    location: str = Field(default="")
    start_date: str = Field(default="")
    end_date: str = Field(default="")
    gpa: Optional[str] = None
    coursework: Optional[str] = None


class ExperienceEntry(BaseModel):
    title: str = Field(min_length=1)
    company: str = Field(min_length=1)
    location: str = Field(default="")
    start_date: str = Field(default="")
    end_date: str = Field(default="")
    bullets: List[str] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)


class ProjectEntry(BaseModel):
    name: str = Field(min_length=1)
    tech_stack: str = Field(default="")
    description: str = Field(default="")
    impact: str = Field(default="")
    link: Optional[HttpUrl] = None


class CertificationEntry(BaseModel):
    name: str = Field(min_length=1)
    issuer: str = Field(default="")
    date_obtained: str = Field(default="")
    credential_link: Optional[str] = None


class Skills(BaseModel):
    technical: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)


class ResumeData(BaseModel):
    personal_info: PersonalInfo
    summary: str = Field(default="")
    education: List[EducationEntry] = Field(default_factory=list)
    experience: List[ExperienceEntry] = Field(default_factory=list)
    skills: Skills = Field(default_factory=Skills)
    projects: List[ProjectEntry] = Field(default_factory=list)
    certifications: List[CertificationEntry] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    awards: List[str] = Field(default_factory=list)
    publications: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_resume(self):
        if not self.personal_info.full_name.strip():
            raise ValueError("Full name is required")
        if not self.education and not self.experience:
            raise ValueError("At least one education or experience entry is required")
        return self
