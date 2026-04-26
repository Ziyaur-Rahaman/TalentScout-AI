from pymongo import MongoClient
from datetime import datetime
from passlib.context import CryptContext
from dotenv import load_dotenv
import certifi
import os

load_dotenv()

# ─────────────────────────────────────────
# CONNECT
# ─────────────────────────────────────────
client = MongoClient(os.getenv("MONGODB_URL"), tlsCAFile=certifi.where())
db = client[os.getenv("DATABASE_NAME")]

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password):
    return pwd_context.hash(password[:72])

# ─────────────────────────────────────────
# CLEAR ALL DATA
# ─────────────────────────────────────────
def clear_all():
    db.recruiters.delete_many({})
    db.candidates.delete_many({})
    db.jobs.delete_many({})
    db.matches.delete_many({})
    db.conversations.delete_many({})
    print("🗑️  All existing data cleared")

# ─────────────────────────────────────────
# SEED RECRUITER
# ─────────────────────────────────────────
def seed_recruiter():
    recruiter = {
        "name": "Arjun Mehta",
        "company": "TechVentures India",
        "email": "recruiter@techventures.com",
        "password_hash": hash_password("recruiter123"),
        "created_at": datetime.utcnow()
    }
    result = db.recruiters.insert_one(recruiter)
    print(f"✅ Recruiter created: {recruiter['email']} / recruiter123")
    return str(result.inserted_id)

# ─────────────────────────────────────────
# SEED CANDIDATES
# ─────────────────────────────────────────
def seed_candidates():
    candidates = [

        # ── STRONG MATCH 1 ──────────────────
        {
            "name": "Ziyaur Rahaman",
            "email": "ziyaur@gmail.com",
            "password_hash": hash_password("candidate123"),
            "phone": "9876543210",
            "location": "Hyderabad, AP",
            "experience_years": 1,
            "current_role": "AI/ML Intern",
            "expected_salary": 10,
            "notice_period": "immediate",
            "job_preference": "hybrid",
            "skills": ["Python", "FastAPI", "LangChain", "LangGraph", "MongoDB", "REST API", "Prompt Engineering"],
            "bio": "Final year B.Tech student specializing in AI/ML. Completed NLP internship at Infosys Springboard. Built agentic AI systems using LangGraph and Claude API.",
            "status": "actively_looking",
            "created_at": datetime.utcnow()
        },

        # ── STRONG MATCH 2 ──────────────────
        {
            "name": "Priya Nair",
            "email": "priya.nair@gmail.com",
            "password_hash": hash_password("candidate123"),
            "phone": "9876543211",
            "location": "Hyderabad, Telangana",
            "experience_years": 2,
            "current_role": "Backend Developer",
            "expected_salary": 12,
            "notice_period": "30_days",
            "job_preference": "hybrid",
            "skills": ["Python", "FastAPI", "MongoDB", "REST API", "LangChain", "Docker"],
            "bio": "Backend developer with 2 years experience building Python APIs. Recently started working with LangChain for LLM integrations. Strong in FastAPI and MongoDB.",
            "status": "actively_looking",
            "created_at": datetime.utcnow()
        },

        # ── STRONG MATCH 3 ──────────────────
        {
            "name": "Rahul Sharma",
            "email": "rahul.sharma@gmail.com",
            "password_hash": hash_password("candidate123"),
            "phone": "9876543212",
            "location": "Hyderabad, Telangana",
            "experience_years": 1.5,
            "current_role": "Python Developer",
            "expected_salary": 9,
            "notice_period": "30_days",
            "job_preference": "hybrid",
            "skills": ["Python", "Flask", "FastAPI", "REST API", "PostgreSQL", "AWS", "HuggingFace"],
            "bio": "Python developer with experience in Flask and FastAPI. Exploring AI integrations with HuggingFace models. Deployed 2 production APIs on AWS.",
            "status": "actively_looking",
            "created_at": datetime.utcnow()
        },

        # ── GOOD MATCH 4 ──────────────────
        {
            "name": "Sneha Reddy",
            "email": "sneha.reddy@gmail.com",
            "password_hash": hash_password("candidate123"),
            "phone": "9876543213",
            "location": "Hyderabad, Telangana",
            "experience_years": 1,
            "current_role": "Fresher",
            "expected_salary": 8,
            "notice_period": "immediate",
            "job_preference": "hybrid",
            "skills": ["Python", "MongoDB", "REST API", "LangChain", "Machine Learning"],
            "bio": "Recent graduate with strong Python foundation. Completed projects on ML and LangChain. Looking for first role in AI backend development.",
            "status": "actively_looking",
            "created_at": datetime.utcnow()
        },

        # ── WEAK MATCH 5 ──────────────────
        {
            "name": "Amit Kumar",
            "email": "amit.kumar@gmail.com",
            "password_hash": hash_password("candidate123"),
            "phone": "9876543214",
            "location": "Bangalore, Karnataka",
            "experience_years": 3,
            "current_role": "Frontend Developer",
            "expected_salary": 18,
            "notice_period": "60_days",
            "job_preference": "remote",
            "skills": ["React", "JavaScript", "Node.js", "CSS", "HTML"],
            "bio": "Frontend developer with 3 years experience. Mostly worked on React and Node.js. Interested in switching to backend but limited Python experience.",
            "status": "open_to_offers",
            "created_at": datetime.utcnow()
        },

        # ── WEAK MATCH 6 ──────────────────
        {
            "name": "Kavya Singh",
            "email": "kavya.singh@gmail.com",
            "password_hash": hash_password("candidate123"),
            "phone": "9876543215",
            "location": "Pune, Maharashtra",
            "experience_years": 2,
            "current_role": "Data Analyst",
            "expected_salary": 16,
            "notice_period": "60_days",
            "job_preference": "remote",
            "skills": ["SQL", "Excel", "Power BI", "Python (basic)", "Tableau"],
            "bio": "Data analyst with 2 years experience in SQL and visualization tools. Basic Python knowledge. Interested in moving to ML roles in future.",
            "status": "open_to_offers",
            "created_at": datetime.utcnow()
        }
    ]

    ids = []
    for c in candidates:
        result = db.candidates.insert_one(c)
        ids.append(str(result.inserted_id))
        print(f"  👤 {c['name']} — {c['skills'][:3]}...")

    print(f"✅ {len(candidates)} candidates created (password: candidate123)")
    return ids

# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────
if __name__ == "__main__":
    print("\n🚀 Starting seed...\n")
    clear_all()

    recruiter_id = seed_recruiter()

    print(f"\n👥 Creating candidates...")
    candidate_ids = seed_candidates()

    print(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ SEED COMPLETE

RECRUITER LOGIN:
  Email:    recruiter@techventures.com
  Password: recruiter123

CANDIDATE LOGINS (all same password: candidate123)
  Ziyaur Rahaman  → ziyaur@gmail.com        (Strong Match)
  Priya Nair      → priya.nair@gmail.com    (Strong Match)
  Rahul Sharma    → rahul.sharma@gmail.com  (Strong Match)
  Sneha Reddy     → sneha.reddy@gmail.com   (Good Match)
  Amit Kumar      → amit.kumar@gmail.com    (Weak Match)
  Kavya Singh     → kavya.singh@gmail.com   (Weak Match)

NEXT STEPS:
  1. Login as recruiter
  2. Paste JD text or upload PDF/DOCX
  3. Click Find Candidates Automatically
  4. Login as each candidate and chat
  5. Generate report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """)