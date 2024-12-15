import os
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from dotenv import load_dotenv
import json
from bs4 import BeautifulSoup
import dashscope
from http import HTTPStatus
import sys

load_dotenv()

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(PROJECT_ROOT)

load_dotenv()

try:
    from config.settings import settings
except ModuleNotFoundError:
    # Fallback settings if config module is not found
    from dataclasses import dataclass

    @dataclass
    class Settings:
        DASHSCOPE_API_KEY: str = os.getenv("DASHSCOPE_API_KEY", "")
        DASHSCOPE_HTTP_BASE_URL: str = os.getenv("DASHSCOPE_HTTP_BASE_URL", "https://dashscope-intl.aliyuncs.com/api/v1")
        QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
        NVIDIA_API_KEY: str = os.getenv("NVIDIA_API_KEY", "")
        NVIDIA_BASE_URL: str = os.getenv("NVIDIA_BASE_URL", "")
        NVIDIA_EMB_MODEL: str = os.getenv("NVIDIA_EMB_MODEL", "")

    settings = Settings()

dashscope.base_http_api_url = 'https://dashscope-intl.aliyuncs.com/api/v1'

def embed_with_str(input):
    resp = dashscope.TextEmbedding.call(
        model=dashscope.TextEmbedding.Models.text_embedding_v3,
        api_key=settings.DASHSCOPE_API_KEY,
        input=input
    )
    if resp.status_code == HTTPStatus.OK:
        return resp.output['embeddings'][0]['embedding']
    else:
        print(resp)

# Load JSON data from file
with open("./data.json", "r") as file:
    data = json.load(file)


# Function to clean HTML tags
def clean_html(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text()


articles = []
metadatas = []
# Iterate over items and extract title and clean content
items = data["rss"]["channel"]["item"]
for item in items:
    # Handle title
    if item != "":
        title = item.get("title", "")
        link = item.get("link", "")
        if isinstance(title, dict):
            title = title.get("__cdata", title)

        # Handle encoded content
        content = item.get("encoded", "")
        if isinstance(content, list):
            content = content[
                0
            ]  # Assuming we are interested in the first item if it's a list
        if isinstance(content, dict):
            content = content.get("__cdata", content)

        # Clean the content
        clean_content = clean_html(content)
        full_article = f"Title: {title}\nContent: {clean_content}"
        metadata = {"title": title, "link": link, "content": clean_content}

        # Append to the list
        articles.append(full_article)
        metadatas.append(metadata)
        # Print the results

len(articles)

client = QdrantClient(url="http://localhost:6333")

is_collection = client.collection_exists(collection_name="knowledge_base_collection")

if not is_collection:
    client.create_collection(
        collection_name="knowledge_base_collection",
        vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
    )

operation_info = client.upsert(
    collection_name="knowledge_base_collection",
    points=[
        PointStruct(id=idx, vector=embed_with_str(articles[idx]), payload={
            "title": metadatas[idx]["title"], "source_link": metadatas[idx]["link"],
            "content": metadatas[idx]["content"]
        }) for idx in range(len(articles))
    ],
    wait=True
)


print(operation_info)

results = client.query_points(
    collection_name="knowledge_base_collection",
    query=embed_with_str("diabetes definition"),
    with_payload=True,
    limit=3,
    score_threshold=0.5,
)

print(results.points)
