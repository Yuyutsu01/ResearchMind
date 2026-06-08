import os
import sys
import time

# Ensure parent modules can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.web_search_tool import search_web, get_wikipedia_definition
from memory.postgres.db import log_tool_call
from rag.retrieve import add_documents_to_index
import re

def expansion_node(state: dict) -> dict:
    """
    LangGraph node to expand on complex scientific concepts using Wikipedia & Web Search.
    """
    start_time = time.time()
    query = state.get("query")
    rl_actions = state.get("rl_actions", {})
    depth_choice = rl_actions.get("expansion_depth", 1) # default: shallow
    task_id = state.get("task_id", 0)
    
    print(f"[Expansion Agent] Expanding knowledge for: '{query}' at depth: {depth_choice}")
    
    messages = list(state.get("messages", []))
    messages.append("Knowledge Expansion Agent: Expanding academic context.")
    
    external_context = []
    
    if depth_choice == 0:
        messages.append("Knowledge Expansion Agent: Depth is None. Skipping.")
        return state
        
    # 1. Attempt Wikipedia definition lookup
    wiki_res = get_wikipedia_definition(query)
    if wiki_res and wiki_res.get("snippet"):
        external_context.append(f"Source: {wiki_res['title']} (Wikipedia)\nSnippet: {wiki_res['snippet']}\nLink: {wiki_res['url']}")
        add_documents_to_index(wiki_res['snippet'], f"wiki_{wiki_res['title'].replace(' ', '_')}.txt", task_id)
        
    # 2. Search definitions
    search_q = f"what is {query} research overview"
    results = search_web(search_q, max_results=3 if depth_choice == 2 else 1)
    
    for r in results:
        external_context.append(f"Source: {r['title']}\nSnippet: {r['snippet']}\nLink: {r['url']}")
        if len(r['snippet']) > 30:
            safe_title = re.sub(r'[^\w\s-]', '', r['title']).strip().replace(" ", "_")[:50]
            add_documents_to_index(r['snippet'], f"web_{safe_title}.txt", task_id)
        
    # Log the tool call in DB
    duration_ms = (time.time() - start_time) * 1000.0
    log_tool_call(
        task_id=task_id,
        step_index=3,
        tool_name="web_expander",
        kwargs={"search_query": search_q, "depth": depth_choice},
        output=f"Extracted {len(external_context)} background snippets.",
        success=True,
        duration_ms=duration_ms
    )
    
    messages.append(f"Knowledge Expansion Agent: Collected {len(external_context)} concept reference snippets and updated RAG.")
    
    return {
        **state,
        "external_context": external_context,
        "messages": messages
    }
