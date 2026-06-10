import os
import sys
import time
import re

# Ensure parent modules can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.arxiv_tool import search_arxiv, search_semantic_scholar
from tools.web_search_tool import search_web
from memory.postgres.db import log_tool_call

def retrieval_node(state: dict) -> dict:
    """
    LangGraph node to search and retrieve supporting research papers.
    """
    start_time = time.time()
    query = state.get("query")
    rl_actions = state.get("rl_actions", {})
    source_choice = rl_actions.get("source_selection", 0) # default: arxiv
    
    print(f"[Retrieval Agent] Running retrieval for: '{query}' with source: {source_choice}")
    
    messages = list(state.get("messages", []))
    messages.append("Research Retrieval Agent: Querying scientific databases.")
    
    retrieved = []
    tool_name = "arxiv"
    
    if source_choice == 0:
        tool_name = "search_arxiv"
        retrieved = search_arxiv(query, max_results=3)
    elif source_choice == 1:
        tool_name = "search_semantic_scholar"
        retrieved = search_semantic_scholar(query, limit=3)
    else:
        tool_name = "search_web"
        web_results = search_web(query, max_results=3)
        for w in web_results:
            retrieved.append({
                "source": "web",
                "title": w["title"],
                "abstract": w["snippet"],
                "url": w["url"]
            })
            
    # Log the tool call in DB
    duration_ms = (time.time() - start_time) * 1000.0
    log_tool_call(
        task_id=state.get("task_id", 0),
        step_index=2,
        tool_name=tool_name,
        kwargs={"query": query},
        output=f"Retrieved {len(retrieved)} entries.",
        success=True,
        duration_ms=duration_ms
    )
    
    # 2. Add retrieved paper abstracts to RAG index dynamically so agents can search them
    from rag.retrieve import add_documents_to_index
    for paper in retrieved:
        title = paper.get("title", "unnamed_paper")
        abstract = paper.get("abstract", "")
        if len(abstract) > 30:
            safe_title = re.sub(r'[^\w\s-]', '', title).strip().replace(" ", "_")[:50]
            add_documents_to_index(abstract, f"retrieved_{safe_title}.txt", state.get("task_id", 0))
            
    messages.append(f"Research Retrieval Agent: Retrieved {len(retrieved)} related references via {tool_name} and indexed summaries for RAG search.")
    
    return {
        **state,
        "retrieved_papers": retrieved,
        "messages": messages
    }
