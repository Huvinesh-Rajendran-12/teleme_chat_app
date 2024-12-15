import sys
import os
from dotenv import load_dotenv
from typing import Dict, List, Any, Tuple
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from openai import OpenAI
import json
from bs4 import BeautifulSoup
import tiktoken

# Add the project's root directory to the Python path
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
        QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
        NVIDIA_API_KEY: str = os.getenv("NVIDIA_API_KEY", "")
        NVIDIA_BASE_URL: str = os.getenv("NVIDIA_BASE_URL", "")
        NVIDIA_EMB_MODEL: str = os.getenv("NVIDIA_EMB_MODEL", "")

    settings = Settings()

class KnowledgeBaseStore:
    def __init__(self, collection_name: str = "knowledge_base_collection"):
        """Initialize the KnowledgeBaseStore with OpenAI and Qdrant clients.

        Args:
            collection_name (str): Name of the Qdrant collection
        """
        self.collection_name = collection_name
        self.openai_client = OpenAI(
            api_key=settings.NVIDIA_API_KEY,
            base_url=settings.NVIDIA_BASE_URL
        )
        self.emb_model = settings.NVIDIA_EMB_MODEL
        self.qdrant_client = QdrantClient(url=settings.QDRANT_URL)

    def create_collection_if_not_exists(self) -> None:
        """Create Qdrant collection if it doesn't exist."""
        if not self.qdrant_client.collection_exists(self.collection_name):
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
            )

    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for a text using OpenAI API.

        Args:
            text (str): Text to get embedding for

        Returns:
            List[float]: Embedding vector
        """
        try:
            response = self.openai_client.embeddings.create(
                input=text,
                model=self.emb_model,
                encoding_format="float",
                extra_body={"input_type": "query", "truncate": "NONE"}
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error getting embedding: {e}")
            raise

    def clean_html(self, html_content: str) -> str:
        """Clean HTML tags from content.
        
        Args:
            html_content (str): HTML content to clean
            
        Returns:
            str: Cleaned text
        """
        soup = BeautifulSoup(html_content, "html.parser")
        return soup.get_text()

    def process_json_data(self, data: Dict) -> tuple[List[str], List[Dict]]:
        """Process JSON data to extract articles and metadata.
        
        Args:
            data (Dict): JSON data containing articles
            
        Returns:
            tuple[List[str], List[Dict]]: Processed articles and their metadata
        """
        articles = []
        metadatas = []
        
        items = data["rss"]["channel"]["item"]
        for item in items:
            if item == "":
                continue
                
            title = item.get("title", "")
            link = item.get("link", "")
            if isinstance(title, dict):
                title = title.get("__cdata", title)

            content = item.get("encoded", "")
            if isinstance(content, list):
                content = content[0]
            if isinstance(content, dict):
                content = content.get("__cdata", content)

            clean_content = self.clean_html(content)
            full_article = f"Title: {title}\nContent: {clean_content}"
            metadata = {"title": title, "link": link, "content": clean_content}

            articles.append(full_article)
            metadatas.append(metadata)
            
        return articles, metadatas

    def chunk_text(self, text: str, max_tokens: int = 512) -> List[str]:
        """Split text into chunks that don't exceed max_tokens.
        
        Args:
            text (str): Text to chunk
            max_tokens (int): Maximum tokens per chunk
            
        Returns:
            List[str]: List of text chunks
        """
        encoding = tiktoken.encoding_for_model("cl100k_base")
        tokens = encoding.encode(text)
        chunks = []
        
        current_chunk = []
        current_length = 0
        
        for token in tokens:
            if current_length + 1 > max_tokens:
                # Convert tokens back to text and add to chunks
                chunk_text = encoding.decode(current_chunk)
                chunks.append(chunk_text)
                current_chunk = [token]
                current_length = 1
            else:
                current_chunk.append(token)
                current_length += 1
        
        # Add the last chunk if it exists
        if current_chunk:
            chunk_text = encoding.decode(current_chunk)
            chunks.append(chunk_text)
            
        return chunks

    def store_knowledge_base(self, articles: List[str], metadatas: List[Dict]) -> None:
        """Store knowledge base articles in Qdrant.
        
        Args:
            articles (List[str]): List of articles to store
            metadatas (List[Dict]): List of metadata for each article
        """
        try:
            points = []
            current_id = 0
            
            for idx, article in enumerate(articles):
                # Split article into chunks
                chunks = self.chunk_text(article)
                
                # Create a point for each chunk
                for chunk_idx, chunk in enumerate(chunks):
                    points.append(
                        PointStruct(
                            id=current_id,
                            vector=self.get_embedding(chunk),
                            payload={
                                "title": metadatas[idx]["title"],
                                "source_link": metadatas[idx]["link"],
                                "content": chunk,
                                "chunk_index": chunk_idx,
                                "total_chunks": len(chunks)
                            }
                        )
                    )
                    current_id += 1
            
            operation_info = self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=points,
                wait=True
            )
            print(f"Data stored successfully: {operation_info}")
        except Exception as e:
            print(f"Error storing data: {e}")
            raise

    def search_articles(self, query: str, limit: int = 3, threshold: float = 0.5) -> List[Tuple[Dict, float]]:
        """Search for articles based on a query.
        
        Args:
            query (str): Search query
            limit (int): Maximum number of results
            threshold (float): Minimum similarity score
            
        Returns:
            List[Tuple[Dict, float]]: List of matching articles with scores
        """
        try:
            query_vector = self.get_embedding(query)
            results = self.qdrant_client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                with_payload=True,
                limit=limit,
                score_threshold=threshold,
            )
            
            # Group chunks by title and combine their content
            grouped_results = {}
            for point in results.points:
                title = point.payload["title"]
                if title not in grouped_results:
                    grouped_results[title] = {
                        "title": title,
                        "source_link": point.payload["source_link"],
                        "content": point.payload["content"],
                        "score": point.score
                    }
                else:
                    # Append content and average the scores
                    grouped_results[title]["content"] += "\n" + point.payload["content"]
                    grouped_results[title]["score"] = (grouped_results[title]["score"] + point.score) / 2

            return list(grouped_results.values())
        except Exception as e:
            print(f"Error searching articles: {e}")
            raise

def main():
    """Main function to demonstrate usage."""
    try:
        # Load JSON data
        with open("./data.json", "r") as file:
            data = json.load(file)

        # Initialize store
        store = KnowledgeBaseStore()
        store.create_collection_if_not_exists()

        # Process and store data
        articles, metadatas = store.process_json_data(data)
        store.store_knowledge_base(articles, metadatas)

        # Example search
        results = store.search_articles("diabetes definition")
        print("Search results:", results)

    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

