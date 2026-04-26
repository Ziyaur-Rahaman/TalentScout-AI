from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from database import get_db
from auth import get_current_recruiter
from models import JobPost
from agent.jd_parser import parse_jd, parse_jd_from_file
from agent.matcher import find_and_score_candidates
from agent.ranker import generate_report
from datetime import datetime, timedelta
from bson import ObjectId
import os
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io

router = APIRouter(tags=["Recruiter"])

@router.get("/jobs/{job_id}/download-report")
def download_report(job_id: str, current_user: dict = Depends(get_current_recruiter)):
    db = get_db()

    job = db.jobs.find_one({"_id": ObjectId(job_id)})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if not job.get("report_generated"):
        raise HTTPException(status_code=404, detail="Report not generated yet")

    report = job.get("report", {})

    # ─────────────────────────────────────────
    # BUILD PDF
    # ─────────────────────────────────────────
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()
    elements = []

    # ── Custom Styles ──
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=22,
        textColor=colors.HexColor('#4f46e5'),
        spaceAfter=6,
        alignment=TA_CENTER
    )
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#6b7280'),
        spaceAfter=4,
        alignment=TA_CENTER
    )
    section_style = ParagraphStyle(
        'Section',
        parent=styles['Heading2'],
        fontSize=13,
        textColor=colors.HexColor('#1e1b4b'),
        spaceBefore=16,
        spaceAfter=8,
        borderPad=4
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#374151'),
        spaceAfter=4,
        leading=16
    )
    small_style = ParagraphStyle(
        'Small',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#6b7280'),
        spaceAfter=3
    )
    rank_style = ParagraphStyle(
        'Rank',
        parent=styles['Normal'],
        fontSize=18,
        textColor=colors.HexColor('#4f46e5'),
        alignment=TA_CENTER
    )

    # ── HEADER ──
    elements.append(Paragraph("TalentScout AI", title_style))
    elements.append(Paragraph("AI-Powered Recruitment Report", subtitle_style))
    elements.append(Spacer(1, 0.3*cm))
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#4f46e5')))
    elements.append(Spacer(1, 0.5*cm))

    # ── JOB INFO ──
    elements.append(Paragraph(f"📋 {report.get('job_title', 'Job Report')}", section_style))

    job_info_data = [
        ['Job Title', report.get('job_title', '-')],
        ['Location', job.get('parsed_data', {}).get('location', '-')],
        ['Salary Range', f"{job.get('parsed_data', {}).get('salary_min', 0)} - {job.get('parsed_data', {}).get('salary_max', 0)} LPA"],
        ['Required Skills', ', '.join(job.get('parsed_data', {}).get('required_skills', []))],
        ['Report Generated', report.get('generated_at', '-')[:19].replace('T', ' ')],
        ['Trigger', report.get('trigger', '-').replace('_', ' ').title()],
    ]

    job_table = Table(job_info_data, colWidths=[4*cm, 12*cm])
    job_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#eef2ff')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#4f46e5')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
        ('ROWBACKGROUNDS', (1, 0), (1, -1), [colors.white, colors.HexColor('#f9fafb')]),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(job_table)
    elements.append(Spacer(1, 0.5*cm))

    # ── SUMMARY STATS ──
    elements.append(Paragraph("📊 Summary", section_style))

    total_matched = report.get('total_matched', 0)
    total_chatted = report.get('total_chatted', 0)
    total_no_response = report.get('total_no_response', 0)
    total_shortlisted = len([
        c for c in report.get('shortlisted', [])
        if c.get('final_score', 0) >= 60
    ])

    total_shortlisted = len(report.get('shortlisted', []))
    total_no_response = len(report.get('no_response', []))

    stats_data = [
        ['Total Matched', 'Responded', 'No Response', 'Shortlisted'],
        [
            str(report.get('total_matched', 0)),
            str(report.get('total_chatted', 0)),
            str(total_no_response),
            str(total_shortlisted)
        ]
    ]

    stats_table = Table(stats_data, colWidths=[4.5*cm, 4.5*cm, 4.5*cm, 4.5*cm])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, 1), 20),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 1), (0, -1), colors.HexColor('#4f46e5')),
        ('TEXTCOLOR', (1, 1), (1, -1), colors.HexColor('#059669')),
        ('TEXTCOLOR', (2, 1), (2, -1), colors.HexColor('#6b7280')),
        ('TEXTCOLOR', (3, 1), (3, -1), colors.HexColor('#7c3aed')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f0fdf4')]),
          ('PADDING', (0, 0), (-1, -1), 18),
        ('TOPPADDING', (0, 1), (-1, 1), 22),
        ('BOTTOMPADDING', (0, 1), (-1, 1), 22),
        ('WORDWRAP', (0, 0), (-1, -1), True),
    ]))
    elements.append(stats_table)
    elements.append(Spacer(1, 0.5*cm))

    # ── SHORTLISTED CANDIDATES ──
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e5e7eb')))
    elements.append(Paragraph("✅ Shortlisted Candidates", section_style))

    for i, candidate in enumerate(report.get('shortlisted', [])):
        # Rank + Name Header
        rank_color = ['#4f46e5', '#7c3aed', '#059669', '#0891b2', '#d97706']
        bg_color = ['#eef2ff', '#f5f3ff', '#f0fdf4', '#ecfeff', '#fffbeb']

        header_data = [[
            Paragraph(f"#{i+1}", ParagraphStyle('r', fontSize=16, textColor=colors.HexColor(rank_color[i % 5]), alignment=TA_CENTER, fontName='Helvetica-Bold')),
            Paragraph(f"<b>{candidate.get('name', '')}</b>", ParagraphStyle('n', fontSize=13, textColor=colors.HexColor('#1e1b4b'), fontName='Helvetica-Bold')),
            Paragraph(
                f"<b>Final Score: {candidate.get('final_score', 0)}/100</b>",
                ParagraphStyle('s', fontSize=12, textColor=colors.HexColor(rank_color[i % 5]), alignment=TA_CENTER, fontName='Helvetica-Bold')
            )
        ]]

        header_table = Table(header_data, colWidths=[1.5*cm, 10*cm, 4.5*cm])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(bg_color[i % 5])),
            ('PADDING', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROUNDEDCORNERS', [4]),
        ]))
        elements.append(header_table)

        # Score Breakdown
        score_data = [
            ['Match Score', 'Interest Score', 'Interest Level', 'Experience'],
            [
                f"{candidate.get('match_score', 0)}/100",
                f"{candidate.get('interest_score', 0)}/100",
                candidate.get('interest_level', '-'),
                f"{candidate.get('experience_years', 0)} years"
            ]
        ]
        score_table = Table(score_data, colWidths=[4*cm, 4*cm, 4*cm, 4*cm])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('TEXTCOLOR', (0, 1), (0, -1), colors.HexColor('#4f46e5')),
            ('TEXTCOLOR', (1, 1), (1, -1), colors.HexColor('#7c3aed')),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica-Bold'),
        ]))
        elements.append(score_table)

        # Details
       # Details — separate rows to avoid overlap
        details = [
            ['Location', candidate.get('location', '-'),
             'Email', candidate.get('email', '-')],
        ]
        details_table = Table(details, colWidths=[3*cm, 6*cm, 2.5*cm, 4.5*cm])
        details_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#4f46e5')),
            ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#4f46e5')),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
            ('PADDING', (0, 0), (-1, -1), 7),
            ('WORDWRAP', (0, 0), (-1, -1), True),
        ]))
        elements.append(details_table)

        # Skills on separate rows — full width to avoid overlap
        skills_data = [
            ['Matched Skills', ', '.join(candidate.get('matched_skills', []))  or 'None'],
            ['Missing Skills', ', '.join(candidate.get('missing_skills', [])) or 'None'],
        ]
        skills_table = Table(skills_data, colWidths=[3*cm, 13*cm])
        skills_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#4f46e5')),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
            ('PADDING', (0, 0), (-1, -1), 7),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
            ('WORDWRAP', (1, 0), (1, -1), True),
        ]))
        elements.append(skills_table)

        # Why matched
        if candidate.get('match_explanation'):
            elements.append(Spacer(1, 0.2*cm))
            elements.append(Paragraph(
                f"<b>Why matched:</b> {candidate.get('match_explanation', '')}",
                small_style
            ))

        # Key Positives
        if candidate.get('key_positives'):
            positives = ' • '.join(candidate.get('key_positives', []))
            elements.append(Paragraph(
                f"<b>✅ Positives:</b> {positives}",
                ParagraphStyle('pos', parent=small_style, textColor=colors.HexColor('#059669'))
            ))

        # Key Concerns
        if candidate.get('key_concerns'):
            concerns = ' • '.join(candidate.get('key_concerns', []))
            elements.append(Paragraph(
                f"<b>⚠️ Concerns:</b> {concerns}",
                ParagraphStyle('con', parent=small_style, textColor=colors.HexColor('#d97706'))
            ))

        elements.append(Spacer(1, 0.4*cm))

    # ── NO RESPONSE ──
    if report.get('no_response'):
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e5e7eb')))
        elements.append(Paragraph("❌ Did Not Respond", section_style))

        no_resp_data = [['Name', 'Match Score', 'Reason']]
        for c in report.get('no_response', []):
            no_resp_data.append([
                c.get('name', '-'),
                f"{c.get('match_score', 0)}/100",
                'Did not respond to chat invitation'
            ])

        no_resp_table = Table(no_resp_data, colWidths=[5*cm, 3*cm, 8*cm])
        no_resp_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#6b7280')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
        ]))
        elements.append(no_resp_table)

    # ── FOOTER ──
    elements.append(Spacer(1, 1*cm))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e5e7eb')))
    elements.append(Spacer(1, 0.3*cm))
    elements.append(Paragraph(
        "Generated by TalentScout AI — AI-Powered Autonomous Recruitment Platform",
        ParagraphStyle('footer', parent=styles['Normal'], fontSize=8,
                      textColor=colors.HexColor('#9ca3af'), alignment=TA_CENTER)
    ))

    # Build PDF
    doc.build(elements)
    buffer.seek(0)

    filename = f"report_{report.get('job_title', 'job').replace(' ', '_')}.pdf"

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# ─────────────────────────────────────────
# POST JOB (text)
# ─────────────────────────────────────────

