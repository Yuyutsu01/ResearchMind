import json
from typing import Dict, Any, List
from src.domain.agents.base import BaseAgent
from src.domain.blackboard.blackboard import ResearchBlackboard
from src.adapters.llm_adapter import llm_client
from src.domain.agents.registry import agent_registry

class UiAgent(BaseAgent):
    def __init__(self):
        super().__init__("UIAgent")

    def execute(self, blackboard: ResearchBlackboard, payload: dict):
        action = payload.get("action", "explain_findings")
        
        if action == "generate_quiz":
            self._generate_learning_quiz(blackboard)
        else:
            self._explain_findings(blackboard)

    def _explain_findings(self, blackboard: ResearchBlackboard):
        print("[UI Agent] Translating working memory into output summaries...")
        synthesis = blackboard.working_memory.get("report_synthesis", "No research completed yet.")
        blackboard.working_memory["final_report"] = f"# Research Brief\n\n{synthesis}"
        
        blackboard.add_event("RESEARCH_COMPLETE", {
            "msg": "Research completed. Ready for export."
        })

    def _generate_learning_quiz(self, blackboard: ResearchBlackboard):
        print("[UI Agent] Generating scientific quiz for researcher learning gain assessment...")
        
        # Collate concepts
        nodes_data = []
        for node in blackboard.knowledge_graph.nodes:
            attrs = blackboard.knowledge_graph.nodes[node]
            if attrs.get("type") == "concept":
                nodes_data.append(f"Concept: {node} - Definition: {attrs.get('definition', '')}")
                
        concepts_text = "\n".join(nodes_data[:4])
        if not concepts_text:
            concepts_text = "No concepts extracted."
            
        system_prompt = """You are an academic educator. Based on the extracted research concepts, generate 3 multiple-choice questions to test the researcher's understanding.
For each question, provide 4 options and denote the single correct answer index (0-3).
Output ONLY a JSON object. Do not include markdown wraps or explanations.

Target Structure:
{
  "quiz": [
    {
      "question": "What is the primary optimization goal of Self-Attention?",
      "options": [
        "Reducing CPU temperature",
        "Relating different sequence positions to compute representations",
        "Disk speed optimization",
        "Caching memory vectors"
      ],
      "correct_index": 1
    }
  ]
}
"""
        user_prompt = f"Concepts:\n{concepts_text}"
        
        try:
            quiz_data = llm_client.get_structured_json(blackboard, system_prompt, user_prompt)
            blackboard.working_memory["learning_quiz"] = quiz_data.get("quiz", [])
            print(f"[UI Agent] Generated quiz with {len(quiz_data.get('quiz', []))} questions.")
            
            blackboard.add_event("QUIZ_GENERATED", {
                "msg": "Researcher quiz generated successfully."
            })
        except Exception as e:
            print(f"[UI Agent Error] Quiz generation failed: {e}")
            blackboard.working_memory["learning_quiz"] = []

# Register to Registry
ui_agent = UiAgent()
agent_registry.register_agent(
    "UIAgent",
    ui_agent,
    tasks=["explain_findings", "generate_quiz"],
    event_subs=["RESEARCH_COMPLETE"]
)
