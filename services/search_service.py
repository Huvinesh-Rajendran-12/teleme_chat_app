import asyncio
from typing import List, Dict, Any, Tuple
from config.settings import settings
from qdrant_client import QdrantClient
import dashscope
from http import HTTPStatus


client = QdrantClient(url=settings.QDRANT_URL)


dashscope.base_http_api_url = 'https://dashscope-intl.aliyuncs.com/api/v1'

def embed_with_str(query: str):
    resp = dashscope.TextEmbedding.call(
        model=dashscope.TextEmbedding.Models.text_embedding_v3,
        api_key=settings.DASHSCOPE_API_KEY,
        input=query)
    if resp.status_code == HTTPStatus.OK:
        return resp.output['embeddings'][0]['embedding']
    else:
        print(resp)

async def search_knowledge_base(query: str) -> Tuple[List[Dict[str, Any]], str]:
    """
    Search the knowledge base for relevant information.

    Args:
        query: str -> query used to retrieve the relevant information.
    Returns:
        Tuple containing:
        1. List of the formatted results with title, content preview, and source link
        2. String joining all relevant information from results
    """

    embed = embed_with_str(query)
    results = client.query_points(
        collection_name="knowledge_base_collection",
        query=embed,
        with_payload=True,
        limit=3,
        score_threshold=0.6
    )
    formatted_results = []
    combined_text_parts = []
    for result in results.points:
        # Format dictionary result
        content_preview = result.payload["content"][:200] + "..." if len(result.payload["content"]) > 200 else result.payload["content"]
        formatted_results.append({
            "title": result.payload["title"],
            "content_preview": content_preview,
            "source_link": result.payload["source_link"],
            "relevance_score": round(result.score, 3)
        })

        # Add to combined text
        combined_text_parts.append(
            f"Title: {result.payload['title']}\n"
            f"Content: {result.payload['content']}\n"
            f"Source: {result.payload['source_link']}\n"
        )

    combined_text = "\n".join(combined_text_parts)
    return formatted_results, combined_text

async def search_doctors(query: str) -> Tuple[List[Dict[str, Any]], str]:
    """
    Search for doctors based on query.
    Returns:
        Tuple containing:
        1. List of formatted results with doctor information
        2. String joining all relevant information from results
    """
    embed = embed_with_str(query)
    results = client.query_points(
        collection_name="doctor_collection",
        query=embed,
        with_payload=True,
        limit=3,
        score_threshold=0.5,
    )

    formatted_results = []
    combined_text_parts = []

    for result in results.points:
        # Format dictionary result
        formatted_results.append({
            "doctor_name": result.payload["doctor_name"],
            "specialization": result.payload["doctor_field"],
            "description": result.payload["doctor_description"],
            "availability_status": "Available" if result.payload["availability"] else "Not Available",
            "appointment_link": result.payload["appointment_link"],
            "relevance_score": round(result.score, 3)
        })

        # Add to combined text
        combined_text_parts.append(
            f"Specialization: {result.payload['doctor_field']}\n"
            f"Description: {result.payload['doctor_description']}\n"
        )

    combined_text = "\n".join(combined_text_parts)
    return formatted_results, combined_text