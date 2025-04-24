from fastapi import FastAPI, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Optional
import logging
from models import SignupModel, LoginModel, RequestOTPModel
from database import users_collection
from utils import generate_otp, send_otp_email, store_otp, verify_otp
from passlib.context import CryptContext
from bson.objectid import ObjectId


import fitz  # PyMuPDF
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Spacer, Paragraph
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from ats_utils import extract_keywords, evaluate_ats_score 
from ai_agent import get_rewritten_resume

app = FastAPI(title="OptiCV Resume Optimizer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

resume_text_global: Optional[str] = None
rewritten_resume_global: Optional[str] = None




pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@app.post("/request-otp")
async def request_otp(data: RequestOTPModel):
    # ✅ Fix: await the DB call!
    existing_user = await users_collection.find_one({"email": data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already signed up. Please log in.")

    otp = generate_otp()
    try:
        send_otp_email(data.email, otp)
        store_otp(data.email, otp)
        return {"message": f"OTP sent to {data.email}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send OTP: {str(e)}")

@app.post("/signup")
async def signup(data: SignupModel):
    user = await users_collection.find_one({"email": data.email})
    if user:
        raise HTTPException(status_code=400, detail="User already exists")

    if not verify_otp(data.email, data.otp):
        raise HTTPException(status_code=400, detail="Invalid OTP")

    hashed_password = pwd_context.hash(data.password)
    await users_collection.insert_one({
        "email": data.email,
        "password": hashed_password
    })
    return {"message": "User registered successfully"}

@app.post("/login")
async def login(data: LoginModel):
    user = await users_collection.find_one({"email": data.email})
    if not user or not pwd_context.verify(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"message": "Login successful"}


@app.post("/upload")
async def upload_resume(resume: UploadFile, jd: str = Form(...)):
    global resume_text_global
    contents = await resume.read()
    pdf = fitz.open(stream=contents, filetype="pdf")
    extracted_text = "\n".join([page.get_text() for page in pdf])
    resume_text_global = extracted_text

    return {
        "message": "Resume uploaded successfully",
        "resume_text": extracted_text,
        "job_description": jd
    }

@app.post("/ats-score")
async def ats_score(jd: str = Form(...)):
    if not resume_text_global:
        return JSONResponse(status_code=400, content={"error": "Upload resume first."})

    jd_keywords = extract_keywords(jd)
    final_score, keyword_score, similarity_score = evaluate_ats_score(resume_text_global, jd_keywords)

    return {
        "ats_score": final_score,
        "keyword_score": keyword_score,
        "similarity_score": similarity_score
    }

@app.post("/rewrite")
async def rewrite_resume(jd: str = Form(...)):
    global rewritten_resume_global
    if not resume_text_global:
        return JSONResponse(status_code=400, content={"error": "Upload resume first."})

    rewritten_resume = await get_rewritten_resume(resume_text_global, jd)
    rewritten_resume_global = rewritten_resume

    jd_keywords = extract_keywords(jd)

   
    final_score, keyword_score, similarity_score = evaluate_ats_score(rewritten_resume, jd_keywords)

    return {
        "rewritten_resume": rewritten_resume,
        "ats_score": final_score
    }

@app.get("/generate-ats-pdf")
async def generate_ats_pdf():
    if not rewritten_resume_global:
        return JSONResponse(status_code=400, content={"error": "No resume to convert"})

    buffer = BytesIO()

    try:
        pdfmetrics.registerFont(TTFont('Arial', 'Arial.ttf'))
        pdfmetrics.registerFont(TTFont('Arial-Bold', 'Arial Bold.ttf'))
        base_font = 'Arial'
    except Exception as e:
        base_font = 'Helvetica'
        logging.warning(f"Arial font not found - falling back to Helvetica. Error: {str(e)}")

    styles = {
        'title': ParagraphStyle(
            name='Title',
            fontName=f'{base_font}-Bold' if base_font == 'Arial' else 'Helvetica-Bold',
            fontSize=14,
            leading=16,
            spaceAfter=12,
            alignment=1  
        ),
        'section': ParagraphStyle(
            name='Section',
            fontName=f'{base_font}-Bold' if base_font == 'Arial' else 'Helvetica-Bold',
            fontSize=12,
            leading=14,
            spaceAfter=8,
            textTransform='uppercase',
            alignment=1 
        ),
        'bullet': ParagraphStyle(
            name='Bullet',
            fontName=base_font,
            fontSize=11,
            leading=13,
            leftIndent=10,
            bulletIndent=5,
            spaceBefore=4,
            spaceAfter=4,
            alignment=1 
        ),
        'normal': ParagraphStyle(
            name='Normal',
            fontName=base_font,
            fontSize=11,
            leading=13,
            spaceAfter=6,
            alignment=1  
        ),
        'footer': ParagraphStyle(
            name='Footer',
            fontName=base_font,
            fontSize=8,
            leading=10,
            alignment=1,  
            textColor=colors.grey
        ),
    }

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=36,  
        rightMargin=36,
        topMargin=72, 
        bottomMargin=36
    )
    
    story = []
    current_section = None
    
    
    
    for line in rewritten_resume_global.split('\n'):
        line = line.strip()
        if not line:
            continue
        if line.upper() in ['PROFESSIONAL SUMMARY', 'WORK EXPERIENCE', 
                          'EDUCATION', 'TECHNICAL SKILLS', 'PROJECTS']:
            current_section = line.upper()
            story.append(Paragraph(f"<b>{current_section}</b>", styles['section']))
            continue
        
        if line.startswith(('- ', '• ', '* ')):
            story.append(Paragraph(f"• {line[2:]}", styles['bullet']))
        elif any(x in line.lower() for x in ['@', 'linkedin.com', 'github.com']):
            story.append(Paragraph(line, styles['normal']))
        else:
            story.append(Paragraph(line, styles['normal']))

        story.append(Spacer(1, 4))  
    def add_footer(canvas, doc):
        canvas.saveState()
        footer_text = f"Page {doc.page}"
        canvas.setFont('Helvetica', 8)
        canvas.drawString(270, 30, footer_text) 
        canvas.restoreState()

    doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)

    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=ats_optimized_resume.pdf",
            "Content-Type": "application/pdf",
            "X-ATS-Optimized": "true" 
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=9999)
