from langchain_groq import ChatGroq
from database import get_db
from dotenv import load_dotenv
from datetime import datetime
from bson import ObjectId
import os

load_dotenv()

llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model_name="llama-3.3-70b-versatile",
    temperature=0.7
)

MAX_QUESTIONS = 5

def get_opening_message(candidate: dict, job: dict) -> str:
    """
    Generate personalized opening message for candidate
    """
    parsed_jd = job.get("parsed_data", {})

    prompt = f"""
You are a friendly AI recruiter assistant. Write a short, warm opening message to a candidate.

Candidate Name: {candidate.get('name')}
Job Role: {parsed_jd.get('role')}
Job Location: {parsed_jd.get('location')}
Salary Range: {parsed_jd.get('salary_min')} - {parsed_jd.get('salary_max')} LPA

Write a 2-3 sentence opening message that:
1. Greets them by name
2. Mentions the role and why their profile matched
3. Asks if they are open to discussing this opportunity
4. Mentions it will only take 3-4 minutes

Be conversational and friendly. No bullet points. Plain text only.
"""
    response = llm.invoke(prompt)
    return response.content.strip()


def get_next_question(
    conversation_history: list,
    candidate: dict,
    job: dict,
    questions_asked: int
) -> str:
    """
    Generate the next smart question based on conversation so far
    """
    parsed_jd = job.get("parsed_data", {})

    history_text = "\n".join([
        f"{msg['role'].upper()}: {msg['content']}"
        for msg in conversation_history
    ])

    prompt = f"""
You are an AI recruiter conducting a candidate screening conversation.

JOB DETAILS:
- Role: {parsed_jd.get('role')}
- Location: {parsed_jd.get('location')}
- Salary: {parsed_jd.get('salary_min')} - {parsed_jd.get('salary_max')} LPA
- Required Skills: {parsed_jd.get('required_skills')}
- Job Type: {parsed_jd.get('job_preference')}

CANDIDATE:
- Name: {candidate.get('name')}
- Skills: {candidate.get('skills')}
- Experience: {candidate.get('experience_years')} years
- Location: {candidate.get('location')}
- Expected Salary: {candidate.get('expected_salary')} LPA
- Notice Period: {candidate.get('notice_period')}

CONVERSATION SO FAR:
{history_text}

Questions asked so far: {questions_asked} out of {MAX_QUESTIONS}

Generate the next single question to ask. Focus on topics not yet covered:
- Current job search status and motivation
- Relevant technical experience with required skills
- Availability and notice period
- Salary expectations
- Location/remote work preferences

Rules:
- Ask ONE question only
- Be conversational and friendly
- Keep it short (1-2 sentences max)
- Don't repeat already answered topics
- If this is the last question ({questions_asked} == {MAX_QUESTIONS - 1}), 
  make it a closing question and thank them

Return ONLY the question text, nothing else.
"""
    response = llm.invoke(prompt)
    return response.content.strip()


def get_closing_message(candidate_name: str) -> str:
    return f"Thank you {candidate_name}! I have everything I need. Our recruiter will review your profile and reach out within 24 hours if you're shortlisted. Best of luck! 🙏"


def start_conversation(conversation_id: str) -> dict:
    """
    Initialize and start a conversation
    """
    db = get_db()

    conversation = db.conversations.find_one({"_id": ObjectId(conversation_id)})
    if not conversation:
        raise ValueError("Conversation not found")

    candidate = db.candidates.find_one({"_id": ObjectId(conversation["candidate_id"])})
    job = db.jobs.find_one({"_id": ObjectId(conversation["job_id"])})

    if not candidate or not job:
        raise ValueError("Candidate or job not found")

    # Generate opening message
    opening = get_opening_message(candidate, job)

    # Update conversation
    db.conversations.update_one(
        {"_id": ObjectId(conversation_id)},
        {"$set": {
            "messages": [{"role": "agent", "content": opening, "timestamp": datetime.utcnow()}],
            "chat_status": "in_progress",
            "started_at": datetime.utcnow(),
            "questions_asked": 0
        }}
    )

    return {"message": opening, "questions_asked": 0, "max_questions": MAX_QUESTIONS}


def process_candidate_reply(conversation_id: str, candidate_message: str) -> dict:
    db = get_db()

    conversation = db.conversations.find_one({"_id": ObjectId(conversation_id)})
    if not conversation:
        raise ValueError("Conversation not found")

    if conversation.get("chat_status") == "completed":
        return {"message": "This conversation has already been completed.", "completed": True}

    candidate = db.candidates.find_one({"_id": ObjectId(conversation["candidate_id"])})
    job = db.jobs.find_one({"_id": ObjectId(conversation["job_id"])})

    messages = conversation.get("messages", [])
    questions_asked = conversation.get("questions_asked", 0)

    # Add candidate message
    messages.append({
        "role": "candidate",
        "content": candidate_message,
        "timestamp": datetime.utcnow()
    })

    # Generate next question FIRST
    next_question = get_next_question(messages, candidate, job, questions_asked)
    questions_asked += 1

    messages.append({
        "role": "agent",
        "content": next_question,
        "timestamp": datetime.utcnow()
    })

    # NOW check if completed AFTER adding the question
    completed = questions_asked >= MAX_QUESTIONS

    if completed:
        # Add closing message
        closing = get_closing_message(candidate.get("name", ""))
        messages.append({
            "role": "agent",
            "content": closing,
            "timestamp": datetime.utcnow()
        })
        db.conversations.update_one(
            {"_id": ObjectId(conversation_id)},
            {"$set": {
                "messages": messages,
                "chat_status": "completed",
                "completed_at": datetime.utcnow(),
                "questions_asked": questions_asked
            }}
        )
        return {
            "message": closing,
            "completed": True,
            "questions_asked": questions_asked,
            "max_questions": MAX_QUESTIONS
        }

    db.conversations.update_one(
        {"_id": ObjectId(conversation_id)},
        {"$set": {
            "messages": messages,
            "questions_asked": questions_asked
        }}
    )

    return {
        "message": next_question,
        "completed": False,
        "questions_asked": questions_asked,
        "max_questions": MAX_QUESTIONS
    }