"""
GLTCH File Operations
Safe file read/write operations with guards.
"""

import os
from typing import Optional, List, Tuple


def file_write(filepath: str, content: str) -> Tuple[bool, str]:
    """
    Create or overwrite a file.
    
    Returns:
        (success, message)
    """
    filepath = filepath.strip()
    if not filepath:
        return False, "No filepath provided"
    
    try:
        parent = os.path.dirname(filepath)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return True, f"Written: {filepath} ({len(content)} bytes)"
    except Exception as e:
        return False, f"Write failed: {e}"


def file_append(filepath: str, content: str) -> Tuple[bool, str]:
    """
    Append to a file.
    
    Returns:
        (success, message)
    """
    filepath = filepath.strip()
    if not filepath:
        return False, "No filepath provided"
    
    try:
        parent = os.path.dirname(filepath)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(content + "\n")
        return True, f"Appended to: {filepath}"
    except Exception as e:
        return False, f"Append failed: {e}"


def file_read(filepath: str) -> Tuple[bool, str]:
    """
    Read a file's contents.
    
    Returns:
        (success, content_or_error)
    """
    filepath = filepath.strip()
    if not filepath:
        return False, "No filepath provided"
    
    if not os.path.exists(filepath):
        return False, f"File not found: {filepath}"
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return True, content
    except Exception as e:
        return False, f"Read failed: {e}"


def file_ls(path: str = ".") -> Tuple[bool, List[dict]]:
    """
    List directory contents.
    
    Returns:
        (success, list_of_entries_or_error)
    """
    path = path.strip() or "."
    
    if not os.path.exists(path):
        return False, f"Path not found: {path}"
    
    if not os.path.isdir(path):
        return False, f"Not a directory: {path}"
    
    try:
        entries = []
        for entry in sorted(os.listdir(path)):
            full_path = os.path.join(path, entry)
            is_dir = os.path.isdir(full_path)
            size = 0 if is_dir else os.path.getsize(full_path)
            entries.append({
                "name": entry,
                "is_dir": is_dir,
                "size": size
            })
        return True, entries
    except Exception as e:
        return False, f"ls failed: {e}"
