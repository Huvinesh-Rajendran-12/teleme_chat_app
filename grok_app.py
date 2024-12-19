from fasthtml.common import *
from openai import OpenAI
from services.search_service import search_knowledge_base, search_doctors
from config.settings import settings
import json
from threading import Thread

# App initialization remains the same...
app = FastHTML(hdrs=(
    Script(src="https://cdn.tailwindcss.com"),
    Script(src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"),
    MarkdownJS(),
    Script("""
        // Configure marked options
        marked.setOptions({
            breaks: true,
            gfm: true,
            sanitize: true
        });
        
        // Helper function to render markdown
        function renderMarkdown() {
            document.querySelectorAll('[data-markdown="true"]').forEach(el => {
                el.innerHTML = marked.parse(el.textContent);
            });
        }
        
        // Helper function for tab handling
        function handleTabClick(event) {
            const button = event.target;
            if (!button.classList.contains('tab-button')) return;
            
            // Remove active state from all tabs
            document.querySelectorAll('.tab-button').forEach(tab => {
                tab.classList.remove('active', 'text-blue-600', 'border-blue-600');
                tab.classList.add('text-gray-500');
            });
            
            // Add active state to clicked tab
            button.classList.add('active', 'text-blue-600', 'border-blue-600');
            button.classList.remove('text-gray-500');
        }
        
        // Initialize tab click handlers
        document.addEventListener('htmx:afterSettle', function() {
            renderMarkdown();
        });
    """)
))

# Initialize OpenAI client and global state...
client = OpenAI(
    api_key=settings.DASHSCOPE_API_KEY,
    base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
)

messages = []
global fn_call_in_progress
fn_call_in_progress = False
current_sources = {
    "knowledge_base": [],
    "doctors": []
}

# Tools definition remains the same...

tools_definition = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Retrieve health information from the knowledge base given the query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The user query, e.g. what is diabetes ?"
                    },
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_doctors",
            "description": "Get the suitalbe doctors based on the user's query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The user query, e.g. recommend me a doctor for diabetes"
                    }
                },
                "required": ["query"]
            }
        }
    }
]

tools_map = {
    "search_knowledge_base": search_knowledge_base,
    "search_doctors": search_doctors,
}

def reset_messages():
    global messages
    messages = []


def ChatMessage(msg_idx):
    """Render a chat message with markdown support"""
    msg = messages[msg_idx]
    text = "..." if msg['content'] == "" else msg['content']
    is_user = msg['role'] == 'user'
    generating = msg.get('generating', False)
    
    align_cls = "ml-auto" if is_user else "mr-auto"
    bg_cls = "bg-blue-600" if is_user else "bg-white"
    text_cls = "text-black" if is_user else "text-gray-800"
    
    # Common classes for the message bubble
    bubble_cls = f"p-4 rounded-2xl shadow-sm {bg_cls} {text_cls} max-w-[80%] whitespace-pre-wrap"

    stream_args = {
        "hx_trigger": "every 50ms",
        "hx_swap": "outerHTML",
        "hx_get": f"/chat_message/{msg_idx}"
    } if generating else {}
    
    if generating:
        content_div = Div(
            text,
            id=f"content-{msg_idx}",
            cls=bubble_cls
        )
    else:
        content_div = Div(
            # Use a data attribute to store raw content for markdown
            text,
            data_markdown=True,
            id=f"content-{msg_idx}",
            cls=f"{bubble_cls} prose prose-sm"
        )

    if fn_call_in_progress:
        status = Div(
            "Retrieving Data...",
            cls="text-sm text-gray-500 mt-1"
        )
        
    return Div(
        Div(msg['role'].capitalize(), 
            cls=f"text-sm {text_cls} mb-1"),
        content_div,
        status,
        cls=f"mb-6 {align_cls}",
        id=f"msg-{msg_idx}",
        **stream_args,
        _=f"""
        on load
            if {msg_idx} > 0
                send updateSources({msg_idx}) to #sources-panel 
        end
        """
    )

def ChatInput():
    """Render the chat input field"""
    return Input(
        type="text",
        name='msg',
        id='msg-input',
        placeholder="Ask about health topics or find a doctor...",
        cls="w-full px-4 py-3 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent",
        autofocus=True,
        hx_swap_oob='true'
    )

