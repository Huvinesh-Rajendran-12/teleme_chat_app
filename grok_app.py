from fasthtml.common import *
from openai import OpenAI, AsyncOpenAI
import json
from threading import Thread
from config.settings import settings
from services.search_service import search_doctors, search_knowledge_base

# Initialize app with required headers
app, rt = fast_app(
    pico=False,  # We'll use Tailwind instead
    exts="ws",
    hdrs=(
        Script(src="https://cdn.tailwindcss.com"),
        MarkdownJS(),
    )
)

# Initialize OpenAI client and global state
client = OpenAI(
    api_key=settings.XAI_API_KEY,
    base_url=settings.XAI_BASE_URL
)  # Configure with environment variables

async_client = AsyncOpenAI(
    api_key=settings.XAI_API_KEY,
    base_url=settings.XAI_BASE_URL
)

messages = []

# Tool definitions
tools_definition = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Retrieve health information from the knowledge base given the query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The user query, e.g. what is diabetes ?"},
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_doctors",
            "description": "Get the suitable doctors based on the user's query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The user query, e.g. recommend me a doctor for diabetes"},
                },
                "required": ["query"]
            }
        }
    }
]

tool_maps = {
    'search_knowledge_base': search_knowledge_base,
    'search_doctors': search_doctors
}

# Define component functions
def ChatMessage(msg_idx):
    """Render a chat message with sources"""
    if msg_idx >= len(messages):
        return ""
    
    msg = messages[msg_idx]
    text = msg.get('content', '')
    is_user = msg['role'] == 'user'
    
    return Div(
        Div(
            Div(msg['role'].title(), cls="text-xs text-gray-500 mb-1"),
            Div(text,
                cls=f"px-4 py-2 rounded-lg {'bg-blue-500 text-white' if is_user else 'bg-gray-200 text-gray-800'} max-w-[80%] break-words marked"),
            cls=f"{'ml-auto' if is_user else 'mr-auto'} max-w-[80%]"
        ),
        cls="mb-4",
        id=f"chat-message-{msg_idx}",
    )

def ChatInput():
    """Render chat input field"""
    return Input(
        type="text",
        name="msg",
        id="chat-input",
        placeholder="Type your health-related question here...",
        cls="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500",
        hx_swap_oob="true"
    )

def format_sources(sources):
    """Format sources for a specific message"""

    formatted_sources = []


    for source in json.loads(sources):
        if 'doctor_name' in source:  # Doctor source
            formatted_sources.append(
                Div(
                    H4(source['doctor_name'], cls="font-semibold text-lg"),
                    P(f"Specialization: {source['specialization']}", cls="text-gray-600"),
                    P(source['description'], cls="mt-1"),
                    A("Book Appointment",
                      href=source['appointment_link'],
                      cls="inline-block mt-2 text-blue-500 hover:text-blue-700",
                      target="_blank"),
                    cls="mb-4 border-b border-gray-200 pb-4"
                )
            )
        else:  # Knowledge base source
            formatted_sources.append(
                Div(
                    H4(source['title'], cls="font-semibold text-lg"),
                    P(source['content_preview'], cls="mt-1"),
                    A("Source Link",
                      href=source['source_link'],
                      cls="inline-block mt-2 text-blue-500 hover:text-blue-700",
                      target="_blank"),
                    cls="mb-4 border-b border-gray-200 pb-4"
                )
            )
    
    return formatted_sources

