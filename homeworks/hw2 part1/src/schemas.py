# src/schemas.py
from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class ExperienceItem(BaseModel):
    company: str
    title: str
    start_date: Optional[str] = None   # "2020", "2020-05", "May 2020"
    end_date: Optional[str] = None     # "Present" / "2023"
    location: Optional[str] = None
    description: Optional[str] = None

class EducationItem(BaseModel):
    school: str
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    graduation_year: Optional[str] = None
    start_year: Optional[str] = None
    end_year: Optional[str] = None

class CVProfile(BaseModel):
    full_name: str
    headline: Optional[str] = None
    current_location: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    experiences: List[ExperienceItem] = Field(default_factory=list)
    education: List[EducationItem] = Field(default_factory=list)
    raw_text_excerpt: Optional[str] = None

class SocialCandidate(BaseModel):
    platform: Literal["linkedin", "facebook"]
    candidate_id: str
    display_name: str
    profile_url: Optional[str] = None
    score: float = 0.0
    reason: Optional[str] = None

class Discrepancy(BaseModel):
    field: str                       # e.g. "experience.company", "education.graduation_year"
    severity: Literal["low", "medium", "high"]
    status: Literal["match", "partial_match", "mismatch", "missing", "unverifiable"]
    cv_value: Optional[str] = None
    social_value: Optional[str] = None
    evidence: Optional[str] = None
    rationale: Optional[str] = None

class VerificationResult(BaseModel):
    file: str
    person_name: str
    overall_status: Literal["verified", "partially_verified", "suspicious", "unable_to_verify"]
    confidence: float
    selected_linkedin: Optional[dict] = None
    selected_facebook: Optional[dict] = None
    discrepancies: List[Discrepancy] = Field(default_factory=list)
    summary: str