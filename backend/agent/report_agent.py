import json
import re
import time
import os
from agent.planner import get_openai_client, get_model_name
from tools.report_tool import compile_markdown_report, compile_pdf_report, compile_docx_report, compile_pptx_report
from memory.postgres.db import save_report, log_tool_call

def generate_synthesis_via_llm(query: str, retrieved_papers: list, external_context: list) -> dict:
    """
    Synthesizes search results and external crawler context into a unified structured brief.
    """
    client = get_openai_client()
    
    # Collate context from papers
    context_text = ""
    for paper in retrieved_papers[:3]:
        context_text += f"\nTitle: {paper.get('title')}\nAbstract: {paper.get('abstract')}\n"
    for ctx in external_context[:3]:
        context_text += f"\n{ctx}\n"
        
    if not context_text:
        context_text = f"General query: {query}"
        
    prompt = f"""You are a senior AI research scientist. Synthesize a unified research analysis for the query: "{query}" using the retrieved contexts below.
Generate a valid JSON object. Do not include markdown wraps or explanations.

Context:
{context_text[:5000]}

Target JSON Structure:
{{
  "executive_brief": {{
    "problem_statement": "A clear description of the core problem addressed by the query",
    "proposed_solution": "The proposed method or solutions identified in the literature",
    "key_innovation": "Core advancements or techniques that distinguish these methods",
    "main_results": "Summary of major empirical achievements or benchmarks",
    "impact": "High-level summary of scientific/industry impact",
    "difficulty_score": "Difficulty score from 1 to 10 (integer or string)",
    "reading_time": "Estimated reading time (e.g. '10 mins')",
    "research_domain": "Core research field"
  }},
  "key_contributions": [
    {{
      "title": "Title of key contribution 1",
      "description": "Short explanation of the contribution",
      "importance": "Why it matters scientifically"
    }}
  ],
  "why_it_matters": {{
    "historical_importance": "Evolutionary history of this topic in the literature",
    "industry_impact": "How it is applied in commercial systems",
    "academic_impact": "Academic citation significance",
    "papers_influenced": ["Paper A", "Paper B"],
    "modern_applications": "List modern systems or systems using it"
  }},
  "reading_roadmap": {{
    "before_reading": ["Prerequisite 1", "Prerequisite 2"],
    "after_reading": ["Next paper 1", "Next paper 2"],
    "learning_path": "Learning roadmap summary description"
  }},
  "paper_deconstruction": {{
    "problem": "Clear problem summary (under 3 sentences)",
    "motivation": "Why solving this topic is important (under 3 sentences)",
    "methodology": "Overview of common architectures or approaches (under 4 sentences)",
    "experiments": "Standard dataset benchmarks and training setups (under 3 sentences)",
    "results": "Typical findings and performance comparisons (under 3 sentences)",
    "limitations": "Current limitations or scaling bottlenecks (under 3 sentences)",
    "future_work": "Next research directions (under 3 sentences)"
  }},
  "opportunities": [
    {{
      "title": "Research Opportunity Title",
      "description": "Description of an underexplored path or potential thesis topic",
      "novelty": "Novelty score from 1 to 10",
      "impact": "Impact score from 1 to 10",
      "difficulty": "Difficulty score from 1 to 10",
      "time": "Research duration",
      "funding": "Funding potential",
      "publication": "Publication potential"
    }}
  ],
  "equations": [
    {{
      "equation": "LaTeX formula (e.g. \\\\mathcal{{L}} = -\\\\sum y \\\\log(\\\\hat{{y}}))",
      "purpose": "A 1-sentence description of the formula's purpose",
      "variables": {{
        "y": "True label distribution",
        "\\hat{{y}}": "Predicted label distribution"
      }},
      "intuition": "Intuition summary (under 2 sentences)",
      "explanation": "Step-by-step breakdown",
      "worked_example": "Simple example values and output",
      "difficulty": "Beginner, Intermediate, Researcher, or Expert"
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
        print(f"[Report Agent] Synthesis LLM extraction error: {e}")
    return {}

def report_node(state: dict) -> dict:
    """
    LangGraph node to compile reports in multiple formats (Markdown, PDF, DOCX, PPTX).
    """
    start_time = time.time()
    query = state.get("query")
    print(f"[Report Agent] Compiling reports for task: '{query}'")
    
    messages = list(state.get("messages", []))
    messages.append("Report Generation Agent: Compiling output files.")
    
    # Create outputs folder if it doesn't exist
    output_dir = "reports"
    os.makedirs(output_dir, exist_ok=True)
    
    # Format a safe filename base
    safe_name = "".join(x for x in query if x.isalnum() or x in " -_").strip().replace(" ", "_")[:30]
    if not safe_name:
        safe_name = "research_report"
        
    md_path = os.path.join(output_dir, f"{safe_name}.md")
    pdf_path = os.path.join(output_dir, f"{safe_name}.pdf")
    docx_path = os.path.join(output_dir, f"{safe_name}.docx")
    pptx_path = os.path.join(output_dir, f"{safe_name}.pptx")
    
    # Prepare text content sections
    sections = state.get("sections", {})
    
    # If sections is empty or executive_brief is missing (e.g. text query), generate it dynamically
    if not sections or "executive_brief" not in sections:
        synthesis = generate_synthesis_via_llm(query, state.get("retrieved_papers", []), state.get("external_context", []))
        
        # Merge any existing sections
        if sections:
            for k, v in sections.items():
                synthesis[k] = v
        sections = synthesis
        
        # Format clean summary string
        brief = sections.get("executive_brief", {})
        summary_text = "### Executive Research Brief\n\n"
        summary_text += f"* **Research Domain:** {brief.get('research_domain', 'N/A')}\n"
        summary_text += f"* **Estimated Reading Time:** {brief.get('reading_time', 'N/A')}\n"
        summary_text += f"* **Difficulty Score:** {brief.get('difficulty_score', 'N/A')}/10\n\n"
        summary_text += f"#### Problem Statement\n{brief.get('problem_statement', 'N/A')}\n\n"
        summary_text += f"#### Proposed Solution\n{brief.get('proposed_solution', 'N/A')}\n\n"
        summary_text += f"#### Key Innovation\n{brief.get('key_innovation', 'N/A')}\n\n"
        summary_text += f"#### Main Results\n{brief.get('main_results', 'N/A')}\n\n"
        summary_text += f"#### Impact\n{brief.get('impact', 'N/A')}\n"
        
        sections["summary"] = summary_text
        state["sections"] = sections
        
    # Build reference text bibliography
    references = []
    for paper in state.get("retrieved_papers", []):
        ref_str = f"{', '.join(paper.get('authors', [])) or 'Anon'}. {paper.get('title')}. ({paper.get('published')})."
        references.append(ref_str)
    if not references:
        references = ["No external bibliography sources retrieved."]
        
    # Filter out non-string fields from sections to prevent compiler crashes on nested structures
    compilation_sections = {k: v for k, v in sections.items() if isinstance(v, str)}
    
    # Compile the files
    title = f"Autonomous Research on {query}"
    compile_markdown_report(title, compilation_sections, references, md_path)
    compile_pdf_report(title, compilation_sections, references, pdf_path)
    compile_docx_report(title, compilation_sections, references, docx_path)
    compile_pptx_report(title, compilation_sections, references, pptx_path)
    
    # Save metadata to DB (including full JSON sections)
    task_id = state.get("task_id", 0)
    save_report(task_id, md_path, "Markdown", sections)
    save_report(task_id, pdf_path, "PDF", sections)
    save_report(task_id, docx_path, "DOCX", sections)
    save_report(task_id, pptx_path, "PPTX", sections)
    
    # Log telemetry
    duration_ms = (time.time() - start_time) * 1000.0
    log_tool_call(
        task_id=task_id,
        step_index=5,
        tool_name="report_compiler",
        kwargs={"output_directory": output_dir},
        output=f"Successfully generated reports and parsed JSON synthesis.",
        success=True,
        duration_ms=duration_ms
    )
    
    messages.append(f"Report Generation Agent: Created artifacts in {output_dir}/.")
    
    reports = {
        "markdown": md_path,
        "pdf": pdf_path,
        "docx": docx_path,
        "pptx": pptx_path
    }
    
    return {
        **state,
        "reports": reports,
        "messages": messages
    }
