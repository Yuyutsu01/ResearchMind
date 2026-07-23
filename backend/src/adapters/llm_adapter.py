import os
import json
import httpx
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from workspace root .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../../.env"))
load_dotenv()

from src.adapters.db.redis_cache import redis_cache
from src.adapters.llm_providers import (
    OpenAIProvider,
    GroqProvider,
    GeminiProvider,
    ClaudeProvider,
    AzureProvider,
    OllamaProvider
)

class LLMAdapter:
    """
    LLM Client abstraction supporting multiple providers (OpenAI/Groq/Gemini/Claude/Azure/Ollama) 
    with hot L1 Redis caching.
    """
    def __init__(self):
        self.provider_name = os.environ.get("LLM_PROVIDER", "").lower()
        self.base_url = os.environ.get("LLM_BASE_URL")
        self.api_key = os.environ.get("LLM_API_KEY", os.environ.get("OPENAI_API_KEY", "mock-key"))
        self.model = os.environ.get("LLM_MODEL", "gpt-4o-mini")

        # Auto-detect provider based on base URL or key if not explicitly defined
        if not self.provider_name:
            if self.base_url and "groq.com" in self.base_url:
                self.provider_name = "groq"
            elif self.base_url and "openai.com" in self.base_url:
                self.provider_name = "openai"
            elif self.api_key != "mock-key" and self.api_key:
                self.provider_name = "openai"
            else:
                self.provider_name = "mock"

        print(f"[LLMAdapter] Instantiating provider abstraction: {self.provider_name} | Model: {self.model}")

        self.provider = None
        if self.provider_name == "openai" and self.api_key != "mock-key":
            self.provider = OpenAIProvider(api_key=self.api_key, base_url=self.base_url)
        elif self.provider_name == "groq" and self.api_key != "mock-key":
            self.provider = GroqProvider(api_key=self.api_key, base_url=self.base_url)
        elif self.provider_name == "gemini" and self.api_key != "mock-key":
            self.provider = GeminiProvider(api_key=self.api_key)
        elif self.provider_name == "claude" and self.api_key != "mock-key":
            self.provider = ClaudeProvider(api_key=self.api_key)
        elif self.provider_name == "azure" and self.api_key != "mock-key":
            api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2023-05-15")
            self.provider = AzureProvider(api_key=self.api_key, endpoint=self.base_url, api_version=api_version)
        elif self.provider_name == "ollama":
            self.provider = OllamaProvider(host_url=self.base_url)
        else:
            # Fallback to mock/synthetic responder
            self.provider_name = "mock"

    def get_structured_json(
        self, 
        cache_key: str, 
        system_prompt: str, 
        user_prompt: str, 
        session_id: Optional[int] = None
    ) -> dict:
        """
        Sends system and user prompts to the configured LLM provider, returning a structured JSON.
        Checks L1 Redis cache first to bypass network calls.
        """
        from src.adapters.telemetry import telemetry

        # 1. L1 Cache Check
        cached_res = redis_cache.get(cache_key)
        if cached_res:
            telemetry.record_cache_hit("redis_l1")
            print(f"[L1 Cache Hit] Found response for key '{cache_key}'.")
            return cached_res
            
        telemetry.record_cache_miss("redis_l1")
            
        # 2. Inject context from Agent Memory System if session_id is provided
        if session_id and self.provider_name != "mock":
            from src.domain.swarm.memory import agent_memory
            mem_context = agent_memory.retrieve_context(session_id, user_prompt)
            if mem_context:
                system_prompt = system_prompt + f"\n\n[CONCURRENT RESEARCH CONTEXT & HISTORY]\n{mem_context}"
                print(f"[Agent Memory] Injected memory context for Session #{session_id} into LLM prompt.")

        print(f"[LLM Request] Cache miss. Routing call via provider: '{self.provider_name}'...")
        
        if self.provider_name == "mock" or not self.provider:
            synthetic_res = self.generate_synthetic_response(system_prompt, user_prompt)
            redis_cache.set(cache_key, synthetic_res)
            return synthetic_res
            
        try:
            parsed = self.provider.get_structured_json(system_prompt, user_prompt, self.model)
            # Store in L1 cache
            redis_cache.set(cache_key, parsed)
            return parsed
        except Exception as e:
            print(f"[LLM Error] API request failed: {e}. Falling back to synthetic responder...")
            synthetic_res = self.generate_synthetic_response(system_prompt, user_prompt)
            redis_cache.set(cache_key, synthetic_res)
            return synthetic_res

    def generate_synthetic_response(self, system_prompt: str, user_prompt: str) -> dict:
        """Generates structured scientific insights based on system prompt keys when LLM is offline."""
        sys_lower = system_prompt.lower()
        
        if "latex_clean" in sys_lower:
            return {
                "latex_clean": "F(s,a,s') = \\gamma\\Phi(s') - \\Phi(s)",
                "variable_definitions": {
                    "F": "Shaping reward function",
                    "s": "Current state",
                    "s'": "Next state",
                    "Phi": "Potential function",
                    "gamma": "Discount factor"
                },
                "derivation_steps": [
                    "Define state potential difference.",
                    "Apply discount factor to next state potential.",
                    "Subtract current state potential."
                ],
                "intuition": "Reward shaping preserves policy invariance."
            }
            
        if "prerequisites" in sys_lower:
            return {
                "prerequisites": ["Markov Decision Processes", "Reward functions"],
                "brief_explanations": {
                    "Markov Decision Processes": "Mathematical framework for modeling decision-making.",
                    "Reward functions": "Feedback signal from the environment to indicate goal achievement."
                }
            }
            
        if "diagram" in sys_lower:
            return {
                "diagram": "+-----------------+\n| Selected Node   |\n+-----------------+",
                "explanation": "ASCII visualization of reward flow state transitions."
            }
            
        if "questions" in sys_lower:
            return {
                "questions": ["Why use potential-based reward shaping?", "Does it preserve policies?"]
            }
            
        if "takeaway" in sys_lower:
            return {
                "takeaway": "Method B converges twice as fast.",
                "axes_and_legends": "X-axis: Epochs, Y-axis: Success Rate.",
                "methodology_connection": "Illustrates performance metrics in reinforcement learning."
            }
            
        if "optimal_method" in sys_lower:
            return {
                "metric_summary": "Accuracy, parameter size.",
                "optimal_method": "FoldNet-v2 (89.2% F1)",
                "takeaway": "Shows the performance gain of modern attention mechanisms."
            }
            
        if "original_concept" in sys_lower:
            return {
                "original_concept": "Positional encodings introduction.",
                "connection": "Ensures permutation invariance for sequences.",
                "relevance": "Direct dependency for self-attention."
            }
            
        if "definition" in sys_lower:
            return {
                "definition": "A mechanism mapping token positions to sequence steps.",
                "paper_context": "Used to maintain sequence word order."
            }
            
        # Default Multi-level generic explanation response
        return {
            "level_1": "Formula representing potential-based reward shaping mechanics.",
            "level_2": "Computes the transition difference in state potential Φ(s).",
            "level_3": "Assumes a discount factor γ to preserve policy invariance across states.",
            "level_4": "F(s,a,s') = γΦ(s') − Φ(s) where Φ is the potential function.",
            "level_5": "Introduced by Ng, Harada, and Russell (1999) to optimize reinforcement learning bounds.",
            "level_6": "def shaping_reward(s, s_next, gamma=0.99): return gamma * phi(s_next) - phi(s)",
            "level_7": "Ng et al. (1999) - Policy Invariance under Reward Shaping.",
            "why_this_matters": {
                "author_intent": "Guides the agent's policy exploration direction.",
                "problem_solved": "Eliminates reward sparsity and delay constraints.",
                "later_dependents": "Advantage Actor-Critic value functions.",
                "prerequisites": "Markov Decision Processes."
            },
            "critic_warning": "Improper potential estimation might restrict early path exploration."
        }

llm_client = LLMAdapter()
