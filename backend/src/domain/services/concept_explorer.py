import os
import sys
import time
import json
import re

# Ensure backend directory is in path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
while current_dir and os.path.basename(current_dir) != "backend":
    parent = os.path.dirname(current_dir)
    if parent == current_dir:
        break
    current_dir = parent

if current_dir and current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from src.adapters.db.postgres_db import log_tool_call, save_concept
from src.domain.services.planner import get_openai_client, get_model_name

def concept_node(state: dict) -> dict:
    """
    LangGraph node to extract, define, and explain complex research concepts.
    """
    start_time = time.time()
    query = state.get("query", "")
    task_id = state.get("task_id", 0)
    messages = list(state.get("messages", []))
    messages.append("Concept Explorer Agent: Analyzing paper sections for technical key concepts.")
    
    sections = state.get("sections", {})
    # Collate a subset of paper text
    paper_text = ""
    for sec_name, sec_content in sections.items():
        if sec_name.lower() in ["abstract", "introduction", "methodology"]:
            paper_text += f"\n--- {sec_name.upper()} ---\n{sec_content[:2000]}"
            
    if not paper_text:
        paper_text = query
        
    client = get_openai_client()
    prompt = f"""You are an expert scientific concept analyzer. Extract the top 3-5 core technical or mathematical concepts/methods from the research text below.
For each concept, formulate its formal definition, mathematical representations (using LaTeX or plain text equations), and primary practical applications.

Text:
{paper_text[:4000]}

You MUST output ONLY a valid JSON array of objects. Do not wrap in markdown or include conversational text.
Target JSON Structure:
[
  {{
    "term": "Self-Attention",
    "definition": "A mechanism relating different positions of a single sequence in order to compute a representation of the sequence.",
    "math_formula": "Attention(Q, K, V) = softmax(Q K^T / sqrt(d_k)) V",
    "applications": "Transformer models, natural language processing, machine translation, audio processing"
  }},
  ...
]
"""
    extracted_count = 0
    try:
        response = client.chat.completions.create(
            model=get_model_name(),
            messages=[
                {"role": "system", "content": "You output JSON arrays only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        content = response.choices[0].message.content
        json_match = re.search(r'\[.*\]', content, re.DOTALL)
        if json_match:
            concepts = json.loads(json_match.group(0))
            for c in concepts:
                term = c.get("term", "").strip()
                definition = c.get("definition", "").strip()
                math_formula = c.get("math_formula", "").strip()
                applications = c.get("applications", "").strip()
                
                if term and definition:
                    save_concept(task_id, term, definition, math_formula, applications)
                    extracted_count += 1
    except Exception as e:
        print(f"[Concept Agent] Concept extraction failed: {e}")
        
    duration_ms = (time.time() - start_time) * 1000.0
    log_tool_call(
        task_id=task_id,
        step_index=4,
        tool_name="concept_extractor",
        kwargs={"query": query},
        output=f"Extracted and saved {extracted_count} conceptual terms to DB.",
        success=True,
        duration_ms=duration_ms
    )
    
    messages.append(f"Concept Explorer Agent: Successfully extracted and saved {extracted_count} scientific terms to memory database.")
    
    return {
        **state,
        "messages": messages
    }
