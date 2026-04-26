from database import get_db
from agent.interest_scorer import score_interest
from datetime import datetime
from bson import ObjectId


def calculate_final_score(match_score: float, interest_score: float) -> float:
    return round((match_score * 0.6) + (interest_score * 0.4), 2)


def generate_report(job_id: str, trigger: str) -> dict:
    db = get_db()

    job = db.jobs.find_one({"_id": ObjectId(job_id)})
    if not job:
        raise ValueError("Job not found")

    # Block duplicate reports
    result = db.jobs.find_one_and_update(
        {"_id": ObjectId(job_id), "report_generated": False},
        {"$set": {"report_generated": True}}
    )

    if result is None:
        existing = db.jobs.find_one({"_id": ObjectId(job_id)})
        return existing.get("report", {})

    # Get all matches for this job
    matches = list(db.matches.find({"job_id": job_id}))

    shortlisted = []
    no_response = []

    for match in matches:
        candidate_id = match["candidate_id"]
        match_id = str(match["_id"])

        # ✅ FIX: Find conversation by job_id + candidate_id (not match_id)
        conversation = db.conversations.find_one({
            "job_id": job_id,
            "candidate_id": candidate_id
        })

        candidate = db.candidates.find_one({"_id": ObjectId(candidate_id)})

        if conversation and conversation.get("chat_status") == "completed":
            # Score interest from conversation
            try:
                interest_data = score_interest(str(conversation["_id"]))
                interest_score = interest_data["interest_score"]
            except Exception as e:
                print(f"  ⚠️ Interest scoring failed for {candidate_id}: {e}")
                interest_score = 50
                interest_data = {
                    "interest_score": 50,
                    "interest_level": "Medium",
                    "key_positives": [],
                    "key_concerns": [],
                    "summary": "Could not analyze conversation."
                }

            final_score = calculate_final_score(match["match_score"], interest_score)

            # Update conversation
            db.conversations.update_one(
                {"_id": conversation["_id"]},
                {"$set": {
                    "interest_score": interest_score,
                    "interest_data": interest_data,
                    "final_score": final_score
                }}
            )

            # Update match
            db.matches.update_one(
                {"_id": match["_id"]},
                {"$set": {
                    "interest_score": interest_score,
                    "final_score": final_score,
                    "application_status": "under_review"
                }}
            )

            shortlisted.append({
                "candidate_id": candidate_id,
                "name": candidate.get("name") if candidate else "Unknown",
                "email": candidate.get("email", ""),
                "location": candidate.get("location", ""),
                "skills": candidate.get("skills", []),
                "experience_years": candidate.get("experience_years", 0),
                "match_score": match["match_score"],
                "interest_score": interest_score,
                "final_score": final_score,
                "matched_skills": match.get("matched_skills", []),
                "missing_skills": match.get("missing_skills", []),
                "match_explanation": match.get("explanation", ""),
                "interest_level": interest_data.get("interest_level", ""),
                "key_positives": interest_data.get("key_positives", []),
                "key_concerns": interest_data.get("key_concerns", []),
                "interest_summary": interest_data.get("summary", "")
            })

        else:
            # No response
            db.matches.update_one(
                {"_id": match["_id"]},
                {"$set": {"application_status": "not_selected"}}
            )

            no_response.append({
                "candidate_id": candidate_id,
                "name": candidate.get("name") if candidate else "Unknown",
                "match_score": match["match_score"],
                "reason": "Did not respond to chat invitation"
            })

    # Sort by final score
    shortlisted.sort(key=lambda x: x["final_score"], reverse=True)

    # Update application status
    for i, c in enumerate(shortlisted):
        status = "shortlisted" if i < 5 else "not_selected"
        db.matches.update_one(
            {"candidate_id": c["candidate_id"], "job_id": job_id},
            {"$set": {"application_status": status}}
        )
        if status == "shortlisted":
            db.candidates.update_one(
                {"_id": ObjectId(c["candidate_id"])},
                {"$set": {f"job_statuses.{job_id}": status}}
            )

    report = {
        "job_id": job_id,
        "job_title": job.get("title"),
        "total_matched": len(matches),
        "total_chatted": len(shortlisted),
        "total_no_response": len(no_response),
        "shortlisted": shortlisted,
        "no_response": no_response,
        "trigger": trigger,
        "generated_at": datetime.utcnow().isoformat()
    }

    db.jobs.update_one(
        {"_id": ObjectId(job_id)},
        {"$set": {
            "report": report,
            "report_generated_at": datetime.utcnow(),
            "report_trigger": trigger,
            "report_generated": True
        }}
    )

    print(f"✅ Report generated — Shortlisted: {len(shortlisted)}, No response: {len(no_response)}")
    return report