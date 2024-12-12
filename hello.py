from fasthtml.common import *
import json
import httpx
from dotenv import load_dotenv
import asyncio

app = FastHTML(hdrs=(Script(src="https://cdn.tailwindcss.com"),))

load_dotenv()
api_uri = os.getenv("API_URI", "")

# Global message store
messages = []

def reset_messages():
    global messages 
    messages = []

def ChatMessage(msg_idx):
    if msg_idx >= len(messages):
        return ""
    
    msg = messages[msg_idx]
    text = msg.get('content', '')
    is_user = msg['role'] == 'user'
    align_class = "ml-auto" if is_user else "mr-auto"
    width_class = "max-w-[25%]" if is_user else "max-w-[75%]"
    bg_class = "bg-blue-500 text-white" if is_user else "bg-gray-200 text-gray-800"
    
    generating = msg.get('generating', False)
    stream_args = {
        "hx_trigger": "every 50ms",
        "hx_swap": "outerHTML",
        "hx_get": f"/chat_message/{msg_idx}"
    } if generating else {}
    
    # Status message
    status = ""
    if msg.get('status'):
        status = Div(
            msg['status'],
            cls="text-sm text-gray-500 mt-1"
        )
    
    # Sources section
    sources = ""
    if msg.get('sources'):
        sources_content = []
        for source in msg['sources']:
            if 'doctor_name' in source:  # Doctor source
                sources_content.append(
                    Div(
                        H4(source['doctor_name'], cls="font-semibold text-lg"),
                        P(f"Specialization: {source['specialization']}", cls="text-gray-600"),
                        P(source['description'], cls="mt-1"),
                        A("Book Appointment",
                          href=source['appointment_link'],
                          cls="inline-block mt-2 text-blue-500 hover:text-blue-700"),
                        cls="mb-4 border-b border-gray-200 pb-4"
                    )
                )
            else:  # Knowledge base source
                sources_content.append(
                    Div(
                        H4(source['title'], cls="font-semibold text-lg"),
                        P(source['content_preview'], cls="mt-1"),
                        A("Source Link",
                          href=source['source_link'],
                          cls="inline-block mt-2 text-blue-500 hover:text-blue-700"),
                        cls="mb-4 border-b border-gray-200 pb-4"
                    )
                )
        sources = Div(
            H3("Related Information", cls="text-xl font-bold mb-3"),
            *sources_content,
            cls="bg-gray-50 p-4 rounded-lg mt-4 shadow-sm"
        )
    
    return Div(
        Div(
            Div(msg['role'].title(), cls="text-xs text-gray-500 mb-1"),
            Div(text,
                cls=f"px-4 py-2 rounded-lg {bg_class} max-w-[80%] break-words"),
            status,
            sources,
            cls=f"{align_class} {width_class}"
        ),
        cls="mb-4",
        id=f"chat-message-{msg_idx}",
        **stream_args
    )

def ChatInput():
    return Input(
        type="text",
        name='text',
        id='chat-input',
        placeholder="Type your health-related question here...",
        cls="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent",
        hx_swap_oob='true'
    )

@app.get("/chat_message/{msg_idx}")
async def get_chat_message(msg_idx: int):
    return ChatMessage(msg_idx)

async def process_message(msg_idx):
    try:
        async with httpx.AsyncClient() as client:
            async with client.stream(
                'POST',
                api_uri,
                json={'text': messages[msg_idx-1]['content']},
                timeout=30.0
            ) as response:
                async for line in response.aiter_lines():
                    if not line:
                        continue
                        
                    data = json.loads(line)
                    msg = messages[msg_idx]
                    
                    if data['type'] == 'action':
                        msg['status'] = data['message']
                    elif data['type'] == 'sources':
                        msg['sources'] = data['sources']
                        msg['status'] = None
                    elif data['type'] == 'stream':
                        if 'content' not in msg:
                            msg['content'] = ''
                        msg['content'] += data['content']
                    elif data['type'] == 'final_answer':
                        msg['generating'] = False
                        msg['status'] = None
                        if not msg.get('content'):
                            msg['content'] = data['content']
                        if 'sources' in data:
                            msg['sources'] = data['sources']['data']
                        break
                    
    except Exception as e:
        print(f"Error in process_message: {e}")
        messages[msg_idx]['content'] = f"Error: {str(e)}"
        messages[msg_idx]['generating'] = False

@app.route("/")
def get():
    reset_messages()
    page = Body(
        Div(
            H1('Teleme Health Assistant', cls="text-3xl font-bold text-gray-800 mb-6"),
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
            cls="max-w-5xl mx-auto py-8"
        ),
        cls="min-h-screen bg-gray-50"
    )
    return Title('Teleme Health Assistant'), page

@app.post("/")
async def post(text: str):
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
    
    # Create task but don't await it
    asyncio.create_task(process_message(assistant_idx))
    
    return (
        ChatMessage(user_idx),
        ChatMessage(assistant_idx),
        ChatInput()
    )

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=5001, reload=True)