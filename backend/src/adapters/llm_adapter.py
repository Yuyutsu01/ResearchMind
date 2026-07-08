import re
import json
from openai import OpenAI
from src.config.app_config import Config
from src.domain.scheduler.scheduler import BudgetManager
from src.domain.blackboard.blackboard import ResearchBlackboard

class LLMAdapter:
    def __init__(self):
        print(f"[LLM Adapter] Initializing OpenAI client connected to {Config.LLM_BASE_URL} using model '{Config.LLM_MODEL}'")
        self.client = OpenAI(
            base_url=Config.LLM_BASE_URL,
            api_key=Config.LLM_API_KEY
        )

    def get_completion(self, blackboard: ResearchBlackboard, system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
        """Calls the configured LLM and registers token consumption with BudgetManager."""
        try:
            kwargs = {
                "model": Config.Config.LLM_MODEL if hasattr(Config, "Config") else Config.LLM_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.1
            }
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
                
            response = self.client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content
            
            # Record budget usage
            prompt_tokens = response.usage.prompt_tokens if response.usage else len(system_prompt + user_prompt) // 4
            completion_tokens = response.usage.completion_tokens if response.usage else len(content) // 4
            BudgetManager.record_llm_call(blackboard, prompt_tokens, completion_tokens)
            
            return content
        except Exception as e:
            print(f"[LLM Adapter Error] Chat completion failed: {e}")
            raise e

    def get_structured_json(self, blackboard: ResearchBlackboard, system_prompt: str, user_prompt: str) -> dict:
        """Retrieves and parses structured JSON from LLM outputs robustly."""
        content = self.get_completion(blackboard, system_prompt, user_prompt, json_mode=True)
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Fallback regex extraction
            match = re.search(r'(\{.*\}|\[.*\])', content, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except Exception:
                    pass
            raise ValueError(f"Could not parse valid JSON from LLM content: {content}")

# Singleton Instance
llm_client = LLMAdapter()
