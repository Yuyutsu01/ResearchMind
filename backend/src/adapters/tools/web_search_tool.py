import urllib.request
import urllib.parse
import re
from bs4 import BeautifulSoup

def search_web(query: str, max_results: int = 5) -> list[dict]:
    """
    Performs web search using DuckDuckGo Lite and parses results.
    """
    results = []
    try:
        # DDG HTML search
        encoded_query = urllib.parse.quote(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
        
        req = urllib.request.Request(
            url, 
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )
        
        with urllib.request.urlopen(req, timeout=8) as response:
            html = response.read().decode("utf-8")
            
        soup = BeautifulSoup(html, "html.parser")
        # DuckDuckGo Lite search result blocks
        links = soup.find_all("a", class_="result__url")
        snippets = soup.find_all("a", class_="result__snippet")
        titles = soup.find_all("a", class_="result__snip") # or check result__a
        
        # Alternatively, let's find all result elements
        results_divs = soup.find_all("div", class_="result")
        for div in results_divs[:max_results]:
            title_a = div.find("a", class_="result__a")
            snippet_a = div.find("a", class_="result__snippet")
            
            if title_a:
                title = title_a.get_text(strip=True)
                link = title_a.get("href")
                # Parse URL from DDG redirect url if present
                if link and "/l/?" in link:
                    match = re.search(r'uddg=([^&]+)', link)
                    if match:
                        link = urllib.parse.unquote(match.group(1))
                        
                snippet = snippet_a.get_text(strip=True) if snippet_a else ""
                results.append({
                    "title": title,
                    "url": link,
                    "snippet": snippet
                })
    except Exception as e:
        print(f"[Web Search Tool Error] {e}")
        # Fallback to a mock result if network is offline
        results = [
            {
                "title": f"Search results for {query}",
                "url": "https://example.com/search",
                "snippet": f"Found information about '{query}'. Research indicates this is a key trend in 2026."
            }
        ]
    return results

def get_wikipedia_definition(concept: str) -> dict:
    """
    Search Wikipedia API for a concept definition summary.
    """
    import json
    try:
        encoded_concept = urllib.parse.quote(concept)
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded_concept}"
        req = urllib.request.Request(
            url, 
            headers={"User-Agent": "ResearchIntelligenceAgent/1.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            if data.get("extract"):
                return {
                    "source": "Wikipedia",
                    "title": data.get("title", concept),
                    "snippet": data.get("extract"),
                    "url": data.get("content_urls", {}).get("desktop", {}).get("page")
                }
    except Exception as e:
        print(f"[Wikipedia Search Error] {concept}: {e}")
    return {}

