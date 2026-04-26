# TalentScout AI 🤖
### AI-Powered Autonomous Talent Scouting & Engagement Agent

> Built for **Catalyst Hackathon by Deccan AI**
> Submission by **Shaik Ziyaur Rahaman**

---

## 🎯 Problem Statement

Recruiters spend hours sifting through profiles and chasing candidate interest. TalentScout AI is an autonomous AI agent that takes a Job Description as input, discovers matching candidates, engages them conversationally to assess genuine interest, and outputs a ranked shortlist scored on two dimensions: **Match Score** and **Interest Score** — with zero recruiter involvement in between.

---

## 🚀 Live Demo

- **Deployed URL:** `https://talentscout-ai-1.onrender.com`
- **Demo Video:** `https://your-loom-link`
- **GitHub:** `https://github.com/Ziyaur-Rahaman/TalentScout-AI.git`

---

## ✨ Key Features

### For Recruiters
- Post jobs via **text paste, PDF upload, or DOCX upload**
- AI agent **automatically parses JD** and extracts structured requirements
- Agent **scans all registered candidates** and scores each on match
- **Live dashboard** showing candidate chat status in real time
- **Automated report generation** (3 trigger modes)
- **Download ranked report as PDF**
- **Delete jobs** with all associated data
- **Analytics dashboard** — platform stats, chats completed, candidates registered

### For Candidates
- Register with full profile — skills, experience, salary, preferences
- **AI agent proactively reaches out** when a matching job is posted
- **Autonomous chat** — AI conducts 5-question screening interview
- Candidate just answers — no recruiter involved
- See **application status** — Under Review / Shortlisted / Not Selected
- View **Match Score, Interest Score, Final Score** on dashboard

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                              │
│   Landing Page → Auth → Recruiter Dashboard → Candidate     │
│                    Dashboard → AI Chat UI                    │
│              HTML + Tailwind CSS + Vanilla JS                │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP REST API
┌──────────────────────▼──────────────────────────────────────┐
│                     FASTAPI BACKEND                          │
│                                                              │
│   /api/auth        → Register, Login (JWT)                  │
│   /api/recruiter   → Post Job, Analytics, Report, Delete    │
│   /api/candidate   → Dashboard, Conversation Status         │
│   /api/chat        → Start Chat, Send Message, Get Messages │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                  LANGGRAPH AI AGENT PIPELINE                 │
│                                                              │
│  ┌─────────────┐   ┌──────────────┐   ┌─────────────────┐  │
│  │  Node 1     │   │   Node 2     │   │    Node 3       │  │
│  │  JD Parser  │──▶│  Candidate   │──▶│  Chat Conductor │  │
│  │             │   │  Matcher     │   │  (Autonomous)   │  │
│  │ Extracts:   │   │             │   │                 │  │
│  │ - Skills    │   │ Match Score  │   │  5 Questions    │  │
│  │ - Exp years │   │ (0-100)      │   │  Smart follow-  │  │
│  │ - Location  │   │ Explainability│  │  up based on   │  │
│  │ - Salary    │   │              │   │  candidate      │  │
│  │ - Job type  │   │ Top 15 only  │   │  profile        │  │
│  └─────────────┘   └──────────────┘   └────────┬────────┘  │
│                                                 │           │
│  ┌──────────────────────────────────────────────▼────────┐  │
│  │              Node 4: Interest Scorer                   │  │
│  │   Analyzes conversation → Interest Score (0-100)      │  │
│  │   Evaluates: enthusiasm, salary fit, availability,    │  │
│  │   location match, job search status                   │  │
│  └──────────────────────────────┬────────────────────────┘  │
│                                 │                            │
│  ┌──────────────────────────────▼────────────────────────┐  │
│  │              Node 5: Final Ranker                      │  │
│  │   Final Score = (Match × 0.6) + (Interest × 0.4)     │  │
│  │   Sort by Final Score → Generate Report               │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                   INFRASTRUCTURE                             │
│   MongoDB Atlas  → Cloud database (free tier)               │
│   Groq API       → LLM inference (llama-3.3-70b-versatile) │
│   Render         → Deployment (free tier)                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🧠 AI Agent Deep Dive

