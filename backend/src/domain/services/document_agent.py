import os
import sys
import time
import json
import re
from openai import OpenAI

# Ensure backend directory is in path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
while current_dir and os.path.basename(current_dir) != "backend":
    parent = os.path.dirname(current_dir)
    if parent == current_dir:
        break
    current_dir = parent

if current_dir and current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from src.adapters.tools.pdf_tool import extract_pdf_content, extract_txt_content
from src.adapters.db.postgres_db import log_tool_call
from src.adapters.rag.retrieve import add_documents_to_index
from src.domain.services.planner import get_openai_client, get_model_name

def extract_brief_roadmap_matters_via_llm(sections: dict) -> dict:
    """
    Call 1: Extracts Executive Brief, Contributions, Why Paper Matters, and Reading Roadmap.
    """
    client = get_openai_client()
    abstract = sections.get("abstract", "")[:2500]
    intro = sections.get("introduction", "")[:2000]
    conclusion = sections.get("conclusion", "")[:2000]
    
    prompt = f"""You are an expert scientific analyst. Analyze the abstract, introduction, and conclusion of the research paper provided below.
Generate a valid JSON object. Do not include markdown wraps or explanations.

Abstract:
{abstract}

Introduction Snippet:
{intro}

Conclusion Snippet:
{conclusion}

Target JSON Structure:
{{
  "executive_brief": {{
    "problem_statement": "A clear description of the core problem addressed by the paper",
    "proposed_solution": "The proposed method or model introduced by the authors",
    "key_innovation": "What makes this solution unique compared to existing work",
    "main_results": "Summary of the major empirical findings or theoretical proofs",
    "impact": "High-level summary of the scientific or practical impact",
    "difficulty_score": "Difficulty score from 1 to 10 (integer or string)",
    "reading_time": "Estimated time to read in minutes (e.g. '15 mins')",
    "research_domain": "Core research field (e.g. 'Natural Language Processing')"
  }},
  "key_contributions": [
    {{
      "title": "Title of contribution 1",
      "description": "Short explanation of the contribution",
      "importance": "Why this specific contribution matters scientifically"
    }}
  ],
  "why_it_matters": {{
    "historical_importance": "The historical importance of this work in scientific lineage",
    "industry_impact": "How this research changed industry practices or commercial tech",
    "academic_impact": "How it influenced academic studies and citation flow",
    "papers_influenced": ["Paper A", "Paper B", "Modern LLMs (GPT, Llama, Claude, etc.)"],
    "modern_applications": "List modern systems or products using this technology"
  }},
  "reading_roadmap": {{
    "before_reading": ["Prerequisite subject or paper 1", "Prerequisite subject or paper 2"],
    "after_reading": ["Recommended follow-up paper 1", "Recommended follow-up paper 2"],
    "learning_path": "Brief description of the visual roadmap or logical steps to learn this topic"
  }}
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
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
    except Exception as e:
        print(f"[Document Agent] Brief LLM extraction error: {e}")
    return {}

def extract_deconstruction_opportunities_via_llm(sections: dict) -> dict:
    """
    Call 2: Renders the Paper Deconstruction collapsible elements and the Research Gaps/Opportunities.
    """
    client = get_openai_client()
    abstract = sections.get("abstract", "")[:1500]
    intro = sections.get("introduction", "")[:1500]
    methodology = sections.get("methodology", "")[:2500]
    results = sections.get("results", "")[:2500]
    
    prompt = f"""You are an expert scientific peer reviewer and analyst. Analyze the abstract, introduction, methodology, and results of the research paper provided below.
Generate a valid JSON object. Do not include markdown wraps or explanations.

Abstract:
{abstract}

Introduction Snippet:
{intro}

Methodology Snippet:
{methodology}

Results Snippet:
{results}

