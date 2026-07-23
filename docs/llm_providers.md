# LLM Provider Abstraction Config Guide

ResearchMind integrates a unified provider abstraction allowing seamless switching between commercial and local LLM backends without altering application logic.

---

## 1. Environment Configurations

To switch providers, update the following parameters in your `.env` configuration file:

```env
# 1. Select the Provider
# Supported: openai, groq, gemini, claude, azure, ollama, mock
LLM_PROVIDER=groq

# 2. Base Endpoint URL (optional for OpenAI, Groq, Claude, Gemini)
# Required for Azure and Ollama
LLM_BASE_URL=https://api.groq.com/openai/v1

# 3. Model API Authentication Key
LLM_API_KEY=gsk_...

# 4. Model Target
LLM_MODEL=llama-3.3-70b-versatile
```

### Auto-Detection Mode
If `LLM_PROVIDER` is left blank, the adapter automatically scans the environment variables:
* If `LLM_BASE_URL` contains `"groq.com"`, it defaults to **Groq**.
* If `LLM_BASE_URL` contains `"openai.com"` or `OPENAI_API_KEY` is set, it defaults to **OpenAI**.
* If no key is set, it defaults to the **Mock** offline synthetic provider.

---

## 2. Provider Details & Endpoint Mapping

| Provider | Key Variable | Endpoint URL | JSON Mode Mode |
| :--- | :--- | :--- | :--- |
| **OpenAI** | `LLM_API_KEY` or `OPENAI_API_KEY` | `https://api.openai.com/v1/chat/completions` | Native JSON Object |
| **Groq** | `LLM_API_KEY` or `GROQ_API_KEY` | `https://api.groq.com/openai/v1/chat/completions` | Native JSON Object |
| **Gemini** | `LLM_API_KEY` | `https://generativelanguage.googleapis.com/v1beta/models/...:generateContent` | Native schema-less JSON |
| **Claude** | `LLM_API_KEY` | `https://api.anthropic.com/v1/messages` | Cleaned text-blocks parsing |
| **Azure** | `LLM_API_KEY` | `https://{resource}.openai.azure.com/openai/deployments/...` | Native JSON Object |
| **Ollama** | N/A | `http://localhost:11434/api/chat` | Native JSON format parameter |
| **Mock** | N/A | Local logic | Hardcoded synthetic schemas |

---

## 3. Resilience Features

### Exponential Backoff Retry Policy
All network calls are wrapped with a resilient decorator:
* **Max Retries**: 3 attempts.
* **Initial Delay**: 1.0 seconds.
* **Backoff Factor**: 2.0x increase per attempt.
* **Jitter**: Random noise added to prevent synchronized server hammering.
* **Trigger Conditions**: Triggers on HTTP `429` (Rate Limiting), HTTP `5xx` (Server Errors), request timeouts, or connection failures.

### Telemetry Logs
Each completion call outputs log tokens to standard output for Prometheus/observability parsing:
```text
[Telemetry] Provider: Groq | Model: llama-3.3-70b-versatile | Prompt Tokens: 1240 | Completion Tokens: 345
```