### Node 1 — JD Parser
Accepts raw JD text, PDF, or DOCX. Uses Groq LLM to extract:
```json
{
  "role": "AI Backend Engineer",
  "required_skills": ["Python", "FastAPI", "LangChain"],
  "experience_years": 1,
  "location": "Hyderabad",
  "salary_min": 8,
  "salary_max": 14,
  "job_preference": "hybrid",
  "notice_period_days": 30
}
```

### Node 2 — Candidate Matcher & Scorer
Scans ALL registered candidates. For each candidate, Groq LLM scores:

| Dimension | Weight | Description |
|---|---|---|
| Skills Match | 40 pts | Required skills overlap |
| Experience | 20 pts | Years vs requirement |
| Location | 15 pts | City/remote compatibility |
| Salary | 15 pts | Expected vs offered range |
| Availability | 10 pts | Notice period + status |

Returns **Match Score (0-100)** + explanation per candidate. Top 15 forwarded.

### Node 3 — Chat Conductor (Autonomous)
The heart of the system. AI plays the recruiter role completely:
- Generates **personalized opening message** per candidate
- Asks **5 smart questions** based on JD + candidate profile
- **Adapts questions** based on previous answers
- No recruiter types anything — fully autonomous

**Sample conversation:**
```
🤖 Agent:  "Hi Ziyaur! I found your profile matches our AI Backend 
            Engineer role in Hyderabad (8-14 LPA). Got 3 minutes?"

👤 Candidate: "Yes, sure!"

🤖 Agent:  "Great! Are you currently actively looking or just open 
            to good opportunities?"

👤 Candidate: "Actively looking"

🤖 Agent:  "Your profile shows Python and FastAPI experience. 
            Have you worked with LangChain or LangGraph before?"

👤 Candidate: "Yes, built 2 production projects with LangGraph"

🤖 Agent:  "The role is hybrid in Hyderabad. Are you comfortable 
            with that?"

👤 Candidate: "Yes, I'm based in Hyderabad"

🤖 Agent:  "Budget is 8-14 LPA. What's your expected CTC?"

👤 Candidate: "Around 10-11 LPA"

🤖 Agent:  "Last one — what's your notice period?"

👤 Candidate: "Immediate joiner"

🤖 Agent:  "Thank you Ziyaur! Our recruiter will review your 
            profile and reach out within 24 hours if shortlisted."
```

### Node 4 — Interest Scorer
Groq LLM reads the **full conversation transcript** and scores:

| Dimension | Weight | Description |
|---|---|---|
| Job Search Status | 25 pts | Actively looking scores higher |
| Enthusiasm | 25 pts | Positive, engaged responses |
| Salary Alignment | 20 pts | Expected vs offered |
| Availability | 15 pts | Notice period fit |
| Location Fit | 15 pts | Location compatibility |

Returns **Interest Score (0-100)** + interest level + key positives/concerns

### Node 5 — Final Ranker
```
Final Score = (Match Score × 0.6) + (Interest Score × 0.4)
```
Sorts all candidates, assigns statuses, generates report.

---

## 📊 Report Generation — 3 Trigger Modes

```
WAY 1 → 24 hours after job posted → AUTO generates
WAY 2 → All candidates completed chat → AUTO generates  
WAY 3 → Recruiter clicks "Generate Now" → MANUAL

Rule: Only ONE report per job (atomic MongoDB update prevents duplicates)
```

**Report contains:**
- Total matched / responded / no response
- Ranked shortlist with Match + Interest + Final scores
- Explainability per candidate (why matched, positives, concerns)
- Candidates who didn't respond (listed separately)
- Downloadable as professional PDF

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Backend | FastAPI + Uvicorn | REST API server |
| AI Agent | LangGraph + LangChain | Agent pipeline orchestration |
| LLM | Groq (llama-3.3-70b-versatile) | Ultra-fast AI inference |
| Database | MongoDB Atlas | Cloud document storage |
| Auth | passlib + python-jose | Password hashing + JWT tokens |
| File Parsing | PyPDF2 + python-docx | PDF and DOCX JD extraction |
| PDF Reports | ReportLab | Professional PDF generation |
| Frontend | HTML + Tailwind CSS + JS | Clean responsive UI |
| Deployment | Render | Free cloud hosting |