@router.post("/post-job")
def post_job(data: JobPost, current_user: dict = Depends(get_current_recruiter)):
    db = get_db()

    print(f"📋 Parsing JD for: {data.title}")

    # Parse JD
    parsed_data = parse_jd(data.description)

    # Save job to DB
    job = {
        "recruiter_id": current_user["_id"],
        "title": data.title,
        "description": data.description,
        "parsed_data": parsed_data,
        "matched_count": 0,
        "chatted_count": 0,
        "in_progress_count": 0,
        "not_responded_count": 0,
        "report_generated": False,
        "report_generated_at": None,
        "report_trigger": None,
        "report": None,
        "posted_at": datetime.utcnow(),
        "chat_deadline": datetime.utcnow() + timedelta(hours=24)
    }

    result = db.jobs.insert_one(job)
    job_id = str(result.inserted_id)

    print(f"✅ Job saved: {job_id}")

    # Find and score candidates
    scored_candidates = find_and_score_candidates(parsed_data, job_id)

    if not scored_candidates:
        return {
            "job_id": job_id,
            "message": "Job posted. No matching candidates found yet.",
            "matched_count": 0
        }

    # Save matches to DB
    for candidate in scored_candidates:
        match = {
            "job_id": job_id,
            "candidate_id": candidate["candidate_id"],
            "match_score": candidate["match_score"],
            "skills_score": candidate.get("skills_score", 0),
            "experience_score": candidate.get("experience_score", 0),
            "location_score": candidate.get("location_score", 0),
            "salary_score": candidate.get("salary_score", 0),
            "availability_score": candidate.get("availability_score", 0),
            "matched_skills": candidate.get("matched_skills", []),
            "missing_skills": candidate.get("missing_skills", []),
            "explanation": candidate.get("explanation", ""),
            "recommendation": candidate.get("recommendation", ""),
            "interest_score": None,
            "final_score": None,
            "application_status": "under_review",
            "created_at": datetime.utcnow()
        }
        match_result = db.matches.insert_one(match)
        match_id = str(match_result.inserted_id)

        # Create conversation for each match
        conversation = {
            "match_id": match_id,
            "job_id": job_id,
            "candidate_id": candidate["candidate_id"],
            "messages": [],
            "questions_asked": 0,
            "max_questions": 5,
            "interest_score": None,
            "interest_data": None,
            "final_score": None,
            "chat_status": "pending",
            "started_at": None,
            "completed_at": None,
            "created_at": datetime.utcnow()
        }
        db.conversations.insert_one(conversation)

    # Update job with match count
    db.jobs.update_one(
        {"_id": ObjectId(job_id)},
        {"$set": {
            "matched_count": len(scored_candidates),
            "not_responded_count": len(scored_candidates)
        }}
    )

    print(f"✅ {len(scored_candidates)} candidates matched and notified")

    return {
        "job_id": job_id,
        "message": f"Job posted successfully! {len(scored_candidates)} candidates matched.",
        "matched_count": len(scored_candidates),
        "parsed_jd": parsed_data
    }


