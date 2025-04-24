import os
import logging
import re
import asyncio
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from ats_utils import extract_keywords, evaluate_ats_score

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


section_llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.2)
feedback_llm = ChatGroq(model_name="llama-3.1-8b-instant", temperature=0.25)

EDUCATION_ALIASES = {
    "education", "academic background", "academic qualifications",
    "academic history", "educational qualifications", "qualifications",
    "academics", "educational background"
}
PERSONAL_ALIASES = {
    "personal information", "personal details", "contact information",
    "contact details", "profile", "about me"
}

COLLEGE_PATTERN = re.compile(r"\b(college|institute|university|academy|school of)\b", re.IGNORECASE)
EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_PATTERN = re.compile(r"\+?[0-9]{1,4}?[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,3}[-.\s]?\d{1,4}")
SOCIAL_LINKS_PATTERN = re.compile(r"(linkedin|github)\.(com|in)\/([A-Za-z0-9-]+)", re.IGNORECASE)

section_prompt = ChatPromptTemplate.from_template("""
You are an expert Resume Optimization Assistant specializing in ATS alignment and professional resume writing.

🎯 OBJECTIVES:
1. Optimize for these specific keywords: {keywords}
   - Prioritize natural incorporation of multi-word phrases
   - Maintain original meaning while including keywords
2. Enhance professional impact by:
   - Quantifying achievements (metrics, percentages, $ amounts)
   - Using strong action verbs
   - Following the STAR method (Situation-Task-Action-Result)
3. Improve readability with:
   - Consistent bullet point structure
   - Parallel grammatical structure
   - Concise phrasing (1-2 lines per bullet)

📌 STRICT RULES:
- NEVER add skills/experience not in original
- Preserve all factual information
- Maintain original section length ±20%
- Use only professional, formal language

📝 TRANSFORMATION GUIDELINES:
BAD: "Managed team projects"
GOOD: "Led 5 cross-functional projects (3-8 members each), delivering all on time and 15% under budget"

Now optimize this {section_type} section while following all above rules:

Original Section:
{section_text}

Job Description Context:
{job_description}

Return ONLY the optimized section content (no headings or extra text).
""")
section_chain = section_prompt | section_llm | StrOutputParser()

feedback_prompt = ChatPromptTemplate.from_template("""
You are a Senior Resume Refinement Specialist conducting final quality assurance.

ANALYSIS:
- Original ATS Score: {ats_score}%
  - Keyword Match: {keyword_score}%
  - Semantic Similarity: {similarity_score}%
- Job Description Keywords: {keywords}

TASK:
Perform FINAL optimization pass to:
1. Maximize keyword density without sacrificing readability
2. Improve semantic alignment where similarity score was low
3. Ensure all sections maintain consistent:
   - Verb tense (past/present)
   - Bullet formatting
   - Measurement units (%, $, numbers)
4. Resolve any remaining issues:
   - Overly long bullet points
   - Passive voice
   - Vague content without metrics

RULES:
- Only refine based on original resume content
- Preserve all factual data
- Prioritize clarity over keyword stuffing

Input Resume:
{resume}

Return ONLY the improved resume with NO additional commentary.
""")
feedback_chain = feedback_prompt | feedback_llm | StrOutputParser()

async def rewrite_section(section_type, section_text, jd_keywords, job_description):
    try:
        logging.info(f"Rewriting section: {section_type}")
        if len(section_text.split('\n')) < 2 and len(section_text) < 100:
            return section_type, section_text.strip()

        result = await section_chain.ainvoke({
            "section_type": section_type,
            "section_text": section_text.strip(),
            "job_description": job_description,
            "keywords": ", ".join(jd_keywords)
        })

        return section_type, re.sub(r'\n{3,}', '\n\n', result.strip())

    except Exception as e:
        logging.error(f"Error rewriting {section_type}: {e}")
        return section_type, section_text.strip()