---

## 📁 Project Structure

```
talent-scout/
├── main.py                    # FastAPI app entry point
├── database.py                # MongoDB Atlas connection
├── models.py                  # Pydantic models + enums
├── auth.py                    # JWT auth + password hashing
├── seed.py                    # Demo data injection script
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables
│
├── agent/
│   ├── __init__.py
│   ├── jd_parser.py           # Node 1: Parse JD text/PDF/DOCX
│   ├── matcher.py             # Node 2: Score candidates vs JD
│   ├── chat_conductor.py      # Node 3: Autonomous AI chat
│   ├── interest_scorer.py     # Node 4: Score conversation
│   └── ranker.py              # Node 5: Rank + generate report
│
├── routes/
│   ├── __init__.py
│   ├── auth.py                # Register + Login endpoints
│   ├── recruiter.py           # Job posting + analytics + report
│   ├── candidate.py           # Dashboard + conversation status
│   └── chat.py                # Chat start + message endpoints
│
├── utils/
│   ├── __init__.py
│   └── file_parser.py         # PDF + DOCX text extraction
│
└── static/
    ├── index.html             # Landing page
    ├── login.html             # Login (recruiter + candidate)
    ├── register.html          # Register (recruiter + candidate)
    ├── recruiter.html         # Recruiter dashboard
    ├── candidate.html         # Candidate dashboard
    └── chat.html              # AI conversation UI
```

---

## ⚙️ Local Setup Instructions

### Prerequisites
- Python 3.11+
- MongoDB Atlas account (free)
- Groq API key (free)

### Step 1 — Clone repo
```bash
git clone https://github.com/your-username/talent-scout.git
cd talent-scout
```

### Step 2 — Create virtual environment
```bash
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
```

### Step 3 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Setup environment variables
Create `.env` file:
```env
GROQ_API_KEY=your_groq_api_key_here
MONGODB_URL=your_mongodb_atlas_connection_string
SECRET_KEY=your_random_secret_key_here
DATABASE_NAME=talentscout
ACCESS_TOKEN_EXPIRE_MINUTES=1440
CHAT_WINDOW_HOURS=24
```

**Get Groq API Key:** https://console.groq.com → Free account → Create API key

**Get MongoDB URL:** https://mongodb.com/atlas → Free M0 cluster → Connect → Copy connection string

**Generate Secret Key:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Step 5 — Seed demo data
```bash
python seed.py
```

### Step 6 — Run server
```bash
python -m uvicorn main:app --reload
```

### Step 7 — Open browser
```
http://localhost:8000
```

---

## 🔐 Demo Credentials

### Recruiter
```
Email:    recruiter@techventures.com
Password: recruiter123
```

### Candidates (all use password: candidate123)
```
Ziyaur Rahaman   → ziyaur@gmail.com        (Strong Match)
Priya Nair       → priya.nair@gmail.com    (Strong Match)
Rahul Sharma     → rahul.sharma@gmail.com  (Strong Match)
Sneha Reddy      → sneha.reddy@gmail.com   (Good Match)
Amit Kumar       → amit.kumar@gmail.com    (Weak Match)
Kavya Singh      → kavya.singh@gmail.com   (Weak Match)
```

---

## 🎬 Demo Flow

```
1. Login as Recruiter
2. Paste JD or upload PDF → Click "Find Candidates Automatically"
3. Agent parses JD + scores all 6 candidates (30-60 seconds)
4. See matched candidates with scores in job details

5. Login as Ziyaur → See job match → Click "Start Chat"
6. Chat with AI agent (5 questions, ~3 minutes)
7. Repeat for Priya, Rahul, Sneha

8. Login as Recruiter → Click "Generate Report Now"
9. See ranked shortlist with scores + explanations
10. Download PDF report
```

---

## 📊 Sample Input & Output