# ─────────────────────────────────────────
# POST JOB (file upload)
# ─────────────────────────────────────────

@router.post("/post-job-file")
async def post_job_file(
    title: str = Form(...),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_recruiter)
):
    db = get_db()

    # Determine file type
    filename = file.filename.lower()
    if filename.endswith(".pdf"):
        file_type = "pdf"
    elif filename.endswith(".docx"):
        file_type = "docx"
    else:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files supported")

    file_bytes = await file.read()

    print(f"📎 Parsing {file_type.upper()} file: {filename}")

    # Parse JD from file
    parsed_data = parse_jd_from_file(file_bytes, file_type)

    # Use title from form or from parsed data
    job_title = title or parsed_data.get("role", "Untitled Job")

    # Save job
    job = {
        "recruiter_id": current_user["_id"],
        "title": job_title,
        "description": f"Uploaded from {filename}",
        "parsed_data": parsed_data,
        "matched_count": 0,
        "chatted_count": 0,
        "in_progress_count": 0,
        "not_responded_count": 0,
        "report_generated": False,
        "report_generated_at": None,
        "report_trigger": None,
        "report": None,
        "posted_at": datetime.utcnow(),
        "chat_deadline": datetime.utcnow() + timedelta(hours=24)
    }

    result = db.jobs.insert_one(job)
    job_id = str(result.inserted_id)

    # Find and score candidates
    scored_candidates = find_and_score_candidates(parsed_data, job_id)

    # Save matches
    for candidate in scored_candidates:
        match = {
            "job_id": job_id,
            "candidate_id": candidate["candidate_id"],
            "match_score": candidate["match_score"],
            "matched_skills": candidate.get("matched_skills", []),
            "missing_skills": candidate.get("missing_skills", []),
            "explanation": candidate.get("explanation", ""),
            "recommendation": candidate.get("recommendation", ""),
            "interest_score": None,
            "final_score": None,
            "application_status": "under_review",
            "created_at": datetime.utcnow()
        }
        match_result = db.matches.insert_one(match)
        match_id = str(match_result.inserted_id)

        conversation = {
            "match_id": match_id,
            "job_id": job_id,
            "candidate_id": candidate["candidate_id"],
            "messages": [],
            "questions_asked": 0,
            "max_questions": 5,
            "interest_score": None,
            "final_score": None,
            "chat_status": "pending",
            "started_at": None,
            "completed_at": None,
            "created_at": datetime.utcnow()
        }
        db.conversations.insert_one(conversation)

    db.jobs.update_one(
        {"_id": ObjectId(job_id)},
        {"$set": {
            "matched_count": len(scored_candidates),
            "not_responded_count": len(scored_candidates)
        }}
    )

    return {
        "job_id": job_id,
        "message": f"Job posted successfully! {len(scored_candidates)} candidates matched.",
        "matched_count": len(scored_candidates),
        "parsed_jd": parsed_data
    }


