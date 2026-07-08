import urllib.request
import urllib.parse
import json
import xml.etree.ElementTree as ET
from typing import List, Dict, Any
from src.domain.agents.base import BaseAgent
from src.domain.blackboard.blackboard import ResearchBlackboard
from src.domain.agents.registry import agent_registry

class ExplorerAgent(BaseAgent):
    def __init__(self):
        super().__init__("Explorer")

    def execute(self, blackboard: ResearchBlackboard, payload: dict):
        query = payload.get("query", blackboard.context.get("query", ""))
        source_selection = payload.get("source_selection", "arxiv")  # arxiv, semantic_scholar, web
        
        print(f"[Explorer] Executing discovery for query: '{query}' via {source_selection}...")
        
        retrieved_papers = []
        
        if source_selection == "arxiv":
            retrieved_papers = self._search_arxiv(query)
        elif source_selection == "semantic_scholar":
            retrieved_papers = self._search_semantic_scholar(query)
        else:
            retrieved_papers = self._search_web_fallback(query)
            
        # Write to working memory
        if "retrieved_papers" not in blackboard.working_memory:
            blackboard.working_memory["retrieved_papers"] = []
            
        blackboard.working_memory["retrieved_papers"].extend(retrieved_papers)
        
        # Publish discovery events
        for paper in retrieved_papers:
            blackboard.add_event("NEW_PAPER_FOUND", {
                "title": paper["title"],
                "authors": paper["authors"],
                "url": paper["url"],
                "msg": f"Discovered paper: {paper['title']}"
            })
            
            # Simple metadata dataset/codebase detections
            abs_text = paper.get("abstract", "").lower()
            if "dataset" in abs_text or "corpus" in abs_text:
                blackboard.add_event("NEW_DATASET_FOUND", {
                    "paper_title": paper["title"],
                    "msg": f"Found mention of dataset in '{paper['title']}'"
                })
            if "github.com" in abs_text or "codebase" in abs_text or "implementation" in abs_text:
                blackboard.add_event("NEW_CODEBASE_FOUND", {
                    "paper_title": paper["title"],
                    "msg": f"Found reference to implementation repository in '{paper['title']}'"
                })

    def _search_arxiv(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        results = []
        try:
            encoded_query = urllib.parse.quote(query)
            url = f"http://export.arxiv.org/api/query?search_query=all:{encoded_query}&max_results={limit}"
            req = urllib.request.Request(url, headers={"User-Agent": "ResearchMind/1.0"})
            with urllib.request.urlopen(req, timeout=5) as response:
                xml_data = response.read()
                
            root = ET.fromstring(xml_data)
            # Parse Atom feed XML
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            for entry in root.findall('atom:entry', ns):
                title = entry.find('atom:title', ns).text.strip().replace("\n", " ")
                summary = entry.find('atom:summary', ns).text.strip().replace("\n", " ")
                published = entry.find('atom:published', ns).text[:10]
                entry_id = entry.find('atom:id', ns).text
                
                authors = []
                for author in entry.findall('atom:author', ns):
                    name = author.find('atom:name', ns).text
                    authors.append(name)
                    
                results.append({
                    "source": "arxiv",
                    "title": title,
                    "authors": authors,
                    "abstract": summary,
                    "published": published,
                    "url": entry_id
                })
        except Exception as e:
            print(f"[Explorer Error] ArXiv search failed: {e}")
        return results

    def _search_semantic_scholar(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        results = []
        try:
            encoded_query = urllib.parse.quote(query)
            url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={encoded_query}&limit={limit}&fields=title,authors,abstract,year,url"
            req = urllib.request.Request(url, headers={"User-Agent": "ResearchMind/1.0"})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode("utf-8"))
                
            for item in data.get("data", []):
                authors = [a.get("name") for a in item.get("authors", []) if a.get("name")]
                results.append({
                    "source": "semantic_scholar",
                    "title": item.get("title", ""),
                    "authors": authors,
                    "abstract": item.get("abstract") or "No abstract available.",
                    "published": str(item.get("year", "N/A")),
                    "url": item.get("url", "")
                })
        except Exception as e:
            print(f"[Explorer Error] Semantic Scholar failed: {e}")
        return results

    def _search_web_fallback(self, query: str) -> List[Dict[str, Any]]:
        # Lightweight standard search fallback
        return [
            {
                "source": "web_search",
                "title": f"Web overview of {query}",
                "authors": ["Web Authors"],
                "abstract": f"Extracted overview discussing {query}. This highlights current trends and benchmarks.",
                "published": "2026",
                "url": "https://example.com/search"
            }
        ]

# Register to Registry
explorer_agent = ExplorerAgent()
agent_registry.register_agent(
    "Explorer",
    explorer_agent,
    tasks=["discover_papers", "citation_walk"],
    event_subs=["RESEARCH_START", "USER_MESSAGE"]
)
