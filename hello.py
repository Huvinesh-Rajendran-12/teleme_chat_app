from fasthtml.common import *
import json
import httpx
from datetime import datetime

# Set up the app with Tailwind only
app = FastHTML(hdrs=(Script(src="https://cdn.tailwindcss.com"), MarkdownJS()), exts='ws')

# Store messages, current sources, and history
messages = []
current_sources = {"knowledge_base": [], "doctors": []}
search_history = []  # List to store past searches with timestamps

def format_historical_source(source, timestamp):
    """Format a historical source result"""
    return Div(
        Div(
            Div(
                H4(source["title"], cls="text-md font-semibold text-gray-800"),
                P(timestamp.strftime("%Y-%m-%d %H:%M"), 
                  cls="text-xs text-gray-500"),
                cls="flex justify-between items-center"
            ),
            P(source["content_preview"], cls="mt-2 text-gray-600 text-sm line-clamp-2"),
            A("Read more →", href=source["source_link"], 
              cls="text-blue-600 hover:text-blue-800 text-sm mt-2 inline-block", 
              target="_blank"),
            cls="p-4"
        ),
        cls="bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200"
    )

def format_source(source, source_type):
    """Format source information for display"""
    if source_type == "search_knowledge_base":
        return Div(
            Div(
                H3(source["title"], cls="text-lg font-semibold text-gray-800"),
                P(source["content_preview"], cls="mt-2 text-gray-600 text-sm"),
                Div(
                    A("Read more →", href=source["source_link"], 
                      cls="text-blue-600 hover:text-blue-800 font-medium", target="_blank"),
                    P(f"Relevance: {source['relevance_score']}", 
                      cls="text-sm text-gray-500"),
                    cls="flex justify-between items-center mt-3"
                ),
                cls="p-6"
            ),
            cls="bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200"
        )
    else:  # search_doctors
        status_color = "text-green-600" if source["availability_status"] == "Available" else "text-red-500"
        return Div(
            Div(
                H3(source["doctor_name"], cls="text-lg font-semibold text-gray-800"),
                P(f"Specialization: {source['specialization']}", 
                  cls="text-gray-600 font-medium mt-2"),
                P(source["description"], cls="mt-2 text-gray-600 text-sm"),
                Div(
                    P(f"Status: {source['availability_status']}", 
                      cls=f"{status_color} font-medium"),
                    P(f"Relevance: {source['relevance_score']}", 
                      cls="text-sm text-gray-500"),
                    cls="flex justify-between items-center mt-3"
                ),
                A("Book Appointment →", href=source["appointment_link"],
                  cls="inline-block mt-3 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors duration-200",
                  target="_blank"),
                cls="p-6"
            ),
            cls="bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200"
        )

def HistoryPanel():
    """Render the search history panel"""
    if not search_history:
        return Div(
            P("No previous searches yet", cls="text-gray-500 text-center italic"),
            cls="p-4"
        )
    
    return Div(
        *[format_historical_source(source, timestamp) 
          for sources, timestamp in reversed(search_history) 
          for source in sources],
        cls="space-y-4"
    )

def Sources():
    """Render sources panel with history toggle"""
    kb_sources = [format_source(s, "search_knowledge_base") 
                 for s in current_sources["knowledge_base"]]
    doc_sources = [format_source(s, "search_doctors") 
                  for s in current_sources["doctors"]]
    
    return Div(
        # Tab navigation
        Div(
            Button("Current Results", 
                  hx_get="/current-sources",
                  hx_target="#sources-content",
                  cls="px-4 py-2 bg-blue-600 text-white rounded-tl-lg rounded-tr-lg"),
            Button("Search History",
                  hx_get="/history",
                  hx_target="#sources-content",
                  cls="px-4 py-2 bg-gray-200 text-gray-700 rounded-tl-lg rounded-tr-lg hover:bg-gray-300"),
            cls="space-x-2 mb-4"
        ),
        # Content area
        Div(
            H2("Knowledge Base Results", cls="text-xl font-bold text-gray-800 mb-4") if kb_sources else None,
            Div(*kb_sources,
                cls="space-y-4 mb-8"),
            H2("Recommended Doctors", cls="text-xl font-bold text-gray-800 mb-4") if doc_sources else None,
            Div(*doc_sources,
                cls="space-y-4"),
            id="sources-content",
            cls="space-y-6"
        ),
        id="sources-panel",
        cls="bg-gray-50 p-6 rounded-lg overflow-y-auto h-[85vh]"
    )

@app.route("/current-sources")
def get():
    """Return current sources panel content"""
    kb_sources = [format_source(s, "search_knowledge_base") 
                 for s in current_sources["knowledge_base"]]
    doc_sources = [format_source(s, "search_doctors") 
                  for s in current_sources["doctors"]]
    
    return (
        Div(*kb_sources,
            H2("Knowledge Base Results", cls="text-xl font-bold text-gray-800 mb-4") if kb_sources else None,
            cls="space-y-4 mb-8"),
        Div(*doc_sources,
            H2("Recommended Doctors", cls="text-xl font-bold text-gray-800 mb-4") if doc_sources else None,
            cls="space-y-4")
    )

