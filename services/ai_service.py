from openai import OpenAI
from typing import List, Dict, Any
from config.settings import settings

# Tool definitions
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Query the knowledge base for information based on the user query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The query submitted by the user.",
                    }
                },
            },
            "required": ["query"],
        },
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
                        "description": "The query submitted by the user.",
                    }
                },
            },
            "required": ["query"],
        },
    },
]

class AIService:
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.DASHSCOPE_API_KEY,
            base_url=settings.DASHSCOPE_HTTP_BASE_URL
        )

    def get_response(self, messages: List[Dict[str, Any]], stream: bool = False):
        """Get response from the AI model"""
        completion = self.client.chat.completions.create(
            model=settings.QWEN_MODEL,
            messages=messages,
            tools=tools,
            stream=stream
        )
        if stream:
            return completion
        return completion.model_dump()

    async def process_message(self, message: str, conversation_history: List[dict]):
        """Process a message with conversation history"""
        messages = []
        
        # Add conversation history
        for msg in conversation_history:
            messages.append({
                "content": msg["content"],
                "role": msg["role"]
            })
        
        # Add current message
        messages.append({"content": message, "role": "user"})
        
        # Get initial response
        first_response = self.get_response(messages, stream=False)
        return first_response['choices'][0]['message']

ai_service = AIService()