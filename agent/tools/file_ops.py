"""
GLTCH File Operations
Safe file read/write operations with guards.
"""

import os
import re as _re
import glob as _glob
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


def file_read(filepath: str, start_line: int = None, end_line: int = None) -> Tuple[bool, str]:
    """
    Read a file's contents, optionally a specific line range (1-indexed, inclusive).
    e.g. file_read("foo.py", 50, 100) reads lines 50–100.

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
            if start_line is None and end_line is None:
                content = f.read()
                total = content.count('\n') + 1
                return True, f"[{filepath} — {total} lines]\n{content}"
            else:
                lines = f.readlines()
                total = len(lines)
                s = max(1, start_line or 1) - 1
                e = min(total, end_line or total)
                selected = lines[s:e]
                header = f"[{filepath} — lines {s+1}–{e} of {total}]\n"
                return True, header + "".join(selected)
    except Exception as ex:
        return False, f"Read failed: {ex}"


def file_delete(path: str) -> Tuple[bool, str]:
    """
    Delete a file or empty directory.

    Returns:
        (success, message)
    """
    path = path.strip()
    if not path:
        return False, "No path provided"

    if not os.path.exists(path):
        return False, f"Not found: {path}"

    try:
        if os.path.isdir(path):
            os.rmdir(path)
            return True, f"✓ deleted directory: {path}"
        else:
            os.remove(path)
            return True, f"✓ deleted: {path}"
    except Exception as ex:
        return False, f"Delete failed: {ex}"


def file_move(src: str, dst: str) -> Tuple[bool, str]:
    """
    Move or rename a file/directory.

    Returns:
        (success, message)
    """
    import shutil
    src = src.strip()
    dst = dst.strip()
    if not src or not dst:
        return False, "Both src and dst required"

    if not os.path.exists(src):
        return False, f"Source not found: {src}"

    try:
        parent = os.path.dirname(dst)
        if parent:
            os.makedirs(parent, exist_ok=True)
        shutil.move(src, dst)
        return True, f"✓ moved: {src} → {dst}"
    except Exception as ex:
        return False, f"Move failed: {ex}"


def file_edit(filepath: str, old_str: str, new_str: str, replace_all: bool = False) -> Tuple[bool, str]:
    """
    Find and replace an exact string in a file (like Claude Code's Edit tool).
    With replace_all=False (default): fails if string not found or appears more than once.
    With replace_all=True: replaces every occurrence.
    On failure, returns the file content snippet so the LLM can self-correct.

    Returns:
        (success, message)
    """
    filepath = filepath.strip()
    if not filepath:
        return False, "No filepath provided"

    success, content = file_read(filepath)
    if not success:
        return False, content

    if old_str not in content:
        # Return a snippet of the file so the LLM can see what's actually there
        preview_lines = content.splitlines()[:40]
        preview = "\n".join(preview_lines)
        return False, (
            f"String not found in {filepath} (whitespace/indentation must be exact).\n"
            f"File preview (first 40 lines):\n{preview}"
        )

    count = content.count(old_str)
    if count > 1 and not replace_all:
        return False, (
            f"String found {count} times in {filepath} — add more surrounding context "
            f"to make it unique, or use [ACTION:edit_all|...] to replace all occurrences"
        )

    if replace_all:
        new_content = content.replace(old_str, new_str)
        replaced = count
    else:
        new_content = content.replace(old_str, new_str, 1)
        replaced = 1

    ok, msg = file_write(filepath, new_content)
    if ok:
        return True, f"Edited {filepath} ({replaced} replacement{'s' if replaced != 1 else ''})"
    return False, msg


def file_grep(pattern: str, path: str = ".", max_results: int = 50) -> Tuple[bool, List[dict]]:
    """
    Search file contents with a regex pattern (like Claude Code's Grep tool).
    Skips binary files, hidden dirs, venvs, and __pycache__.

    Returns:
        (success, list_of_matches) where each match is {file, line, content}
    """
    path = path.strip() or "."

    if not os.path.exists(path):
        return False, [{"file": "", "line": 0, "content": f"Path not found: {path}"}]

    try:
        regex = _re.compile(pattern, _re.IGNORECASE)
    except _re.error as e:
        return False, [{"file": "", "line": 0, "content": f"Invalid regex: {e}"}]

    matches = []
    _SKIP_DIRS = {'.venv', 'venv', '__pycache__', 'node_modules', '.git', 'dist', 'build', '.mypy_cache'}
    _TEXT_EXTS = {
        '.py', '.js', '.ts', '.jsx', '.tsx', '.json', '.txt', '.md', '.sh',
        '.yaml', '.yml', '.toml', '.cfg', '.ini', '.env', '.html', '.css',
        '.rs', '.go', '.java', '.c', '.cpp', '.h', '.rb', '.php', '.cs'
    }

    def search_file(fpath):
        try:
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                for line_num, line in enumerate(f, 1):
                    if regex.search(line):
                        matches.append({"file": fpath, "line": line_num, "content": line.rstrip()})
                        if len(matches) >= max_results:
                            return
        except Exception:
            pass

    if os.path.isfile(path):
        search_file(path)
    else:
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if d not in _SKIP_DIRS and not d.startswith('.')]
            for fname in files:
                if os.path.splitext(fname)[1].lower() in _TEXT_EXTS:
                    search_file(os.path.join(root, fname))
                    if len(matches) >= max_results:
                        break
            if len(matches) >= max_results:
                break

    return True, matches


def file_glob(pattern: str, path: str = ".") -> Tuple[bool, List[str]]:
    """
    Find files matching a glob pattern (like Claude Code's Glob tool).
    Supports ** for recursive matching (e.g. **/*.py).

    Returns:
        (success, list_of_paths)
    """
    pattern = pattern.strip()
    path = path.strip() or "."

    if not pattern:
        return False, []

    _SKIP = {'.venv', 'venv', '__pycache__', 'node_modules', '.git'}

    try:
        if os.path.isabs(pattern) or pattern.startswith('**'):
            results = _glob.glob(pattern, recursive=True)
        else:
            results = _glob.glob(os.path.join(path, "**", pattern), recursive=True)
            if not results:
                results = _glob.glob(os.path.join(path, pattern), recursive=True)

        filtered = [
            r for r in results
            if not any(skip in r.replace('\\', '/').split('/') for skip in _SKIP)
        ]
        return True, sorted(filtered)[:100]
    except Exception as e:
        return False, [str(e)]


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