### Input (JD)
```
Role: AI Backend Engineer
Location: Hyderabad
Experience: 1-3 years | Salary: 8-14 LPA | Type: Hybrid
Required: Python, FastAPI, LangChain, REST API, MongoDB
```

### Output (Ranked Shortlist)
```
Rank  Name            Match  Interest  Final   Status
  1   Ziyaur Rahaman   92     92       92.0   ✅ Shortlisted
  2   Priya Nair       92     92       92.0   ✅ Shortlisted
  3   Rahul Sharma     85     88       86.2   ✅ Shortlisted
  4   Sneha Reddy      78     80       78.8   ✅ Shortlisted
  5   Amit Kumar       35     --        --    ❌ No Response
  6   Kavya Singh      30     --        --    ❌ No Response
```

---

## 🌐 API Endpoints

### Auth
```
POST /api/auth/recruiter/register
POST /api/auth/recruiter/login
POST /api/auth/candidate/register
POST /api/auth/candidate/login
```

### Recruiter
```
POST   /api/recruiter/post-job
POST   /api/recruiter/post-job-file
GET    /api/recruiter/jobs
GET    /api/recruiter/jobs/{job_id}
DELETE /api/recruiter/jobs/{job_id}
POST   /api/recruiter/jobs/{job_id}/generate-report
GET    /api/recruiter/jobs/{job_id}/report
GET    /api/recruiter/jobs/{job_id}/download-report
GET    /api/recruiter/analytics
GET    /api/recruiter/candidate/{candidate_id}
```

### Candidate
```
GET /api/candidate/dashboard
GET /api/candidate/conversation/{conversation_id}
```

### Chat
```
POST /api/chat/start/{conversation_id}
POST /api/chat/message/{conversation_id}
GET  /api/chat/messages/{conversation_id}
```

---

## 🔑 Key Design Decisions

**Why Groq over OpenAI/Gemini?**
Groq delivers 300+ tokens/second — critical for real-time chat. Free tier with high limits made it perfect for this project.

**Why MongoDB over SQL?**
Candidate profiles, conversations, and JD parsed data are all flexible JSON documents. MongoDB's native JSON storage avoids rigid schema constraints.

**Why LangGraph for agent?**
LangGraph provides explicit node-based agent architecture with state management — ideal for a multi-step pipeline where each node has a clear responsibility.

**Why simulate conversations instead of real outreach?**
Building a real platform where candidates register means conversations happen in-app — more reliable, faster, and no email deliverability issues.

**Duplicate report prevention:**
MongoDB's atomic `findOneAndUpdate` with condition `report_generated: False` ensures only one report is ever generated per job, even if multiple triggers fire simultaneously.

---

## 📦 requirements.txt

```
fastapi
uvicorn
langgraph
langchain
langchain-groq
pymongo
python-dotenv
pydantic
groq
passlib[bcrypt]
python-jose[cryptography]
pypdf2
python-docx
python-multipart
certifi
reportlab
bcrypt==4.0.1
```

---

## 🗄️ MongoDB Collections

```
recruiters      → Recruiter accounts
candidates      → Candidate profiles + skills
jobs            → Posted JDs + parsed data + report
matches         → Candidate-Job match scores
conversations   → Chat transcripts + interest scores
```

---

## 👨‍💻 Built By

**Ziyaur Rahaman Shaik**

Full Stack AI Developer | Python | SQL | Node.js | Express | MongoDB | Machine Learning

BTech student in Artificial Intelligence & Machine Learning with a deep passion
for building intelligent backend systems and real-world ML applications.

**Experience:**
- 🏢 Infosys Springboard Intern — NLP & Transformer-based Text Summarization (BART, FLAN-T5)

**Key Projects:**
- 🏙️ UrbanSense AI — Smart city monitoring system with real-time air quality, traffic and weather data. Built with LangGraph agentic AI, FastAPI, React.js, MongoDB, deployed on AWS
- 🌊 Flood & Disaster Prediction System — ML model for early disaster detection and alerting

**Location:** Guntur, Andhra Pradesh, India
---

## 📄 License

MIT License — Built for Catalyst Hackathon by Deccan AI
