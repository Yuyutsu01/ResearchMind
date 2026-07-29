"""
Unit Tests for Observability & Evaluation Engine
"""

import pytest
from src.runtime.observability.telemetry import telemetry_engine, StageMetrics
from src.runtime.evaluation.evaluator import evaluation_engine

def test_telemetry_engine_recording():
    """Verifies TelemetryEngine tracks stage metrics and computes summary stats."""
    m = telemetry_engine.start_request("req_001")
    m.redis_lookup_ms = 4.5
    m.intent_router_ms = 0.2
    m.context_builder_ms = 12.0
    m.execution_ms = 450.0
    m.ttft_ms = 466.7
    m.total_ms = 466.7
    m.cache_hit = False
    
    telemetry_engine.record_completed_request(m)
    
    summary = telemetry_engine.get_summary_telemetry()
    assert summary["total_requests"] > 0
    assert summary["avg_ttft_ms"] > 0

def test_evaluation_engine_completeness_and_citation():
    """Verifies EvaluationEngine scores response completeness and citation validity."""
    sample_payload = {
        "citation_references": [],
        "composer": {
            "composed_markdown": "# Overview\nTransformers use self-attention mechanisms.\n# Key Takeaways\nTakeaway 1.\n# Background Concepts\nPrerequisites."
        }
    }
    
    report = evaluation_engine.evaluate_response(
        request_id="req_002",
        session_id=123,
        selection_text="Transformers use self-attention mechanisms.",
        response_payload=sample_payload
    )
    
    assert report.response_completeness == 1.0
    assert report.hallucination_score >= 0.7
    assert report.to_dict()["is_quality_pass"] is True