@app.route("/history")
def get():
    """Return history panel content"""
    return HistoryPanel()

def ChatMessage(msg_idx, **kwargs):
    """Render a chat message"""
    msg = messages[msg_idx]
    is_user = msg['role'] == 'user'
    align_cls = "ml-auto" if is_user else "mr-auto"
    bg_cls = "bg-blue-600 text-white" if is_user else "bg-white text-gray-800"

    # Add markdown class and prose styling for better markdown formatting
    content_cls = f"px-4 py-3 rounded-lg {bg_cls} shadow-sm markdown prose prose-sm max-w-none"
    # Add light/dark specific styles for markdown content
    if is_user:
        content_cls += " prose-invert" # Light text for dark background
    else:
        content_cls += " prose-gray"  # Dark text for light background
    
    return Div(
        Div(
            P(msg['content'],
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

@app.route("/")
def get():
    """Main page route"""
    page = Body(
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
                    Div(*[ChatMessage(msg_idx) for msg_idx, msg in enumerate(messages)],
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
                    Sources(),
                    cls="bg-white rounded-lg shadow-lg"
                ),
                cls="grid grid-cols-2 gap-8 max-w-7xl mx-auto px-4"
            ),
            cls="min-h-screen bg-white"
        ),
        cls="bg-gradient-to-b from-blue-50 to-white"
    )
    return Title('Health Assistant'), page

async def handle_stream_response(response_stream, send, msg_idx):
    """Handle streaming response from backend"""
    action_status = None
    async for line in response_stream.aiter_lines():
        if not line.strip():
            continue
        
        data = json.loads(line)
        
        if data["type"] == "action":
            if action_status != data["status"]:
                action_status = data["status"]
                await send(Div(
                    Div(cls="w-2 h-2 bg-blue-600 rounded-full animate-bounce"),
                    Div(cls="w-2 h-2 bg-blue-600 rounded-full animate-bounce delay-100"),
                    Div(cls="w-2 h-2 bg-blue-600 rounded-full animate-bounce delay-200"),
                    id="loading-indicator",
                    cls="flex justify-center items-center space-x-2 py-4"
                ))
        
        elif data["type"] == "sources":
            if data["fn_name"] == "search_knowledge_base":
                current_sources["knowledge_base"] = data["sources"]
                # Add to history with timestamp
                search_history.append((data["sources"], datetime.now()))
            else:
                current_sources["doctors"] = data["sources"]
            await send(Sources())
        
        elif data["type"] == "stream":
            messages[msg_idx]["content"] += data["content"]
            await send(Span(
                data["content"],
                id=f"chat-content-{msg_idx}",
                hx_swap_oob="beforeend"
            ))
        
        elif data["type"] == "final_answer":
            messages[msg_idx]["content"] = data["content"]
            if "sources" in data:
                if data["sources"]["fn_name"] == "search_knowledge_base":
                    current_sources["knowledge_base"] = data["sources"]["data"]
                    # Add to history with timestamp
                    search_history.append((data["sources"]["data"], datetime.now()))
                else:
                    current_sources["doctors"] = data["sources"]["data"]
                await send(Sources())
            await send(Div("", id="loading-indicator", cls="hidden"))


@app.ws('/wscon')
async def ws(msg: str, send):
    """WebSocket connection handler"""
    # Add user message
    messages.append({"role": "user", "content": msg.rstrip()})
    await send(Div(
        ChatMessage(len(messages)-1),
        hx_swap_oob="beforeend",
        id="chatlist"
    ))
    
    # Clear input
    await send(ChatInput())
    
    # Show loading indicator
    await send(Div(
        Div(cls="w-2 h-2 bg-blue-600 rounded-full animate-bounce"),
        Div(cls="w-2 h-2 bg-blue-600 rounded-full animate-bounce delay-100"),
        Div(cls="w-2 h-2 bg-blue-600 rounded-full animate-bounce delay-200"),
        id="loading-indicator",
        cls="flex justify-center items-center space-x-2 py-4"
    ))
    
    # Add empty assistant message
    messages.append({"role": "assistant", "content": ""})
    msg_idx = len(messages) - 1
    await send(Div(
        ChatMessage(msg_idx),
        hx_swap_oob="beforeend",
        id="chatlist"
    ))

    api_uri = os.getenv("API_URI", "")
    
    # Call backend API with proper streaming
    async with httpx.AsyncClient() as client:
        async with client.stream('POST', 
                               api_uri,
                               json={"text": msg, "history": messages}, timeout=30.0) as response:
            await handle_stream_response(response, send, msg_idx)

if __name__ == "__main__":
    serve()