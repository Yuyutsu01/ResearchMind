from typing import Dict, Any
from src.adapters.llm_adapter import llm_client
from src.runtime.harness.harness import ai_harness

class BaseAgent:
    def __init__(self, name: str):
        self.name = name

    def generate_cache_key(self, session_id: int, target_id: str, prompt_hash: str) -> str:
        return f"cache:agent:{self.name}:{session_id}:{target_id}:{prompt_hash}"

class ExplanationAgent(BaseAgent):
    """Converts scientific content into detailed, expert mentor-level research explanations."""
    def __init__(self):
        super().__init__("ExplanationAgent")

    def explain(self, session_id: int, target_id: str, text: str) -> dict:
        cache_key = self.generate_cache_key(session_id, target_id, "exp_detailed")
        system_prompt = """
        You are an expert scientific researcher teaching a peer.
        Provide a detailed, substantive, technically accurate, and structured explanation of the selected text.
        Do NOT write short 1-2 sentence summaries. Write multiple thorough paragraphs and explanatory bullet points.
        
        Structure JSON as:
        {
          "what_authors_say": "Substantial paragraph directly explaining the passage.",
          "what_it_means": "Substantial paragraph translating technical ideas into clear concepts.",
          "how_it_works": "Step-by-step technical explanation of the underlying mechanism.",
          "how_it_connects": "How this passage fits into the broader methodology and findings of the paper.",
          "takeaways": [
            "Detailed explanatory bullet point 1 detailing specific mechanisms and results.",
            "Detailed explanatory bullet point 2 detailing architectural specialization and trade-offs.",
            "Detailed explanatory bullet point 3 detailing evaluation across benchmarks.",
            "Detailed explanatory bullet point 4 detailing intermediate information exchange.",
            "Detailed explanatory bullet point 5 detailing limitations or domain assumptions."
          ],
          "why_it_matters": "2-3 substantial paragraphs explaining why this idea is important, what problem it solves, and what limitation of previous approaches it addresses.",
          "intuition": "Detailed real-world analogy explaining the concept, why it works, and where the analogy breaks down."
        }
        """
        user_prompt = f"Selected paper text:\n\"\"{text}\"\""
        return ai_harness.execute(cache_key, system_prompt, user_prompt, session_id=session_id)

class MathematicsAgent(BaseAgent):
    """Parses equations and step-by-step mathematical derivations."""
    def __init__(self):
        super().__init__("MathematicsAgent")

    def analyze_equation(self, session_id: int, target_id: str, equation_text: str) -> dict:
        cache_key = self.generate_cache_key(session_id, target_id, "math_equation")
        system_prompt = """
        Provide a comprehensive mathematical analysis of the equation.
        Structure JSON as:
        {
          "latex_clean": "Formatted clean LaTeX formula",
          "variable_definitions": {"x": "Detailed definition of variable x, its physical/algorithmic meaning, and units if applicable"},
          "term_roles": {"term_1": "Role and contribution of this term in the equation"},
          "derivation_steps": [
            "Step 1: Initial mathematical formulation and underlying assumptions",
            "Step 2: Algebraic transformation or optimization objective step",
            "Step 3: Final objective formulation"
          ],
          "intuition": "Deep conceptual explanation of what this equation measures or optimizes",
          "numerical_example": "Small concrete example demonstrating how the calculation behaves",
          "algorithm_connection": "Where and when this formula is executed in the paper's algorithm flow"
        }
        """
        user_prompt = f"Formula text: {equation_text}"
        return ai_harness.execute(cache_key, system_prompt, user_prompt, session_id=session_id)

class BackgroundKnowledgeAgent(BaseAgent):
    """Identifies prerequisite concepts required to understand the target highlight."""
    def __init__(self):
        super().__init__("BackgroundKnowledgeAgent")

    def get_prerequisites(self, session_id: int, target_id: str, text: str) -> dict:
        cache_key = self.generate_cache_key(session_id, target_id, "background_prereqs")
        system_prompt = """
        Identify prerequisite background concepts required to understand the highlight.
        Structure JSON as:
        {
          "concepts": [
            {
              "name": "Concept Name",
              "definition": "Detailed explanation of what this prerequisite concept is",
              "why_it_matters_here": "How this concept directly connects to the selected passage",
              "connection_to_paper": "Role of this concept in the paper's overarching paradigm"
            }
          ]
        }
        """
        user_prompt = f"Selected passage: \"\"{text}\"\""
        return ai_harness.execute(cache_key, system_prompt, user_prompt, session_id=session_id)

