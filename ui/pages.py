# ui/pages.py
from fasthtml.common import *
from .components.chat import ChatInput, ChatList
from .components.sources import Sources

def HomePage(messages=None, current_sources=None):
    """Main page layout"""
    # Set default values if none provided
    messages = messages or []
    current_sources = current_sources or {
        "knowledge_base": [],
        "doctors": []
    }

    return Div(
        # Header
        Div(
            H1('Health Assistant', 
               cls="text-3xl font-bold text-gray-800"),
            P("Ask questions about health topics or find suitable doctors", 
              cls="text-gray-600 mt-1"),
            cls="text-center mb-8 pt-8"
        ),
        # Main content
        Div(
            # Chat section
            Div(
                ChatList(messages),  # Pass the messages to ChatList
                ChatInput(),
                cls="bg-gray-100 rounded-lg shadow-lg"
            ),
            # Sources section
            Div(
                Sources(current_sources),  # Pass the current sources
                cls="bg-white rounded-lg shadow-lg"
            ),
            cls="grid grid-cols-2 gap-8 max-w-7xl mx-auto px-4"
        ),
        cls="min-h-screen bg-white"
    )

def ErrorPage(title: str, message: str):
    """Error page layout"""
    return Div(
        Div(
            H1(title, cls="text-3xl font-bold text-gray-800 mb-4"),
            P(message, cls="text-gray-600"),
            A("← Go back home", href="/", 
              cls="mt-8 inline-block text-blue-600 hover:text-blue-800"),
            cls="text-center"
        ),
        cls="min-h-screen flex items-center justify-center"
    )