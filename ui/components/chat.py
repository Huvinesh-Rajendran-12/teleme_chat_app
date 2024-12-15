from fasthtml.common import *
from typing import List

def ChatMessage(msg_idx: int, messages: List[dict], **kwargs):
    """Render a chat message with markdown support"""
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
    """Render the chat input field"""
    return Input(
        type="text",
        name='msg',
        id='msg-input',
        placeholder="Ask about health topics or find a doctor...",
        cls="w-full px-4 py-3 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent",
        hx_swap_oob='true'
    )

def LoadingIndicator():
    """Render loading indicator"""
    return Div(
        Div(cls="w-2 h-2 bg-blue-600 rounded-full animate-bounce"),
        Div(cls="w-2 h-2 bg-blue-600 rounded-full animate-bounce delay-100"),
        Div(cls="w-2 h-2 bg-blue-600 rounded-full animate-bounce delay-200"),
        id="loading-indicator",
        cls="flex justify-center items-center space-x-2 py-4 hidden"
    )