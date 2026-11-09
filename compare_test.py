from sentence_transformers import SentenceTransformer, util
from app.services.keyword_matcher import keyword_score

student_interest = "natural language processing and machine translation"

opportunities = [
    "Fully funded PhD on large language models and text understanding",
    "Research position on speech recognition and multilingual NLP",
    "PhD in software testing and automated program repair",
    "Master's scholarship in computer networks and cybersecurity",
    "Funded PhD in computer vision and medical image analysis",
    "Scholarship for master's students in civil engineering",
]

model = SentenceTransformer("all-MiniLM-L6-v2")
student_vec = model.encode(student_interest, convert_to_tensor=True)
opp_vecs = model.encode(opportunities, convert_to_tensor=True)
semantic = util.cos_sim(student_vec, opp_vecs)[0]

print(f"{'keyword':>8} {'semantic':>9}  opportunity")
for text, sem in zip(opportunities, semantic):
    kw, matched = keyword_score(student_interest, text)
    print(f"{kw:8.3f} {float(sem):9.3f}  {text}  {matched}")