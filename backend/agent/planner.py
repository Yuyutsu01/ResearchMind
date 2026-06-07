import os
import json
import time
from openai import OpenAI
from agent.telemetry import telemetry

def get_openai_client():
    """Initializes and returns the OpenAI client configured for local Ollama."""
    return OpenAI(
        base_url='http://localhost:11434/v1',
        api_key='ollama'  # required but ignored by Ollama
    )

def create_plan(user_request: str) -> list[str]:
    """
    Calls the LLM to produce a JSON plan for the given user request.
    """
    start_time = time.time()
    client = get_openai_client()
    
    system_prompt = '''You are an agent planner. Given a user request and available tools (search_api, file_reader, file_writer, email_sender, retrieve_rag), you MUST output ONLY a valid JSON object. 
Do not include any conversational text or explanation.
If the user's request is a simple greeting or vague, generate a plan to greet them or ask for clarification.

Format:
{"plan": ["step description including tool to use", ...]}'''

    user_prompt = f"User Request: {user_request}"
    
    try:
        response = client.chat.completions.create(
            model="llama3",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2
        )
        
        content = response.choices[0].message.content
        print(f"[Planner] Raw LLM Output:\n{content}")
        
        # Robust JSON extraction using regex to find the first '{' and last '}'
        import re
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            content = json_match.group(0)
        
        try:
            plan_data = json.loads(content)
        except json.JSONDecodeError as e:
            print(f"[Planner] JSON Decode Error: {e}")
            # Try one more fallback: if the model returned just a list
            list_match = re.search(r'\[.*\]', content, re.DOTALL)
            if list_match:
                plan_data = {"plan": json.loads(list_match.group(0))}
            else:
                raise e
        
        duration = (time.time() - start_time) * 1000
        if "plan" in plan_data and isinstance(plan_data["plan"], list):
            telemetry.record_metric("Planning Latency", duration, success=True)
            return plan_data["plan"]
        else:
            telemetry.record_metric("Planning Latency", duration, success=False)
            print("[Planner] Error: Expected 'plan' list in JSON.")
            return []
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        telemetry.record_metric("Planning Latency", duration, success=False)
        print(f"[Planner] API call failed: {e}")
        return []
