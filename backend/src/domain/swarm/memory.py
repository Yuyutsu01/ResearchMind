import time
from typing import List, Dict, Any, Optional
from src.adapters.db.postgres import execute_query
from src.adapters.db.redis_session import redis_session
from src.adapters.db.qdrant import semantic_memory

class AgentMemorySystem:
    """
    Unified memory system managing short-term (active session), 
    long-term (cross-session notes), and semantic vector memory.
    """
    def retrieve_context(self, session_id: int, query_text: str) -> str:
        """
        Gathers short-term, long-term, and semantic memories,
        compiling them into a structured prompt context block.
        """
        # 1. Semantic Memory: Vector search inside Qdrant
        semantic_chunks = []
        if semantic_memory:
            try:
                # Query nearest vectors filtered by session_id
                hits = semantic_memory.search(session_id, query_text, top_k=3)
                for hit in hits:
                    if hit.get("score", 0.0) > 0.4:
                        semantic_chunks.append(hit["text"])
            except Exception as e:
                print(f"[Memory System Warning] Semantic search failed: {e}")

        # 2. Short-Term Memory: Live session timeline history from Redis
        short_term_history = []
        try:
            history = redis_session.get_stream_history(session_id)
            # Take last 3 interactions to avoid prompt bloat
            for item in history[-3:]:
                short_term_history.append(
                    f"- User read highlight: \"{item['text']}\" | Summary: {item['summary']}"
                )
        except Exception as e:
            print(f"[Memory System Warning] Short-term history read failed: {e}")

        # 3. Long-Term Memory: Notebook annotations across all sessions of the user
        long_term_notes = []
        try:
            # Resolve user_id of the current session to fetch historical notes
            notes = execute_query(
                """
                SELECT selection_text, user_note FROM research_notebook
                WHERE session_id = %s OR session_id IN (
                    SELECT id FROM sessions WHERE user_id = (
                        SELECT user_id FROM sessions WHERE id = %s
                    )
                )
                ORDER BY id DESC LIMIT 3;
                """,
                (session_id, session_id),
                fetch=True
            )
            if notes:
                for n in notes:
                    note_details = f" (Annotation: {n['user_note']})" if n["user_note"] else ""
                    long_term_notes.append(f"- Concept: \"{n['selection_text']}\"{note_details}")
        except Exception as e:
            print(f"[Memory System Warning] Long-term memory query failed: {e}")

        # Assemble unified context prompt block
        context_sections = []
        if semantic_chunks:
            context_sections.append("--- RELEVANT PAPER SECTIONS ---\n" + "\n".join(semantic_chunks))
        if short_term_history:
            context_sections.append("--- LIVE SESSION READING HISTORY ---\n" + "\n".join(short_term_history))
        if long_term_notes:
            context_sections.append("--- HISTORICAL ANNOTATIONS & PREFERENCES ---\n" + "\n".join(long_term_notes))

        return "\n\n".join(context_sections)

agent_memory = AgentMemorySystem()
