from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

# ─────────────────────────────────────────
# ENUMS
# ─────────────────────────────────────────

class UserRole(str, Enum):
    recruiter = "recruiter"
    candidate = "candidate"

class CandidateStatus(str, Enum):
    actively_looking = "actively_looking"
    open_to_offers = "open_to_offers"
    not_looking = "not_looking"

class JobPreference(str, Enum):
    remote = "remote"
    onsite = "onsite"
    hybrid = "hybrid"

class NoticePeriod(str, Enum):
    immediate = "immediate"
    thirty_days = "30_days"
    sixty_days = "60_days"

class ApplicationStatus(str, Enum):
    under_review = "under_review"
    shortlisted = "shortlisted"
    not_selected = "not_selected"

class ChatStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"

class ReportTrigger(str, Enum):
    auto_24hr = "24hr_window"
    all_chatted = "all_chatted"
    manual = "manual"

# ─────────────────────────────────────────
# RECRUITER
# ─────────────────────────────────────────

class RecruiterRegister(BaseModel):
    name: str
    company: str
    email: str
    password: str

class RecruiterLogin(BaseModel):
    email: str
    password: str

# ─────────────────────────────────────────
# CANDIDATE
# ─────────────────────────────────────────

class CandidateRegister(BaseModel):
    name: str
    email: str
    password: str
    phone: str
    location: str
    experience_years: float
    current_role: str
    expected_salary: float
    notice_period: NoticePeriod
    job_preference: JobPreference
    skills: List[str]
    bio: str
    status: CandidateStatus

class CandidateLogin(BaseModel):
    email: str
    password: str

# ─────────────────────────────────────────
# JOB
# ─────────────────────────────────────────

class JobPost(BaseModel):
    title: str
    description: str

# ─────────────────────────────────────────
# CHAT
# ─────────────────────────────────────────

class ChatMessage(BaseModel):
    message: str

# ─────────────────────────────────────────
# RESPONSE MODELS
# ─────────────────────────────────────────

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    role: str
    user_id: str
    name: str