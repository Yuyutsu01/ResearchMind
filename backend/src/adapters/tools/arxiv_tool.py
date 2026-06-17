import urllib.request
import urllib.parse
import json
import arxiv

def search_arxiv(query: str, max_results: int = 5) -> list[dict]:
    """
    Search Arxiv for relevant research papers.
    """
    results = []
    try:
        client = arxiv.Client()
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )
        for r in client.results(search):
            results.append({
                "source": "arxiv",
                "id": r.entry_id.split("/abs/")[-1].split("v")[0],
                "title": r.title,
                "authors": [a.name for a in r.authors],
                "abstract": r.summary,
                "published": r.published.strftime("%Y-%m-%d"),
                "pdf_url": r.pdf_url,
                "url": r.entry_id
            })
    except Exception as e:
        print(f"[ArXiv Tool Error] {e}")
    return results

def search_semantic_scholar(query: str, limit: int = 5) -> list[dict]:
    """
    Search Semantic Scholar for related research papers.
    """
    results = []
    try:
        encoded_query = urllib.parse.quote(query)
        # Query free public API endpoint
        url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={encoded_query}&limit={limit}&fields=title,authors,abstract,year,citationCount,url"
        
        req = urllib.request.Request(
            url, 
            headers={"User-Agent": "ResearchIntelligenceAgent/1.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            for item in data.get("data", []):
                authors = [a.get("name") for a in item.get("authors", []) if a.get("name")]
                results.append({
                    "source": "semantic_scholar",
                    "id": item.get("paperId"),
                    "title": item.get("title"),
                    "authors": authors,
                    "abstract": item.get("abstract") or "No abstract available.",
                    "published": str(item.get("year", "N/A")),
                    "url": item.get("url"),
                    "citation_count": item.get("citationCount", 0)
                })
    except Exception as e:
        print(f"[Semantic Scholar Error] {e}")
    return results
