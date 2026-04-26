from langchain_groq import ChatGroq
from database import get_db
from dotenv import load_dotenv
import os
import json

load_dotenv()

llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model_name="llama-3.3-70b-versatile",
    temperature=0
)

def calculate_match_score(parsed_jd: dict, candidate: dict) -> dict:
    """
    Use Groq to score a candidate against a JD
    Returns match score + explanation
    """

    prompt = f"""
You are an expert technical recruiter. Score this candidate against the job description.

JOB REQUIREMENTS:
- Role: {parsed_jd.get('role')}
- Required Skills: {parsed_jd.get('required_skills')}
- Nice to Have: {parsed_jd.get('nice_to_have_skills')}
- Experience Needed: {parsed_jd.get('experience_years')} years
- Location: {parsed_jd.get('location')}
- Salary Range: {parsed_jd.get('salary_min')} - {parsed_jd.get('salary_max')} LPA
- Job Type: {parsed_jd.get('job_preference')}

CANDIDATE PROFILE:
- Name: {candidate.get('name')}
- Skills: {candidate.get('skills')}
- Experience: {candidate.get('experience_years')} years
- Location: {candidate.get('location')}
- Expected Salary: {candidate.get('expected_salary')} LPA
- Job Preference: {candidate.get('job_preference')}
- Notice Period: {candidate.get('notice_period')}
- Status: {candidate.get('status')}
- Bio: {candidate.get('bio')}

Score this candidate from 0-100 based on:
1. Skills match (40 points) - how many required skills they have
2. Experience match (20 points) - years of experience vs required
3. Location match (15 points) - location compatibility
4. Salary match (15 points) - expected vs offered range
5. Availability (10 points) - notice period and status

Return ONLY a valid JSON object:
{{
  "match_score": 85,
  "skills_score": 35,
  "experience_score": 18,
  "location_score": 12,
  "salary_score": 12,
  "availability_score": 8,
  "matched_skills": ["Python", "FastAPI"],
  "missing_skills": ["PostgreSQL"],
  "explanation": "Strong Python and FastAPI skills match 2 of 3 required skills. Experience slightly below requirement. Location matches. Salary within range.",
  "recommendation": "Strong Match"
}}

recommendation must be one of: "Strong Match", "Good Match", "Partial Match", "Weak Match"
Return ONLY JSON, no explanation, no markdown.
"""

    response = llm.invoke(prompt)
    content = response.content.strip()

    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()

    return json.loads(content)


def find_and_score_candidates(parsed_jd: dict, job_id: str) -> list:
    """
    Scan all candidates from DB and score each one
    Returns top candidates sorted by match score
    """
    db = get_db()

    # Get all active candidates
    candidates = list(db.candidates.find({
        "status": {"$in": ["actively_looking", "open_to_offers"]}
    }))

    if not candidates:
        return []

    print(f"📊 Scoring {len(candidates)} candidates...")

    scored_candidates = []

    for candidate in candidates:
        try:
            candidate_id = str(candidate["_id"])
            score_data = calculate_match_score(parsed_jd, candidate)

            scored_candidates.append({
                "candidate_id": candidate_id,
                "candidate_name": candidate["name"],
                "candidate_email": candidate["email"],
                "match_score": score_data["match_score"],
                "skills_score": score_data.get("skills_score", 0),
                "experience_score": score_data.get("experience_score", 0),
                "location_score": score_data.get("location_score", 0),
                "salary_score": score_data.get("salary_score", 0),
                "availability_score": score_data.get("availability_score", 0),
                "matched_skills": score_data.get("matched_skills", []),
                "missing_skills": score_data.get("missing_skills", []),
                "explanation": score_data.get("explanation", ""),
                "recommendation": score_data.get("recommendation", "")
            })

            print(f"  ✅ {candidate['name']}: {score_data['match_score']}/100")

        except Exception as e:
            print(f"  ❌ Error scoring {candidate.get('name')}: {e}")
            continue

    # Sort by match score descending
    scored_candidates.sort(key=lambda x: x["match_score"], reverse=True)

    # Return top 15 only
    return scored_candidates[:15]