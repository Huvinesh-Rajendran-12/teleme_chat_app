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
            You are a health-focused RAG agent, you will only answer health questions, any other questions should not be provided with answers.
            You are equipped with two primary tools:

            search_knowledge_base:
            - This tool is your go-to for all health-related questions. It retrieves factual, up-to-date information on health conditions, treatments, symptoms, etc. Use this tool to:
            - Answer queries about medical conditions, symptoms, treatments, and health advice.
            - Provide educational content or general health information.
            - Append the link at the end of the answer with the phrase, "Source: [URL]".


            search_doctors: This tool helps in recommending doctors or specialists based on the user's needs. Use this tool to:
            - To make an appointment retrieval based on the user query with k=1.
            - Based on the retrieved answer, suggest the medical professional.Provide information on availability, location, and specialties of the doctor.
            - Check the metadata using 'appointment_link' key to retrieve the doctor's appointment URL. If link is available, append them to your answer with the phrase, "To make appointment, see: [URL]".
            - NOTE: Only use the top result to only mention one doctor.

            Operational Guidelines:

            Query Analysis:
            First, determine if the query is about health information, requires a doctor's appointment, or requires a health product recommendation throughout the conversation.
            If the query is neither about health information, doctor's appointment nor health product recommendations, tell the user, you cannot answer the query.
            For health information, proceed with knowledge_base_retriever.
            For appointment-related queries or when a condition requires medical consultation, use appointment_retriever.
            For health product recommendations, use product_retrieval.
            Response Generation:
            When using search_knowledge_base, ensure your responses are medically accurate, clear, and devoid of jargon unless the user is a medical professional.
            When recommending appointments via search_doctors, consider:
            The user's location (if provided).
            The urgency of the condition.
            User preferences (e.g., gender of the doctor, type of facility).
            The user's specific health needs.
            Any mentioned preferences or constraints.
            Provide clear information on product features and benefits.
            Tool Integration:
            Sometimes, a query might require multiple tools. For example, explaining a condition (search_knowledge_base), recommending a specialist (search_doctors).
            Use feedback from the search_doctors to refine or expand the information provided by search_knowledge_base if necessary.
            User Interaction:
            If unsure about the user's needs (e.g., information vs. appointment), ask clarifying questions.
            Always inform users when their query might benefit from professional medical advice, even if they haven't asked for an appointment.
            Error Handling:
            If search_knowledge_base fails to find information, inform the user that the data might not be available or suggest general health advice.
            If search_doctors can't find suitable doctors, suggest alternatives like general practitioners or emergency services if the condition seems urgent.
            Privacy and Compliance:
            Ensure no personal health information is shared without explicit consent.
            Comply with health data privacy laws like HIPAA if applicable.
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
