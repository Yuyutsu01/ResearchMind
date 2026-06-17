import json
import time
from openai import OpenAI
import os
import sys
# Ensure backend directory is in path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
while current_dir and os.path.basename(current_dir) != "backend":
    parent = os.path.dirname(current_dir)
    if parent == current_dir:
        break
    current_dir = parent

if current_dir and current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from src.adapters.tools.search import search_api
from src.adapters.tools.file_ops import file_reader, file_writer
from src.adapters.tools.email import email_sender
from src.adapters.rag.retrieve import retrieve
from src.domain.services.planner import get_openai_client, get_model_name
from src.domain.services.telemetry import telemetry

def execute_step(step_description: str, context: str) -> str:
    """
    Executes a specific step by determining the required tool or action using an LLM.
    Returns the output of the step.
    """
    start_time = time.time()
    client = get_openai_client()
    
    system_prompt = '''You are an executor agent. Read the step description and the current context.
Determine which tool to execute. Output your choice in JSON format.
Tools available:
- search_api: requires "query" (string)
- file_reader: requires "path" (string)
- file_writer: requires "path" (string) and "content" (string)
- email_sender: requires "to" (string), "subject" (string), "body" (string)
- retrieve_rag: requires "query" (string) for searching local documents
- llm_action: use this when no specific external tool is needed (e.g. summarizing or reasoning). Requires "prompt" (string).

Output JSON format exactly:
{
  "tool": "tool_name",
  "kwargs": {"arg1": "val1", ...}
}
'''
    
    user_prompt = f"Step Description: {step_description}\nContext from previous steps:\n{context}"
    
    try:
        response = client.chat.completions.create(
            model=get_model_name(),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        
        action_data = json.loads(response.choices[0].message.content)
        tool = action_data.get("tool")
        kwargs = action_data.get("kwargs", {})
        
        print(f"    -> [Executor] Calling {tool} with args: {kwargs}")
        
        result = ""
        if tool == "search_api":
            result = search_api(**kwargs)
        elif tool == "file_reader":
            result = file_reader(**kwargs)
        elif tool == "file_writer":
            result = file_writer(**kwargs)
        elif tool == "email_sender":
            result = email_sender(**kwargs)
        elif tool == "retrieve_rag":
            result = "\\n".join(retrieve(**kwargs))
        elif tool == "llm_action":
            # Just directly answer using LLM
            prompt = kwargs.get("prompt", "")
            result = call_llm_action(prompt, context)
        else:
            result = f"Error: Unknown tool {tool}"
            
        duration = (time.time() - start_time) * 1000
        telemetry.record_metric("Execution Latency", duration, success=("Error" not in result))
        return result
            
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        telemetry.record_metric("Execution Latency", duration, success=False)
        return f"Error executing step: {e}"

def call_llm_action(prompt: str, context: str) -> str:
    """Executes a pure LLM transformation (like summarizing)."""
    client = get_openai_client()
    
    try:
        response = client.chat.completions.create(
            model=get_model_name(),
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Context provided below."},
                {"role": "user", "content": f"Context:\n{context}\n\nTask: {prompt}"}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error in LLM action: {e}"
