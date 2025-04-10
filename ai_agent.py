import os
import logging
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from sentence_transformers import SentenceTransformer, util
from keybert import KeyBERT

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


logging.info("Loading LLM and similarity model...")
section_llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.3)
feedback_llm = ChatGroq(model_name="llama-3.1-8b-instant", temperature=0.3)
similarity_model = SentenceTransformer("all-MiniLM-L6-v2")



sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
kw_model = KeyBERT(model=sentence_model)

def extract_keywords(text, top_n=15):
    keywords = kw_model.extract_keywords(
        text,
        top_n=top_n,
        keyphrase_ngram_range=(1, 3),
        stop_words='english',
        use_maxsum=True,         # Optional: reduces redundancy
        diversity=0.7            # Optional: increases variation
    )
    return [kw for kw, _ in keywords]


def evaluate_ats_score(resume, jd_keywords):
    logging.info("Evaluating ATS Score using keywords + semantic similarity...")
    resume_text = resume.lower()
    keyword_matches = sum(1 for word in jd_keywords if word in resume_text)
    keyword_score = round((keyword_matches / len(jd_keywords)) * 100, 2)
    
    embedding1 = similarity_model.encode(resume, convert_to_tensor=True)
    embedding2 = similarity_model.encode(" ".join(jd_keywords), convert_to_tensor=True)
    similarity_score = round(util.pytorch_cos_sim(embedding1, embedding2).item() * 100, 2)

    final_score = round((keyword_score * 0.6 + similarity_score * 0.4), 2)
    
    logging.info(f"Keyword Score: {keyword_score}%, Semantic Similarity: {similarity_score}%, ATS Score: {final_score}%")
    return final_score, keyword_score, similarity_score


section_prompt = ChatPromptTemplate.from_template("""
You are an expert Resume Optimization Assistant specializing in ATS alignment.

🎯 GOALS:
1. Inject relevant keywords: {keywords}
2. Improve professionalism, clarity, and impact using quantifiable results.
3. Align the resume to the job role by enhancing each section.
4. Keep the information accurate and logically consistent.
5. Maintain a clean, structured format using bullet points.

📌 RULES:
- DO NOT fabricate experience, skills, or achievements.
- Only rephrase or improve what's already present.
- Use impactful, concise phrasing.

Now rewrite the following section of the resume:

✍️ Section Type: {section_type}
📄 Original Section: {section_text}
🧾 Job Description: {job_description}

Return only the improved section.
""")
section_chain = section_prompt | section_llm | StrOutputParser()

feedback_prompt = ChatPromptTemplate.from_template("""
You are a resume refinement assistant.

Here is the original resume:
{original_resume}

Here is the ATS-optimized draft:
{resume}

📊 Scores:
- Current ATS Score: {ats_score}%
- Similarity: {similarity_score}%

Your task:
- Make a final improvement to maximize ATS score
- Ensure it uses relevant keywords from the job description
- Keep it aligned with the original resume

Return the improved resume only.
""")
feedback_chain = feedback_prompt | feedback_llm | StrOutputParser()


def get_rewritten_resume(resume_text, job_description):
    logging.info("Starting resume rewrite process...")

    jd_keywords = extract_keywords(job_description)
    logging.info(f"Jd keywords: {jd_keywords}")

    logging.info("Splitting resume into sections...")
    sections = {
        "Personal Details": "",
        "Summary": "",
        "Skills": "",
        "Experience": "",
        "Projects": "",
        "Education": ""
    }
    current_section = None
    for line in resume_text.splitlines():
        line = line.strip()
        if not line:
            continue
        for section in sections:
            if line.lower().startswith(section.lower()):
                current_section = section
                sections[section] = ""
                break
        else:
            if current_section:
                sections[current_section] += line + "\n"

    logging.info("Rewriting each section using LLM...")
    rewritten_sections = {}
    for sec_type, sec_text in sections.items():
        if sec_text.strip():
            logging.info(f"Rewriting section: {sec_type}")
            
            rewritten = section_chain.invoke({
                "section_type": sec_type,
                "section_text": sec_text.strip(),
                "job_description": job_description,
                "keywords": ", ".join(jd_keywords)
            })
            rewritten_sections[sec_type] = rewritten.strip()
        else:
            rewritten_sections[sec_type] = ""

    first_pass_resume = "\n\n".join(f"{k}\n{v}" for k, v in rewritten_sections.items() if v)

    ats_score_1, keyword_1, similarity_1 = evaluate_ats_score(first_pass_resume, jd_keywords)
    logging.info(f"🔍 ATS Score (Stage 1 - Initial Rewrite): {ats_score_1}%, Similarity: {similarity_1}%")


    logging.info("Refining resume using feedback...")
    improved_resume = feedback_chain.invoke({
        "original_resume": resume_text,
        "resume": first_pass_resume,
        "ats_score": ats_score_1,
        "similarity_score": similarity_1
    })

    ats_score_2, keyword_2, similarity_2 = evaluate_ats_score(improved_resume, jd_keywords)
    logging.info(f"🔁 ATS Score (Stage 2 - Feedback Rewrite): {ats_score_2}%, Similarity: {similarity_2}%")

    final_resume = improved_resume
    return final_resume.strip()
