import json
import httpx
import time
import random
from typing import Dict, Any, Optional

def retry_with_backoff(max_retries: int = 3, initial_delay: float = 1.0, backoff_factor: float = 2.0):
    """
    Decorator that retries a function using exponential backoff with random jitter.
    Catches common network and API errors.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            delay = initial_delay
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except httpx.HTTPStatusError as e:
                    # Retry on Rate Limit (429) or Server Errors (5xx)
                    if e.response.status_code == 429 or e.response.status_code >= 500:
                        if attempt == max_retries:
                            raise e
                        sleep_time = delay + random.uniform(0, 0.5 * delay)
                        print(f"[LLM Retry] HTTP status {e.response.status_code} on attempt {attempt}. Retrying in {sleep_time:.2f}s...")
                        time.sleep(sleep_time)
                        delay *= backoff_factor
                    else:
                        raise e
                except (httpx.RequestError, httpx.TimeoutException) as e:
                    if attempt == max_retries:
                        raise e
                    sleep_time = delay + random.uniform(0, 0.5 * delay)
                    print(f"[LLM Retry] Network/Timeout error on attempt {attempt}: {e}. Retrying in {sleep_time:.2f}s...")
                    time.sleep(sleep_time)
                    delay *= backoff_factor
        return wrapper
    return decorator

def track_tokens_and_cost(provider_name: str, model: str, prompt_tokens: int, completion_tokens: int, duration: float = 0.0):
    """
    Logs token metrics for observability and records Prometheus counters.
    """
    print(f"[Telemetry] Provider: {provider_name} | Model: {model} | Prompt Tokens: {prompt_tokens} | Completion Tokens: {completion_tokens}")
    from src.adapters.telemetry import telemetry
    telemetry.record_llm_request(provider_name, model, duration, prompt_tokens, completion_tokens)

class LLMProvider:
    """Base class exposing the unified provider interface."""
    def get_structured_json(self, system_prompt: str, user_prompt: str, model: str, timeout: float = 30.0) -> dict:
        raise NotImplementedError("Providers must implement get_structured_json")

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        self.api_key = api_key
        raw_url = base_url or "https://api.openai.com/v1"
        self.base_url = raw_url.rstrip("/").removesuffix("/chat/completions").removesuffix("/chat")

    @retry_with_backoff()
    def get_structured_json(self, system_prompt: str, user_prompt: str, model: str, timeout: float = 30.0) -> dict:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }
        with httpx.Client() as client:
            res = client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=timeout
            )
            res.raise_for_status()
            data = res.json()
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            track_tokens_and_cost("OpenAI", model, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0))
            return json.loads(content)

class GroqProvider(LLMProvider):
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        self.api_key = api_key
        raw_url = base_url or "https://api.groq.com/openai/v1"
        self.base_url = raw_url.rstrip("/").removesuffix("/chat/completions").removesuffix("/chat")

    @retry_with_backoff()
    def get_structured_json(self, system_prompt: str, user_prompt: str, model: str, timeout: float = 30.0) -> dict:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }
        with httpx.Client() as client:
            res = client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=timeout
            )
            res.raise_for_status()
            data = res.json()
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            track_tokens_and_cost("Groq", model, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0))
            return json.loads(content)

class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key

    @retry_with_backoff()
    def get_structured_json(self, system_prompt: str, user_prompt: str, model: str, timeout: float = 30.0) -> dict:
        # Standard Google Gemini content generation endpoint
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {
                    "parts": [{"text": f"{system_prompt}\n\nUser Input:\n{user_prompt}"}]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json"
            }
        }
        with httpx.Client() as client:
            res = client.post(url, headers=headers, json=payload, timeout=timeout)
            res.raise_for_status()
            data = res.json()
            content = data["candidates"][0]["content"]["parts"][0]["text"]
            # Gemini does not return exact tokens in standard REST, mock usage
            track_tokens_and_cost("Gemini", model, 0, 0)
            return json.loads(content)

class ClaudeProvider(LLMProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key

    @retry_with_backoff()
    def get_structured_json(self, system_prompt: str, user_prompt: str, model: str, timeout: float = 30.0) -> dict:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        # Enforce json response output context
        payload = {
            "model": model,
            "max_tokens": 4096,
            "system": system_prompt + "\nIMPORTANT: Return ONLY raw valid JSON. Do not include markdown code block syntax.",
            "messages": [
                {"role": "user", "content": user_prompt}
            ]
        }
        with httpx.Client() as client:
            res = client.post(url, headers=headers, json=payload, timeout=timeout)
            res.raise_for_status()
            data = res.json()
            content = data["content"][0]["text"].strip()
            
            # Clean markdown code blocks if returned by the model
            if content.startswith("```"):
                content = content.split("\n", 1)[-1]
                if content.endswith("```"):
                    content = content.rsplit("```", 1)[0]
                content = content.strip()
                
            usage = data.get("usage", {})
            track_tokens_and_cost("Claude", model, usage.get("input_tokens", 0), usage.get("output_tokens", 0))
            return json.loads(content)

class AzureProvider(LLMProvider):
    def __init__(self, api_key: str, endpoint: str, api_version: str):
        self.api_key = api_key
        self.endpoint = endpoint.rstrip("/")
        self.api_version = api_version

    @retry_with_backoff()
    def get_structured_json(self, system_prompt: str, user_prompt: str, model: str, timeout: float = 30.0) -> dict:
        # deployment ID matches the model variable passed
        url = f"{self.endpoint}/openai/deployments/{model}/chat/completions?api-version={self.api_version}"
        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }
        with httpx.Client() as client:
            res = client.post(url, headers=headers, json=payload, timeout=timeout)
            res.raise_for_status()
            data = res.json()
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            track_tokens_and_cost("AzureOpenAI", model, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0))
            return json.loads(content)

class OllamaProvider(LLMProvider):
    def __init__(self, host_url: Optional[str] = None):
        self.host_url = host_url or "http://localhost:11434"

    @retry_with_backoff()
    def get_structured_json(self, system_prompt: str, user_prompt: str, model: str, timeout: float = 30.0) -> dict:
        url = f"{self.host_url}/api/chat"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "format": "json",
            "stream": False
        }
        with httpx.Client() as client:
            res = client.post(url, json=payload, timeout=timeout)
            res.raise_for_status()
            data = res.json()
            content = data["message"]["content"]
            track_tokens_and_cost("Ollama", model, 0, 0)
            return json.loads(content)
