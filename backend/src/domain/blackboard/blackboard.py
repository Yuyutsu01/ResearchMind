import time
import json
import networkx as nx
from typing import Dict, List, Any
from src.adapters.db.postgres import execute_query

class ResearchBlackboard:
    def __init__(self, session_id: int):
        self.session_id = session_id
        
        # 1. Working Memory (Facts, extracted context, parsed documents)
        self.working_memory: Dict[str, Any] = {}
        
        # 2. Event Queue (List of events that have occurred in the session)
        self.event_queue: List[Dict[str, Any]] = []
        
        # 3. Active Tasks (Queue of tasks managed by the Task Scheduler)
        self.active_tasks: List[Dict[str, Any]] = []
        
        # 4. Context (Query prompt, constraints)
        self.context: Dict[str, Any] = {
            "query": "",
            "pdf_path": "",
            "start_time": time.time()
        }
        
        # 5. Session State (Research state machine value)
        self.session_state = "IDLE"  # IDLE, SEARCHING, READING, VERIFYING, SYNTHESIZING, QUESTIONING_USER, COMPLETE
        
        # 6. Budget Management tracking
        self.budget = {
            "tokens_used": 0,
            "cost_usd": 0.0,
            "api_calls": 0
        }
        
        # 7. Knowledge Graph (NetworkX object in RAM)
        self.knowledge_graph = nx.DiGraph()
        
        # 8. Claims and Hypotheses Graphs (lists/dicts of metadata)
        self.claims: List[Dict[str, Any]] = []
        self.hypotheses: List[Dict[str, Any]] = []

    def load_from_db(self):
        """Loads the blackboard state and knowledge graph from PostgreSQL checkpoint."""
        try:
            # 1. Load Session info
            sess_row = execute_query(
                "SELECT prompt, status FROM sessions WHERE id = %s",
                (self.session_id,),
                fetch=True
            )
            if sess_row:
                self.context["query"] = sess_row[0]["prompt"]
                self.session_state = sess_row[0]["status"]
                
            # 2. Load latest Blackboard checkpoint
            checkpoint_row = execute_query(
                "SELECT blackboard_state FROM blackboard_checkpoints WHERE session_id = %s ORDER BY id DESC LIMIT 1",
                (self.session_id,),
                fetch=True
            )
            if checkpoint_row:
                state = checkpoint_row[0]["blackboard_state"]
                if isinstance(state, str):
                    state = json.loads(state)
                self.working_memory = state.get("working_memory", {})
                self.event_queue = state.get("event_queue", [])
                self.active_tasks = state.get("active_tasks", [])
                self.budget = state.get("budget", self.budget)
                
            # 3. Load NetworkX graph state
            graph_row = execute_query(
                "SELECT nodes, edges FROM knowledge_graph WHERE session_id = %s ORDER BY id DESC LIMIT 1",
                (self.session_id,),
                fetch=True
            )
            if graph_row:
                self.knowledge_graph.clear()
                nodes = graph_row[0]["nodes"]
                edges = graph_row[0]["edges"]
                if isinstance(nodes, str):
                    nodes = json.loads(nodes)
                if isinstance(edges, str):
                    edges = json.loads(edges)
                for node in nodes:
                    self.knowledge_graph.add_node(node["id"], **node)
                for edge in edges:
                    self.knowledge_graph.add_edge(edge["source"], edge["target"], **edge)
                    
            # 4. Load Claims
            claims_rows = execute_query(
                "SELECT claim_text, confidence_score, evidence, status FROM confidence_claims WHERE session_id = %s",
                (self.session_id,),
                fetch=True
            )
            if claims_rows:
                self.claims = [
                    {
                        "claim_text": c["claim_text"],
                        "confidence_score": c["confidence_score"],
                        "evidence": json.loads(c["evidence"]) if isinstance(c["evidence"], str) else c["evidence"],
                        "status": c["status"]
                    }
                    for c in claims_rows
                ]
                
            # 5. Load Hypotheses
            hyp_rows = execute_query(
                "SELECT hypothesis_text, status, evidence FROM hypotheses WHERE session_id = %s",
                (self.session_id,),
                fetch=True
            )
            if hyp_rows:
                self.hypotheses = [
                    {
                        "hypothesis_text": h["hypothesis_text"],
                        "status": h["status"],
                        "evidence": json.loads(h["evidence"]) if isinstance(h["evidence"], str) else h["evidence"]
                    }
                    for h in hyp_rows
                ]
        except Exception as e:
            print(f"[Blackboard Error] Failed to load session data from DB: {e}")

    def save_to_db(self):
        """Autosaves a snapshot checkpoint of the blackboard and NetworkX graph to PostgreSQL."""
        try:
            # 1. Update session status
            execute_query(
                "UPDATE sessions SET status = %s WHERE id = %s",
                (self.session_state, self.session_id)
            )
            
            # 2. Serialize blackboard
            state_json = json.dumps({
                "working_memory": self.working_memory,
                "event_queue": self.event_queue,
                "active_tasks": self.active_tasks,
                "budget": self.budget
            })
            execute_query(
                "INSERT INTO blackboard_checkpoints (session_id, blackboard_state) VALUES (%s, %s)",
                (self.session_id, state_json)
            )
            
            # 3. Serialize NetworkX Knowledge Graph
            nodes = [{"id": n, **self.knowledge_graph.nodes[n]} for n in self.knowledge_graph.nodes]
            edges = [{"source": u, "target": v, **self.knowledge_graph.edges[u, v]} for u, v in self.knowledge_graph.edges]
            execute_query(
                "INSERT INTO knowledge_graph (session_id, nodes, edges) VALUES (%s, %s, %s)",
                (self.session_id, json.dumps(nodes), json.dumps(edges))
            )
            
            # 4. Save Claims
            execute_query("DELETE FROM confidence_claims WHERE session_id = %s", (self.session_id,))
            for c in self.claims:
                execute_query(
                    "INSERT INTO confidence_claims (session_id, claim_text, confidence_score, evidence, status) VALUES (%s, %s, %s, %s, %s)",
                    (self.session_id, c["claim_text"], c["confidence_score"], json.dumps(c["evidence"]), c["status"])
                )
                
            # 5. Save Hypotheses
            execute_query("DELETE FROM hypotheses WHERE session_id = %s", (self.session_id,))
            for h in self.hypotheses:
                execute_query(
                    "INSERT INTO hypotheses (session_id, hypothesis_text, status, evidence) VALUES (%s, %s, %s, %s)",
                    (self.session_id, h["hypothesis_text"], h["status"], json.dumps(h["evidence"]))
                )
                
            print(f"[Blackboard] Autosave checkpoint completed for Session #{self.session_id}.")
        except Exception as e:
            print(f"[Blackboard Error] Autosave checkpoint failed: {e}")

    def add_event(self, event_type: str, details: Dict[str, Any]):
        """Pushes an event into the session's event queue."""
        event = {
            "type": event_type,
            "details": details,
            "timestamp": time.time()
        }
        self.event_queue.append(event)
        print(f"[Event Queue] Published event: {event_type} - {details.get('msg', '')}")
