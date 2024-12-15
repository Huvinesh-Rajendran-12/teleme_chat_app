from fasthtml.common import *
import json
from datetime import datetime

from models.chat import ChatState
from services.ai_service import ai_service
from services.search_service import search_knowledge_base, search_doctors
from ui.pages import HomePage
from ui.components.chat import ChatMessage, ChatInput
from ui.components.sources import Sources
from config.settings import settings

# Initialize FastHTML app
app = FastHTML(hdrs=(
    Script(src="https://cdn.jsdelivr.net/npm/htmx.org@1.9.2/dist/htmx.min.js"),
    Script(src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"),
))

# Define routes
@app.route('/')
def get_home():
    """Render the home page."""
    return HomePage()

@app.route('/chat', methods=['POST'])
def handle_chat(state: ChatState):
    """Handle incoming chat messages."""
    user_message = state.user_message
    response = ai_service.process_message(user_message)
    return ChatMessage(msg_idx=len(state.messages) + 1, messages=state.messages + [{"user": "You", "message": user_message}, {"user": "Bot", "message": response}])

@app.route('/search', methods=['POST'])
def handle_search(query: str):
    """Handle search queries for knowledge base."""
    results, source = search_knowledge_base(query)
    return Sources(results=results, source=source)

@app.route('/doctors', methods=['POST'])
def handle_doctor_search(query: str):
    """Handle search queries for doctors."""
    doctor_results = search_doctors(query)
    return Sources(results=doctor_results)

# Error handler
@app.exception_handler(404)
def not_found(request, exc):
    return Titled("404 Not Found", P("The page you are looking for does not exist."))

# Main entry point
if __name__ == "__main__":
    serve(app, host=settings.API_HOST, port=settings.API_PORT)
