# models/chat.py
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

class Message(BaseModel):
    role: str
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None

class ChatState:
    def __init__(self):
        # Regular attributes, not Pydantic fields
        self._messages = []  
        self._current_sources = {
            "knowledge_base": [],
            "doctors": []
        }
        self._search_history = []
    
    @property
    def messages(self):
        return self._messages
    
    @property
    def current_sources(self):
        return self._current_sources
    
    @property
    def search_history(self):
        return self._search_history

    def add_message(self, role: str, content: str) -> int:
        """Add a message and return its index"""
        self._messages.append({"role": role, "content": content})
        return len(self._messages) - 1
    
    def add_source(self, results: List[Dict[str, Any]], source_type: str):
        """Add search results"""
        if source_type == "knowledge_base":
            self._current_sources["knowledge_base"] = results
            self._search_history.append((results, datetime.now()))
        else:
            self._current_sources["doctors"] = results