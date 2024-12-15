from openai import OpenAI
from typing import List, Dict, Any
from config.settings import settings

tool_definitions = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Query the knowledge base for health-related information based on the user query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The health query submitted by the user."
                    }
                },
                "additionalProperties": False,
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_doctors",
            "description": "Query for doctors requested by the user based on their health query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The doctor query submitted by the user."
                    }
                },
                "additionalProperties": False,
                "required": ["query"]
            }
        }
    }
]

class AIService:
    def __init__(self) -> None:
        self.client = OpenAI(
            api_key=settings.DASHSCOPE_API_KEY,
            base_url=settings.DASHSCOPE_HTTP_BASE_URL
        )

    def get_response(self, messages_list: List[Dict[str, Any]], stream: bool = False):
        """Get response from the AI model"""
        completion = self.client.chat.completions.create(
            model=settings.QWEN_MODEL,
            messages=messages_list,
            tools=tool_definitions,
            stream=stream
        )

        if stream:
            return completion
        return completion.model_dump()

ai_service = AIService()
