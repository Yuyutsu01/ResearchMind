import asyncio
import json
import uuid
from typing import Dict, Any, List, Callable
from src.adapters.db.postgres import execute_query
from src.domain.swarm.agents import (
    explanation_agent,
    math_agent,
    background_agent,
    visual_agent,
    figure_agent,
    table_agent,
    citation_agent,
    terminology_agent,
    question_agent
)

class SwarmOrchestrator:
    """
    Coordinates specialized swarm agents with transactional checkpoints,
    task persistence, failure recovery, and cancellation support.
    """
    
    # DB HELPER METHODS FOR WORKFLOW ORCHESTRATION
    def _create_run(self, run_id: str, session_id: int, text: str, selection_type: str):
        execute_query(
            """
            INSERT INTO workflow_runs (run_id, session_id, selection_text, selection_type, status)
            VALUES (%s, %s, %s, %s, 'PENDING');
            """,
            (run_id, session_id, text, selection_type)
        )

    def _update_run_status(self, run_id: str, status: str):
        execute_query(
            "UPDATE workflow_runs SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE run_id = %s;",
            (status, run_id)
        )

    def _create_checkpoint(self, task_id: str, run_id: str, agent_name: str):
        execute_query(
            """
            INSERT INTO task_checkpoints (task_id, run_id, agent_name, status, retries)
            VALUES (%s, %s, %s, 'PENDING', 0);
            """,
            (task_id, run_id, agent_name)
        )

    def _update_checkpoint(self, task_id: str, status: str, result: Any = None, retries: int = 0):
        res_json = json.dumps(result) if result is not None else None
        execute_query(
            """
            UPDATE task_checkpoints
            SET status = %s, result = %s, retries = %s, updated_at = CURRENT_TIMESTAMP
            WHERE task_id = %s;
            """,
            (status, res_json, retries, task_id)
        )

    def _is_run_cancelled(self, run_id: str) -> bool:
        rows = execute_query("SELECT status FROM workflow_runs WHERE run_id = %s;", (run_id,), fetch=True)
        if rows and rows[0]["status"] == "CANCELLED":
            return True
        return False

    async def execute_checkpointed_task(
        self, 
        task_id: str, 
        run_id: str, 
        agent_name: str, 
        agent_func: Callable, 
        *args
    ) -> Dict[str, Any]:
        """
        Executes a sub-task with transactional database checkpoints, 
        verifying cancellations, and retrying on failures.
        """
        if self._is_run_cancelled(run_id):
            self._update_checkpoint(task_id, "CANCELLED")
            return {"error": "Task cancelled"}

        max_retries = 3
        retries = 0
        
        while retries < max_retries:
            self._update_checkpoint(task_id, "RUNNING", retries=retries)
            try:
                # Run synchronous LLM call inside a thread to prevent blocking FastAPI
                result = await asyncio.to_thread(agent_func, *args)
                
                # Double-check cancellation post execution
                if self._is_run_cancelled(run_id):
                    self._update_checkpoint(task_id, "CANCELLED")
                    return {"error": "Task cancelled"}

                self._update_checkpoint(task_id, "COMPLETED", result=result, retries=retries)
                return result
            except Exception as e:
                retries += 1
                print(f"[Orchestrator Task Error] Agent '{agent_name}' failed (Attempt {retries}/{max_retries}): {e}")
                if retries >= max_retries:
                    self._update_checkpoint(task_id, "FAILED", result={"error": str(e)}, retries=retries)
                    return {"error": str(e)}
                # Jittered backoff sleep between retries
                await asyncio.sleep(1.0 * retries)
                
        return {"error": "Task execution exhausted retries"}

    async def process_selection(
        self, 
        session_id: int, 
        selection_text: str, 
        selection_type: str, 
        obj_id: str = None
    ) -> Dict[str, Any]:
        """
        Main entry point for interactive text selection.
        Orchestrates specialized sub-agents in parallel with persistent checkpoints.
        """
        run_id = str(uuid.uuid4())
        print(f"[Orchestrator] Starting Persistent Run #{run_id} | Selected item: '{selection_text}' (Type: {selection_type})")
        
        self._create_run(run_id, session_id, selection_text, selection_type)
        self._update_run_status(run_id, "RUNNING")
        
        s_type = selection_type.lower()
        
        # Mapping definition for selective parallel routing
        routing_targets = []
        if s_type == "equation":
            routing_targets = [
                ("math", math_agent.analyze_equation, (session_id, obj_id or "eq", selection_text)),
                ("background", background_agent.get_prerequisites, (session_id, obj_id or "eq", selection_text)),
                ("visual", visual_agent.generate_diagram, (session_id, obj_id or "eq", selection_text)),
                ("questions", question_agent.predict_questions, (session_id, obj_id or "eq", selection_text))
            ]
        elif s_type == "figure":
            routing_targets = [
                ("figure", figure_agent.explain_figure, (session_id, obj_id or "fig", selection_text)),
                ("background", background_agent.get_prerequisites, (session_id, obj_id or "fig", selection_text)),
                ("visual", visual_agent.generate_diagram, (session_id, obj_id or "fig", selection_text))
            ]
        elif s_type == "table":
            routing_targets = [
                ("table", table_agent.analyze_table, (session_id, obj_id or "table", selection_text)),
                ("background", background_agent.get_prerequisites, (session_id, obj_id or "table", selection_text)),
                ("questions", question_agent.predict_questions, (session_id, obj_id or "table", selection_text))
            ]
        elif s_type == "citation":
            routing_targets = [
                ("citation", citation_agent.explain_citation, (session_id, obj_id or "citation", selection_text)),
                ("terminology", terminology_agent.define_term, (session_id, obj_id or "citation", selection_text))
            ]
        else:
            routing_targets = [
                ("explanation", explanation_agent.explain, (session_id, obj_id or "para", selection_text, "Beginner")),
                ("background", background_agent.get_prerequisites, (session_id, obj_id or "para", selection_text)),
                ("visual", visual_agent.generate_diagram, (session_id, obj_id or "para", selection_text)),
                ("terminology", terminology_agent.define_term, (session_id, obj_id or "para", selection_text)),
                ("questions", question_agent.predict_questions, (session_id, obj_id or "para", selection_text))
            ]

        # 1. Create checkpoints for all tasks
        execution_tasks = []
        for name, func, args in routing_targets:
            task_id = str(uuid.uuid4())
            self._create_checkpoint(task_id, run_id, name)
            execution_tasks.append(
                (name, self.execute_checkpointed_task(task_id, run_id, name, func, *args))
            )

        # 2. Parallel execution of checkpointed tasks
        keys = [t[0] for t in execution_tasks]
        futures = [t[1] for t in execution_tasks]
        results = await asyncio.gather(*futures, return_exceptions=True)

        # 3. Merging results
        merged_res = {}
        has_failures = False
        
        for key, res in zip(keys, results):
            if isinstance(res, Exception):
                print(f"[Orchestrator Warning] Task '{key}' failed with unhandled exception: {res}")
                merged_res[key] = {"error": str(res)}
                has_failures = True
            elif isinstance(res, dict) and "error" in res:
                merged_res[key] = res
                has_failures = True
            else:
                merged_res[key] = res

        # 4. Finalize run status
        if self._is_run_cancelled(run_id):
            self._update_run_status(run_id, "CANCELLED")
        elif has_failures:
            self._update_run_status(run_id, "FAILED")
        else:
            self._update_run_status(run_id, "COMPLETED")

        # Format timeline logging in Postgres on success
        try:
            execute_query(
                "INSERT INTO reading_timeline (session_id, action_type, details) VALUES (%s, 'TEXT_SELECTED', %s);",
                (
                    session_id,
                    json.dumps({
                        "text": selection_text,
                        "type": selection_type,
                        "summary": merged_res.get("explanation", {}).get("level_1") or f"Analyzed {selection_type}"
                    })
                )
            )
        except Exception as err:
            print(f"[Orchestrator DB Warning] Failed to log selection to timeline: {err}")

        return merged_res

    def recover_pending_workflows(self):
        """
        Startup Recovery Hook.
        Scans database for PENDING or RUNNING workflows, logging metrics, and cleaning stale records.
        """
        print("[Orchestrator] Scanning database to recover pending workflow runs...")
        try:
            runs = execute_query(
                "SELECT run_id, session_id, selection_text, selection_type FROM workflow_runs WHERE status IN ('PENDING', 'RUNNING');",
                fetch=True
            )
            if runs:
                print(f"[Orchestrator Recovery] Found {len(runs)} incomplete runs. Setting them to FAILED for safe recovery state.")
                for run in runs:
                    # In a fully distributed system, we would re-enqueue these runs to a background worker queue.
                    # As a safe baseline, we mark them as failed/aborted to maintain system consistency on reboot.
                    self._update_run_status(run["run_id"], "FAILED")
            else:
                print("[Orchestrator Recovery] No incomplete runs found. System state clean.")
        except Exception as e:
            print(f"[Orchestrator Recovery Error] Failed to scan or recover workflows: {e}")

swarm_orchestrator = SwarmOrchestrator()
