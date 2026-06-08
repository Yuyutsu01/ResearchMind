import os
import sys
import time
import json
import re
from openai import OpenAI

# Ensure parent modules can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.pdf_tool import extract_pdf_content, extract_txt_content
from memory.postgres.db import log_tool_call
from rag.retrieve import add_documents_to_index
from agent.planner import get_openai_client, get_model_name

def extract_academic_details_via_llm(sections: dict) -> dict:
    """
    Calls Ollama to parse paper abstract/intro and extract structured metadata.
    """
    client = get_openai_client()
    
    # Grab first part of document to avoid context length overflow
    abstract = sections.get("abstract", "")
    intro = sections.get("introduction", "")[:1500]
    
    prompt = f"""You are an expert academic paper analyzer. Analyze the provided abstract and introduction to extract key metadata.
You MUST respond with ONLY a valid JSON object. Do not include markdown wraps or explanations.

Abstract:
{abstract}

Introduction Snippet:
{intro}

Target JSON Structure:
{{
  "title": "Official paper title",
  "authors": ["Author name 1", "Author name 2"],
  "datasets": ["Dataset Name A", "Dataset Name B"],
  "methodology": "Brief description of the model architecture, equations, or proposed framework",
  "key_findings": "Summary of experimental results or core contributions"
}}
"""
    try:
        response = client.chat.completions.create(
            model=get_model_name(),
            messages=[
                {"role": "system", "content": "You output JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        content = response.choices[0].message.content
        # Extract json matching braces
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
    except Exception as e:
        print(f"[Document Agent] LLM metadata extraction error: {e}")
    return {}

def parse_references(references_text: str) -> list[str]:
    """Splits references section text into individual citation strings."""
    if not references_text:
        return []
    lines = references_text.split("\n")
    refs = []
    current_ref = ""
    for line in lines:
        line_s = line.strip()
        if not line_s:
            continue
        # If it starts with [1], 1., or [Author, Year], it starts a new citation
        if re.match(r'^(\[\d+\]|\d+\.|\b\w+ et al\.,? \d{4})', line_s):
            if current_ref:
                refs.append(current_ref.strip())
            current_ref = line_s
        else:
            current_ref += " " + line_s
            
    if current_ref:
        refs.append(current_ref.strip())
    return [r for r in refs if len(r) > 15]

def document_node(state: dict) -> dict:
    """
    LangGraph node to analyze research papers.
    """
    start_time = time.time()
    pdf_path = state.get("pdf_path")
    task_id = state.get("task_id", 0)
    filename = os.path.basename(pdf_path) if pdf_path else "uploaded_doc"
    
    print(f"[Document Agent] Processing document: {pdf_path}")
    messages = list(state.get("messages", []))
    messages.append("Document Analysis Agent: Started parsing document.")
    
    if not pdf_path or not os.path.exists(pdf_path):
        state["errors"].append("Document path is invalid or file missing.")
        messages.append("Document Analysis Agent: Failed. Invalid document path.")
        return {**state, "messages": messages}
        
    # Choose parser based on extension
    if pdf_path.endswith(".pdf"):
        doc_data = extract_pdf_content(pdf_path)
    else:
        doc_data = extract_txt_content(pdf_path)
        
    if "error" in doc_data:
        state["errors"].append(doc_data["error"])
        messages.append(f"Document Analysis Agent: Failed to parse. {doc_data['error']}")
        return {**state, "messages": messages}
        
    sections = doc_data.get("sections", {})
    raw_text = doc_data.get("raw_text", "")
    
    # 1. Add chunks to RAG Vector & Keyword index
    add_documents_to_index(raw_text, filename, task_id)
    
    # 2. Extract detailed structural references
    ref_list = parse_references(sections.get("references", ""))
    
    # 3. Call LLM for structured metadata
    llm_metadata = extract_academic_details_via_llm(sections)
    
    paper_metadata = {
        "title": llm_metadata.get("title") or doc_data.get("title") or filename,
        "authors": llm_metadata.get("authors") or ["Unknown"],
        "datasets": llm_metadata.get("datasets") or [],
        "methodology": llm_metadata.get("methodology") or "Not explicitly detailed.",
        "key_findings": llm_metadata.get("key_findings") or "Not analyzed.",
        "num_pages": doc_data.get("num_pages", 1),
        "num_tables": len(doc_data.get("tables", [])),
        "num_citations": len(ref_list),
        "citations_extracted": ref_list[:15]  # Store first 15 references
    }
    
    # Update sections with LLM summaries
    state_sections = dict(state.get("sections", {}))
    for k, v in sections.items():
        state_sections[k] = v
        
    # Store key structured data back into state sections
    state_sections["metadata"] = json.dumps(paper_metadata)
    
    # Log telemetry
    duration_ms = (time.time() - start_time) * 1000.0
    log_tool_call(
        task_id=task_id,
        step_index=1,
        tool_name="academic_pdf_parser",
        kwargs={"pdf_path": pdf_path},
        output=f"Extracted {len(state_sections)} sections, {paper_metadata['num_citations']} references, and indexed text chunks for RAG.",
        success=True,
        duration_ms=duration_ms
    )
    
    messages.append(f"Document Analysis Agent: Parsed '{paper_metadata['title']}' by {', '.join(paper_metadata['authors'][:3])}.")
    
    return {
        **state,
        "sections": state_sections,
        "paper_metadata": paper_metadata,
        "messages": messages
    }