class VisualTeachingAgent(BaseAgent):
    """Generates ASCII structural diagrams or flowchart animations."""
    def __init__(self):
        super().__init__("VisualTeachingAgent")

    def generate_diagram(self, session_id: int, target_id: str, text: str) -> dict:
        cache_key = self.generate_cache_key(session_id, target_id, "visual_teaching")
        system_prompt = """
        Generate a clear ASCII structural diagram and step-by-step data flow mechanics.
        Structure JSON as:
        {
          "diagram": "ASCII block flow representation",
          "explanation": "Detailed step-by-step reading guide explaining data flow between components",
          "technical_steps": [
            "1. Input data ingestion and preprocessing",
            "2. Component routing and transformation",
            "3. Result aggregation and output emission"
          ]
        }
        """
        user_prompt = f"Selected concept: \"\"{text}\"\""
        return ai_harness.execute(cache_key, system_prompt, user_prompt, session_id=session_id)

class FigureInterpretationAgent(BaseAgent):
    """Explains axes, trends, components, and takeaways from figures."""
    def __init__(self):
        super().__init__("FigureInterpretationAgent")

    def explain_figure(self, session_id: int, target_id: str, caption: str) -> dict:
        cache_key = self.generate_cache_key(session_id, target_id, "figure_interpretation")
        system_prompt = """
        Provide an in-depth interpretation of the figure based on its caption and context.
        Structure JSON as:
        {
          "purpose": "Overall purpose of what the figure illustrates",
          "components": "Visual components, markers, colors, or structural blocks",
          "axes_and_legend": "Detailed breakdown of X-axis, Y-axis, markers, and legend categories",
          "step_by_step_reading": "How a researcher should read this chart/figure step-by-step",
          "main_observation": "Primary empirical trend or quantitative finding shown",
          "author_interpretation": "Conclusion drawn directly by the authors",
          "deeper_insight": "System inference on methodological trade-offs or implications"
        }
        """
        user_prompt = f"Figure caption details: {caption}"
        return ai_harness.execute(cache_key, system_prompt, user_prompt, session_id=session_id)

class TableAnalysisAgent(BaseAgent):
    """Analyzes benchmark metrics, rows, and columns in tables."""
    def __init__(self):
        super().__init__("TableAnalysisAgent")

    def analyze_table(self, session_id: int, target_id: str, caption: str) -> dict:
        cache_key = self.generate_cache_key(session_id, target_id, "table_analysis")
        system_prompt = """
        Provide a detailed comparative breakdown of the table data.
        Structure JSON as:
        {
          "table_purpose": "What baseline approaches or benchmarks are being compared",
          "columns_breakdown": "Explanation of evaluation metrics and column indicators",
          "rows_breakdown": "Explanation of baseline models vs proposed method rows",
          "best_results": "Which method achieves state-of-the-art results and by what numerical margin",
          "key_patterns": "Significant patterns, scaling trends, or ablation observations",
          "interpretation": "Substantive conclusion about what these results prove regarding the paper's hypotheses"
        }
        """
        user_prompt = f"Table caption details: {caption}"
        return ai_harness.execute(cache_key, system_prompt, user_prompt, session_id=session_id)

class CitationAgent(BaseAgent):
    """Resolves citation references and maps relationship links."""
    def __init__(self):
        super().__init__("CitationAgent")

    def explain_citation(self, session_id: int, target_id: str, citation_text: str) -> dict:
        cache_key = self.generate_cache_key(session_id, target_id, "citation_info")
        system_prompt = """
        Analyze the cited work and its connection to the current paper.
        Structure JSON as:
        {
          "cited_work": "Name and context of the work being cited",
          "original_concept": "Foundational idea or baseline method introduced in the cited work",
          "citation_type": "Foundational, Methodological, Comparative, or Contextual",
          "connection": "Why the authors cite this paper in this specific passage",
          "relevance": "How this cited concept supports or contrasts with the current paper's approach"
        }
        """
        user_prompt = f"Citation reference: {citation_text}"
        return ai_harness.execute(cache_key, system_prompt, user_prompt, session_id=session_id)

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
          "definition": "Clear, comprehensive definition of the term",
          "why_it_matters": "Why this concept is critical in scientific research",
          "paper_context": "Specific role and usage of this term within the active paper"
        }
        """
        user_prompt = f"Term: {term}"
        return ai_harness.execute(cache_key, system_prompt, user_prompt, session_id=session_id)

class QuestionPredictionAgent(BaseAgent):
    """Predicts user follow-up questions."""
    def __init__(self):
        super().__init__("QuestionPredictionAgent")

    def predict_questions(self, session_id: int, target_id: str, text: str) -> dict:
        cache_key = self.generate_cache_key(session_id, target_id, "question_prediction")
        system_prompt = """
        Suggest 3 thoughtful follow-up research questions a researcher would ask next.
        Structure JSON as:
        {
          "questions": ["Follow-up Question 1?", "Follow-up Question 2?", "Follow-up Question 3?"]
        }
        """
        user_prompt = f"Selected text: \"\"{text}\"\""
        return ai_harness.execute(cache_key, system_prompt, user_prompt, session_id=session_id)

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