# ─────────────────────────────────────────
# GET ALL JOBS
# ─────────────────────────────────────────

@router.get("/jobs")
def get_jobs(current_user: dict = Depends(get_current_recruiter)):
    db = get_db()

    jobs = list(db.jobs.find(
        {"recruiter_id": current_user["_id"]}
    ).sort("posted_at", -1))

    result = []
    for job in jobs:
        job["_id"] = str(job["_id"])
        job.pop("report", None)  # Exclude full report from list

        # Calculate time remaining
        deadline = job.get("chat_deadline")
        if deadline:
            remaining = deadline - datetime.utcnow()
            hours_left = max(0, int(remaining.total_seconds() / 3600))
            job["hours_left"] = hours_left
        else:
            job["hours_left"] = 0

        result.append(job)

    return result


# ─────────────────────────────────────────
# GET JOB DETAILS + LIVE STATUS
# ─────────────────────────────────────────

@router.get("/jobs/{job_id}")
def get_job_details(job_id: str, current_user: dict = Depends(get_current_recruiter)):
    db = get_db()

    job = db.jobs.find_one({"_id": ObjectId(job_id)})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job["_id"] = str(job["_id"])

    # Get all conversations for live status
    conversations = list(db.conversations.find({"job_id": job_id}))

    candidate_statuses = []
    chatted = 0
    in_progress = 0
    not_responded = 0

    for conv in conversations:
        candidate = db.candidates.find_one(
            {"_id": ObjectId(conv["candidate_id"])}
        )
        match = db.matches.find_one({
            "job_id": job_id,
            "candidate_id": conv["candidate_id"]
        })

        status = conv.get("chat_status", "pending")
        if status == "completed":
            chatted += 1
        elif status == "in_progress":
            in_progress += 1
        else:
            not_responded += 1

        candidate_statuses.append({
            "candidate_id": conv["candidate_id"],
            "name": candidate.get("name") if candidate else "Unknown",
            "chat_status": status,
            "match_score": match.get("match_score") if match else 0,
            "final_score": match.get("final_score") if match else None,
            "started_at": conv.get("started_at"),
            "completed_at": conv.get("completed_at")
        })

    # Update counts
    db.jobs.update_one(
        {"_id": ObjectId(job_id)},
        {"$set": {
            "chatted_count": chatted,
            "in_progress_count": in_progress,
            "not_responded_count": not_responded
        }}
    )

    # Check if should auto generate report (WAY 1 or WAY 2)
    # Check if should auto generate report
    if not job.get("report_generated"):
        deadline = job.get("chat_deadline")
        total_matched = job.get("matched_count", 0)

        # WAY 2 — All candidates chatted (chatted = matched, none pending)
        all_done = total_matched > 0 and (chatted == total_matched)

        # WAY 1 — 24hr window passed
        time_up = deadline and datetime.utcnow() > deadline

        if time_up:
            try:
                generate_report(job_id, "24hr_window")
                print(f"⏰ Auto report: 24hr window")
            except Exception as e:
                print(f"Report error: {e}")
        elif all_done:
            try:
                generate_report(job_id, "all_chatted")
                print(f"✅ Auto report: all chatted")
            except Exception as e:
                print(f"Report error: {e}")

    return {
        **job,
        "chatted_count": chatted,
        "in_progress_count": in_progress,
        "not_responded_count": not_responded,
        "candidate_statuses": candidate_statuses
    }

