import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.domain.blackboard.blackboard import ResearchBlackboard
from src.domain.scheduler.scheduler import TaskScheduler, ResearchStateMachine
from src.domain.agents.registry import agent_registry
from src.domain.rl.strategist import rl_strategist
from src.domain.services.event_bus import EventBus
from src.domain.services.metrics import MetricsEngine

router = APIRouter()

@router.websocket("/ws/v1/research/{session_id}")
async def websocket_research(websocket: WebSocket, session_id: int):
    await websocket.accept()
    print(f"[WebSocket] Connected to session {session_id}.")
    
    # 1. Initialize Blackboard and Scheduler
    blackboard = ResearchBlackboard(session_id)
    blackboard.load_from_db()
    
    scheduler = TaskScheduler(agent_registry)
    event_bus = EventBus(scheduler)
    
    # Trigger initial research start event
    blackboard.add_event("RESEARCH_START", {"msg": "Starting event-driven swarm intelligence."})
    
    # Helper to stream status back to client
    async def send_client_payload(data: dict):
        try:
            await websocket.send_text(json.dumps(data))
        except Exception as e:
            print(f"[WebSocket Send Warning] Failed to stream data: {e}")

    # Set up active state machine callback
    def state_machine_callback(new_state: str):
        asyncio.create_task(send_client_payload({
            "type": "state_change",
            "state": new_state
        }))

    try:
        # Initial state transition
        ResearchStateMachine.transition_to(blackboard, "SEARCHING", state_machine_callback)
        
        loop_counter = 0
        max_loops = 20
        finished = False
        
        while not finished and loop_counter < max_loops:
            loop_counter += 1
            
            # A. Select Action using RL Strategist PPO model
            action = rl_strategist.select_action(blackboard)
            print(f"[Strategist PPO] Recommending Action: {action} (Loop {loop_counter}/{max_loops})")
            
            # Map action to Task
            rl_strategist.execute_action(blackboard, action, scheduler)
            
            # Notify client of the selected action step
            action_names = ["SEARCH_PAPERS", "ANALYZE_PAPER", "VERIFY_CLAIM", "CONNECT_CONCEPTS", "CLARIFY_USER", "TERMINATE"]
            act_name = action_names[action] if action < len(action_names) else "UNKNOWN"
            
            await send_client_payload({
                "type": "agent_step",
                "agent": "RLStrategist",
                "action": act_name,
                "description": f"Strategist recommended sequential research action '{act_name}'."
            })
            
            # B. Execute scheduled tasks in Priority Queue
            has_tasks = True
            while has_tasks:
                has_tasks = scheduler.execute_next_task(blackboard)
                # Check for active completed tasks to trigger downstream event chains
                for event in list(blackboard.event_queue):
                    # Publish events in Event Bus to schedule subsequent activations
                    await event_bus.publish_event(blackboard, event["type"], event["details"])
                    # Remove from active queue to prevent re-triggering
                    blackboard.event_queue.remove(event)
                    
                # Short delay to prevent CPU lock and simulate async work
                await asyncio.sleep(0.5)
                
            # C. Compute the 5 Telemetry Metrics
            metrics = MetricsEngine.calculate_session_metrics(blackboard)
            MetricsEngine.save_metrics_to_db(session_id, metrics)
            
            # Stream metrics back to frontend in real-time
            await send_client_payload({
                "type": "telemetry_update",
                "metrics": {
                    "task_completion_rate": metrics["task_completion_rate"],
                    "autonomy_score": metrics["autonomy_score"],
                    "answer_grounding_score": metrics["answer_grounding_score"],
                    "hallucination_rate": metrics["hallucination_rate"],
                    "cost_usd": metrics["cost_usd"]
                },
                "budget": {
                    "tokens_remaining": 500000 - blackboard.budget["tokens_used"],
                    "dollars_remaining": 10.00 - blackboard.budget["cost_usd"]
                }
            })
            
            # Check for user clarification interrupt
            if action == 4: # CLARIFY_USER
                await send_client_payload({
                    "type": "ui_prompt",
                    "prompt_id": f"clarify_{loop_counter}",
                    "message": f"Strategist paused research on '{blackboard.context.get('query')}' to verify details. Please clarify target methods:",
                    "options": [
                        "Focus on scaling properties",
                        "Focus on training memory efficiency",
                        "Summarize both features"
                    ]
                })
                
                # Wait for user input message
                print("[UI Agent] Awaiting clarification response...")
                user_answered = False
                while not user_answered:
                    try:
                        # Non-blocking wait for websocket response
                        data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                        msg = json.loads(data)
                        if msg.get("type") == "user_message":
                            selected = msg.get("selected_option")
                            # Record clarification event
                            blackboard.add_event("USER_CLARIFICATION", {
                                "option": selected,
                                "msg": f"Researcher selected option: {selected}"
                            })
                            user_answered = True
                            print(f"[UI Agent] Clarification received: {selected}")
                    except asyncio.TimeoutError:
                        # Auto fallback if user takes too long
                        blackboard.add_event("USER_CLARIFICATION", {
                            "option": "Timeout fallback",
                            "msg": "Clarification prompt timed out."
                        })
                        user_answered = True
                        
            # Check if terminated
            if action == 5: # TERMINATE
                finished = True
                
        # Research complete: transition to COMPLETE and generate quiz
        ResearchStateMachine.transition_to(blackboard, "COMPLETE", state_machine_callback)
        
        # UI Agent generates researcher learning quiz
        ui_agent_task = {"action": "generate_quiz"}
        scheduler.schedule_task(blackboard, "generate_quiz", priority=10, payload=ui_agent_task)
        scheduler.execute_next_task(blackboard)
        
        # Save final state checkpoint
        blackboard.save_to_db()
        
        # Compile final outputs to send to client
        synthesis = blackboard.working_memory.get("report_synthesis", "No narrative synthesised.")
        quiz = blackboard.working_memory.get("learning_quiz", [])
        
        await send_client_payload({
            "type": "result",
            "session_id": session_id,
            "report": synthesis,
            "quiz": quiz,
            "metrics": MetricsEngine.calculate_session_metrics(blackboard)
        })
        
    except WebSocketDisconnect:
        print(f"[WebSocket] Client disconnected from session {session_id}.")
    except Exception as e:
        print(f"[WebSocket Error] Exception inside streaming loop: {e}")
        await send_client_payload({
            "type": "error",
            "message": f"Internal execution error: {str(e)}"
        })
