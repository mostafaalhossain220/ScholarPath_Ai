from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer("all-MiniLM-L6-v2")

student_interest = "natural language processing and machine translation"

opportunities = [
    "Fully funded PhD on large language models and text understanding",
    "Scholarship for master's students in civil engineering",
    "Research position on speech recognition and multilingual NLP",
]

student_vec = model.encode(student_interest, convert_to_tensor=True)
opp_vecs = model.encode(opportunities, convert_to_tensor=True)
scores = util.cos_sim(student_vec, opp_vecs)[0]

for text, score in sorted(zip(opportunities, scores), key=lambda x: -x[1]):
    print(f"{float(score):.3f}  {text}")