from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer("all-MiniLM-L6-v2")

def compute_similarity(jd_text, profiles):
    jd_embedding = model.encode(jd_text, convert_to_tensor=True)
    results = []
    for p in profiles:
        emb = model.encode(p.content, convert_to_tensor=True)
        score = util.pytorch_cos_sim(jd_embedding, emb).item()
        results.append((p.id, score))
    return sorted(results, key=lambda x: x[1], reverse=True)
