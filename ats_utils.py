from sentence_transformers import SentenceTransformer, util

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
