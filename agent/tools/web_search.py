"""
GLTCH Web Search Tool
Multi-strategy web search - no API key required.
1. DuckDuckGo Instant Answer API (for quick facts)
2. DuckDuckGo HTML search (for general queries)
3. Brave Search fallback
Falls back gracefully if network is offline.
"""

import urllib.request
import urllib.parse
import urllib.error
import json
import re
import html as html_module
from typing import List, Dict, Any


def web_search(query: str, num_results: int = 5) -> Dict[str, Any]:
    """
    Search the web using multiple strategies.
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
    results = []
    answer = ""
    
    # Special handler: Weather queries → use wttr.in for real data
    weather_match = re.search(r'weather\s+(?:in\s+)?(.+)', query, re.IGNORECASE)
    if not weather_match:
        weather_match = re.search(r'(?:temperature|forecast|rain|snow)\s+(?:in\s+)?(.+)', query, re.IGNORECASE)
    
    if weather_match:
        location = weather_match.group(1).strip().rstrip('?.')
        weather_data = _get_weather(location)
        if weather_data:
            answer = weather_data
            results.append({
                "title": f"Weather in {location}",
                "url": f"https://wttr.in/{urllib.parse.quote(location)}",
                "snippet": weather_data
            })
            # Return early with real weather data
            formatted = _format_results(query, results, answer)
            return {
                "success": True,
                "query": query,
                "results": results,
                "answer": answer,
                "formatted": formatted
            }
    
    # Strategy 1: DuckDuckGo Instant Answer API (fast, good for definitions)
    try:
        api_results, api_answer = _ddg_instant_answer(query)
        results.extend(api_results)
        if api_answer:
            answer = api_answer
    except Exception:
        pass
    
    # Strategy 2: DuckDuckGo HTML search (general web results)
    if len(results) < 2:
        try:
            html_results = _ddg_html_search(query, num_results)
            # Avoid duplicates
            existing_urls = {r["url"] for r in results}
            for r in html_results:
                if r["url"] not in existing_urls:
                    results.append(r)
                    existing_urls.add(r["url"])
        except Exception:
            pass
    
    # Strategy 3: Brave Search (another free option)
    if len(results) < 2:
        try:
            brave_results = _brave_html_search(query, num_results)
            existing_urls = {r["url"] for r in results}
            for r in brave_results:
                if r["url"] not in existing_urls:
                    results.append(r)
        except Exception:
            pass
    
    # If we have results but no answer, try to fetch content from first result
    if results and not answer:
        try:
            first_url = results[0].get("url", "")
            if first_url and not any(x in first_url for x in ['youtube.com', 'twitter.com', 'reddit.com']):
                content = _fetch_page_text(first_url)
                if content:
                    answer = content[:500]
                    results[0]["snippet"] = content[:200]
        except Exception:
            pass
    
    # Determine success
    success = len(results) > 0 or bool(answer)
    formatted = _format_results(query, results[:num_results], answer)
    
    return {
        "success": success,
        "query": query,
        "results": results[:num_results],
        "answer": answer,
        "formatted": formatted
    }


def _ddg_instant_answer(query: str):
    """DuckDuckGo Instant Answer API - good for Wikipedia-type lookups."""
    encoded_q = urllib.parse.quote_plus(query)
    api_url = f"https://api.duckduckgo.com/?q={encoded_q}&format=json&no_redirect=1&no_html=1"
    
    req = urllib.request.Request(api_url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    
    with urllib.request.urlopen(req, timeout=8) as response:
        data = json.loads(response.read().decode())
    
    results = []
    answer = ""
    
    if data.get("AbstractText"):
        answer = data["AbstractText"]
        if data.get("AbstractURL"):
            results.append({
                "title": data.get("AbstractSource", "Wikipedia"),
                "url": data["AbstractURL"],
                "snippet": data["AbstractText"][:200]
            })
    
    # Check Answer field (calculator, conversions, etc.)
    if data.get("Answer"):
        answer = str(data["Answer"])
    
    # Related topics
    for topic in data.get("RelatedTopics", [])[:3]:
        if isinstance(topic, dict) and topic.get("Text"):
            results.append({
                "title": topic.get("Text", "")[:80],
                "url": topic.get("FirstURL", ""),
                "snippet": topic.get("Text", "")[:200]
            })
    
    return results, answer


def _ddg_html_search(query: str, num_results: int = 5) -> List[Dict[str, str]]:
    """Scrape DuckDuckGo HTML version for real search results."""
    encoded_q = urllib.parse.quote_plus(query)
    url = f"https://html.duckduckgo.com/html/?q={encoded_q}"
    
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    })
    
    with urllib.request.urlopen(req, timeout=10) as response:
        raw_html = response.read().decode('utf-8', errors='replace')
    
    results = []
    
    # DuckDuckGo HTML results have this structure:
    # <a rel="nofollow" class="result__a" href="...">Title</a>
    # <a class="result__snippet" href="...">Snippet text</a>
    
    # Extract result blocks
    result_blocks = re.findall(
        r'<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>.*?'
        r'(?:<a[^>]*class="result__snippet"[^>]*>(.*?)</a>)?',
        raw_html, re.DOTALL
    )
    
    for href, title_html, snippet_html in result_blocks[:num_results]:
        # Clean up the URL (DDG wraps in redirect)
        actual_url = href
        if 'uddg=' in href:
            url_match = re.search(r'uddg=([^&]+)', href)
            if url_match:
                actual_url = urllib.parse.unquote(url_match.group(1))
        
        # Clean HTML from title and snippet
        title = _strip_html(title_html).strip()
        snippet = _strip_html(snippet_html).strip() if snippet_html else ""
        
        if title and actual_url.startswith('http'):
            results.append({
                "title": title[:80],
                "url": actual_url,
                "snippet": snippet[:200]
            })
    
    # Fallback: try a simpler pattern if the above didn't work
    if not results:
        # Try matching any href with nofollow
        links = re.findall(r'<a[^>]+rel="nofollow"[^>]*href="(https?://[^"]+)"[^>]*>(.*?)</a>', raw_html)
        for href, title_html in links[:num_results]:
            if 'duckduckgo.com' not in href:
                title = _strip_html(title_html).strip()
                if title:
                    results.append({
                        "title": title[:80],
                        "url": href,
                        "snippet": ""
                    })
    
    return results


def _brave_html_search(query: str, num_results: int = 5) -> List[Dict[str, str]]:
    """Scrape Brave Search as fallback."""
    try:
        encoded_q = urllib.parse.quote_plus(query)
        url = f"https://search.brave.com/search?q={encoded_q}"
        
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html",
        })
        
        with urllib.request.urlopen(req, timeout=10) as response:
            raw_html = response.read().decode('utf-8', errors='replace')
        
        results = []
        
        # Brave has structured result blocks
        # Look for snippet divs with data-pos attribute
        snippets = re.findall(
            r'<a[^>]*href="(https?://[^"]+)"[^>]*>.*?<span[^>]*class="[^"]*snippet-title[^"]*"[^>]*>(.*?)</span>.*?'
            r'(?:<p[^>]*class="[^"]*snippet-description[^"]*"[^>]*>(.*?)</p>)?',
            raw_html, re.DOTALL
        )
        
        for href, title_html, desc_html in snippets[:num_results]:
            title = _strip_html(title_html).strip()
            desc = _strip_html(desc_html).strip() if desc_html else ""
            if title and 'brave.com' not in href:
                results.append({
                    "title": title[:80],
                    "url": href,
                    "snippet": desc[:200]
                })
        
        return results
    except Exception:
        return []


def _strip_html(text: str) -> str:
    """Remove HTML tags and decode entities."""
    if not text:
        return ""
    # Remove tags
    clean = re.sub(r'<[^>]+>', '', text)
    # Decode HTML entities
    clean = html_module.unescape(clean)
    # Normalize whitespace
    clean = re.sub(r'\s+', ' ', clean)
    return clean


def _get_weather(location: str) -> str:
    """Get real weather data from wttr.in (free, no API key)."""
    try:
        safe_loc = urllib.parse.quote(location)
        # Format: location: condition, temp
        url = f"https://wttr.in/{safe_loc}?format=%l:+%C+%t+%h+humidity+wind+%w"
        
        req = urllib.request.Request(url, headers={
            "User-Agent": "GLTCH-Agent/0.2",
            "Accept": "text/plain"
        })
        
        with urllib.request.urlopen(req, timeout=8) as response:
            data = response.read().decode('utf-8', errors='replace').strip()
        
        if data and 'Unknown' not in data and 'Sorry' not in data:
            # Also get 3-day forecast summary
            try:
                url2 = f"https://wttr.in/{safe_loc}?format=%l:+%C+%t+|+Feels+like+%f+|+Humidity+%h+|+Wind+%w+|+UV+%u+|+Sunrise+%S+Sunset+%s"
                req2 = urllib.request.Request(url2, headers={
                    "User-Agent": "GLTCH-Agent/0.2",
                    "Accept": "text/plain"
                })
                with urllib.request.urlopen(req2, timeout=5) as response2:
                    detailed = response2.read().decode('utf-8', errors='replace').strip()
                if detailed and 'Unknown' not in detailed:
                    return detailed
            except Exception:
                pass
            return data
        
        return ""
    except Exception:
        return ""


def _fetch_page_text(url: str, max_chars: int = 1000) -> str:
    """Fetch and extract main text content from a web page."""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html"
        })
        
        with urllib.request.urlopen(req, timeout=8) as response:
            html = response.read().decode('utf-8', errors='replace')
        
        # Remove script and style blocks
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<nav[^>]*>.*?</nav>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<header[^>]*>.*?</header>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<footer[^>]*>.*?</footer>', '', html, flags=re.DOTALL | re.IGNORECASE)
        
        # Strip tags
        text = _strip_html(html)
        
        # Clean up
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Return meaningful content (skip if too short)
        if len(text) > 50:
            return text[:max_chars]
        return ""
    except Exception:
        return ""


def _format_results(query: str, results: List[Dict], answer: str = "") -> str:
    """Format search results for GLTCH to read and summarize."""
    lines = [f"🔍 Search: {query}"]
    
    if answer:
        lines.append(f"\n📋 {answer[:400]}")
    
    if results:
        lines.append("")
        for i, r in enumerate(results[:5], 1):
            title = r.get("title", "No title")[:80]
            url = r.get("url", "")
            snippet = r.get("snippet", "")[:150]
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
    import sys
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "weather in miami"
    result = web_search(query)
    print(result["formatted"])
    print(f"\nSuccess: {result['success']}, Results: {len(result['results'])}")
