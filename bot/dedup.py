import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from bot.config import client


def deduplicate_articles(articles, threshold=0.85):
    if len(articles) <= 1:
        embeddings = np.array([]) if not articles else _embed(articles)
        return articles, embeddings

    embeddings = _embed(articles)
    sim_matrix = cosine_similarity(embeddings)

    keep_indices = []
    removed = set()

    for i in range(len(articles)):
        if i in removed:
            continue
        keep_indices.append(i)
        for j in range(i + 1, len(articles)):
            if j not in removed and sim_matrix[i][j] > threshold:
                removed.add(j)
                print(f"Dedup: removed '{articles[j]['title']}' (similar to '{articles[i]['title']}', score={sim_matrix[i][j]:.2f})")

    kept = [articles[i] for i in keep_indices]
    kept_embeddings = embeddings[keep_indices]
    print(f"Deduplication: {len(articles)} -> {len(kept)} articles ({len(removed)} duplicates removed)")
    return kept, kept_embeddings


def _embed(articles):
    texts = [f"{a['title']} {a['summary']}" for a in articles]
    response = client.embeddings.create(model="text-embedding-3-small", input=texts)
    return np.array([e.embedding for e in response.data])