def normalize_header(header):
    return header.lower().strip()

async def get_rewritten_resume(resume_text, job_description):
    logging.info("Starting resume optimization...")
    jd_keywords = extract_keywords(job_description)
    logging.info(f"Extracted JD Keywords: {jd_keywords}")

    lines = resume_text.splitlines()
    sections, index = {}, 0
    personal_lines = []

    for i, line in enumerate(lines[:10]):
        if any([  
            re.search(EMAIL_PATTERN, line),
            re.search(PHONE_PATTERN, line),
            re.search(SOCIAL_LINKS_PATTERN, line)
        ]) or re.match(r"^[A-Z][A-Za-z\s]+$", line.strip()):
            personal_lines.append(line)
        else:
            break

    if personal_lines:
        sections["Personal Details"] = "\n".join(personal_lines)
        index = len(personal_lines)

    current_section = None
    for line in lines[index:]:
        clean = line.strip()
        if not clean:
            continue
        norm = normalize_header(clean)
        is_education = any(norm == alias or norm.startswith(alias) for alias in EDUCATION_ALIASES)
        is_personal = any(norm == alias or norm.startswith(alias) for alias in PERSONAL_ALIASES)
        is_header = (is_education or is_personal or 
                    re.match(r"^[A-Z][A-Za-z\s]+$", clean))
        
        if is_header:
            current_section = clean
            sections[current_section] = ""
        elif current_section:
            sections[current_section] += line + "\n"

    if not any(normalize_header(k) in EDUCATION_ALIASES for k in sections):
        edu_lines = [line for line in lines if COLLEGE_PATTERN.search(line)]
        if edu_lines:
            sections["Education"] = "\n".join(edu_lines)

    rewritable_sections, excluded_sections = {}, {}
    for header, content in sections.items():
        norm = normalize_header(header)
        is_excluded = (
            any(norm == alias or norm.startswith(alias) for alias in EDUCATION_ALIASES) or
            any(norm == alias or norm.startswith(alias) for alias in PERSONAL_ALIASES)
        )
        
        if is_excluded:
            excluded_sections[header] = content.strip()
        else:
            rewritable_sections[header] = content.strip()

    if "Education" in sections and sections["Education"].strip():
        excluded_sections["Education"] = sections["Education"].strip()
        del sections["Education"]  # Remove from rewritable sections

    tasks = [
        rewrite_section(header, content, jd_keywords, job_description)
        for header, content in rewritable_sections.items() if content.strip()
    ]
    rewritten = await asyncio.gather(*tasks)
    rewritten_dict = dict(rewritten)

    all_sections = {**rewritten_dict, **excluded_sections}
    ordered_resume = "\n\n".join(
        f"{header}\n{all_sections[header]}" 
        for header in sections 
        if header in all_sections
    )

    ats_score_1, keyword_score_1, similarity_score_1 = evaluate_ats_score(ordered_resume, jd_keywords)
    

    improved_resume = await feedback_chain.ainvoke({
        "resume": ordered_resume,
        "original_resume": resume_text,
        "ats_score": ats_score_1,
        "keyword_score": keyword_score_1,
        "similarity_score": similarity_score_1,
        "keywords": ", ".join(jd_keywords)
    })

    ats_score_2, _, similarity_score_2 = evaluate_ats_score(improved_resume, jd_keywords)
    

    return improved_resume.strip()

if __name__ == "__main__":
    resume_text = """
    Jane Doe
    johndoe@gmail.com | +1234567890 | github.com/johndoe | linkedin.com/in/johndoe
    Summary: Enthusiastic software engineer with expertise in Python and AI.
    Skills: Python, ML, NLP, TensorFlow, PyTorch
    Experience: Software Engineer at XYZ Corp
    """

    job_description = "Looking for a software engineer with experience in AI, Python, and TensorFlow."
    rewritten = asyncio.run(get_rewritten_resume(resume_text, job_description))
    print(rewritten)
