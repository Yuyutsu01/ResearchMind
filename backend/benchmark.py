import sys
import os
import json
import time
import argparse
from unittest.mock import MagicMock

# Ensure backend modules can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent.planner import create_plan
from agent.executor import execute_step
from agent.validator import validate_step
from agent.memory import retrieve_similar_task, store_task, MEMORY_FILE
from agent.telemetry import telemetry
from rag.retrieve import init_retriever

BENCHMARK_PROMPTS = [
    "Hello there! Who are you?",
    "What are the action items from the meeting notes?",
    "Write a summary of the project goals to a file named goals.txt",
    "Read the content of notes.txt and tell me who is preparing marketing material.",
    "Hello there! Who are you?" # Repeat to test cache
]

def run_benchmark(mock=False):
    print(f"=== Starting Benchmark (Mock Mode: {mock}) ===")
    
    if mock:
        setup_mocks()
    
    # Initialize RAG
    init_retriever()
    
    # Clear memory for clean start (optional, but good for benchmarks)
    if os.path.exists(MEMORY_FILE):
        os.remove(MEMORY_FILE)

    for prompt in BENCHMARK_PROMPTS:
        print(f"\n[Benchmark] Testing Prompt: '{prompt}'")
        
        # 1. Check Memory
        cached_output = retrieve_similar_task(prompt)
        if cached_output:
            print("[Benchmark] Served from cache.")
            continue
            
        # 2. Plan
        plan = create_plan(prompt)
        if not plan:
            print("[Benchmark] Failed to generate plan.")
            continue
            
        # 3. Execute
        context = ""
        last_output = ""
        for step in plan:
            output = execute_step(step, context)
            is_valid, reason = validate_step(step, output)
            
            context += f"\nStep: {step}\nOutput: {output}\n"
            last_output = output
            
        # 4. Store
        store_task(prompt, last_output)

    print("\n" + "="*40)
    print("      BENCHMARK RESULTS")
    print("="*40)
    
    summary = telemetry.get_summary()
    print(json.dumps(summary, indent=4))
    
    print("\n[Target Comparison]")
    print(f"Planning Latency: {summary.get('Planning Latency', {}).get('avg_duration_ms', 'N/A')}ms (Target: <1200ms)")
    print(f"Validation Rate:  {summary.get('Validation Rate', {}).get('success_rate', 'N/A')}% (Target: >85%)")
    print(f"Cache Hit Rate:   {summary.get('cache', {}).get('hit_rate', 'N/A')}% (Target: ~30%)")

def setup_mocks():
    """Mocks the LLM calls to avoid dependency on Ollama during testing."""
    import agent.planner
    import agent.executor
    
    # Mock OpenAI client
    mock_client = MagicMock()
    agent.planner.get_openai_client = MagicMock(return_value=mock_client)
    agent.executor.get_openai_client = MagicMock(return_value=mock_client)
    
    # Mock Response handler
    def mock_llm_response(*args, **kwargs):
        messages = kwargs.get('messages', [])
        system_content = messages[0]['content'] if messages else ""
        user_content = messages[1]['content'] if len(messages) > 1 else ""
        
        mock_res = MagicMock()
        
        if "agent planner" in system_content.lower():
            # Planner response
            if "Hello" in user_content:
                plan = ["Greet the user", "Ask how to help"]
            elif "action items" in user_content:
                plan = ["retrieve_rag for action items", "Summarize action items"]
            elif "goals.txt" in user_content:
                plan = ["file_writer path='goals.txt' content='Our goal is to build an autonomous agent.'"]
            elif "marketing material" in user_content:
                plan = ["file_reader path='notes.txt'", "Find person for marketing material"]
            else:
                plan = ["Default step"]
            mock_res.choices[0].message.content = json.dumps({"plan": plan})
            
        elif "executor agent" in system_content.lower():
            # Executor response
            if "Greet" in user_content:
                action = {"tool": "llm_action", "kwargs": {"prompt": "Hello! I am your autonomous agent. How can I help you today?"}}
            elif "retrieve_rag" in user_content:
                action = {"tool": "retrieve_rag", "kwargs": {"query": "action items"}}
            elif "file_writer" in user_content:
                action = {"tool": "file_writer", "kwargs": {"path": "goals.txt", "content": "Our goal is to build an autonomous agent."}}
            elif "file_reader" in user_content:
                action = {"tool": "file_reader", "kwargs": {"path": "notes.txt"}}
            else:
                action = {"tool": "llm_action", "kwargs": {"prompt": "I have completed the task."}}
            mock_res.choices[0].message.content = json.dumps(action)
            
        else:
            mock_res.choices[0].message.content = "Mock response"
            
        return mock_res

    mock_client.chat.completions.create.side_effect = mock_llm_response

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mock", action="store_true", help="Run in mock mode")
    args = parser.parse_args()
    
    run_benchmark(mock=args.mock)
