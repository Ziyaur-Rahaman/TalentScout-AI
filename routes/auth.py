from fastapi import APIRouter, HTTPException, status, Depends
from database import get_db
from models import RecruiterRegister, CandidateRegister, RecruiterLogin, CandidateLogin, TokenResponse
from auth import hash_password, verify_password, create_token, get_current_user
from datetime import datetime

router = APIRouter(tags=["Auth"])

# ─────────────────────────────────────────
# RECRUITER REGISTER
# ─────────────────────────────────────────

@router.post("/recruiter/register")
def recruiter_register(data: RecruiterRegister):
    db = get_db()

    # Check if email exists
    if db.recruiters.find_one({"email": data.email}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Save recruiter
    recruiter = {
        "name": data.name,
        "company": data.company,
        "email": data.email,
        "password_hash": hash_password(data.password),
        "created_at": datetime.utcnow()
    }

    result = db.recruiters.insert_one(recruiter)

    # Create token
    token = create_token({
        "user_id": str(result.inserted_id),
        "role": "recruiter"
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": "recruiter",
        "user_id": str(result.inserted_id),
        "name": data.name
    }

# ─────────────────────────────────────────
# RECRUITER LOGIN
# ─────────────────────────────────────────

@router.post("/recruiter/login")
def recruiter_login(data: RecruiterLogin):
    db = get_db()

    recruiter = db.recruiters.find_one({"email": data.email})

    if not recruiter or not verify_password(data.password, recruiter["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    token = create_token({
        "user_id": str(recruiter["_id"]),
        "role": "recruiter"
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": "recruiter",
        "user_id": str(recruiter["_id"]),
        "name": recruiter["name"]
    }

# ─────────────────────────────────────────
# CANDIDATE REGISTER
# ─────────────────────────────────────────

@router.post("/candidate/register")
def candidate_register(data: CandidateRegister):
    db = get_db()

    # Check if email exists
    if db.candidates.find_one({"email": data.email}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Save candidate
    candidate = {
        "name": data.name,
        "email": data.email,
        "password_hash": hash_password(data.password),
        "phone": data.phone,
        "location": data.location,
        "experience_years": data.experience_years,
        "current_role": data.current_role,
        "expected_salary": data.expected_salary,
        "notice_period": data.notice_period,
        "job_preference": data.job_preference,
        "skills": data.skills,
        "bio": data.bio,
        "status": data.status,
        "created_at": datetime.utcnow()
    }

    result = db.candidates.insert_one(candidate)

    token = create_token({
        "user_id": str(result.inserted_id),
        "role": "candidate"
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": "candidate",
        "user_id": str(result.inserted_id),
        "name": data.name
    }

# ─────────────────────────────────────────
# CANDIDATE LOGIN
# ─────────────────────────────────────────

@router.post("/candidate/login")
def candidate_login(data: CandidateLogin):
    db = get_db()

    candidate = db.candidates.find_one({"email": data.email})

    if not candidate or not verify_password(data.password, candidate["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    token = create_token({
        "user_id": str(candidate["_id"]),
        "role": "candidate"
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": "candidate",
        "user_id": str(candidate["_id"]),
        "name": candidate["name"]
    }

# ─────────────────────────────────────────
# GET PROFILE
# ─────────────────────────────────────────

@router.get("/profile")
def get_profile(current_user: dict = Depends(get_current_user)):
    current_user.pop("password_hash", None)
    return current_user

# Import at bottom to avoid circular import
from auth import get_current_user