import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    # ALIBABA CLOUD
    ALIBABA_CLOUD_AK: str = os.getenv("ALIBABA_CLOUD_AK", "")
    ALIBABA_CLOUD_SK: str = os.getenv("ALIBABA_CLOUD_SK", "")
    ALIBABA_REGION_ID: str = os.getenv("ALIBABA_REGION_ID", "")
    ALIBABA_INSTANCE_ID: str = os.getenv("ALIBABA_INSTANCE_ID", "")
    ALIBABA_ACCOUNT: str = os.getenv("ALIBABA_ACCOUNT", "")
    ALIBABA_ACCOUNT_PASSWORD: str = os.getenv("ALIBABA_ACCOUNT_PASSWORD", "")

    # DATABASE settings
    ANALYTIC_DB_HOST: str = os.getenv("ANALYTIC_DB_HOST", "")
    ANALYTIC_DB_PORT: str = os.getenv("ANALYTIC_DB_PORT", "5432")
    ANALYTIC_DB_DATABASE: str = os.getenv("ANALYTIC_DB_DATABASE", "")
    ANALYTIC_DB_USER: str = os.getenv("ANALYTIC_DB_USER", "")
    ANALYTIC_DB_PASSWORD: str = os.getenv("ANALYTIC_DB_PASSWORD", "")
    ANALYTIC_DB_INSTANCE_ID: str = os.getenv("ANALYTIC_DB_INSTANCE_ID", "")
    ANALYTIC_DB_EMBED_DIM: int = int(os.getenv("ANALYTIC_DB_EMBED_DIM", 1024))

    # NEO4J settings
    NEO4J_URL: str = os.getenv("NEO4J_URL", "")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "")
    NEO4J_USERNAME: str = os.getenv("NEO4J_USERNAME", "")
    NEO4J_DATABASE: str = os.getenv("NEO4J_DATABASE", "")
    NEO4J_PRODUCT_EMBEDDING_INDEX: str = os.getenv("NEO4J_PRODUCT_EMBEDDING_INDEX", "")
    NEO4J_EMBEDDING_DIM: int = int(os.getenv("NEO4J_EMBEDDING_DIM", 720))

    # API settings
    API_HOST: str = os.getenv("API_HOST", "localhost")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))

    # MODEL settings
    DASHSCOPE_API_KEY: str = os.getenv("DASHSCOPE_API_KEY", "")
    DASHSCOPE_HTTP_BASE_URL: str = os.getenv("DASHSCOPE_HTTP_BASE_URL", "")
    QWEN_MODEL: str = os.getenv("QWEN_MODEL", "")
    QWEN_CACHE: bool = os.getenv("QWEN_CACHE", "True").lower() == "true"
    QWEN_STREAMING: bool = os.getenv("QWEN_STREAMING", "True").lower() == "true"

    # NVIDIA settings 
    NVIDIA_API_KEY: str = os.getenv("NVIDIA_API_KEY", "")
    NVIDIA_BASE_URL: str = os.getenv("NVIDIA_BASE_URL", "")
    NVIDIA_MODEL: str = os.getenv("NVIDIA_MODEL", "")
    NVIDIA_EMB_MODEL: str = os.getenv("NVIDIA_EMB_MODEL", "")

    # QDRANT settings
    QDRANT_URL: str = os.getenv("QDRANT_URL", "")

    # EMBEDDING settings
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "")

    # CACHING settings
    ENABLE_CACHE: bool = os.getenv("ENABLE_CACHE", "True").lower() == "true"

    @property
    def SYSTEM_PROMPT(self) -> str:
        return """
            You are an AI health assistant designed to provide accurate and concise information on health-related queries. You have access to two tools:

            search_knowledge_base: Use this function to retrieve general health information or answer specific health questions. The function takes a query parameter which should be the user's exact or closely paraphrased query.
            search_doctors: Use this function when the user explicitly asks for doctors or medical professionals related to their health query. The function also takes a query parameter, which should reflect the user's need for finding medical professionals.

            Rules for Interaction:

            Do not output any links in your responses. Instead, summarize the information or findings in your own words.
            Be concise yet thorough. Aim for clarity and accuracy without unnecessary elaboration.
            Privacy and Sensitivity: Always handle health queries with confidentiality and respect. Do not ask for or suggest sharing sensitive personal information unless it's absolutely necessary for the query's context.
            Accuracy: Base your answers on the outputs from these tools. If the information from the tools isn't clear or sufficient, acknowledge this and suggest consulting a healthcare provider.
            Response Structure: 
            For health information queries, summarize the key points from search_knowledge_base quickly, keep the answer to one paragraph.
            For doctor searches, list the specialties or general availability of doctors in relation to the query from search_doctors, without revealing specific details about individuals.

            Example User Query and Response:

            User Query: "What are the symptoms of seasonal allergies?"

            AI Response: 
            "The symptoms of seasonal allergies typically include sneezing, runny or stuffy nose, itchy or watery eyes, and sometimes fatigue or headache."

            User Query: "I need a dermatologist for eczema."

            AI Response: 
            "There are dermatologists available who specialize in treating conditions like eczema. They can offer consultations for managing symptoms and improving skin health."

            Remember: 
            Always use the appropriate tool based on the query's intent.
            If you can't provide an answer or if the query is outside the scope of these tools, admit it and suggest alternatives like seeking professional medical advice.
            """

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.ANALYTIC_DB_USER}:{self.ANALYTIC_DB_PASSWORD}@{self.ANALYTIC_DB_HOST}:{self.ANALYTIC_DB_PORT}/{self.ANALYTIC_DB_DATABASE}"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


def validate_env_variables():
    missing_vars = [
        var for var in [
            "ALIBABA_CLOUD_AK", "ALIBABA_CLOUD_SK", "ALIBABA_REGION_ID", "ANALYTIC_DB_HOST",
            "ANALYTIC_DB_DATABASE", "ANALYTIC_DB_USER", "ANALYTIC_DB_PASSWORD", "NEO4J_URL",
            "NEO4J_PASSWORD", "API_HOST", "DASHSCOPE_API_KEY"
        ] if not os.getenv(var)
    ]
    if missing_vars:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

validate_env_variables()

settings = Settings()
