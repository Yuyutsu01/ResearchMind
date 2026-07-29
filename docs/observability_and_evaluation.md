# ResearchMind Observability & Evaluation Engine Documentation

## 1. Executive Summary

The **Observability Engine** (`backend/src/runtime/observability/telemetry.py`) and **Evaluation Engine** (`backend/src/runtime/evaluation/evaluator.py`) provide real-time latency telemetry and automated response quality evaluation across ResearchMind's AI pipeline.

---

## 2. Observability Metrics & Telemetry Schema

### Recorded Pipeline Stage Timings
- `redis_lookup_ms`: Redis cache lookup duration (< 10ms target).
- `intent_router_ms`: Selective agent routing evaluation (< 10ms target).
- `context_builder_ms`: Single-pass `SharedContext` assembly (< 50ms target).
- `execution_ms`: Concurrent agent execution duration.
- `ttft_ms`: Time-To-First-Token delivered over WebSocket (< 700ms target).
- `total_ms`: End-to-end request duration.

### Telemetry Summary Payload Format
```json
{
  "request_id": "req_001",
  "cache": "MISS",
  "redis_lookup_ms": 3.8,
  "intent_router_ms": 0.2,
  "context_builder_ms": 12.4,
  "execution_ms": 450.0,
  "ttft_ms": 466.4,
  "total_ms": 466.4,
  "prompt_tokens": 120,
  "completion_tokens": 180,
  "total_tokens": 300,
  "estimated_cost_usd": 0.000204,
  "provider": "groq"
}
```

---

## 3. Evaluation Engine Quality Scoring

The `EvaluationEngine` computes automated scores for each finalized response:

| Metric | Formula / Evaluation Logic | Quality Target |
| :--- | :--- | :--- |
| **Hallucination Score** | Evaluates source text word overlap vs. generated Markdown claims. | `≥ 0.70` |
| **Citation Correctness** | Validates citation IDs against PostgreSQL `paper_objects` metadata. | `1.00` |
| **Response Completeness** | Verifies presence of required section headers (`Overview`, `Takeaways`, `Background`). | `1.00` |
| **Grounding Score** | Semantic alignment between selection highlight and explanation. | `≥ 0.70` |
