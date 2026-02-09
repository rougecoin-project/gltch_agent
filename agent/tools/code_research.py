"""
GLTCH Code Research Module
Automatically researches coding topics before sending to OpenCode.
Searches web for docs, scans local references, and bundles context.
"""

import os
import re
import json
import time
import hashlib
from typing import List, Dict, Optional
from pathlib import Path

from agent.config.settings import DATA_DIR


# === Config ===
REFERENCES_DIR = os.path.join(DATA_DIR, "references")
CACHE_DIR = os.path.join(DATA_DIR, "research_cache")
CACHE_TTL = 86400  # 24 hours
MAX_WEB_SEARCHES = 3
MAX_PAGES_FETCHED = 2
MAX_CONTEXT_CHARS = 6000  # Keep total context reasonable for LLM

# Tech stopwords — filter these from keyword extraction
STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "can", "shall", "to", "of", "in", "for",
    "on", "with", "at", "by", "from", "as", "into", "about", "between",
    "through", "during", "before", "after", "above", "below", "and", "but",
    "or", "nor", "not", "so", "yet", "both", "either", "neither", "each",
    "every", "all", "any", "few", "more", "most", "some", "such", "no",
    "only", "own", "same", "than", "too", "very", "just",
    # Coding-generic words (not useful for doc search)
    "build", "create", "make", "write", "code", "implement", "add",
    "use", "using", "app", "application", "project", "file", "function",
    "class", "method", "get", "set", "update", "delete", "new", "simple",
    "basic", "full", "complete", "working", "good", "best", "me", "my",
    "i", "want", "need", "please", "help", "how", "what", "that", "this",
    "it", "like", "also", "then", "now", "here", "there",
}

# Prefer official doc sites — these get priority when fetching pages
PRIORITY_DOMAINS = [
    "docs.python.org", "readthedocs.io", "fastapi.tiangolo.com",
    "flask.palletsprojects.com", "django-docs", "developer.mozilla.org",
    "nodejs.org/docs", "react.dev", "nextjs.org/docs", "vuejs.org",
    "docs.rs", "pkg.go.dev", "docs.oracle.com",
    "pypi.org", "npmjs.com", "github.com",
]


def extract_tech_keywords(prompt: str) -> List[str]:
    """
    Extract technical keywords from a coding prompt.
    Returns list of meaningful terms for documentation search.
    """
    # Normalize
    text = prompt.lower().strip()
    
    # Extract quoted strings first (these are intentional terms)
    quoted = re.findall(r'"([^"]+)"|\'([^\']+)\'', text)
    quoted_terms = [q[0] or q[1] for q in quoted]
    
    # Split on non-alphanumeric (keep hyphens for terms like "jwt-auth")
    words = re.findall(r'[a-z0-9][\w\-]*[a-z0-9]|[a-z0-9]+', text)
    
    # Filter stopwords and very short terms
    keywords = [w for w in words if w not in STOPWORDS and len(w) > 1]
    
    # Add back quoted terms (high priority)
    keywords = quoted_terms + keywords
    
    # Deduplicate while preserving order
    seen = set()
    unique = []
    for kw in keywords:
        if kw not in seen:
            seen.add(kw)
            unique.append(kw)
    
    return unique[:10]  # Cap at 10 keywords


def build_search_queries(keywords: List[str]) -> List[str]:
    """
    Build smart search queries from keywords.
    Combines related terms and appends 'documentation' or 'api reference'.
    """
    if not keywords:
        return []
    
    queries = []
    
    # Primary query: first 3 keywords + "documentation"
    primary = " ".join(keywords[:3])
    queries.append(f"{primary} documentation")
    
    # If there are framework/library names, search those specifically
    # Common patterns: "flask jwt", "react hooks", "fastapi websocket"
    if len(keywords) >= 2:
        queries.append(f"{keywords[0]} {keywords[1]} example tutorial")
    
    # Third query: specific API reference if we have enough keywords
    if len(keywords) >= 3:
        queries.append(f"{keywords[0]} {keywords[2]} api reference")
    
    return queries[:MAX_WEB_SEARCHES]


def _cache_key(query: str) -> str:
    """Generate a cache key for a search query."""
    return hashlib.md5(query.encode()).hexdigest()


def _get_cached(query: str) -> Optional[str]:
    """Check cache for previous research results."""
    try:
        cache_file = os.path.join(CACHE_DIR, f"{_cache_key(query)}.json")
        if not os.path.exists(cache_file):
            return None
        
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Check TTL
        if time.time() - data.get("timestamp", 0) > CACHE_TTL:
            os.remove(cache_file)
            return None
        
        return data.get("content", "")
    except Exception:
        return None


