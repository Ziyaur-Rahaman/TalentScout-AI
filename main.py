import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from routes import auth, recruiter, candidate, chat
from database import connect_db

app = FastAPI(title="TalentScout AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    connect_db()

# API Routes first
app.include_router(auth.router, prefix="/api/auth")
app.include_router(recruiter.router, prefix="/api/recruiter")
app.include_router(candidate.router, prefix="/api/candidate")
app.include_router(chat.router, prefix="/api/chat")

# Serve landing page at root
@app.get("/")
def root():
    return FileResponse("static/index.html")

@app.get("/login.html")
def login_page():
    return FileResponse("static/login.html")

@app.get("/register.html")
def register_page():
    return FileResponse("static/register.html")

@app.get("/recruiter.html")
def recruiter_page():
    return FileResponse("static/recruiter.html")

@app.get("/candidate.html")
def candidate_page():
    return FileResponse("static/candidate.html")

@app.get("/chat.html")
def chat_page():
    return FileResponse("static/chat.html")

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")