def SourcesPanel(msg_idx):
    is_tool = messages[msg_idx].get('role') == 'tool' 
    if msg_idx >= len(messages) or not is_tool:
        return Div(
            P("No available sources yet", cls="text-gray-500 text-center mt-4"),
            id="sources-panel",
            cls="w-full h-full"
        )

    msg = messages[msg_idx]
    data = msg.get('content') if is_tool else []

    return Div(
        Div(
            Button(
                "Medical Experts",
                cls="px-4 py-2 font-medium rounded-t-lg focus:outline-none",
                id="tab-doctors",
                hx_get=f"/sources/{msg_idx}/doctors",
                hx_target="#tab-content",
                _="on click add bg-white text-blue-600 remove bg-gray-100 text-gray-600 to me "
                   "add bg-gray-100 text-gray-600 remove bg-white text-blue-600 to #tab-knowledge"
            ),
            Button(
                "Knowledge Base",
                cls="px-4 py-2 font-medium rounded-t-lg focus:outline-none",
                id="tab-knowledge",
                hx_get=f"/sources/{msg_idx}/knowledge",
                hx_target="#tab-content",
                _="on click add bg-white text-blue-600 remove bg-gray-100 text-gray-600 to me "
                   "add bg-gray-100 text-gray-600 remove bg-white text-blue-600 to #tab-doctors"
            ),
            cls="flex space-x-1 border-b border-gray-200"
        ),
        Div(
            id="tab-content",
            cls="p-4 bg-white flex-grow overflow-y-auto"
        ),
        id="sources-panel",
        cls="flex flex-col h-full"
    )


def format_source(source, source_type):
    """Format a single source item for display"""
    if source_type == "knowledge_base":
        return Div(
            Div(
                H3(source["title"], 
                   cls="text-lg font-semibold text-gray-800"),
                P(source["content_preview"], 
                  cls="mt-2 text-sm text-gray-600 line-clamp-2"),  # Limit preview text
                Div(
                    A("Read more", 
                      href=source["source_link"], 
                      cls="text-blue-600 hover:text-blue-700 hover:underline text-sm"),
                    P(f"Relevance: {source.get('relevance_score', 'N/A')}", 
                      cls="text-sm text-gray-500"),
                    cls="flex justify-between items-center mt-3"
                ),
                cls="p-6 bg-white rounded-xl shadow-md hover:shadow-lg transition-shadow duration-200"
            ),
            cls="mb-4 last:mb-0"
        )
    else:  # doctors
        return Div(
            Div(
                Div(
                    H3(source["doctor_name"], 
                       cls="text-lg font-semibold text-gray-800"),
                    P(source["specialization"], 
                      cls="text-sm text-blue-600 font-medium"),
                    cls="mb-3"
                ),
                P(source["description"], 
                  cls="text-sm text-gray-600 line-clamp-3"),  # Limit description text
                Div(
                    P(source["availability_status"],
                      cls="px-3 py-1 rounded-full text-sm font-medium " + 
                          ("bg-green-100 text-green-800" if source["availability_status"] == "Available"
                           else "bg-red-100 text-red-800")),
                    P(f"Relevance: {source.get('relevance_score', 'N/A')}", 
                      cls="text-sm text-gray-500"),
                    cls="flex justify-between items-center mt-4"
                ),
                A("Book Appointment",
                  href=source["appointment_link"],
                  cls="mt-4 inline-block px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200 text-sm font-medium"),
                cls="p-6 bg-white rounded-xl shadow-md hover:shadow-lg transition-shadow duration-200"
            ),
            cls="mb-4 last:mb-0"
        )

def Sources():
    """Render sources panel with enhanced tab handling"""
    return Div(
        # Tab buttons with improved state handling
        Div(
            Button("Knowledge Base",
                  id="kb-tab",
                  cls="tab-button px-4 py-2 text-sm font-medium active text-blue-600 border-b-2 border-blue-600",
                  hx_get="/sources-content?tab=knowledge",
                  hx_target="#tab-content",
                  onclick="handleTabClick(event)"),
            Button("Available Doctors",
                  id="doctors-tab",
                  cls="tab-button px-4 py-2 text-sm font-medium text-gray-500",
                  hx_get="/sources-content?tab=doctors",
                  hx_target="#tab-content",
                  onclick="handleTabClick(event)"),
            cls="flex space-x-1 border-b border-gray-200 bg-white"
        ),
        # Content area
        Div(id="tab-content",
            cls="bg-white p-4 flex-grow overflow-y-auto"),
        cls="h-full flex flex-col"
    )

