from fastapi import APIRouter, Depends, HTTPException
from database import get_db
from auth import get_current_candidate
from models import ChatMessage
from agent.chat_conductor import start_conversation, process_candidate_reply
from bson import ObjectId

router = APIRouter(tags=["Chat"])

# ─────────────────────────────────────────
# START CONVERSATION
# ─────────────────────────────────────────

@router.post("/start/{conversation_id}")
def start_chat(
    conversation_id: str,
    current_user: dict = Depends(get_current_candidate)
):
    db = get_db()

    conversation = db.conversations.find_one({"_id": ObjectId(conversation_id)})
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if conversation["candidate_id"] != current_user["_id"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    if conversation.get("chat_status") == "completed":
        return {
            "message": "This conversation is already completed.",
            "completed": True,
            "messages": conversation.get("messages", [])
        }

    if conversation.get("chat_status") == "in_progress":
        return {
            "message": conversation["messages"][-1]["content"] if conversation.get("messages") else "",
            "completed": False,
            "messages": conversation.get("messages", []),
            "questions_asked": conversation.get("questions_asked", 0),
            "max_questions": 5
        }

    # Start fresh conversation
    result = start_conversation(conversation_id)
    return {**result, "completed": False}


# ─────────────────────────────────────────
# SEND MESSAGE
# ─────────────────────────────────────────

@router.post("/message/{conversation_id}")
def send_message(
    conversation_id: str,
    data: ChatMessage,
    current_user: dict = Depends(get_current_candidate)
):
    db = get_db()

    conversation = db.conversations.find_one({"_id": ObjectId(conversation_id)})
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if conversation["candidate_id"] != current_user["_id"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Check previous status before processing
    previous_status = conversation.get("chat_status", "pending")

    result = process_candidate_reply(conversation_id, data.message)

    # Update job counts only when NEWLY completed
    if result.get("completed") and previous_status != "completed":
        db.jobs.update_one(
            {"_id": ObjectId(conversation["job_id"])},
            {
                "$inc": {
                    "chatted_count": 1,
                    "not_responded_count": -1,
                    "in_progress_count": -1
                }
            }
        )
    # Update in_progress count when first message sent
    elif previous_status == "pending":
        db.jobs.update_one(
            {"_id": ObjectId(conversation["job_id"])},
            {"$inc": {"in_progress_count": 1, "not_responded_count": -1}}
        )

    return result

# ─────────────────────────────────────────
# GET MESSAGES
# ─────────────────────────────────────────

@router.get("/messages/{conversation_id}")
def get_messages(
    conversation_id: str,
    current_user: dict = Depends(get_current_candidate)
):
    db = get_db()

    conversation = db.conversations.find_one({"_id": ObjectId(conversation_id)})
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if conversation["candidate_id"] != current_user["_id"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    return {
        "messages": conversation.get("messages", []),
        "chat_status": conversation.get("chat_status"),
        "questions_asked": conversation.get("questions_asked", 0),
        "max_questions": 5
    }