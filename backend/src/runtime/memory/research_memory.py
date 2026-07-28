"""
Research Memory System Module for ResearchMind AI Runtime Architecture (Phase 2)

Tracks concepts learned by the user across papers, manages persistent user memory in PostgreSQL 
and Redis, and automatically adapts LLM prompts to suppress repetitive explanations.
"""

import json
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from src.adapters.db.postgres import execute_query
from src.adapters.db.redis_cache import redis_cache

@dataclass
class UserMemory:
    """
    Structured container storing a user's knowledge state and preferences.
    """
    session_id: int
    learned_concepts: List[str] = field(default_factory=list)
    preferred_level: str = "Beginner"
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "learned_concepts": self.learned_concepts,
            "preferred_level": self.preferred_level,
            "notes": self.notes
        }

class ResearchMemorySystem:
    """
    Persistent memory system for concept tracking and adaptive explanation tuning.
    Includes in-memory fallback dictionary for offline database resilience.
    """

    def __init__(self):
        self._local_memory: Dict[int, UserMemory] = {}

    def _cache_key(self, session_id: int) -> str:
        return f"cache:memory:{session_id}"

    def get_user_memory(self, session_id: int) -> UserMemory:
        """
        Retrieves user memory object from Redis cache, local fallback memory, or PostgreSQL.
        """
        # 1. Check local in-memory fallback first
        if session_id in self._local_memory:
            return self._local_memory[session_id]

        # 2. Check Redis cache
        key = self._cache_key(session_id)
        cached = redis_cache.get(key)
        if cached:
            mem = UserMemory(**cached)
            self._local_memory[session_id] = mem
            return mem

        # 3. Fallback to database lookup
        learned = []
        level = "Beginner"
        notes = []
        try:
            rows = execute_query(
                "SELECT learned_concepts, preferred_level, notes FROM user_research_memory WHERE session_id = %s LIMIT 1;",
                (session_id,),
                fetch=True
            )
            if rows:
                learned = rows[0].get("learned_concepts") or []
                level = rows[0].get("preferred_level") or "Beginner"
                notes = rows[0].get("notes") or []
        except Exception as e:
            print(f"[ResearchMemory Warning] Could not fetch memory from DB: {e}")

        mem = UserMemory(session_id=session_id, learned_concepts=learned, preferred_level=level, notes=notes)
        self._local_memory[session_id] = mem
        redis_cache.set(key, mem.to_dict(), ttl_seconds=86400)
        return mem

    def record_learned_concept(self, session_id: int, concept_name: str) -> UserMemory:
        """
        Adds a newly learned concept to user memory and updates local memory, DB & Redis.
        """
        mem = self.get_user_memory(session_id)
        c_clean = concept_name.strip()
        if c_clean and c_clean not in mem.learned_concepts:
            mem.learned_concepts.append(c_clean)
            self._local_memory[session_id] = mem
            
            # Update Redis cache
            redis_cache.set(self._cache_key(session_id), mem.to_dict(), ttl_seconds=86400)
            
            # Upsert into PostgreSQL database
            try:
                execute_query(
                    """
                    INSERT INTO user_research_memory (session_id, learned_concepts, preferred_level, notes)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (session_id) DO UPDATE SET learned_concepts = EXCLUDED.learned_concepts;
                    """,
                    (session_id, json.dumps(mem.learned_concepts), mem.preferred_level, json.dumps(mem.notes))
                )
            except Exception as e:
                print(f"[ResearchMemory Warning] DB upsert failed: {e}")

            print(f"[ResearchMemory] Recorded concept '{c_clean}' for session #{session_id}")
        return mem

    def build_memory_prompt_context(self, session_id: int) -> str:
        """
        Generates adaptive memory prompt context string for LLM injection.
        """
        mem = self.get_user_memory(session_id)
        if not mem.learned_concepts:
            return ""

        concepts_str = ", ".join(mem.learned_concepts)
        return (
            f"USER KNOWLEDGE STATE:\n"
            f"The user already understands the following concepts: [{concepts_str}].\n"
            f"ADAPTIVE INSTRUCTION: Do NOT explain basic definitions for these mastered concepts. "
            f"Focus directly on novel paper mechanics, mathematical derivations, or paper-specific contributions.\n\n"
        )

research_memory = ResearchMemorySystem()
