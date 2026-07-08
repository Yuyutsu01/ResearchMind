# ResearchMind Swarm v1 - API Specification

This document details the REST endpoints and WebSocket protocols used to interact with the backend swarm.

---

## 1. REST Endpoints

### 1.1 Upload Research Paper
* **URL**: `/api/v1/upload`
* **Method**: `POST`
* **Content-Type**: `multipart/form-data`
* **Request**:
  - `file`: PDF file.
* **Response (200 OK)**:
  ```json
  {
    "file_id": "8f828a2a-b73a-4be0-8022-d023a9d20c32",
    "filename": "attention_is_all_you_need.pdf",
    "status": "uploaded",
    "success": true
  }
  ```

### 1.2 Start Research Session
* **URL**: `/api/v1/sessions`
* **Method**: `POST`
* **Request Body**:
  ```json
  {
    "user_id": 1,
    "prompt": "Analyze the impact of FlashAttention on scaling LLM context windows.",
    "file_id": "8f828a2a-b73a-4be0-8022-d023a9d20c32" // optional
  }
  ```
* **Response (201 Created)**:
  ```json
  {
    "session_id": 42,
    "status": "IDLE",
    "created_at": "2026-07-09T00:00:00Z"
  }
  ```

### 1.3 Fetch Knowledge Graph
* **URL**: `/api/v1/sessions/{session_id}/graph`
* **Method**: `GET`
* **Response (200 OK)**:
  Returns D3/Cytoscape.js compatible node-link structure from the in-memory NetworkX state.
  ```json
  {
    "nodes": [
      { "id": "FlashAttention", "label": "Flash Attention", "type": "method" },
      { "id": "IO-Complexity", "label": "IO Complexity", "type": "concept" }
    ],
    "links": [
      { "source": "FlashAttention", "target": "IO-Complexity", "relationship": "optimizes" }
    ]
  }
  ```

### 1.4 Export Research Report
* **URL**: `/api/v1/sessions/{session_id}/export`
* **Method**: `POST`
* **Request Body**:
  ```json
  {
    "format": "latex" // markdown, pdf, docx, pptx, latex
  }
  ```
* **Response (200 OK)**:
  ```json
  {
    "success": true,
    "download_url": "/reports/flashattention_report.tex"
  }
  ```

---

## 2. WebSocket Stream (`/ws/v1/research/{session_id}`)

Real-time streaming connection for telemetry, execution timelines, and user-in-the-loop prompts.

### 2.1 Server-to-Client Messages

#### Type: `state_change`
Sent when the Research State Machine transitions.
```json
{
  "type": "state_change",
  "state": "SEARCHING"
}
```

#### Type: `agent_step`
Reports which Agent is active and what abstract action it is processing.
```json
{
  "type": "agent_step",
  "agent": "Explorer",
  "action": "SEARCH_PAPERS",
  "description": "Searching Semantic Scholar for 'FlashAttention latency benchmarks'..."
}
```

#### Type: `telemetry_update`
Live update of the 5 key telemetry metrics and current session budget.
```json
{
  "type": "telemetry_update",
  "metrics": {
    "task_completion_rate": 0.0,
    "autonomy_score": 1.0,
    "answer_grounding_score": 0.0,
    "hallucination_rate": 0.0,
    "cost_usd": 0.045
  },
  "budget": {
    "tokens_remaining": 85000,
    "dollars_remaining": 9.955
  }
}
```

#### Type: `ui_prompt`
Sent by the UI Agent when a user response is required (e.g., resolving a contradiction or choosing a path).
```json
{
  "type": "ui_prompt",
  "prompt_id": "resolve_contradiction_4",
  "message": "Analyst found conflicting performance claims between Paper A (15x speedup) and Paper B (2.4x speedup). Which benchmark focus should the Synthesizer prioritize?",
  "options": [
    "Prioritize A100 GPU benchmarks (Paper A)",
    "Prioritize CPU implementation (Paper B)",
    "Document both and list conditions"
  ]
}
```

### 2.2 Client-to-Server Messages

#### Type: `user_message`
Sends user selection or text input to resolve prompts.
```json
{
  "type": "user_message",
  "prompt_id": "resolve_contradiction_4",
  "selected_option": "Document both and list conditions"
}
```
