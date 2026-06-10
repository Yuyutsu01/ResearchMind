import os
import sys
import time
import json
import re

# Ensure parent modules can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory.postgres.db import log_tool_call
from agent.planner import get_openai_client, get_model_name

def gap_detector_node(state: dict) -> dict:
    """
    LangGraph node to analyze papers, find methodological gaps, and discover future work directions.
    """
    start_time = time.time()
    query = state.get("query", "")
    task_id = state.get("task_id", 0)
    messages = list(state.get("messages", []))
    messages.append("Research Gap Detection Agent: Searching methodology for weaknesses and limitations.")
    
    sections = state.get("sections", {})
    # Compile text for analysis
    context_text = ""
    for sec_name, sec_content in sections.items():
        if sec_name.lower() in ["abstract", "introduction", "methodology", "results"]:
            context_text += f"\n--- {sec_name.upper()} ---\n{sec_content[:2000]}"
            
    if not context_text:
        context_text = query
        
    client = get_openai_client()
    prompt = f"""You are an expert scientific peer reviewer and research analyst. Analyze the research methodologies and results context below.
Your goal is to identify unexplored research opportunities, missing experiments, datasets limitations, model bottlenecks, and novel future extensions.

Context:
{context_text[:5000]}

You MUST output ONLY a valid JSON object. Do not wrap in markdown or include conversational text.
Target JSON Structure:
{{
  "gaps": [
    {{
      "title": "Title of the research gap or opportunity",
      "limitations": "Existing methodology bottleneck, dataset constraint, or assumption limitation",
      "proposal": "Actionable proposal, e.g. future model extension or validation strategy",
      "impact": "Expected impact score from 1 to 10 (integer or string)",
      "publication_potential": "Publication potential (e.g. 'High', 'Medium', 'Low')"
    }},
    ...
  ]
}}
"""
    gap_data = {}
    try:
        response = client.chat.completions.create(
            model=get_model_name(),
            messages=[
                {"role": "system", "content": "You output JSON objects only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        content = response.choices[0].message.content
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            gap_data = json.loads(json_match.group(0))
    except Exception as e:
        print(f"[Gap Agent] Gap analysis failed: {e}")
        
    # Format a text summary for the report sections
    gaps_list = gap_data.get("gaps", [])
    gaps_text = "### Identified Research Gaps & Opportunities\n\n"
    if gaps_list:
        for idx, g in enumerate(gaps_list):
            gaps_text += f"{idx+1}. **{g.get('title')}**\n"
            gaps_text += f"   - *Limitation:* {g.get('limitations')}\n"
            gaps_text += f"   - *Actionable Proposal:* {g.get('proposal')}\n"
            gaps_text += f"   - *Expected Impact:* {g.get('impact')}/10\n"
            gaps_text += f"   - *Publication Potential:* {g.get('publication_potential')}\n\n"
    else:
        gaps_text += "No significant research gaps could be determined automatically from the text."
        
    state_sections = dict(state.get("sections", {}))
    state_sections["gaps"] = gaps_text
    state_sections["gaps_data"] = gaps_list # Save structured list for dashboard UI
    
    duration_ms = (time.time() - start_time) * 1000.0
    log_tool_call(
        task_id=task_id,
        step_index=5,
        tool_name="gap_detector",
        kwargs={"query": query},
        output=f"Detected {len(gaps_list)} research gaps.",
        success=True,
        duration_ms=duration_ms
    )
    
    messages.append(f"Research Gap Detection Agent: Identified {len(gaps_list)} distinct future opportunities.")
    
    return {
        **state,
        "sections": state_sections,
        "messages": messages
    }
