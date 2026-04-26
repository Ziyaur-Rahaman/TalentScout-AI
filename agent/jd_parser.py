from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os
import json

load_dotenv()

# Initialize Groq LLM
llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model_name="llama-3.3-70b-versatile",
    temperature=0
)

def parse_jd(jd_text: str) -> dict:
    """
    Parse raw JD text and extract structured data
    """

    prompt = f"""
You are an expert HR assistant. Extract structured information from this job description.

JD TEXT:
{jd_text}

Return ONLY a valid JSON object with exactly these fields:
{{
  "role": "job title/role name",
  "required_skills": ["skill1", "skill2", "skill3"],
  "nice_to_have_skills": ["skill1", "skill2"],
  "experience_years": 2,
  "location": "city name or remote",
  "salary_min": 8,
  "salary_max": 12,
  "job_preference": "remote or onsite or hybrid",
  "notice_period_days": 30,
  "responsibilities": ["resp1", "resp2"],
  "qualifications": ["qual1", "qual2"]
}}

Rules:
- experience_years: integer (minimum years required)
- salary_min and salary_max: numbers in LPA (if not mentioned use 0)
- job_preference: must be exactly "remote", "onsite", or "hybrid"
- notice_period_days: integer (if not mentioned use 30)
- Return ONLY the JSON, no explanation, no markdown
"""

    response = llm.invoke(prompt)
    content = response.content.strip()

    # Clean any markdown if present
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()

    parsed = json.loads(content)
    return parsed


def parse_jd_from_file(file_bytes: bytes, file_type: str) -> dict:
    """
    Extract text from PDF or DOCX then parse JD
    """
    text = ""

    if file_type == "pdf":
        import PyPDF2
        import io
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        for page in reader.pages:
            text += page.extract_text() or ""

    elif file_type == "docx":
        from docx import Document
        import io
        doc = Document(io.BytesIO(file_bytes))
        for para in doc.paragraphs:
            text += para.text + "\n"

    if not text.strip():
        raise ValueError("Could not extract text from file")

    return parse_jd(text)