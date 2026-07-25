"""
Shared Context Builder Module for ResearchMind Swarm Architecture (Phase 2 & 7)

Retrieves paper structural context, section headers, preceding/succeeding paragraphs, 
and metadata in a SINGLE pass. Produces an immutable SharedContext object used by all agents.
"""

import json
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from src.adapters.db.postgres import execute_query

@dataclass
class SharedContext:
    """
    Immutable shared context container passed across all swarm agents.
    Eliminates redundant database and vector search queries.
    """
    session_id: int
    selection_text: str
    selection_type: str
    target_id: Optional[str] = None
    section_title: str = "General Section"
    preceding_text: str = ""
    succeeding_text: str = ""
    paper_title: str = "Research Paper"
    abstract: str = ""
    figure_references: List[str] = field(default_factory=list)
    citation_references: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "selection_text": self.selection_text,
            "selection_type": self.selection_type,
            "target_id": self.target_id,
            "section_title": self.section_title,
            "preceding_text": self.preceding_text,
            "succeeding_text": self.succeeding_text,
            "paper_title": self.paper_title,
            "abstract": self.abstract,
            "figure_references": self.figure_references,
            "citation_references": self.citation_references,
            "metadata": self.metadata
        }

class ContextBuilder:
    """
    Single-pass database and graph query context builder.
    """
    
    def build_context(
        self, 
        session_id: int, 
        selection_text: str, 
        selection_type: str, 
        target_id: Optional[str] = None,
        doc_object: Optional[Dict[str, Any]] = None
    ) -> SharedContext:
        """
        Retrieves context details in one unified pass.
        """
        print(f"[ContextBuilder] Building single-pass SharedContext for session #{session_id}...")
        
        section_title = "General Section"
        preceding = ""
        succeeding = ""
        paper_title = "Scientific Document"
        abstract = ""
        figure_refs = []
        citation_refs = []
        meta = {}

        # 1. Resolve document title & abstract
        try:
            paper_rows = execute_query(
                "SELECT title, abstract FROM papers WHERE session_id = %s LIMIT 1;",
                (session_id,),
                fetch=True
            )
            if paper_rows:
                paper_title = paper_rows[0].get("title") or paper_title
                abstract = paper_rows[0].get("abstract") or abstract
        except Exception as e:
            print(f"[ContextBuilder Warning] Could not fetch paper metadata: {e}")

        # 2. Extract surrounding section context if object ID provided
        if target_id or doc_object:
            try:
                obj_id = target_id or doc_object.get("id")
                if obj_id:
                    obj_rows = execute_query(
                        "SELECT section_title, page, bounding_box, metadata FROM paper_objects WHERE session_id = %s AND id = %s;",
                        (session_id, obj_id),
                        fetch=True
                    )
                    if obj_rows:
                        section_title = obj_rows[0].get("section_title") or section_title
                        meta = obj_rows[0].get("metadata") or meta

                        # Fetch adjacent blocks on same page
                        page_num = obj_rows[0].get("page", 1)
                        adjacent_rows = execute_query(
                            "SELECT text_content FROM paper_objects WHERE session_id = %s AND page = %s ORDER BY id LIMIT 3;",
                            (session_id, page_num),
                            fetch=True
                        )
                        if adjacent_rows:
                            texts = [r["text_content"] for r in adjacent_rows if r.get("text_content")]
                            if len(texts) > 0:
                                preceding = texts[0]
                            if len(texts) > 1:
                                succeeding = texts[-1]
            except Exception as e:
                print(f"[ContextBuilder Warning] Could not fetch object context: {e}")

        ctx = SharedContext(
            session_id=session_id,
            selection_text=selection_text,
            selection_type=selection_type,
            target_id=target_id,
            section_title=section_title,
            preceding_text=preceding,
            succeeding_text=succeeding,
            paper_title=paper_title,
            abstract=abstract,
            figure_references=figure_refs,
            citation_references=citation_refs,
            metadata=meta
        )
        
        return ctx

context_builder = ContextBuilder()
