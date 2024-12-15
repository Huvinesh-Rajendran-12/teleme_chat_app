from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

class Message(BaseModel):
    role: str
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None

class ChatState(BaseModel):
    def __init__(self):
        self.messages: List[Message] = []
        self.current_sources: Dict[str, List[Dict[str, Any]]] = {
            "knowledge_base": [],
            "doctors": []
        } 
        self.search_history: List[tuple[List[Dict[str, Any]], datetime]] = []