# Route handlers
@rt("/")
def get():
    """Main page handler"""
    messages.clear()
    
    page = Main(
        H1('AI Health Assistant', cls="text-3xl font-bold text-gray-800 mb-6 px-4"),
        # Split layout for chat and sources
        Div(
            # Chat section
            Div(
                Div(id="chatlist", cls="h-[calc(100vh-220px)] overflow-y-auto px-4"),
                Div(id="suggestions-container", cls="px-4"),
                Form(
                    Div(
                        ChatInput(),
                        Button("Send", type="submit",
                              cls="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"),
                        cls="flex space-x-4 items-center"
                    ),
                    id="chat-form",
                    ws_send=True,
                    hx_ext="ws",
                    ws_connect="/ws",
                    cls="mt-4 px-4"
                ),
                cls="flex-1"
            ),
            # Sources panel
            Div(
                H2("Sources", cls="text-xl font-semibold mb-4"),
                Div(
                    id="sources-panel",
                    cls="overflow-y-auto"
                ),
                cls="w-96 bg-gray-50 border-l border-gray-200 p-4"
            ),
            cls="flex max-w-7xl mx-auto"
        ),
        cls="bg-gray-50 min-h-screen"
        # Add JavaScript for source updates
    )
    return Title('AI Health Assistant'), page


@rt("/chat")
def post(text: str = ""):
    """Handle chat submission"""
    if not text.strip():
        return ""

    # Add user message
    user_msg_idx = len(messages)
    messages.append({"role": "user", "content": text.strip()})
    
    # Add initial assistant message
    assistant_msg_idx = len(messages)
    messages.append({"role": "assistant", "content": "", "generating": True})
    
    # Process in background
    Thread(target=process_response, args=(messages, assistant_msg_idx), daemon=True).start()
    
    return (
        ChatMessage(user_msg_idx),
        ChatMessage(assistant_msg_idx),
        ChatInput()
    )

async def get_next_questions(last_message: str):
    """Based on the last message get suggestions for follow up questions."""
    try:
        prompt = {
            "role": "user",
            "content": f"""Based on this health-related response: "{last_message}"
            Suggest 2 natural follow-up questions that a patient might want to ask.
            These should be within 4 four words.
            Return ONLY the questions in a Python list format like this: ["question 1", "question 2"]
            The questions should be clear and concise."""
        }
        response = await async_client.chat.completions.create(
            model="grok-2-1212",
            messages=[prompt],
            temperature=0.7
        )

        suggestions_text = response.choices[0].message.content
        import ast
        try:
            suggestions = ast.literal_eval(suggestions_text)
            if isinstance(suggestions, list) and len(suggestions) > 0:
                return suggestions[:2]  # Ensure we only get 2 questions
        except:
            pass

        return ["Could you explain more about that?",
                "Summarize this"]
    except Exception as e:
        print(f"Error generating suggestions: {e}")
        return ["Could you explain more about that?",
                "Summarize this"]

def format_suggestions(suggestions):
    """Format suggestion buttons as websocket-connected forms"""
    return Div(
        Div(
            *(Form(
                Button(
                    suggestion,
                    type="submit",
                    cls="px-4 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-full transition-colors duration-200"
                ),
                Hidden(suggestion, name="msg"),  # Hidden input with the suggestion text
                hx_ext="ws",  # Enable websocket
                ws_send=True,  # Connect to websocket
                ws_connect="/ws",
                cls="inline-block"  # Keep forms inline
              ) for suggestion in suggestions),
            cls="flex flex-wrap gap-2 justify-center mt-2 mb-4"
        ),
        id="suggestions-container",
        hx_swap_oob="innerHTML"
    )

async def process_tool_call(tool_call):
    """Process tool calls from the AI"""
    fn_name = tool_call.function.name
    fn_args = json.loads(tool_call.function.arguments)

    print(f"Processing tool {fn_name} with args: {fn_args}")
    
    result = tool_maps[fn_name](**fn_args)
 
    messages.append({
        "role": "tool",
        "content": json.dumps(result),
        "tool_name": fn_name,
        "tool_call_id": tool_call.id
    })

