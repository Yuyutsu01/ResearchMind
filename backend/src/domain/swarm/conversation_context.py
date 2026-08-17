"""
Conversation Context Module for ResearchMind Swarm Architecture

Manages conversational state, message history, and selected region metadata 
for interactive chat threads attached to PDF selection highlights.
"""

import json
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from src.adapters.db.redis_cache import redis_cache

@dataclass
class ChatMessage:
    role: str  # "user" or "assistant"
    content: str
    timestamp: float = 0.0
    agent_sources: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "agent_sources": self.agent_sources
        }

@dataclass
class ConversationContext:
    """
    State container for a conversational chat thread associated with a paper region.
    """
    conversation_id: str
    session_id: int
    page: int = 1
    section: str = "General Section"
    selected_text: str = ""
    content_type: str = "text"
    surrounding_context: str = ""
    messages: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conversation_id": self.conversation_id,
            "session_id": self.session_id,
            "page": self.page,
            "section": self.section,
            "selected_text": self.selected_text,
            "content_type": self.content_type,
            "surrounding_context": self.surrounding_context,
            "messages": self.messages
        }

class ConversationContextManager:
    """
    Manages creation, retrieval, and message appending for ConversationContext in Redis.
    """

    def _cache_key(self, conversation_id: str) -> str:
        return f"cache:conversation:{conversation_id}"

    def get_conversation(self, conversation_id: str) -> Optional[ConversationContext]:
        """
        Retrieves ConversationContext from Redis.
        """
        key = self._cache_key(conversation_id)
        cached = redis_cache.get(key)
        if cached:
            return ConversationContext(**cached)
        return None

    def save_conversation(self, context: ConversationContext, ttl: int = 86400):
        """
        Saves ConversationContext in Redis with 24-hour TTL.
        """
        key = self._cache_key(context.conversation_id)
        redis_cache.set(key, context.to_dict(), ttl_seconds=ttl)

    def append_message(self, conversation_id: str, message: ChatMessage) -> Optional[ConversationContext]:
        """
        Appends a user or assistant message to an active conversation thread.
        """
        ctx = self.get_conversation(conversation_id)
        if ctx:
            ctx.messages.append(message.to_dict())
            self.save_conversation(ctx)
            print(f"[ConversationManager] Appended {message.role} message to Conversation '{conversation_id}'")
        return ctx

conversation_manager = ConversationContextManager()
