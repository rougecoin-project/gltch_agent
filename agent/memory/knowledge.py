"""
GLTCH Knowledge Base
File-based knowledge storage for persistent information.
"""

import os
from datetime import datetime
from typing import List, Optional


class KnowledgeBase:
    """
    File-based knowledge base for storing and retrieving information.
    Each topic is stored as a separate text file.
    """
    
    def __init__(self, kb_dir: str = "kb"):
        self.kb_dir = kb_dir
        os.makedirs(kb_dir, exist_ok=True)
    
    def _safe_title(self, title: str) -> str:
        """Sanitize title for use as filename."""
        return title.strip().replace("/", "-").replace("\\", "-")
    
    def _file_path(self, title: str) -> str:
        """Get the file path for a KB entry."""
        return os.path.join(self.kb_dir, f"{self._safe_title(title)}.txt")
    
    def add(self, title: str, text: str) -> str:
        """Add or append to a KB entry."""
        title = self._safe_title(title)
        text = text.strip()
        
        if not title or not text:
            raise ValueError("Title and text are required")
        
        path = self._file_path(title)
        timestamp = datetime.now().isoformat(timespec="seconds")
        
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {text}\n")
        
        return path
    
    def read(self, title: str) -> Optional[str]:
        """Read a KB entry."""
        path = self._file_path(title)
        if not os.path.exists(path):
            return None
        
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    
    def delete(self, title: str) -> bool:
        """Delete a KB entry."""
        path = self._file_path(title)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False
    
    def list(self) -> List[str]:
        """List all KB entries."""
        if not os.path.exists(self.kb_dir):
            return []
        
        entries = []
        for filename in sorted(os.listdir(self.kb_dir)):
            if filename.endswith(".txt"):
                entries.append(filename[:-4])  # Remove .txt extension
        return entries
    
    def search(self, keyword: str) -> List[dict]:
        """Search KB entries for a keyword."""
        keyword = keyword.lower()
        results = []
        
        if not os.path.exists(self.kb_dir):
            return results
        
        for filename in os.listdir(self.kb_dir):
            if not filename.endswith(".txt"):
                continue
            
            path = os.path.join(self.kb_dir, filename)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    for line in f:
                        if keyword in line.lower():
                            results.append({
                                "source": f"kb:{filename[:-4]}",
                                "line": line.strip()
                            })
            except Exception:
                continue
        
        return results
