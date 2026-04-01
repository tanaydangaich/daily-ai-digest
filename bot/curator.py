import re
from bot.config import client


def _suppress_embeds(text):
    # Convert markdown links [text](url) to just <url>
    text = re.sub(r'\[([^\]]*)\]\((https?://[^\s\)]+)\)', r'\1: <\2>', text)
    # Wrap any remaining bare URLs not already in angle brackets
    text = re.sub(r'(?<!<)(https?://[^\s>)\]]+)', r'<\1>', text)
    return text


def fetch_nyc_events():
    response = client.chat.completions.create(
        model="gpt-4o-search-preview",
        web_search_options={},
        messages=[{
            "role": "user",
            "content": "Search for upcoming AI meetups, talks, networking events, or conferences in New York City this week. Return 2-3 events with: event name, date, brief description, and registration URL wrapped in angle brackets like <https://example.com>. Format as a simple list."
        }]
    )
    return _suppress_embeds(response.choices[0].message.content)


def rank_articles(articles):
    """Pre-rank articles by source diversity, topic diversity, and recency."""
    source_seen = {}
    topic_seen = {}

    scored = []
    for i, a in enumerate(articles):
        source = a.get("source", "unknown")
        topic = a.get("topic", "general-ai")

        source_seen[source] = source_seen.get(source, 0) + 1
        topic_seen[topic] = topic_seen.get(topic, 0) + 1

        # Penalize repeated sources/topics, reward recency (earlier = more recent)
        source_penalty = 1.0 / source_seen[source]
        topic_penalty = 1.0 / topic_seen[topic]
        recency_score = 1.0 - (i / max(len(articles), 1)) * 0.3

        score = source_penalty * 0.4 + topic_penalty * 0.3 + recency_score * 0.3
        scored.append((score, i, a))

    scored.sort(key=lambda x: x[0], reverse=True)
    ranked = [item[2] for item in scored]

    print(f"Ranking: top 3 sources = {[a.get('source','?') for a in ranked[:3]]}")
    return ranked


def build_digest(articles):
    if not articles:
        return None

    ranked = rank_articles(articles)
    article_list = "\n\n".join([
        f"Title: {a['title']}\nSource: {a['source']}\nURL: {a['url']}\nPreview: {a['summary']}"
        for a in ranked[:30]
    ])

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": f"""You are an AI news curator. From the articles below, select and summarize the 10 most important AI stories from this week.

ARTICLES:
{article_list}

Instructions:
- Pick the 10 most significant and diverse stories (no duplicates or near-duplicates)
- Keep the exact URL from the article — do not modify or guess URLs
- Wrap every URL in angle brackets like <https://example.com> to suppress Discord embeds
- Write summaries relevant to someone transitioning from academia to industry AI roles (experienced in credit risk ML, NLP/BERT, medical imaging, strong classical ML — needs GenAI/LLM portfolio)

For each story use exactly this format:
**#N. [Headline]**
📰 Source: [source name]
🔗 <URL>
💡 [2-3 sentences on why this matters and what to do with it]

After all 10 stories:
---
**🎯 Career Insight of the Day**
[1-2 specific, actionable sentences connecting today's news to a concrete next step for someone with strong classical ML skills (XGBoost, PyTorch, BERT) transitioning from academia to industry AI roles in NYC]"""
        }]
    )

    return _suppress_embeds(response.choices[0].message.content)
