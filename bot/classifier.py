import os
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from bot.config import client, TOPICS

_CACHE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "topic_embeddings.npy")
_TOPIC_NAMES = list(TOPICS.keys())


def _get_topic_embeddings():
    if os.path.exists(_CACHE_PATH):
        return np.load(_CACHE_PATH)

    texts = list(TOPICS.values())
    response = client.embeddings.create(model="text-embedding-3-small", input=texts)
    embeddings = np.array([e.embedding for e in response.data])
    np.save(_CACHE_PATH, embeddings)
    print(f"Cached topic embeddings to {_CACHE_PATH}")
    return embeddings


def classify_articles(articles, article_embeddings, min_threshold=0.20):
    if len(articles) == 0:
        return articles, article_embeddings

    topic_embeddings = _get_topic_embeddings()
    sim_matrix = cosine_similarity(article_embeddings, topic_embeddings)

    classified = []
    keep_indices = []
    rejected = []
    for i, article in enumerate(articles):
        best_idx = np.argmax(sim_matrix[i])
        best_score = sim_matrix[i][best_idx]
        if best_score < min_threshold:
            rejected.append((article["title"], f"{best_score:.3f}"))
            continue
        article["topic"] = _TOPIC_NAMES[best_idx]
        classified.append(article)
        keep_indices.append(i)

    if rejected:
        print(f"Filtered {len(rejected)} non-AI articles:")
        for title, score in rejected:
            print(f"  ✗ [{score}] {title}")

    filtered_embeddings = article_embeddings[keep_indices] if keep_indices else np.empty((0, article_embeddings.shape[1]))

    topic_counts = {}
    for a in classified:
        topic_counts[a["topic"]] = topic_counts.get(a["topic"], 0) + 1
    print(f"Topic classification: {topic_counts}")

    return classified, filtered_embeddings
