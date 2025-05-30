from fasthtml.common import *
from openai import OpenAI
from services.search_service import search_knowledge_base, search_doctors
from config.settings import settings
import json
from threading import Thread

# Set up the app with TailwindCSS
app = FastHTML(
    hdrs=(
        Script(src="https://cdn.tailwindcss.com"),
        MarkdownJS(),
        Script(src="static/js/sources.js")
    ), 
    exts='ws'
    )

# Initialize OpenAI client
client = OpenAI(
    api_key=settings.DASHSCOPE_API_KEY,
    base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
)

# Global state
messages = [
    {
        "role": "system",
        "content": settings.SYSTEM_PROMPT
    }
]

current_message_idx = 0

tools = [
    # Tool 1: obtain the current time
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "This tool can help you query the current time.",
            # No request parameter is needed. The parameters parameter is left empty
            "parameters": {}
        }
    },  
    # Tool 2: obtain the weather of a specific city
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "This tool can help you query the weather of a city.",
            "parameters": {  
                "type": "object",
                "properties": {
                    # The parameters parameter is set to location, which specifies the location whose weather you want to query
                    "location": {
                        "type": "string",
                        "description": "A city, county, or district, such as Beijing, Hangzhou, or Yuhang."
                    }
                }
            },
            "required": [
                "location"
            ]
        }
    }
]

def SourcesPanel():
    """
    Render the sources panel with tabs
    Uses HTMX to track current message
    """
    return Div(
        # Tabs
        Div(
            Button(
                "Medical Experts",
                cls="px-4 py-2 font-medium rounded-t-lg focus:outline-none bg-white text-blue-600",
                id="tab-doctors",
                hx_get="/sources/doctors",
                hx_target="#tab-content",
                _="on click add bg-white text-blue-600 remove bg-gray-100 text-gray-600 to me "
                   "add bg-gray-100 text-gray-600 remove bg-white text-blue-600 to #tab-knowledge"
            ),
            Button(
                "Knowledge Base", 
                cls="px-4 py-2 font-medium rounded-t-lg focus:outline-none bg-gray-100 text-gray-600",
                id="tab-knowledge",
                hx_get="/sources/knowledge",
                hx_target="#tab-content",
                _="on click add bg-white text-blue-600 remove bg-gray-100 text-gray-600 to me "
                   "add bg-gray-100 text-gray-600 remove bg-white text-blue-600 to #tab-doctors"
            ),
            cls="flex space-x-1 border-b border-gray-200"
        ),
        # Tab content
        Div(
            P("Select a message to view sources", cls="text-gray-500 text-center p-4"),
            id="tab-content",
            cls="p-4 bg-white flex-grow overflow-y-auto"
        ),
        id="sources-panel",
        cls="flex flex-col h-full",
        hx_trigger="messageSelected from:body"
    )

def ChatMessage(msg_idx):
    """Render a chat message with click handler to update sources"""
    if msg_idx >= len(messages):
        return ""
    
    msg = messages[msg_idx]
    generating = msg.get('generating', False)
    text = msg.get('content', '')
    is_user = msg['role'] == 'user'
    is_marked = "marked" if not generating else ""
    align_class = "ml-auto" if is_user else "mr-auto"
    bg_class = "bg-blue-500 text-white" if is_user else "bg-gray-200 text-gray-800"
    
    stream_args = {
        "hx_trigger": "every 50ms",
        "hx_swap": "outerHTML",
        "hx_get": f"/chat_message/{msg_idx}"
    } if generating else {}
    
    return Div(
        Div(
            Div(msg['role'].title(), cls="text-xs text-gray-500 mb-1"),
            Div(text,
                cls=f"px-4 py-2 rounded-lg {bg_class} {is_marked} max-w-[80%] break-words cursor-pointer",
                _=f"on click trigger messageSelected with {{msgIdx: {msg_idx}}}"),
            cls=f"{align_class} max-w-[80%]"
        ),
        cls="mb-4",
        id=f"chat-message-{msg_idx}",
        **stream_args
    )

def ChatInput():
    """Render the chat input"""
    return Input(
        type="text",
        name='text',
        id='chat-input',
        placeholder="Type your health-related question here...",
        cls="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent",
        hx_swap_oob='true'
    )

@app.get("/chat_message/{msg_idx}")
def get_chat_message(msg_idx: int):
    return ChatMessage(msg_idx)

