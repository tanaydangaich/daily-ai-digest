import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

RSS_FEEDS = [
    # News outlets
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://venturebeat.com/category/ai/feed/",
    "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "https://arstechnica.com/tag/artificial-intelligence/feed/",
    "https://www.wired.com/feed/tag/ai/latest/rss",
    "https://www.technologyreview.com/topic/artificial-intelligence/feed",
    # AI labs
    "https://blogs.microsoft.com/ai/feed/",
    "https://openai.com/blog/rss.xml",
    "https://blog.google/technology/ai/rss/",
    "https://deepmind.google/blog/rss.xml",
    # Research & industry
    "https://huggingface.co/blog/feed.xml",
    "https://blogs.nvidia.com/blog/category/deep-learning/feed/",
]

TOPICS = {
    "nlp": "natural language processing, text generation, language models, tokenization, sentiment analysis, named entity recognition, machine translation, text classification",
    "computer-vision": "computer vision, image recognition, object detection, image segmentation, visual transformers, video understanding, image generation, diffusion models",
    "llms": "large language models, GPT, Claude, Llama, fine-tuning, RLHF, prompt engineering, context windows, reasoning models, AI agents, chatbots",
    "robotics": "robotics, embodied AI, manipulation, locomotion, sim-to-real, robot learning, autonomous vehicles",
    "general-ai": "artificial intelligence, AI policy, AI safety, AI regulation, AI industry, AI startups, AI funding, AI research",
}
