from src.domain.blackboard.blackboard import ResearchBlackboard
from src.adapters.db.postgres import execute_query

class MetricsEngine:
    @staticmethod
    def calculate_session_metrics(blackboard: ResearchBlackboard) -> dict:
        """Computes the 5 key telemetry metrics for the active session."""
        # 1. Task Completion Rate (TCR)
        has_synthesis = "report_synthesis" in blackboard.working_memory
        tcr = 1.0 if blackboard.session_state == "COMPLETE" and has_synthesis else 0.0
        
        # 2. Autonomy Score
        user_queries = [e for e in blackboard.event_queue if e["type"] == "USER_CLARIFICATION"]
        total_steps = len(blackboard.event_queue) if blackboard.event_queue else 1
        autonomy = max(0.0, (total_steps - len(user_queries)) / total_steps)
        
        # 3. Answer Grounding Score (Percentage of claims backed by evidence)
        grounding = 1.0
        if blackboard.claims:
            backed_claims = [c for c in blackboard.claims if c["status"] == "SUPPORTED"]
            grounding = len(backed_claims) / len(blackboard.claims)
            
        # 4. Hallucination Rate (Claims flagged as hallucination or unsupported)
        hallucinations = 0.0
        if blackboard.claims:
            flagged = [c for c in blackboard.claims if c["status"] in ("HALLUCINATION", "CONTRADICTED")]
            hallucinations = len(flagged) / len(blackboard.claims)
            
        # 5. Cost per Research Session
        cost = blackboard.budget.get("cost_usd", 0.0)
        
        metrics = {
            "task_completion_rate": round(tcr, 2),
            "autonomy_score": round(autonomy, 2),
            "answer_grounding_score": round(grounding, 2),
            "hallucination_rate": round(hallucinations, 2),
            "cost_usd": round(cost, 4)
        }
        
        return metrics

    @staticmethod
    def save_metrics_to_db(session_id: int, metrics: dict):
        """Persists the 5 session metrics to the PostgreSQL database."""
        try:
            # Delete old metrics for this session to update
            execute_query("DELETE FROM telemetry_metrics WHERE session_id = %s", (session_id,))
            
            # Save new metrics
            execute_query(
                "INSERT INTO telemetry_metrics (session_id, metric_name, value, unit) VALUES (%s, %s, %s, %s)",
                (session_id, "TCR", metrics["task_completion_rate"], "ratio")
            )
            execute_query(
                "INSERT INTO telemetry_metrics (session_id, metric_name, value, unit) VALUES (%s, %s, %s, %s)",
                (session_id, "Autonomy", metrics["autonomy_score"], "ratio")
            )
            execute_query(
                "INSERT INTO telemetry_metrics (session_id, metric_name, value, unit) VALUES (%s, %s, %s, %s)",
                (session_id, "Grounding", metrics["answer_grounding_score"], "ratio")
            )
            execute_query(
                "INSERT INTO telemetry_metrics (session_id, metric_name, value, unit) VALUES (%s, %s, %s, %s)",
                (session_id, "Hallucination", metrics["hallucination_rate"], "ratio")
            )
            execute_query(
                "INSERT INTO telemetry_metrics (session_id, metric_name, value, unit) VALUES (%s, %s, %s, %s)",
                (session_id, "Cost", metrics["cost_usd"], "usd")
            )
            print(f"[Metrics Engine] Saved telemetry metrics to DB for Session #{session_id}.")
        except Exception as e:
            print(f"[Metrics Engine Error] Failed to save session metrics to DB: {e}")
