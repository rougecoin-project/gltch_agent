"""
GLTCH Web Search Tool
Lightweight DuckDuckGo search - no API key required.
Falls back gracefully if network is offline.
"""

import urllib.request
import urllib.parse
import urllib.error
import json
import re
from typing import List, Dict, Any


def web_search(query: str, num_results: int = 5) -> Dict[str, Any]:
    """
    Search the web using DuckDuckGo Instant Answer API + HTML scraping fallback.
    No API key needed.
    
    Returns:
        {
            "success": bool,
            "query": str,
            "results": [{"title": str, "url": str, "snippet": str}],
            "answer": str (if instant answer available),
            "formatted": str (human-readable summary)
        }
    """
    try:
        # Try DuckDuckGo Instant Answer API first
        encoded_q = urllib.parse.quote_plus(query)
        api_url = f"https://api.duckduckgo.com/?q={encoded_q}&format=json&no_redirect=1&no_html=1"
        
        req = urllib.request.Request(api_url, headers={
            "User-Agent": "GLTCH-Agent/0.2 (https://github.com/rougecoin-project/gltch_agent)"
        })
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
        
        results = []
        answer = ""
        
        # Check for instant answer
        if data.get("AbstractText"):
            answer = data["AbstractText"]
            if data.get("AbstractURL"):
                results.append({
                    "title": data.get("AbstractSource", "Wikipedia"),
                    "url": data["AbstractURL"],
                    "snippet": data["AbstractText"][:200]
                })
        
        # Related topics
        for topic in data.get("RelatedTopics", [])[:num_results]:
            if isinstance(topic, dict) and topic.get("Text"):
                url = topic.get("FirstURL", "")
                results.append({
                    "title": topic.get("Text", "")[:80],
                    "url": url,
                    "snippet": topic.get("Text", "")[:200]
                })
        
        # If no results from API, try HTML scraping
        if not results:
            results = _scrape_ddg_html(query, num_results)
        
        # Format readable output
        formatted = _format_results(query, results, answer)
        
        return {
            "success": True,
            "query": query,
            "results": results[:num_results],
            "answer": answer,
            "formatted": formatted
        }
        
    except Exception as e:
        return {
            "success": False,
            "query": query,
            "results": [],
            "answer": "",
            "formatted": f"Search failed: {str(e)}"
        }


def _scrape_ddg_html(query: str, num_results: int = 5) -> List[Dict[str, str]]:
    """Fallback: scrape DuckDuckGo HTML lite."""
    try:
        encoded_q = urllib.parse.quote_plus(query)
        url = f"https://lite.duckduckgo.com/lite/?q={encoded_q}"
        
        req = urllib.request.Request(url, headers={
            "User-Agent": "GLTCH-Agent/0.2"
        })
        
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='replace')
        
        results = []
        
        # Parse result links from HTML lite
        link_pattern = r'<a[^>]+rel="nofollow"[^>]+href="([^"]+)"[^>]*>([^<]+)</a>'
        snippet_pattern = r'<td[^>]*class="result-snippet"[^>]*>([^<]+)</td>'
        
        links = re.findall(link_pattern, html)
        snippets = re.findall(snippet_pattern, html)
        
        for i, (href, title) in enumerate(links[:num_results]):
            snippet = snippets[i].strip() if i < len(snippets) else ""
            if href.startswith('http') and 'duckduckgo.com' not in href:
                results.append({
                    "title": title.strip(),
                    "url": href,
                    "snippet": snippet[:200]
                })
        
        return results
        
    except Exception:
        return []


def _format_results(query: str, results: List[Dict], answer: str = "") -> str:
    """Format search results for terminal display."""
    lines = [f"🔍 Search: {query}"]
    
    if answer:
        lines.append(f"\n📋 {answer[:300]}")
    
    if results:
        lines.append("")
        for i, r in enumerate(results[:5], 1):
            title = r.get("title", "No title")[:60]
            url = r.get("url", "")
            snippet = r.get("snippet", "")[:100]
            lines.append(f"  {i}. {title}")
            if url:
                lines.append(f"     {url}")
            if snippet:
                lines.append(f"     {snippet}")
    else:
        lines.append("No results found.")
    
    return "\n".join(lines)


# Quick test
if __name__ == "__main__":
    result = web_search("python asyncio tutorial")
    print(result["formatted"])
