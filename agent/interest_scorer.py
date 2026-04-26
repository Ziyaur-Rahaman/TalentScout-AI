from langchain_groq import ChatGroq
from database import get_db
from dotenv import load_dotenv
from bson import ObjectId
import os
import json

load_dotenv()

llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model_name="llama-3.3-70b-versatile",
    temperature=0
)

def score_interest(conversation_id: str) -> dict:
    """
    Analyze completed conversation and calculate interest score
    """
    db = get_db()

    conversation = db.conversations.find_one({"_id": ObjectId(conversation_id)})
    if not conversation:
        raise ValueError("Conversation not found")

    job = db.jobs.find_one({"_id": ObjectId(conversation["job_id"])})
    parsed_jd = job.get("parsed_data", {})

    # Format conversation
    messages = conversation.get("messages", [])
    conversation_text = "\n".join([
        f"{msg['role'].upper()}: {msg['content']}"
        for msg in messages
    ])

    prompt = f"""
You are an expert recruiter analyzing a candidate screening conversation.

JOB DETAILS:
- Role: {parsed_jd.get('role')}
- Location: {parsed_jd.get('location')}
- Salary Range: {parsed_jd.get('salary_min')} - {parsed_jd.get('salary_max')} LPA
- Job Type: {parsed_jd.get('job_preference')}

CONVERSATION TRANSCRIPT:
{conversation_text}

Analyze the conversation and score the candidate's genuine interest from 0-100.

Scoring criteria:
1. Job Search Status (25 points) - actively looking scores higher
2. Enthusiasm (25 points) - positive, engaged responses
3. Salary Alignment (20 points) - expected salary fits the range
4. Availability (15 points) - notice period fits requirements
5. Location Fit (15 points) - location/preference matches

Return ONLY valid JSON:
{{
  "interest_score": 85,
  "status_score": 22,
  "enthusiasm_score": 20,
  "salary_score": 18,
  "availability_score": 13,
  "location_score": 12,
  "interest_level": "High",
  "key_positives": ["Actively looking", "Salary fits range", "Immediate joiner"],
  "key_concerns": ["Prefers remote but role is onsite"],
  "summary": "Candidate shows high interest with strong enthusiasm and salary alignment."
}}

interest_level must be one of: "High", "Medium", "Low"
Return ONLY JSON, no markdown, no explanation.
"""

    response = llm.invoke(prompt)
    content = response.content.strip()

    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()

    return json.loads(content)