Target JSON Structure:
{{
  "paper_deconstruction": {{
    "problem": "Detailed, clear explanation of the scientific problem being solved (under 3 sentences)",
    "motivation": "Why solving this problem is important and what drove the authors (under 3 sentences)",
    "methodology": "Step-by-step description of the architecture, approach, or algorithms (under 4 sentences)",
    "experiments": "Details on datasets, metrics, and training setup (under 3 sentences)",
    "results": "Empirical outcomes, comparisons, and achievements (under 3 sentences)",
    "limitations": "Bottlenecks, compute constraints, or assumptions admitted or inferred (under 3 sentences)",
    "future_work": "Future paths or directions suggested by authors (under 3 sentences)"
  }},
  "opportunities": [
    {{
      "title": "Opportunity Title",
      "description": "Short explanation of the novel opportunity or extension of this work",
      "novelty": "Novelty score from 1 to 10",
      "impact": "Impact score from 1 to 10",
      "difficulty": "Difficulty score from 1 to 10",
      "time": "Estimated research duration (e.g. '3-6 months')",
      "funding": "Funding potential (e.g. 'High' or 'Medium')",
      "publication": "Publication potential (e.g. 'High')"
    }}
  ]
}}
"""
    try:
        response = client.chat.completions.create(
            model=get_model_name(),
            messages=[
                {"role": "system", "content": "You output JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        content = response.choices[0].message.content
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
    except Exception as e:
        print(f"[Document Agent] Deconstruction LLM extraction error: {e}")
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
    
    # 2. Extract detailed references
    ref_list = parse_references(sections.get("references", ""))
    
    # 3. Call LLM modular extraction functions (Bypassing equations call to optimize ingestion latency)
    brief_data = extract_brief_roadmap_matters_via_llm(sections)
    decon_data = extract_deconstruction_opportunities_via_llm(sections)
    
    brief = brief_data.get("executive_brief", {})
    
    paper_metadata = {
        "title": brief.get("title") or doc_data.get("title") or filename,
        "authors": brief_data.get("why_it_matters", {}).get("authors") or ["Unknown"],
        "datasets": decon_data.get("opportunities", [{}])[0].get("datasets") or [],
        "methodology": brief.get("proposed_solution") or "Not explicitly detailed.",
        "key_findings": brief.get("main_results") or "Not analyzed.",
        "num_pages": doc_data.get("num_pages", 1),
        "num_tables": len(doc_data.get("tables", [])),
        "num_citations": len(ref_list),
        "citations_extracted": ref_list[:15]
    }
    
    # Formulate custom section summary
    state_sections = {}
    for k, v in sections.items():
        state_sections[k] = v
        
    # Put structured briefs inside section summary JSON
    state_sections["executive_brief"] = brief
    state_sections["key_contributions"] = brief_data.get("key_contributions", [])
    state_sections["why_it_matters"] = brief_data.get("why_it_matters", {})
    state_sections["reading_roadmap"] = brief_data.get("reading_roadmap", {})
    state_sections["paper_deconstruction"] = decon_data.get("paper_deconstruction", {})
    state_sections["opportunities"] = decon_data.get("opportunities", [])
    state_sections["equations"] = [] # Kept empty for dashboard schema compatibility

    
    # Compile clean markdown summary text for static compilers
    summary_text = "### Executive Research Brief\n\n"
    summary_text += f"* **Research Domain:** {brief.get('research_domain', 'N/A')}\n"
    summary_text += f"* **Estimated Reading Time:** {brief.get('reading_time', 'N/A')}\n"
    summary_text += f"* **Difficulty Score:** {brief.get('difficulty_score', 'N/A')}/10\n\n"
    summary_text += f"#### Problem Statement\n{brief.get('problem_statement', 'N/A')}\n\n"
    summary_text += f"#### Proposed Solution\n{brief.get('proposed_solution', 'N/A')}\n\n"
    summary_text += f"#### Key Innovation\n{brief.get('key_innovation', 'N/A')}\n\n"
    summary_text += f"#### Main Results\n{brief.get('main_results', 'N/A')}\n\n"
    summary_text += f"#### Impact\n{brief.get('impact', 'N/A')}\n"
    
    state_sections["summary"] = summary_text
    state_sections["metadata"] = json.dumps(paper_metadata)
    
    # Log telemetry
    duration_ms = (time.time() - start_time) * 1000.0
    log_tool_call(
        task_id=task_id,
        step_index=1,
        tool_name="academic_pdf_parser",
        kwargs={"pdf_path": pdf_path},
        output=f"Extracted {len(state_sections)} sections, and compiled structured brief and deconstructions.",
        success=True,
        duration_ms=duration_ms
    )
    
    messages.append(f"Document Analysis Agent: Extracted structured deconstruction and executive roadmap from '{paper_metadata['title']}'.")
    
    return {
        **state,
        "sections": state_sections,
        "paper_metadata": paper_metadata,
        "messages": messages
    }
