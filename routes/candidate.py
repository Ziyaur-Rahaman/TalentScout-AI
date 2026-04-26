from fastapi import APIRouter, Depends, HTTPException
from database import get_db
from auth import get_current_candidate
from bson import ObjectId

router = APIRouter(tags=["Candidate"])

# ─────────────────────────────────────────
# GET CANDIDATE DASHBOARD
# ─────────────────────────────────────────

@router.get("/dashboard")
def get_dashboard(current_user: dict = Depends(get_current_candidate)):
    db = get_db()

    candidate_id = current_user["_id"]

    # Get all matches for this candidate
    matches = list(db.matches.find({"candidate_id": candidate_id}))

    opportunities = []
    for match in matches:
        job = db.jobs.find_one({"_id": ObjectId(match["job_id"])})
        conversation = db.conversations.find_one({
            "job_id": match["job_id"],
            "candidate_id": candidate_id
        })

        if job:
            opportunities.append({
                "job_id": match["job_id"],
                "match_id": str(match["_id"]),
                "conversation_id": str(conversation["_id"]) if conversation else None,
                "job_title": job.get("title"),
                "company": "Hiring Company",
                "location": job.get("parsed_data", {}).get("location"),
                "salary_range": f"{job.get('parsed_data', {}).get('salary_min', 0)} - {job.get('parsed_data', {}).get('salary_max', 0)} LPA",
                "match_score": match.get("match_score"),
                "interest_score": match.get("interest_score"),
                "final_score": match.get("final_score"),
                "application_status": match.get("application_status"),
                "chat_status": conversation.get("chat_status") if conversation else "pending",
                "matched_skills": match.get("matched_skills", []),
                "explanation": match.get("explanation", "")
            })

    return {
        "candidate": {
            "name": current_user.get("name"),
            "email": current_user.get("email"),
            "skills": current_user.get("skills"),
            "location": current_user.get("location"),
            "experience_years": current_user.get("experience_years"),
            "expected_salary": current_user.get("expected_salary"),
            "status": current_user.get("status")
        },
        "opportunities": opportunities,
        "total_matches": len(opportunities),
        "pending_chats": sum(1 for o in opportunities if o["chat_status"] == "pending"),
        "completed_chats": sum(1 for o in opportunities if o["chat_status"] == "completed"),
        "shortlisted": sum(1 for o in opportunities if o["application_status"] == "shortlisted")
    }


# ─────────────────────────────────────────
# GET CONVERSATION STATUS
# ─────────────────────────────────────────

@router.get("/conversation/{conversation_id}")
def get_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_candidate)
):
    db = get_db()

    conversation = db.conversations.find_one({"_id": ObjectId(conversation_id)})
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if conversation["candidate_id"] != current_user["_id"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    conversation["_id"] = str(conversation["_id"])
    return conversation