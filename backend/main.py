import os
import sys

# Suppress TensorFlow OneDNN warning
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

# Ensure local modules can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent.planner import create_plan
from agent.executor import execute_step
from agent.validator import validate_step
from agent.memory import retrieve_similar_task, store_task
from rag.retrieve import init_retriever

MAX_RETRIES = 3

def process_request(user_request: str) -> str:
    print(f"\n--- Processing Request: '{user_request}' ---")
    
    # 1. Check Memory
    print("[Agent] Checking memory for similar past tasks...")
    cached_output = retrieve_similar_task(user_request)
    if cached_output:
        print("[Agent] Found relevant past task. Skipping planning phase.")
        return cached_output
        
    # 2. Plan
    print("[Agent] Generating plan...")
    plan = create_plan(user_request)
    if not plan:
        return "Failed to generate a plan."
        
    print(f"[Agent] Plan generated: {plan}")
    
    # 3. Execute and Validate
    context = ""
    # We maintain the overall context of what's been fetched or done.
    
    for i, step in enumerate(plan):
        print(f"\n[Agent] Step {i+1}/{len(plan)}: {step}")
        
        step_output = ""
        is_valid = False
        reason = ""
        
        for attempt in range(MAX_RETRIES):
            print(f"  [Attempt {attempt+1}] Executing...")
            
            # Execute step
            step_output = execute_step(step, context)
            
            # Validate output
            is_valid, reason = validate_step(step, step_output)
            
            if is_valid:
                print(f"  [Attempt {attempt+1}] Success: Output generated successfully.")
                break
            else:
                print(f"  [Attempt {attempt+1}] Validation failed: {reason}")
                # We could modify the step description to include the feedback for the next attempt.
                step = f"{step} (Previous attempt failed because: {reason}. Try a different approach.)"
                
        if not is_valid:
            print(f"[Agent] Step '{step}' completely failed after {MAX_RETRIES} retries. Aborting.")
            return "Task failed during execution."
            
        # Add to context
        context += f"\n--- Output of Step {i+1}: {step} ---\n{step_output}\n"
        
    # We assume the overall output is summarized by the last step, or implicitly by the whole context.
    # Let's see if the user asked to return something, or it's mostly side-effects.
    final_output = step_output
    
    print("\n[Agent] Workflow complete.")
    
    # 4. Memorize
    store_task(user_request, final_output)
    
    return final_output

def main():
    print("=== Starting Autonomous Multi-Tool AI Agent ===")
    
    # Create required directories and files for testing if they don't exist
    os.makedirs("rag/documents", exist_ok=True)
    if not os.path.exists("notes.txt"):
        with open("notes.txt", "w", encoding="utf-8") as f:
            f.write("Meeting notes: Product launch is scheduled for Q4. Action items: Alice to prepare marketing material, Bob to finalize technical docs.")
            
    # Initialize RAG
    print("[System] Initializing RAG embeddings... (This might take a moment to download models if it's the first time)")
    init_retriever()
    
    print("\nAgent is ready! (Type 'exit' or 'quit' to stop)")
    
    # Start basic REPL
    while True:
        try:
            req = input("\n> ")
            if req.lower() in ["exit", "quit"]:
                break
            if not req.strip():
                continue
                
            final_result = process_request(req)
            print(f"\n[Final Output]\n{final_result}")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
