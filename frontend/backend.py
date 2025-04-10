from fastapi import FastAPI, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Optional

import fitz  # PyMuPDF
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from sentence_transformers import SentenceTransformer, util

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


similarity_model = SentenceTransformer("all-MiniLM-L6-v2")

def extract_keywords(text, top_n=15):
    words = text.lower().split()
    keywords = [w.strip(".,:-()") for w in words if len(w) > 3]
    freq = {}
    for word in keywords:
        freq[word] = freq.get(word, 0) + 1
    sorted_keywords = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [kw for kw, _ in sorted_keywords[:top_n]]

def evaluate_ats_score(resume, jd_keywords):
    resume_text = resume.lower()
    keyword_matches = sum(1 for word in jd_keywords if word in resume_text)
    keyword_score = round((keyword_matches / len(jd_keywords)) * 100, 2)

    embedding1 = similarity_model.encode(resume, convert_to_tensor=True)
    embedding2 = similarity_model.encode(" ".join(jd_keywords), convert_to_tensor=True)
    similarity_score = round(util.pytorch_cos_sim(embedding1, embedding2).item() * 100, 2)

    final_score = round((keyword_score * 0.6 + similarity_score * 0.4), 2)
    return final_score, keyword_score, similarity_score

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

    rewritten_resume = get_rewritten_resume(resume_text_global, jd)
    rewritten_resume_global = rewritten_resume

    return {"rewritten_resume": rewritten_resume}

@app.get("/generate-pdf")
def generate_pdf():
    if not rewritten_resume_global:
        return JSONResponse(status_code=400, content={"error": "Rewrite the resume first."})

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    text_object = p.beginText(40, 750)
    text_object.setFont("Helvetica", 10)

    for line in rewritten_resume_global.split("\n"):
        text_object.textLine(line)

    p.drawText(text_object)
    p.showPage()
    p.save()

    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=optimized_resume.pdf"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=9999)