@app.get("/sources/knowledge")
def get_knowledge_sources():
    """Get knowledge sources for current message"""
    global current_message_idx
    if current_message_idx >= len(messages):
        return P("No message selected", cls="text-gray-500 text-center")
    
    sources = messages[current_message_idx].get('knowledge_sources', [])
    
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
            for source in sources
        ) if sources else P("No knowledge base entries found", cls="text-gray-500 text-center")
    )

@app.get("/sources/doctors")
def get_doctor_sources():
    """Get doctor sources for current message"""
    global current_message_idx
    if current_message_idx >= len(messages):
        return P("No message selected", cls="text-gray-500 text-center")
    
    sources = messages[current_message_idx].get('doctor_sources', [])
    
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
            for source in sources
        ) if sources else P("No medical experts found", cls="text-gray-500 text-center")
    )

@app.get("/update_current_message/{msg_idx}")
def update_current_message(msg_idx: int):
    """Update the current message index"""
    global current_message_idx
    current_message_idx = msg_idx
    return ""

def process_sources(response, msg_idx):
    """Process sources from tools and update message"""
    print('response', response)
    if 'tool_calls' in response:
        for tool_call in response['tool_calls']:
            name = tool_call['function']['name']
            args = json.loads(tool_call['function']['arguments'])
            
            if name == 'search_knowledge_base':
                sources, _ = search_knowledge_base(args['query'])
                messages[msg_idx]['knowledge_sources'] = sources
            elif name == 'search_doctors':
                sources, _ = search_doctors(args['query'])
                messages[msg_idx]['doctor_sources'] = sources

def process_stream(msg_idx):
    """Process streaming response from OpenAI"""
    try:
        response = client.chat.completions.create(
            model=settings.QWEN_MODEL,
            messages=[{"role": m["role"], "content": m["content"]} for m in messages[:-1]],
            tools=tools,
            stream=True
        )
        
        current_msg = ""
        for chunk in response:
            print(chunk)
            if chunk.choices[0].delta.tool_calls:
                print(chunk.choices[0].delta.tool_calls)
                process_sources(chunk.choices[0].delta.model_dump(), msg_idx)

            if chunk.choices[0].delta.content:
                print(chunk.choices[0].delta.content, end="", flush=True)
                current_msg += chunk.choices[0].delta.content
                messages[msg_idx]['content'] = current_msg
            
            # Process tool calls if present
                
        messages[msg_idx]['generating'] = False
        
    except Exception as e:
        messages[msg_idx]['content'] = f"Error: {str(e)}"
        messages[msg_idx]['generating'] = False

@app.route("/")
def get():
    """Render the main page"""
    global current_message_idx
    current_message_idx = 0
    
    # Reset messages
    messages.clear()
    messages.append({
        "role": "system",
        "content": settings.SYSTEM_PROMPT
    })
    
    page = Body(
        # Add hyperscript for message selection
        Script("""
        on messageSelected
            set msgIdx to event.detail.msgIdx
            fetch `/update_current_message/${msgIdx}`
            trigger refreshSources
        end
        """, type="text/hyperscript"),
        
        Div(
            H1('AI Health Assistant', cls="text-3xl font-bold text-gray-800 mb-6 px-4"),
            # Main content area with split layout
            Div(
                # Chat section
                Div(
                    Div(
                        id="chatlist",
                        cls="h-[calc(100vh-220px)] overflow-y-auto px-4"
                    ),
                    Form(
                        Div(
                            ChatInput(),
                            Button(
                                "Send",
                                type="submit",
                                cls="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                            ),
                            cls="flex space-x-4 items-center"
                        ),
                        hx_post="/",
                        hx_target="#chatlist",
                        hx_swap="beforeend",
                        cls="mt-4 px-4"
                    ),
                    cls="flex-1"
                ),
                # Sources panel
                # Div(
                #     SourcesPanel(),
                #     cls="w-96 bg-gray-50 border-l border-gray-200"
                # ),
                # cls="flex flex-row flex-1"
            ),
            cls="max-w-7xl mx-auto h-screen flex flex-col"
        ),
        cls="bg-gray-50"
    )
    return Title('AI Health Assistant'), page

@app.post("/")
def post(text: str):
    """Handle chat form submission"""
    user_idx = len(messages)
    assistant_idx = user_idx + 1
    
    messages.append({
        "role": "user",
        "content": text.strip()
    })
    
    messages.append({
        "role": "assistant",
        "generating": True,
        "content": ""
    })
    
    Thread(target=process_stream, args=(assistant_idx,), daemon=True).start()
    
    return (
        ChatMessage(user_idx),
        ChatMessage(assistant_idx),
        ChatInput()
    )

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=5001, reload=True)