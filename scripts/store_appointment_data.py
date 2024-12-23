from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
import os
from dotenv import load_dotenv
from typing import Dict, List
import dashscope
from http import HTTPStatus
import sys

load_dotenv()

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
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
        DASHSCOPE_HTTP_BASE_URL: str = os.getenv(
            "DASHSCOPE_HTTP_BASE_URL", "https://dashscope-intl.aliyuncs.com/api/v1"
        )
        QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
        NVIDIA_API_KEY: str = os.getenv("NVIDIA_API_KEY", "")
        NVIDIA_BASE_URL: str = os.getenv("NVIDIA_BASE_URL", "")
        NVIDIA_EMB_MODEL: str = os.getenv("NVIDIA_EMB_MODEL", "")

    settings = Settings()

dashscope.base_http_api_url = "https://dashscope-intl.aliyuncs.com/api/v1"


def embed_with_str(input):
    resp = dashscope.TextEmbedding.call(
        model=dashscope.TextEmbedding.Models.text_embedding_v3,
        api_key=settings.DASHSCOPE_API_KEY,
        input=input,
    )
    if resp.status_code == HTTPStatus.OK:
        return resp.output["embeddings"][0]["embedding"]
    else:
        print(resp)


data: Dict[str, List[str | bool]] = {
    "doctor_name": [
        "Dr Hoh Hon Bing",
        "Dr Azlina Firzah",
        "Dr Vijay Ananda Paramasvaran",
    ],
    "doctor_field": ["Ophthalmology", "Breast and Endocrinology", "Endocrinology"],
    "doctor_description": [
        "Dr Hoh Hon Bing is an Ophthalmologist, who is trained to diagnose and treat all eye and visual problems including vision services (glasses and contacts) and provide treatment and prevention of medical disorders of the eye including surgery.",
        "Dr Azlina Firzah is Breast Surgeon who specializes in cases related to breast cancer.",
        "Dr Vijay Ananda Paramasvaran specializes in diabetics diagnosis and treatment. ",
    ],
    "appointment_link": [
        "https://www.pantai.com.my/kuala-lumpur/appointment/hoh-hon-bing",
        "https://www.pantai.com.my/kuala-lumpur/ms/appointment/azlina-firzah-bt-abd-aziz",
        "https://www.pantai.com.my/kuala-lumpur/appointment/vijay-ananda-paramasvaran",
    ],
    "availability": [True, True, False],
}


client = QdrantClient(url="http://localhost:6333")

is_collection = client.collection_exists(collection_name="doctor_collection")

if not is_collection:
    client.create_collection(
        collection_name="doctor_collection",
        vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
    )

operation_info = client.upsert(
    collection_name="doctor_collection",
    points=[
        PointStruct(
            id=idx,
            vector=embed_with_str(data["doctor_description"][idx]),
            payload={
                "doctor_name": data["doctor_name"][idx],
                "doctor_field": data["doctor_field"][idx],
                "doctor_description": data["doctor_description"][idx],
                "availability": data["availability"][idx],
                "appointment_link": data["appointment_link"][idx],
            },
        )
        for idx in range(len(data["doctor_description"]))
    ],
    wait=True,
)

print(operation_info)

results = client.query_points(
    collection_name="doctor_collection",
    query=embed_with_str("diabetes doctor"),
    with_payload=True,
    limit=3,
    score_threshold=0.5,
)

print(results.points)