@app.get("/message-content/{msg_idx}")
def get_message_content(msg_idx: int):
    """Route for getting updated message content"""
    if msg_idx >= len(messages):
        return ""
    
    msg = messages[msg_idx]
    if not msg.get('generating', False):
        # Return final message with markdown rendering trigger
        rendered = ChatMessage(msg_idx)
        return (
            rendered,
            Script(f"""
                const content = document.querySelector('#content-{msg_idx}');
                if (content && content.dataset.markdown) {{
                    content.innerHTML = marked.parse(content.textContent);
                }}
            """)
        )
    
    return ChatMessage(msg_idx)

@app.get("/sources/{msg_idx}/doctors")
def get_doctor_sources(msg_idx: int):
    if msg_idx >= len(messages):
        return ""
    
    sources = messages[msg_idx].get('content', [])
    doctor_sources = [s for s in sources if 'doctor_name' in s]
    
    return Div(
        *(
            Div(
                H4(source['doctor_name'], cls="font-semibold text-lg"),
                P(f"Specialization: {source['specialization']}", cls="text-gray-600"),
                P(source['description'], cls="mt-1"),
                A("Book Appointment",
                  href=source['appointment_link'],
                  cls="inline-block mt-2 text-blue-500 hover:text-blue-700"),
                cls="mb-4 border-b border-gray-200 pb-4"
            )
            for source in doctor_sources
        ) if doctor_sources else P("No medical experts found", cls="text-gray-500 text-center")
    )

@app.get("/sources/{msg_idx}/knowledge")
def get_knowledge_sources(msg_idx: int):
    if msg_idx >= len(messages):
        return ""
    
    sources = messages[msg_idx].get('sources', [])
    knowledge_sources = [s for s in sources if 'doctor_name' not in s]
    
    return Div(
        *(
            Div(
                H4(source['title'], cls="font-semibold text-lg"),
                P(source['content_preview'], cls="mt-1"),
                A("Source Link",
                  href=source['source_link'],
                  cls="inline-block mt-2 text-blue-500 hover:text-blue-700"),
                cls="mb-4 border-b border-gray-200 pb-4"
            )
            for source in knowledge_sources
        ) if knowledge_sources else P("No knowledge base entries found", cls="text-gray-500 text-center")
    )

@app.get("/sources")
def get_sources():
    """Route for getting the entire sources panel"""
    return Sources()

@app.route("/")
def get():
    """Render the main page"""
    app.hdrs += (Script(src="https://unpkg.com/hyperscript.org@0.9.12"),)
    reset_messages()
    page = Body(
            Div(
                # Header section
                Div(
                    H1("Health Assistant", 
                    cls="text-4xl font-bold text-gray-800"),
                    P("Get instant answers to your health questions and find suitable healthcare providers", 
                    cls="text-lg text-gray-600 mt-2"),
                    cls="text-center mb-12"
                ),
                # Main content grid
                Div(
                    # Chat section
                    Div(
                        Div(
                            id="chat-container",
                            cls="h-[70vh] overflow-y-auto px-6 py-8"
                        ),
                        Div(
                            Form(
                                Div(
                                    ChatInput(),
                                    Button("Send",
                                        type="submit",
                                        cls="absolute right-2 top-1/2 transform -translate-y-1/2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200 font-medium"),
                                    cls="relative"
                                ),
                                LoadingIndicator(),
                                hx_post="/chat",
                                hx_target="#chat-container",
                                hx_swap="beforeend",
                                hx_indicator="#loading-indicator",
                                cls="mt-4"
                            ),
                            cls="px-6 py-4 bg-white border-t border-gray-200"
                        ),
                        cls="bg-gray-50 rounded-2xl shadow-lg overflow-hidden"
                    ),
                    # Sources section with fixed height
                    Div(Sources(), 
                        cls="ml-8 h-[70vh] sources-container",
                        id="sources-container",
                        hx_get="/sources",
                        hx_trigger="every 2s",
                        hx_swap="outerHTML"),
                    cls="grid grid-cols-2 gap-8 max-w-7xl mx-auto px-4"
                ),
                cls="container mx-auto px-4 py-8"
            ),
            cls="min-h-screen bg-gradient-to-b from-blue-50 via-white to-blue-50"
        )
    
    # Add styles for tabs and scrolling
    styles = Style("""
        .tab-button {
            transition: all 0.2s;
            position: relative;
        }
        
        .tab-button.active {
            color: rgb(37, 99, 235);
            border-bottom: 2px solid rgb(37, 99, 235);
        }
        
        .tab-button:not(.active):hover {
            background-color: rgb(249, 250, 251);
        }
        
        /* Markdown content styles */
        [data-markdown="true"] {
            overflow-wrap: break-word;
        }
        
        [data-markdown="true"] pre {
            background-color: rgb(243, 244, 246);
            padding: 1rem;
            border-radius: 0.375rem;
            margin: 1rem 0;
        }
        
        [data-markdown="true"] code {
            background-color: rgb(243, 244, 246);
            padding: 0.2rem 0.4rem;
            border-radius: 0.25rem;
        }
    """)
        
    return Title("Health Assistant"), styles, page

