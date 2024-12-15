from fasthtml.common import *
from typing import Dict, Any, List
from datetime import datetime

def format_historical_source(source: Dict[str, Any], timestamp: datetime):
    """Format a historical source result"""
    return Div(
        Div(
            Div(
                H4(source['title'], cls="text-md font-semibold text-gray-800"),
                P(timestamp.strftime("%Y-%m-%d %H:%M"), cls="text-xs text-gray-500"),
                cls="flex justify-between items-center"
            ),
            P(source['content_preview'], cls="mt-2 text-gray-600 text-sm line-clamp-2"),
            A("Read more ->", href=source['source_link'], cls="text-blue-600 hover:text-blue-800 text-sm mt-2 inline-block", target="_blank"),
            cls="p-4"
        ),
        cls="bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200"
    )

def format_source(source: Dict[str, Any], source_type: str):
    """Format source information for display"""
    if source_type == "search_knowledge_base":
        return Div(
            Div(
                H3(source['title'], cls="text-lg font-semibold text-gray-800"),
                P(source['content_preview'], cls="mt-2 text-gray-600 text-sm"),
                Div(
                    A("Read More ->", href=source['source_link'], cls="text-blue-600 hover:text-blue-800 font-medium", target="_blank"),
                    P(f"Relevance: {source['relevance_score']}", cls="text-sm text-gray-500"),
                    cls="flex justify-between items-center mt-3"
                ),
                cls="p-6"
            ),
            cls="bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200"
        )
    else:
        status_color = "text-green-600" if source['availability_status'] == "Available" else "text-red-500"
        return Div(
            Div(
                H3(source['doctor_name'], cls="text-lg font-semibold text-gray-800"),
                P(f"Specialization: {source['specialization']}", cls="text-gray-600 font-medium mt-2"),
                Div(
                    P(f"Status: {source['availability_status']}", cls=f"{status_color} font-medium"),
                    P(f"Relevance: {source['relevance_score']}", cls="text-sm text-gray-500"),
                    cls="flex justify-between items-center mt-3"
                ),
                A("Book Appointment ->", href=source['appointment_link'], 
                  cls="inline-block mt-3 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors duration-200",
                  target="_blank"
                ),
                cls="p-6"
            ),
            cls="bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200"
        )

def Sources(current_sources: Dict[str, List[Dict[str, Any]]]):
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
            Div(*kb_sources,
                H2("Knowledge Base Results", cls="text-xl font-bold text-gray-800 mb-4") if kb_sources else None,
                cls="space-y-4 mb-8"),
            Div(*doc_sources,
                H2("Recommended Doctors", cls="text-xl font-bold text-gray-800 mb-4") if doc_sources else None,
                cls="space-y-4"),
            id="sources-content",
            cls="space-y-6"
        ),
        id="sources-panel",
        cls="bg-gray-50 p-6 rounded-lg overflow-y-auto h-[85vh]"
    )