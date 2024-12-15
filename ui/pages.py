from fasthtml.common import *
from .components.chat import ChatMessage, ChatInput, LoadingIndicator
from .components.sources import Sources

def HomePage(messages, current_sources):
    """Main page layout"""
    return Body(
        Div(
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
                    Div(*[ChatMessage(msg_idx, messages) for msg_idx, msg in enumerate(messages)],
                        id="chatlist",
                        cls="h-[70vh] overflow-y-auto px-4 py-6"),
                    LoadingIndicator(),
                    Form(
                        Div(
                            ChatInput(),
                            Button("Send", 
                                  cls="absolute right-3 top-1/2 transform -translate-y-1/2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors duration-200"),
                            cls="relative"
                        ),
                        ws_send=True,
                        hx_ext="ws",
                        ws_connect="/wscon",
                        cls="px-4 mb-6"
                    ),
                    cls="bg-gray-100 rounded-lg shadow-lg"
                ),
                # Sources section
                Div(
                    Sources(current_sources),
                    cls="bg-white rounded-lg shadow-lg"
                ),
                cls="grid grid-cols-2 gap-8 max-w-7xl mx-auto px-4"
            ),
            cls="min-h-screen bg-white"
        ),
        cls="bg-gradient-to-b from-blue-50 to-white"
    )