@app.post("/chat")
def post(msg: str = ""):
    """Handle chat form submission"""
    if not msg.strip():
        return ""
    
    # Add user message
    user_msg_idx = len(messages)
    messages.append({"role": "user", "content": msg.strip()})
    user_message = ChatMessage(user_msg_idx)
    
    # Add initial assistant message
    assistant_msg_idx = len(messages)
    messages.append({"role": "assistant", "content": "", "generating": True})
    assistant_message = ChatMessage(assistant_msg_idx)
    
    # Start processing in background
    messages_history = [{"content": m["content"], "role": m["role"]} 
                       for m in messages[:-1]]
    Thread(target=process_response, 
           args=(messages_history, assistant_msg_idx)).start()
    
    return (
        Div(user_message, Script(f"""
            const content = document.querySelector('#content-{user_msg_idx}');
            if (content && content.dataset.markdown) {{
                content.innerHTML = marked.parse(content.textContent);
            }}
        """)),
        assistant_message,
        ChatInput(),
        Script("""
            const container = document.getElementById('chat-container');
            if (container) {
                container.scrollTop = container.scrollHeight;
            }
        """)
    )

def process_response(messages_history, idx):
    try:
        response = client.chat.completions.create(
            model="grok-2-1212",
            messages=messages,
            tools=tools_definition,
            tool_choice="auto",
            stream=True
        )

        for chunk in response:

            if chunk.choices[0].delta.content is not None:
                messages[idx]['message'] += chunk.choices[0].delta.content 
                print(chunk.choices[0].delta.content, end="", flush=True)


            if chunk.choices[0].delta.tool_calls:
                print("\n")
                
                for tool_call in chunk.choices[0].delta.tool_calls:
                    fn_call_in_progress = True
                    fn_name = tool_call.function.name
                    fn_args = json.loads(chunk.choices[0].delta.tool_calls[0].function.arguments)


                    result = tools_map[fn_name](**fn_args)

                    messages.append(
                        {
                            "role": "tool",
                            "content": json.dumps(result),
                            "tool_name": fn_name,
                            "tool_call_id": tool_call.id  # tool_call.id supplied in Grok's response
                        }
                    )

        if messages[-1]['role'] == 'tool':
            messages.append({"role": "assistant", "content": "", "generating": True})
            response = client.chat.completions.create(
                model="grok-2-1212",
                messages=messages,
                tools=tools_definition,
                tool_choice="auto",
                stream=True
            )

            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    messages[-1]['content'] += chunk.choices[0].delta.content
                    print(chunk.choices[0].delta.content, end="", flush=True)  
    except Exception as e:
        print(f"Error in process_response: {str(e)}")
        messages[idx]['content'] = "I apologize, but I encountered an error while processing your request. Please try again."
    finally:
        messages[idx]['generating'] = False

# Rest of the code remains the same...

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=5001, reload=True)