import networkx as nx
import json
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

from src.adapters.db.postgres_db import execute_query

def generate_citation_graph(task_id: int) -> dict:
    """
    Builds a directed citation graph using NetworkX based on task documents and retrieved references.
    Returns a node-link dictionary compatible with D3 force-directed layout.
    """
    G = nx.DiGraph()
    
    # 1. Fetch task prompt/topic as central node
    task_query = "SELECT prompt FROM tasks WHERE id = %s"
    task_row = execute_query(task_query, (task_id,), fetch=True)
    topic = task_row[0]["prompt"] if task_row else f"Task #{task_id}"
    
    # Add root node
    G.add_node(topic, label=topic, type="topic", val=1.0)
    
    # 2. Fetch reports section_summary to find metadata
    reports_query = "SELECT section_summary FROM reports WHERE task_id = %s"
    report_rows = execute_query(reports_query, (task_id,), fetch=True)
    
    uploaded_papers = []
    citations = []
    
    # Parse paper metadata if present in state/reports
    for row in report_rows:
        summary_str = row.get("section_summary")
        if summary_str:
            try:
                summary = json.loads(summary_str) if isinstance(summary_str, str) else summary_str
                metadata_str = summary.get("metadata")
                if metadata_str:
                    meta = json.loads(metadata_str) if isinstance(metadata_str, str) else metadata_str
                    title = meta.get("title", "Uploaded Paper")
                    uploaded_papers.append(title)
                    citations.extend(meta.get("citations_extracted", []))
            except Exception as e:
                print(f"[Citation Graph] Failed to parse metadata from report: {e}")
                
    # If no uploaded papers, look for uploaded file name
    if not uploaded_papers:
        uploaded_papers = ["Local Paper Context"]
        
    for paper in uploaded_papers:
        G.add_node(paper, label=paper, type="uploaded", val=0.8)
        G.add_edge(topic, paper, relationship="focus")
        
    # 3. Add extracted reference citations as nodes/links
    for i, ref in enumerate(citations[:20]):  # Limit to 20 for layout readability
        ref_label = ref[:60] + "..." if len(ref) > 60 else ref
        G.add_node(ref, label=ref_label, type="reference", val=0.5)
        for paper in uploaded_papers:
            G.add_edge(paper, ref, relationship="cites")
            
    # Calculate centrality to scale node circles in frontend
    try:
        if len(G) > 1:
            centrality = nx.degree_centrality(G)
        else:
            centrality = {n: 1.0 for n in G.nodes}
    except Exception:
        centrality = {n: 0.5 for n in G.nodes}
        
    nodes = []
    for node, attrs in G.nodes(data=True):
        nodes.append({
            "id": node,
            "label": attrs.get("label", node),
            "type": attrs.get("type", "reference"),
            "centrality": round(centrality.get(node, 0.1) * 10, 2)
        })
        
    links = []
    for u, v, attrs in G.edges(data=True):
        links.append({
            "source": u,
            "target": v,
            "value": 1,
            "relationship": attrs.get("relationship", "cites")
        })
        
    return {"nodes": nodes, "links": links}
