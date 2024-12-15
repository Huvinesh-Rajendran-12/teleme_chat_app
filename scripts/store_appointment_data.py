import sys
import os
from dotenv import load_dotenv
from typing import Dict, List, Any
import dashscope
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

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
        DASHSCOPE_API_KEY: str = os.getenv("DASHSCOPE_API_KEY", "")
        DASHSCOPE_HTTP_BASE_URL: str = os.getenv("DASHSCOPE_HTTP_BASE_URL", "https://dashscope-intl.aliyuncs.com/api/v1")
        QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
        NVIDIA_API_KEY: str = os.getenv("NVIDIA_API_KEY", "")
        NVIDIA_BASE_URL: str = os.getenv("NVIDIA_BASE_URL", "")
        NVIDIA_EMB_MODEL: str = os.getenv("NVIDIA_EMB_MODEL", "")

    settings = Settings()



class DoctorDataStore:
    def __init__(self, collection_name: str = "doctor_collection"):
        """Initialize the DoctorDataStore with OpenAI and Qdrant clients.

        Args:
            collection_name (str): Name of the Qdrant collection
        """
        self.collection_name = collection_name
        self.openai_client = OpenAI(
            api_key=settings.NVIDIA_API_KEY,
            base_url=settings.NVIDIA_BASE_URL
        )
        self.emb_model=settings.NVIDIA_EMB_MODEL
        self.qdrant_client = QdrantClient(url="http://localhost:6333")

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

    def store_doctor_data(self, data: Dict[str, List[Any]]) -> None:
        """Store doctor data in Qdrant.

        Args:
            data (Dict[str, List[Any]]): Doctor data to store
        """
        try:
            points = [
                PointStruct(
                    id=idx,
                    vector=self.get_embedding(data['doctor_field'][idx] + " " + data['doctor_description'][idx]),
                    payload={
                        "doctor_name": data["doctor_name"][idx],
                        "doctor_field": data["doctor_field"][idx],
                        "doctor_description": data["doctor_description"][idx],
                        "availability": data["availability"][idx],
                        "appointment_link": data["appointment_link"][idx]
                    }
                ) for idx in range(len(data['doctor_description']))
            ]
            
            operation_info = self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=points,
                wait=True
            )
            print(f"Data stored successfully: {operation_info}")
        except Exception as e:
            print(f"Error storing data: {e}")
            raise

    def search_doctors(self, query: str, limit: int = 3, threshold: float = 0.1) -> List[Dict]:
        """Search for doctors based on a query.

        Args:
            query (str): Search query
            limit (int): Maximum number of results
            threshold (float): Minimum similarity score

        Returns:
            List[Dict]: List of matching doctors
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
            return [(point.payload, point.score) for point in results.points]
        except Exception as e:
            print(f"Error searching doctors: {e}")
            raise

def main():
    """Main function to demonstrate usage."""
    try:
        # Move this to a separate configuration file in practice
        data: Dict[str, List[Any]] = {
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
            "availability": [True, True, False]
        }

        store = DoctorDataStore()
        store.create_collection_if_not_exists()
        store.store_doctor_data(data)

        # Example search
        results = store.search_doctors("recommend me a doctor for eyesight")
        print("Search results:", results)

    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
