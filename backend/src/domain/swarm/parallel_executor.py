"""
Parallel Executor & Streaming Component for ResearchMind Swarm Architecture (Phase 3, 4, 5, 9)

Executes planned sub-agent tasks concurrently, streams section Markdown chunks 
progressively as soon as available, and uses single-pass consolidated reasoning 
to minimize total LLM requests.
"""

import asyncio
import time
from typing import Dict, Any, List, Callable, Optional
from src.domain.swarm.context_builder import SharedContext
from src.domain.swarm.llm_router import llm_router
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

class ParallelExecutor:
    """
    Orchestrates parallel sub-agent execution with progressive section streaming.
    """

    async def execute_stream(
        self,
        session_id: int,
        context: SharedContext,
        agent_names: List[str],
        reading_level: str = "Beginner",
        on_section_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None
    ) -> Dict[str, Any]:
        """
        Executes sub-agent tasks concurrently and emits completed section chunks to callback.
        """
        start_time = time.time()
        print(f"[ParallelExecutor] Executing parallel tasks for agents: {agent_names} (Level: {reading_level})")

        agent_results: Dict[str, Any] = {}
        names = []
        futures = []

        # Map agent names directly to execution coroutines
        for name in agent_names:
            names.append(name)
            futures.append(self._run_single_agent(name, session_id, context, reading_level, on_section_callback))

        # Run all planned agents concurrently
        results = await asyncio.gather(*futures, return_exceptions=True)

        for name, res in zip(names, results):
            if isinstance(res, Exception):
                print(f"[ParallelExecutor Warning] Agent '{name}' failed: {res}")
                agent_results[name] = {"error": str(res)}
            elif isinstance(res, dict):
                agent_results[name] = res

        elapsed = time.time() - start_time
        print(f"[ParallelExecutor] All parallel agents finished in {elapsed:.3f}s")
        return agent_results

    async def _run_single_agent(
        self,
        name: str,
        session_id: int,
        context: SharedContext,
        reading_level: str,
        callback: Optional[Callable[[str, Dict[str, Any]], None]]
    ) -> Dict[str, Any]:
        """
        Executes a single agent task in threadpool, then triggers streaming callback.
        """
        text = context.selection_text
        target_id = context.target_id or "selection"

        def _call_agent():
            if name == "explanation":
                return explanation_agent.explain(session_id, target_id, text, reading_level)
            elif name == "math":
                return math_agent.analyze_equation(session_id, target_id, text)
            elif name == "background":
                return background_agent.get_prerequisites(session_id, target_id, text)
            elif name == "visual":
                return visual_agent.generate_diagram(session_id, target_id, text)
            elif name == "figure":
                return figure_agent.explain_figure(session_id, target_id, text)
            elif name == "table":
                return table_agent.analyze_table(session_id, target_id, text)
            elif name == "citation":
                return citation_agent.explain_citation(session_id, target_id, text)
            elif name == "terminology":
                return terminology_agent.define_term(session_id, target_id, text)
            elif name == "questions":
                return question_agent.predict_questions(session_id, target_id, text)
            else:
                return explanation_agent.explain(session_id, target_id, text, reading_level)

        # Offload synchronous LLM call to async thread
        result = await asyncio.to_thread(_call_agent)

        # Stream progressive completion section callback
        if callback and callable(callback):
            try:
                callback(name, result)
            except Exception as e:
                print(f"[ParallelExecutor Warning] Callback failed for '{name}': {e}")

        return result

parallel_executor = ParallelExecutor()