def _set_cache(query: str, content: str) -> None:
    """Cache research results."""
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        cache_file = os.path.join(CACHE_DIR, f"{_cache_key(query)}.json")
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump({
                "query": query,
                "timestamp": time.time(),
                "content": content
            }, f)
    except Exception:
        pass


def scan_local_references(keywords: List[str]) -> str:
    """
    Scan ~/.gltch/references/ for matching markdown/text docs.
    Returns concatenated content from matching files.
    """
    if not os.path.exists(REFERENCES_DIR):
        return ""
    
    matches = []
    keywords_lower = {kw.lower() for kw in keywords}
    
    try:
        for fname in os.listdir(REFERENCES_DIR):
            if not fname.endswith((".md", ".txt", ".rst")):
                continue
            
            fname_lower = fname.lower()
            # Check if any keyword appears in filename
            if any(kw in fname_lower for kw in keywords_lower):
                filepath = os.path.join(REFERENCES_DIR, fname)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                    # Truncate long files
                    if len(content) > 2000:
                        content = content[:2000] + "\n... (truncated)"
                    matches.append(f"### Local: {fname}\n{content}")
                except Exception:
                    continue
    except Exception:
        pass
    
    return "\n\n".join(matches)


def search_web_for_docs(queries: List[str]) -> str:
    """
    Search the web for coding documentation.
    Uses GLTCH's existing web_search tool.
    Returns formatted doc snippets.
    """
    try:
        from agent.tools.web_search import web_search, _fetch_page_text
    except ImportError:
        return ""
    
    all_results = []
    fetched_urls = set()
    pages_fetched = 0
    
    for query in queries:
        # Check cache first
        cached = _get_cached(query)
        if cached:
            all_results.append(cached)
            continue
        
        try:
            result = web_search(query, num_results=5)
            if not result.get("success"):
                continue
            
            search_results = result.get("results", [])
            query_content = []
            
            # Sort results: prioritize official doc sites
            def domain_priority(r):
                url = r.get("url", "").lower()
                for i, domain in enumerate(PRIORITY_DOMAINS):
                    if domain in url:
                        return i
                return len(PRIORITY_DOMAINS)
            
            search_results.sort(key=domain_priority)
            
            for sr in search_results[:3]:
                title = sr.get("title", "")
                url = sr.get("url", "")
                snippet = sr.get("snippet", "")
                
                # Always include the snippet
                query_content.append(f"**{title}**\n{snippet}")
                
                # Fetch full page for top priority results (if within budget)
                if pages_fetched < MAX_PAGES_FETCHED and url not in fetched_urls:
                    is_priority = any(d in url.lower() for d in PRIORITY_DOMAINS)
                    if is_priority:
                        page_text = _fetch_page_text(url, max_chars=1500)
                        if page_text and len(page_text) > 100:
                            query_content.append(f"Content from {url}:\n{page_text}")
                            fetched_urls.add(url)
                            pages_fetched += 1
            
            if query_content:
                section = f"### Search: {query}\n" + "\n\n".join(query_content)
                all_results.append(section)
                _set_cache(query, section)
        
        except Exception:
            continue
    
    return "\n\n".join(all_results)


def research_for_coding(prompt: str) -> str:
    """
    Main entry point: research coding topics before sending to OpenCode.
    
    1. Extract tech keywords from prompt
    2. Search web for relevant documentation  
    3. Scan local reference docs
    4. Bundle and return formatted context
    
    Returns formatted context string, or empty string if no useful context found.
    """
    # Extract keywords
    keywords = extract_tech_keywords(prompt)
    if not keywords:
        return ""
    
    context_parts = []
    
    # 1. Local references (fast, always check)
    local_docs = scan_local_references(keywords)
    if local_docs:
        context_parts.append(f"## Local Reference Docs\n{local_docs}")
    
    # 2. Web research (slower, requires network)
    queries = build_search_queries(keywords)
    if queries:
        web_docs = search_web_for_docs(queries)
        if web_docs:
            context_parts.append(f"## Web Documentation\n{web_docs}")
    
    if not context_parts:
        return ""
    
    # Bundle context
    context = "# RESEARCH CONTEXT\n" + \
              "The following documentation was gathered to help with this coding task.\n" + \
              "Use these as reference — prefer official docs over snippets.\n\n" + \
              "\n\n---\n\n".join(context_parts)
    
    # Truncate if too long
    if len(context) > MAX_CONTEXT_CHARS:
        context = context[:MAX_CONTEXT_CHARS] + "\n\n... (research truncated for context limit)"
    
    return context


def clear_cache() -> int:
    """Clear the research cache. Returns number of files removed."""
    if not os.path.exists(CACHE_DIR):
        return 0
    
    count = 0
    for f in os.listdir(CACHE_DIR):
        try:
            os.remove(os.path.join(CACHE_DIR, f))
            count += 1
        except Exception:
            pass
    return count
