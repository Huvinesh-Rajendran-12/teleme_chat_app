# Teleme AI Health Assistant

This project is a web application built with Python and FastHTML that serves as an AI Health Assistant. It leverages a Retrieval-Augmented Generation (RAG) approach to provide helpful and context-aware answers to user health queries by searching a knowledge base and finding relevant medical experts.

## Features

*   Interactive chat interface powered by AI models (e.g., Dashscope).
*   Integration with external databases (Qdrant, Neo4j) for RAG.
*   Ability to search and display information from a knowledge base.
*   Ability to search and display information about medical experts.
*   Modern frontend using TailwindCSS and HTMX for dynamic updates.

## Technologies Used

*   **Backend**: Python, FastHTML
*   **AI/ML**: OpenAI/Dashscope API, Sentence Transformers, Tiktoken
*   **Databases**: Qdrant (Vector DB), Neo4j (Graph DB), Analytic DB (PostgreSQL)
*   **Configuration**: Pydantic Settings, python-dotenv
*   **Frontend**: TailwindCSS, HTMX, MarkdownJS
*   **Dependency Management**: Poetry
*   **Linting**: Ruff

## Setup

### Prerequisites

*   Python 3.12+
*   Poetry (recommended for dependency management)
*   Access to required external services (Alibaba Cloud, databases, AI model APIs).

### Installation

1.  Clone the repository:
    ```bash
    git clone <repository_url>
    cd teleme_chat_app
    ```
2.  Install dependencies using Poetry:
    ```bash
    poetry install
    ```

### Configuration (Environment Variables)

Create a `.env` file in the root directory of the `teleme_chat_app` project and set the following environment variables. Some variables are essential for the application to run correctly, as validated by the application's settings loader.

**Required Variables:**

```dotenv
ALIBABA_CLOUD_AK=your_alibaba_cloud_access_key_id
ALIBABA_CLOUD_SK=your_alibaba_cloud_access_key_secret
ALIBABA_REGION_ID=your_alibaba_cloud_region_id
ANALYTIC_DB_HOST=your_analytic_db_host
ANALYTIC_DB_DATABASE=your_analytic_db_database
ANALYTIC_DB_USER=your_analytic_db_user
ANALYTIC_DB_PASSWORD=your_analytic_db_password
NEO4J_URL=your_neo4j_url
NEO4J_PASSWORD=your_neo4j_password
API_HOST=localhost # Or your desired host
DASHSCOPE_API_KEY=your_dashscope_api_key
```

**Optional Variables:**

```dotenv
ALIBABA_INSTANCE_ID=your_alibaba_instance_id
ALIBABA_ACCOUNT=your_alibaba_account
ALIBABA_ACCOUNT_PASSWORD=your_alibaba_account_password
ANALYTIC_DB_PORT=5432 # Default
ANALYTIC_DB_INSTANCE_ID=your_analytic_db_instance_id
ANALYTIC_DB_EMBED_DIM=1024 # Default
NEO4J_USERNAME=your_neo4j_username
NEO4J_DATABASE=your_neo4j_database
NEO4J_PRODUCT_EMBEDDING_INDEX=your_neo4j_product_embedding_index
NEO4J_EMBEDDING_DIM=720 # Default
API_PORT=8000 # Default
DASHSCOPE_HTTP_BASE_URL=your_dashscope_base_url
QWEN_MODEL=your_qwen_model # e.g., qwen-long
QWEN_CACHE=True # Default
QWEN_STREAMING=True # Default
NVIDIA_API_KEY=your_nvidia_api_key
NVIDIA_BASE_URL=your_nvidia_base_url
NVIDIA_MODEL=your_nvidia_model
NVIDIA_EMB_MODEL=your_nvidia_embedding_model
QDRANT_URL=your_qdrant_url
EMBEDDING_MODEL=your_embedding_model
ENABLE_CACHE=True # Default
XAI_API_KEY=your_xai_api_key
XAI_BASE_URL=your_xai_base_url
```

Replace the placeholder values (`your_...`) with your actual credentials and endpoints.

### Running the Application

Once dependencies are installed and environment variables are set, you can run the application using uvicorn:

```bash
uvicorn teleme_chat_app.app:app --reload --host 0.0.0.0 --port 5001
```

The application should then be accessible in your web browser at `http://localhost:5001` (or the host and port you configured).