@app.ws('/ws')
async def ws(msg: str, send):
    """Web socket handler to stream the AI response."""
    
    # Add user message
    messages.append({
        "role": "user",
        "content": msg.strip()
    })
    user_msg_idx = len(messages) - 1

    # Send user message to chat
    await send(Div(
        ChatMessage(user_msg_idx),
        hx_swap_oob="beforeend",
        id="chatlist"
    ))

    # Reset chat input
    await send(ChatInput())

    try:
        # First, call tools if needed
        response = await async_client.chat.completions.create(
            model="grok-2-1212",
            messages=messages,
            tools=tools_definition,
            tool_choice="auto",
            stream=True
        )

        # Add initial assistant message
        messages.append({
            "role": "assistant",
            "content": ""
        })
        assistant_msg_idx = len(messages) - 1

        # Show initial loading state
        await send(Div(
            ChatMessage(assistant_msg_idx),
            hx_swap_oob="beforeend",
            id="chatlist"
        ))

        async for chunk in response:
            if chunk.choices[0].delta.content is not None:
                messages[assistant_msg_idx]['content'] += chunk.choices[0].delta.content
                # Update the current message
                await send(Div(
                    ChatMessage(assistant_msg_idx),
                    hx_swap_oob="outerHTML",
                    id=f"chat-message-{assistant_msg_idx}"
                ))

            if chunk.choices[0].delta.tool_calls:
                for tool_call in chunk.choices[0].delta.tool_calls:
                    await process_tool_call(tool_call)

                    if messages[-1]['role'] == 'tool':
                        formatted_sources = format_sources(messages[-1]['content'])
                        await send(Div(
                            *formatted_sources,
                            id="sources-panel",
                            hx_swap_oob="innerHTML"
                        ))

        # If last message was a tool response, get another completion
        if messages[-1]['role'] == 'tool':
            messages.append({
                "role": "assistant",
                "content": ""
            })
            assistant_msg_idx = len(messages) - 1

            # Show loading state for new message
            await send(Div(
                ChatMessage(assistant_msg_idx),
                hx_swap_oob="beforeend",
                id="chatlist"
            ))

            response = await async_client.chat.completions.create(
                model="grok-2-1212",
                messages=messages[:-1],  # Exclude empty assistant message
                tools=tools_definition,
                tool_choice="auto",
                stream=True
            )

            async for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    messages[assistant_msg_idx]['content'] += chunk.choices[0].delta.content
                    await send(Div(
                        ChatMessage(assistant_msg_idx),
                        hx_swap_oob="outerHTML",
                        id=f"chat-message-{assistant_msg_idx}"
                    ))

        # Generate and send suggestions after completion
        suggestions = await get_next_questions(messages[-1]['content'])
        await send(format_suggestions(suggestions))

    except Exception as e:
        # Add error message
        messages.append({
            "role": "assistant",
            "content": f"I apologize, but I encountered an error: {str(e)}"
        })
        await send(Div(
            ChatMessage(len(messages)-1),
            hx_swap_oob="beforeend",
            id="chatlist"
        ))

def process_response(messages, idx):
    """Process AI response in background"""
    try:
        while True:
            response = client.chat.completions.create(
                model="grok-2-1212",  # Replace with your model
                messages=messages[:-1],
                tools=tools_definition,
                tool_choice="auto",
                stream=True
            )

            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    messages[idx]['content'] += chunk.choices[0].delta.content

                if chunk.choices[0].delta.tool_calls:
                    for tool_call in chunk.choices[0].delta.tool_calls:
                        process_tool_call(tool_call)
                        idx += 1

            # Handle tool response if needed
            if messages[idx]['role'] == 'tool':
                messages.append({"role": "assistant", "content": "", "generating": True})
                idx += 1
                
                response = client.chat.completions.create(
                    model="grok-2-1212",  # Replace with your model
                    messages=messages[:-1],
                    tools=tools_definition,
                    tool_choice="auto",
                    stream=True
                )

                for chunk in response:
                    if chunk.choices[0].delta.content is not None:
                        messages[idx]['content'] += chunk.choices[0].delta.content
    except Exception as e:
        messages[idx]['content'] = f"I apologize, but I encountered an error: {str(e)}"
    finally:
        messages[idx]['generating'] = False

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=5001)