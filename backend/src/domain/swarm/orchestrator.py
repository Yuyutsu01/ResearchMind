import asyncio
from typing import Dict, Any
from src.adapters.db.postgres import execute_query
from src.domain.swarm.agents import (
    explanation_agent,
    math_agent,
    background_agent,
    visual_agent,
    figure_agent,
    table_agent,
    citation_agent,
    terminology_agent,
    question_agent
)

class SwarmOrchestrator:
    """
    Coordinates specialized swarm agents. Inspects selection type 
    and selectively routes to expert agents in parallel.
    """
    async def process_selection(self, session_id: int, selection_text: str, selection_type: str, obj_id: str = None) -> Dict[str, Any]:
        print(f"[Orchestrator] Selected item: '{selection_text}' (Type: {selection_type}, Obj ID: {obj_id})")
        
        # Determine selection type lower-cased
        s_type = selection_type.lower()
        
        # Tasks dictionary for parallel execution
        tasks = {}
        
        # 1. Routing Decision Matrix (Selective activation)
        if s_type == "equation":
            # Math focus
            tasks["math"] = asyncio.to_thread(math_agent.analyze_equation, session_id, obj_id or "eq", selection_text)
            tasks["background"] = asyncio.to_thread(background_agent.get_prerequisites, session_id, obj_id or "eq", selection_text)
            tasks["visual"] = asyncio.to_thread(visual_agent.generate_diagram, session_id, obj_id or "eq", selection_text)
            tasks["questions"] = asyncio.to_thread(question_agent.predict_questions, session_id, obj_id or "eq", selection_text)
            
        elif s_type == "figure":
            # Image interpretation focus
            tasks["figure"] = asyncio.to_thread(figure_agent.explain_figure, session_id, obj_id or "fig", selection_text)
            tasks["background"] = asyncio.to_thread(background_agent.get_prerequisites, session_id, obj_id or "fig", selection_text)
            tasks["visual"] = asyncio.to_thread(visual_agent.generate_diagram, session_id, obj_id or "fig", selection_text)
            
        elif s_type == "table":
            # Quantitative comparison focus
            tasks["table"] = asyncio.to_thread(table_agent.analyze_table, session_id, obj_id or "table", selection_text)
            tasks["background"] = asyncio.to_thread(background_agent.get_prerequisites, session_id, obj_id or "table", selection_text)
            tasks["questions"] = asyncio.to_thread(question_agent.predict_questions, session_id, obj_id or "table", selection_text)
            
        elif s_type == "citation":
            # Bibliography reference focus
            tasks["citation"] = asyncio.to_thread(citation_agent.explain_citation, session_id, obj_id or "citation", selection_text)
            tasks["terminology"] = asyncio.to_thread(terminology_agent.define_term, session_id, obj_id or "citation", selection_text)
            
        else:
            # Paragraph or custom selected text
            tasks["explanation"] = asyncio.to_thread(explanation_agent.explain, session_id, obj_id or "para", selection_text, "Beginner")
            tasks["background"] = asyncio.to_thread(background_agent.get_prerequisites, session_id, obj_id or "para", selection_text)
            tasks["visual"] = asyncio.to_thread(visual_agent.generate_diagram, session_id, obj_id or "para", selection_text)
            tasks["terminology"] = asyncio.to_thread(terminology_agent.define_term, session_id, obj_id or "para", selection_text)
            tasks["questions"] = asyncio.to_thread(question_agent.predict_questions, session_id, obj_id or "para", selection_text)

        # 2. Parallel agent execution
        keys = list(tasks.keys())
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        
        # 3. Merging swarm analysis results
        merged_res = {}
        for key, res in zip(keys, results):
            if isinstance(res, Exception):
                print(f"[Orchestrator Warning] Agent '{key}' failed: {res}")
                merged_res[key] = {"error": str(res)}
            else:
                merged_res[key] = res
                
        # Format timeline logging in Postgres
        try:
            import json
            execute_query(
                "INSERT INTO reading_timeline (session_id, action_type, details) VALUES (%s, 'TEXT_SELECTED', %s);",
                (
                    session_id,
                    json.dumps({
                        "text": selection_text,
                        "type": selection_type,
                        "summary": merged_res.get("explanation", {}).get("level_1") or f"Analyzed {selection_type}"
                    })
                )
            )
        except Exception as err:
            print(f"[Orchestrator DB Warning] Failed to log selection to timeline: {err}")
            
        return merged_res

swarm_orchestrator = SwarmOrchestrator()
