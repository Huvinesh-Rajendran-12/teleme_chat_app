from fasthtml.common import *
from typing import List

def ChatMessage(msg_idx: int, messages: List[dict], **kwargs):
    """Render a chat message"""
    msg = messages[msg_idx]
    is_user = msg['role'] == 'user'
    align_cls = "ml-auto" if is_user else "mr-auto"
    bg_cls = "bg-blue-600 text-white" if is_user else "bg-white text-gray-800"
    
    content_cls = f"px-4 py-3 rounded-lg {bg_cls} shadow-sm markdown prose prose-sm max-w-none"
    content_cls += " prose-invert" if is_user else " prose-gray"
    
    return Div(
        Div(
            Div(msg['content'],
                id=f"chat-content-{msg_idx}",
                cls=content_cls),
            cls=f"max-w-[80%] {align_cls}"
        ),
        id=f"chat-message-{msg_idx}",
        cls="mb-4",
        **kwargs
    )

def ChatInput():
    """Render the chat input form"""
    return Form(
        Div(
            Input(
                type="text",
                name="message",
                id="chat-input",
                placeholder="Ask about health topics or find a doctor...",
                cls="w-full px-4 py-3 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            ),
            Button(
                "Send",
                type="submit",
                cls="absolute right-3 top-1/2 transform -translate-y-1/2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors duration-200"
            ),
            cls="relative"
        ),
        ws_send=True,  # Enable websocket sending
        hx_ext="ws",   # Use websocket extension
        ws_connect="/wscon",  # Connect to our websocket endpoint
        cls="px-4 mb-6"
    )

def LoadingIndicator(message: str = "Processing..."):
    """Render loading indicator"""
    return Div(
        # Bouncing dots
        Div(
            Div(cls="w-2 h-2 bg-blue-600 rounded-full animate-bounce"),
            Div(cls="w-2 h-2 bg-blue-600 rounded-full animate-bounce delay-100"),
            Div(cls="w-2 h-2 bg-blue-600 rounded-full animate-bounce delay-200"),
            cls="flex space-x-1"
        ),
        # Loading message
        P(message, cls="text-sm text-gray-600 mt-2"),
        id="loading-indicator",
        cls="flex flex-col items-center justify-center py-4"
    )

def ChatList(messages: List[dict]):
    """Render the chat message list"""
    return Div(
        *[ChatMessage(i, messages) for i in range(len(messages))],
        id="chatlist",
        cls="h-[70vh] overflow-y-auto px-4 py-6"
    )