@router.delete("/jobs/{job_id}")
def delete_job(job_id: str, current_user: dict = Depends(get_current_recruiter)):
    db = get_db()

    job = db.jobs.find_one({"_id": ObjectId(job_id)})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["recruiter_id"] != current_user["_id"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Delete job + all related data
    db.jobs.delete_one({"_id": ObjectId(job_id)})
    db.matches.delete_many({"job_id": job_id})
    db.conversations.delete_many({"job_id": job_id})

    print(f"🗑️ Job {job_id} deleted with all matches and conversations")

    return {"message": "Job deleted successfully"}
# ─────────────────────────────────────────
# GENERATE REPORT MANUALLY (WAY 3)
# ─────────────────────────────────────────

@router.post("/jobs/{job_id}/generate-report")
def manual_generate_report(
    job_id: str,
    current_user: dict = Depends(get_current_recruiter)
):
    db = get_db()

    job = db.jobs.find_one({"_id": ObjectId(job_id)})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.get("report_generated"):
        return {"message": "Report already generated", "report": job.get("report")}

    report = generate_report(job_id, "manual")
    return {"message": "Report generated successfully", "report": report}


# ─────────────────────────────────────────
# GET REPORT
# ─────────────────────────────────────────

@router.get("/jobs/{job_id}/report")
def get_report(job_id: str, current_user: dict = Depends(get_current_recruiter)):
    db = get_db()

    job = db.jobs.find_one({"_id": ObjectId(job_id)})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if not job.get("report_generated"):
        raise HTTPException(status_code=404, detail="Report not generated yet")

    return job.get("report")


# ─────────────────────────────────────────
# GET PLATFORM ANALYTICS
# ─────────────────────────────────────────

@router.get("/analytics")
def get_analytics(current_user: dict = Depends(get_current_recruiter)):
    db = get_db()

    total_candidates = db.candidates.count_documents({})
    actively_looking = db.candidates.count_documents({"status": "actively_looking"})
    open_to_offers = db.candidates.count_documents({"status": "open_to_offers"})
    not_looking = db.candidates.count_documents({"status": "not_looking"})
    total_jobs = db.jobs.count_documents({"recruiter_id": current_user["_id"]})
    total_matches = db.matches.count_documents({})
    total_chats = db.conversations.count_documents({"chat_status": "completed"})

    return {
        "total_candidates": total_candidates,
        "actively_looking": actively_looking,
        "open_to_offers": open_to_offers,
        "not_looking": not_looking,
        "total_jobs": total_jobs,
        "total_matches": total_matches,
        "total_chats_completed": total_chats
    }


# ─────────────────────────────────────────
# GET CANDIDATE PROFILE (for recruiter view)
# ─────────────────────────────────────────

@router.get("/candidate/{candidate_id}")
def get_candidate_profile(
    candidate_id: str,
    current_user: dict = Depends(get_current_recruiter)
):
    db = get_db()

    candidate = db.candidates.find_one({"_id": ObjectId(candidate_id)})
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    candidate["_id"] = str(candidate["_id"])
    candidate.pop("password_hash", None)

    return candidate