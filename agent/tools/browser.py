"""
GLTCH Browser Automation Tool
Web browsing, form filling, and data extraction using Playwright.
"""

import asyncio
import json
import base64
from typing import Dict, Any, Optional, List

# Lazy import to avoid dependency issues if playwright not installed
playwright_available = False
try:
    from playwright.async_api import async_playwright, Browser, Page
    playwright_available = True
except ImportError:
    pass


class BrowserTool:
    """Browser automation using Playwright."""
    
    def __init__(self):
        self._browser: Optional[Any] = None
        self._page: Optional[Any] = None
        self._playwright = None
    
    async def _ensure_browser(self) -> bool:
        """Ensure browser is running."""
        if not playwright_available:
            return False
        
        if self._browser is None:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=True)
            self._page = await self._browser.new_page()
        return True
    
    async def close(self):
        """Close browser."""
        if self._browser:
            await self._browser.close()
            self._browser = None
            self._page = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
    
    async def browse(self, url: str) -> Dict[str, Any]:
        """Navigate to URL and extract content."""
        if not await self._ensure_browser():
            return {"success": False, "error": "Playwright not installed. Run: pip install playwright && playwright install chromium"}
        
        try:
            await self._page.goto(url, timeout=30000)
            await self._page.wait_for_load_state("domcontentloaded")
            
            # Extract page info
            title = await self._page.title()
            url_final = self._page.url
            
            # Get text content
            text = await self._page.evaluate("""
                () => {
                    const elements = document.querySelectorAll('h1, h2, h3, p, li, td, th, span, a');
                    const texts = [];
                    elements.forEach(el => {
                        const text = el.innerText?.trim();
                        if (text && text.length > 0 && text.length < 500) {
                            texts.push(text);
                        }
                    });
                    return [...new Set(texts)].slice(0, 100).join('\\n');
                }
            """)
            
            return {
                "success": True,
                "title": title,
                "url": url_final,
                "content": text[:5000],  # Limit content size
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def screenshot(self, url: str) -> Dict[str, Any]:
        """Take screenshot of URL."""
        if not await self._ensure_browser():
            return {"success": False, "error": "Playwright not installed"}
        
        try:
            await self._page.goto(url, timeout=30000)
            await self._page.wait_for_load_state("networkidle", timeout=10000)
            
            # Take screenshot
            screenshot_bytes = await self._page.screenshot(full_page=False)
            screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            return {
                "success": True,
                "url": self._page.url,
                "screenshot_base64": screenshot_b64,
                "format": "png"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def extract(self, url: str, selector: str) -> Dict[str, Any]:
        """Extract elements matching CSS selector."""
        if not await self._ensure_browser():
            return {"success": False, "error": "Playwright not installed"}
        
        try:
            await self._page.goto(url, timeout=30000)
            await self._page.wait_for_load_state("domcontentloaded")
            
            # Extract matching elements
            elements = await self._page.query_selector_all(selector)
            results = []
            for el in elements[:50]:  # Limit results
                text = await el.inner_text()
                href = await el.get_attribute("href")
                results.append({
                    "text": text.strip() if text else "",
                    "href": href
                })
            
            return {
                "success": True,
                "url": self._page.url,
                "selector": selector,
                "count": len(results),
                "elements": results
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def fill_form(self, url: str, fields: Dict[str, str], submit_selector: Optional[str] = None) -> Dict[str, Any]:
        """Fill form fields and optionally submit."""
        if not await self._ensure_browser():
            return {"success": False, "error": "Playwright not installed"}
        
        try:
            await self._page.goto(url, timeout=30000)
            await self._page.wait_for_load_state("domcontentloaded")
            
            # Fill each field
            for selector, value in fields.items():
                await self._page.fill(selector, value)
            
            # Submit if selector provided
            if submit_selector:
                await self._page.click(submit_selector)
                await self._page.wait_for_load_state("networkidle", timeout=10000)
            
            return {
                "success": True,
                "url": self._page.url,
                "fields_filled": list(fields.keys())
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


# Singleton instance
_browser_tool: Optional[BrowserTool] = None


def get_browser_tool() -> BrowserTool:
    """Get or create browser tool instance."""
    global _browser_tool
    if _browser_tool is None:
        _browser_tool = BrowserTool()
    return _browser_tool


# Synchronous wrappers for CLI use
def browse_url(url: str) -> Dict[str, Any]:
    """Browse URL and extract content (sync wrapper)."""
    tool = get_browser_tool()
    return asyncio.get_event_loop().run_until_complete(tool.browse(url))


def take_screenshot(url: str) -> Dict[str, Any]:
    """Take screenshot of URL (sync wrapper)."""
    tool = get_browser_tool()
    return asyncio.get_event_loop().run_until_complete(tool.screenshot(url))


def extract_data(url: str, selector: str) -> Dict[str, Any]:
    """Extract data from URL using selector (sync wrapper)."""
    tool = get_browser_tool()
    return asyncio.get_event_loop().run_until_complete(tool.extract(url, selector))


def fill_and_submit(url: str, fields: Dict[str, str], submit: Optional[str] = None) -> Dict[str, Any]:
    """Fill form and submit (sync wrapper)."""
    tool = get_browser_tool()
    return asyncio.get_event_loop().run_until_complete(tool.fill_form(url, fields, submit))
