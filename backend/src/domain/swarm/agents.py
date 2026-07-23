import json
from typing import Dict, Any, List
from src.adapters.llm_adapter import llm_client

class BaseAgent:
    def __init__(self, name: str):
        self.name = name

    def generate_cache_key(self, session_id: int, target_id: str, prompt_hash: str) -> str:
        return f"cache:agent:{self.name}:{session_id}:{target_id}:{prompt_hash}"

class ExplanationAgent(BaseAgent):
    """Converts scientific content into multi-level explanations (Beginner, Undergrad, Graduate, Researcher)."""
    def __init__(self):
        super().__init__("ExplanationAgent")

    def explain(self, session_id: int, target_id: str, text: str, user_level: str = "Beginner") -> dict:
        cache_key = self.generate_cache_key(session_id, target_id, f"exp_{user_level}")
        system_prompt = f"Explain the text assuming the user is at level: {user_level}. Keep it clear and concise."
        user_prompt = f"Highlight: \"{text}\""
        return llm_client.get_structured_json(cache_key, system_prompt, user_prompt, session_id=session_id)

class MathematicsAgent(BaseAgent):
    """Parses equations and step-by-step derivations."""
    def __init__(self):
        super().__init__("MathematicsAgent")

    def analyze_equation(self, session_id: int, target_id: str, equation_text: str) -> dict:
        cache_key = self.generate_cache_key(session_id, target_id, "math_equation")
        system_prompt = """
        Break down the mathematical formula.
        Structure JSON as:
        {
          "latex_clean": "formatted latex",
          "variable_definitions": {"x": "variable meaning"},
          "derivation_steps": ["step 1 description"],
          "intuition": "plain english intuition"
        }
        """
        user_prompt = f"Formula: {equation_text}"
        return llm_client.get_structured_json(cache_key, system_prompt, user_prompt, session_id=session_id)

class BackgroundKnowledgeAgent(BaseAgent):
    """Identifies prerequisite concepts required to understand the target highlight."""
    def __init__(self):
        super().__init__("BackgroundKnowledgeAgent")

    def get_prerequisites(self, session_id: int, target_id: str, text: str) -> dict:
        cache_key = self.generate_cache_key(session_id, target_id, "background_prereqs")
        system_prompt = """
        List prerequisite concepts needed to understand the highlight.
        Structure JSON as:
        {
          "prerequisites": ["concept 1", "concept 2"],
          "brief_explanations": {"concept 1": "short summary"}
        }
        """
        user_prompt = f"Selected text: \"{text}\""
        return llm_client.get_structured_json(cache_key, system_prompt, user_prompt, session_id=session_id)

class VisualTeachingAgent(BaseAgent):
    """Generates ASCII structural diagrams or flowchart animations."""
    def __init__(self):
        super().__init__("VisualTeachingAgent")

    def generate_diagram(self, session_id: int, target_id: str, text: str) -> dict:
        cache_key = self.generate_cache_key(session_id, target_id, "visual_teaching")
        system_prompt = """
        Generate an ASCII flowchart or text structural diagram illustrating the concept.
        Structure JSON as:
        {
          "diagram": "ASCII block diagram representation",
          "explanation": "how to read this diagram"
        }
        """
        user_prompt = f"Selected concept: \"{text}\""
        return llm_client.get_structured_json(cache_key, system_prompt, user_prompt, session_id=session_id)

class FigureInterpretationAgent(BaseAgent):
    """Explains axes, trends, and takeaways from figures."""
    def __init__(self):
        super().__init__("FigureInterpretationAgent")

    def explain_figure(self, session_id: int, target_id: str, caption: str) -> dict:
        cache_key = self.generate_cache_key(session_id, target_id, "figure_interpretation")
        system_prompt = """
        Analyze the figure based on its description/caption.
        Structure JSON as:
        {
          "takeaway": "Key trend or takeaway from this figure",
          "axes_and_legends": "X-axis, Y-axis representation and colors",
          "methodology_connection": "Why this figure is critical to the paper methodology"
        }
        """
        user_prompt = f"Caption details: {caption}"
        return llm_client.get_structured_json(cache_key, system_prompt, user_prompt, session_id=session_id)

class TableAnalysisAgent(BaseAgent):
    """Analyzes benchmark metrics in tables."""
    def __init__(self):
        super().__init__("TableAnalysisAgent")

    def analyze_table(self, session_id: int, target_id: str, caption: str) -> dict:
        cache_key = self.generate_cache_key(session_id, target_id, "table_analysis")
        system_prompt = """
        Interpret metrics and rows/columns from tables.
        Structure JSON as:
        {
          "metric_summary": "What is measured (e.g. Accuracy, parameter count)",
          "optimal_method": "Which method performs best and by what margin",
          "takeaway": "Brief analysis of results trend"
        }
        """
        user_prompt = f"Table caption: {caption}"
        return llm_client.get_structured_json(cache_key, system_prompt, user_prompt, session_id=session_id)

class CitationAgent(BaseAgent):
    """Resolves citation references and maps relationship links."""
    def __init__(self):
        super().__init__("CitationAgent")

    def explain_citation(self, session_id: int, target_id: str, citation_text: str) -> dict:
        cache_key = self.generate_cache_key(session_id, target_id, "citation_info")
        system_prompt = """
        Analyze a scientific citation.
        Structure JSON as:
        {
          "original_concept": "What prior concept this cited paper introduced",
          "connection": "Why it is referenced in this methodology",
          "relevance": "How it connects to the current work"
        }
        """
        user_prompt = f"Citation callout: {citation_text}"
        return llm_client.get_structured_json(cache_key, system_prompt, user_prompt, session_id=session_id)

class TerminologyAgent(BaseAgent):
    """Defines technical terms within paper contexts."""
    def __init__(self):
        super().__init__("TerminologyAgent")

    def define_term(self, session_id: int, target_id: str, term: str) -> dict:
        cache_key = self.generate_cache_key(session_id, target_id, "terminology_def")
        system_prompt = """
        Define the technical term in the context of scientific literature.
        Structure JSON as:
        {
          "definition": "Clear concise definition",
          "paper_context": "How this term is applied in the active paper"
        }
        """
        user_prompt = f"Term: {term}"
        return llm_client.get_structured_json(cache_key, system_prompt, user_prompt, session_id=session_id)

class QuestionPredictionAgent(BaseAgent):
    """Predicts user follow-up questions."""
    def __init__(self):
        super().__init__("QuestionPredictionAgent")

    def predict_questions(self, session_id: int, target_id: str, text: str) -> dict:
        cache_key = self.generate_cache_key(session_id, target_id, "question_prediction")
        system_prompt = """
        Suggest 2-3 logical follow-up questions a researcher would ask next.
        Structure JSON as:
        {
          "questions": ["Question 1?", "Question 2?"]
        }
        """
        user_prompt = f"Topic: {text}"
        return llm_client.get_structured_json(cache_key, system_prompt, user_prompt, session_id=session_id)

# Instantiate singletons for orchestrator
explanation_agent = ExplanationAgent()
math_agent = MathematicsAgent()
background_agent = BackgroundKnowledgeAgent()
visual_agent = VisualTeachingAgent()
figure_agent = FigureInterpretationAgent()
table_agent = TableAnalysisAgent()
citation_agent = CitationAgent()
terminology_agent = TerminologyAgent()
question_agent = QuestionPredictionAgent()
