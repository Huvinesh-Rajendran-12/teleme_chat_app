from fasthtml.common import *
import json
import httpx
from datetime import datetime
import asyncio

# Set up the app with Tailwind and DaisyUI
app = FastHTML(hdrs=(
    Script(src="https://cdn.tailwindcss.com"),
    Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/daisyui@4.11.1/dist/full.min.css"),
    MarkdownJS()
), exts='ws')

# Store messages, current sources, and history
messages = []
current_sources = {"knowledge_base": [], "doctors": []}
search_history = []

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
    """Render a chat message with polling if still generating"""
    msg = messages[msg_idx]
    is_user = msg['role'] == 'user'
    generating = 'generating' in msg and msg['generating']
    
    # Add polling attributes if message is still generating
    poll_attrs = {
        "hx_trigger": "every 0.1s",
        "hx_swap": "outerHTML",
        "hx_get": f"/chat_message/{msg_idx}"
    } if generating else {}
    
    align_cls = "chat-end" if is_user else "chat-start"
    bubble_cls = "chat-bubble-primary" if is_user else "chat-bubble-secondary"
    
    return Div(
        Div(msg['role'], cls="chat-header"),
        Div(msg['content'] if msg['content'] else "...",
            cls=f"chat-bubble {bubble_cls} markdown prose"),
        id=f"chat-message-{msg_idx}",
        cls=f"chat {align_cls}",
        **poll_attrs,
        **kwargs
    )

@app.get("/chat_message/{msg_idx}")
def get_chat_message(msg_idx: int):
    """Route that gets polled while streaming"""
    if msg_idx >= len(messages):
        return ""
    return ChatMessage(msg_idx)

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
                H1('Health Assistant', cls="text-3xl font-bold"),
                P("Ask questions about health topics or find suitable doctors", 
                  cls="text-gray-600 mt-1"),
                cls="text-center mb-8 pt-8"
            ),
            # Main content
            Div(
                # Chat section
                Div(
                    Div(*[ChatMessage(i) for i in range(len(messages))],
                        id="chatlist",
                        cls="h-[70vh] overflow-y-auto px-4 py-6"),
                    Form(
                        Div(
                            ChatInput(),
                            Button("Send", cls="btn btn-primary"),
                            cls="relative"
                        ),
                        hx_post="/send",
                        hx_target="#chatlist",
                        hx_swap="beforeend",
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

@threaded
def process_stream_response(response_stream, msg_idx):
    """Process streaming response in a separate thread"""
    async def process():
        action_status = None
        async for line in response_stream.aiter_lines():
            if not line.strip():
                continue
            
            data = json.loads(line)
            
            if data["type"] == "stream":
                messages[msg_idx]["content"] += data["content"]
            elif data["type"] == "sources":
                if data["fn_name"] == "search_knowledge_base":
                    current_sources["knowledge_base"] = data["sources"]
                    search_history.append((data["sources"], datetime.now()))
                else:
                    current_sources["doctors"] = data["sources"]
            elif data["type"] == "final_answer":
                messages[msg_idx]["content"] = data["content"]
                messages[msg_idx]["generating"] = False
                
        messages[msg_idx]["generating"] = False
    
    asyncio.run(process())

@app.post("/send")
async def post(msg: str):
    """Handle message submission"""
    # Add user message
    messages.append({"role": "user", "content": msg.rstrip()})
    user_msg_idx = len(messages) - 1
    
    # Add initial assistant message
    messages.append({
        "role": "assistant",
        "content": "",
        "generating": True
    })
    assistant_msg_idx = len(messages) - 1
    
    # Start processing in background
    api_uri = os.getenv("API_URI", "")
    async with httpx.AsyncClient() as client:
        response = await client.stream(
            'POST',
            api_uri,
            json={"text": msg, "history": messages},
            timeout=30.0
        )
        process_stream_response(response, assistant_msg_idx)
    
    return (
        ChatMessage(user_msg_idx),
        ChatMessage(assistant_msg_idx),
        ChatInput()
    )

if __name__ == "__main__":
    serve()