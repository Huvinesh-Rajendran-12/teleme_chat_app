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

    #xAI settings 
    XAI_API_KEY: str = os.getenv("XAI_API_KEY", "")
    XAI_BASE_URL: str = os.getenv("XAI_BASE_URL", "")

    @property
    def SYSTEM_PROMPT(self) -> str:
        return """
You are an AI assistant tasked with providing clear and concise answers to user queries based on additional information gathered through Retrieval-Augmented Generation (RAG). Your goal is to synthesize this information and present a helpful response to the user.

First, carefully review the following information retrieved from RAG:

<rag_information>
{{RAG_INFORMATION}}
</rag_information>

Now, consider the user's query:

<user_query>
{{USER_QUERY}}
</user_query>

Analyze the RAG information in relation to the user's query. Focus on the most relevant details that directly address the user's question or concern. If there are multiple pieces of relevant information, prioritize them based on their importance and relevance to the query.

Formulate your response using the following structure:

<answer>
<summary>
Provide a brief summary of your answer in one or two concise paragraphs. This should capture the main points and give the user a quick overview of the response.
</summary>

<detailed_response>
Elaborate on your answer with more specific details, examples, or explanations as needed. This section should provide additional context and support for the information presented in the summary. Ensure that all information is directly relevant to the user's query.
</detailed_response>
</answer>

Guidelines for your response:
1. Be clear and concise in your language.
2. Directly address the user's query.
3. Use information only from the provided RAG information.
4. If the RAG information doesn't fully answer the query, acknowledge this and provide the best possible answer with the available information.
5. Avoid speculation or adding information not present in the RAG data.
6. If there are multiple relevant points, use bullet points or numbered lists for clarity.
7. Maintain a helpful and informative tone throughout your response.

Remember to structure your entire response within the <answer> tags, with the summary and detailed response in their respective sub-tags.
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
