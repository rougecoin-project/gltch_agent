"""
GLTCH Background Daemon
Async background processing loop with file watchers, cron bridge, and event queue.
"""

import os
import time
import threading
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from queue import Queue, Empty


class EventType(Enum):
    """Background event types"""
    FILE_CHANGED = "file_changed"
    FILE_CREATED = "file_created"
    FILE_DELETED = "file_deleted"
    CRON_TRIGGERED = "cron_triggered"
    INTEGRATION_EVENT = "integration_event"
    HEARTBEAT_DUE = "heartbeat_due"
    CUSTOM = "custom"


@dataclass
class BGEvent:
    """Background event"""
    type: EventType
    source: str
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    acknowledged: bool = False


@dataclass
class FileWatcher:
    """Watches a directory for changes"""
    DEFAULT_IGNORE = [
        "__pycache__", ".git", "node_modules", ".venv", "*.pyc", "*.tmp"
    ]
    
    path: str
    recursive: bool = False
    patterns: List[str] = field(default_factory=lambda: ["*"])
    ignore_patterns: List[str] = field(default_factory=lambda: FileWatcher.DEFAULT_IGNORE.copy())
    _snapshot: Optional[Dict[str, float]] = field(default=None)

    def should_ignore(self, filepath: str) -> bool:
        """Check if a file should be ignored."""
        for pattern in self.ignore_patterns:
            if pattern.startswith("*"):
                if filepath.endswith(pattern[1:]):
                    return True
            elif pattern in filepath:
                return True
        return False

    def take_snapshot(self) -> Dict[str, float]:
        """Take a snapshot of the watched directory."""
        snapshot: Dict[str, float] = {}
        try:
            if self.recursive:
                for root, dirs, files in os.walk(self.path):
                    # Filter out ignored dirs
                    dirs[:] = [d for d in dirs if not self.should_ignore(d)]
                    for f in files:
                        fpath = os.path.join(root, f)
                        if not self.should_ignore(fpath):
                            try:
                                snapshot[fpath] = os.path.getmtime(fpath)
                            except OSError:
                                continue
            else:
                for f in os.listdir(self.path):
                    fpath = os.path.join(self.path, f)
                    if os.path.isfile(fpath) and not self.should_ignore(fpath):
                        try:
                            snapshot[fpath] = os.path.getmtime(fpath)
                        except OSError:
                            continue
        except OSError:
            pass
        return snapshot

    def detect_changes(self) -> List[BGEvent]:
        """Detect file changes since last snapshot."""
        events: List[BGEvent] = []
        new_snapshot = self.take_snapshot()

        if self._snapshot is None:
            # First run, just record state
            self._snapshot = new_snapshot
            return events

        old_files = set(self._snapshot.keys())
        new_files = set(new_snapshot.keys())

        # New files
        for fpath in new_files - old_files:
            events.append(BGEvent(
                type=EventType.FILE_CREATED,
                source=f"watcher:{self.path}",
                message=f"New file: {os.path.relpath(fpath, self.path)}",
                data={"path": fpath, "watch_root": self.path}
            ))

        # Deleted files
        for fpath in old_files - new_files:
            events.append(BGEvent(
                type=EventType.FILE_DELETED,
                source=f"watcher:{self.path}",
                message=f"Deleted: {os.path.relpath(fpath, self.path)}",
                data={"path": fpath, "watch_root": self.path}
            ))

        # Modified files
        for fpath in old_files & new_files:
            if new_snapshot[fpath] != self._snapshot[fpath]:
                events.append(BGEvent(
                    type=EventType.FILE_CHANGED,
                    source=f"watcher:{self.path}",
                    message=f"Modified: {os.path.relpath(fpath, self.path)}",
                    data={"path": fpath, "watch_root": self.path}
                ))

        self._snapshot = new_snapshot
        return events


class BackgroundDaemon:
    """
    Background processing daemon that runs alongside the terminal UI.

    Features:
    - File system watchers (polling-based, no external deps)
    - Event queue for cross-thread communication
    - Cron scheduler bridge
    - Integration polling bridge
    """

    def __init__(self, poll_interval: float = 5.0):
        self.poll_interval = poll_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._event_queue: Queue = Queue(maxsize=100)
        self._watchers: Dict[str, FileWatcher] = {}
        self._event_handlers: List[Callable[[BGEvent], None]] = []
        self._notification_buffer: List[BGEvent] = []
        self._notification_lock = threading.Lock()
        self._integration_pollers: List[Callable[[], List[BGEvent]]] = []
        self._stats = {
            "started_at": None,
            "events_processed": 0,
            "poll_cycles": 0,
            "errors": 0
        }

    # ── Lifecycle ──

    def start(self) -> None:
        """Start the background daemon."""
        if self._running:
            return

        self._running = True
        self._stats["started_at"] = datetime.now().isoformat(timespec="seconds")
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="gltch-bg")
        self._thread.start()

    def stop(self) -> None:
        """Stop the background daemon."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=10)
            self._thread = None

    @property
    def is_running(self) -> bool:
        return self._running

    # ── Configuration ──

    def add_watcher(
        self,
        path: str,
        recursive: bool = False,
        ignore_patterns: Optional[List[str]] = None
    ) -> bool:
        """Add a file system watcher."""
        path = os.path.abspath(path)
        if not os.path.isdir(path):
            return False

        watcher = FileWatcher(
            path=path,
            recursive=recursive,
            ignore_patterns=ignore_patterns or FileWatcher.DEFAULT_IGNORE.copy()
        )
        # Take initial snapshot
        watcher._snapshot = watcher.take_snapshot()
        self._watchers[path] = watcher
        return True

    def remove_watcher(self, path: str) -> bool:
        """Remove a file system watcher."""
        path = os.path.abspath(path)
        if path in self._watchers:
            del self._watchers[path]
            return True
        return False

    def add_integration_poller(self, poller: Callable[[], List[BGEvent]]) -> None:
        """Add an integration poller function."""
        self._integration_pollers.append(poller)

    def on_event(self, handler: Callable[[BGEvent], None]) -> None:
        """Register an event handler callback."""
        self._event_handlers.append(handler)

    # ── Event Queue ──

    def push_event(self, event: BGEvent) -> None:
        """Push an event into the queue."""
        try:
            self._event_queue.put_nowait(event)
        except Exception:
            pass  # Queue full, drop event

    def get_pending_notifications(self) -> List[BGEvent]:
        """Get and clear pending notifications for display."""
        with self._notification_lock:
            notifications = self._notification_buffer.copy()
            self._notification_buffer.clear()
        return notifications

    # ── Main Loop ──

    def _run_loop(self) -> None:
        """Main background processing loop."""
        while self._running:
            try:
                self._stats["poll_cycles"] += 1

                # 1. Check file watchers
                for watcher in self._watchers.values():
                    try:
                        events = watcher.detect_changes()
                        for event in events:
                            self._process_event(event)
                    except Exception:
                        self._stats["errors"] += 1

                # 2. Poll integrations
                for poller in self._integration_pollers:
                    try:
                        events = poller()
                        for event in events:
                            self._process_event(event)
                    except Exception:
                        self._stats["errors"] += 1

                # 3. Process queued events
                while True:
                    try:
                        event = self._event_queue.get_nowait()
                        self._process_event(event)
                    except Empty:
                        break

            except Exception:
                self._stats["errors"] += 1

            time.sleep(self.poll_interval)

    def _process_event(self, event: BGEvent) -> None:
        """Process a single event."""
        self._stats["events_processed"] += 1

        # Add to notification buffer for terminal display
        with self._notification_lock:
            self._notification_buffer.append(event)
            # Cap buffer size
            if len(self._notification_buffer) > 50:
                self._notification_buffer = self._notification_buffer[-50:]

        # Call registered handlers
        for handler in self._event_handlers:
            try:
                handler(event)
            except Exception:
                pass

    # ── Status ──

    def get_status(self) -> Dict[str, Any]:
        """Get daemon status."""
        return {
            "running": self._running,
            "started_at": self._stats["started_at"],
            "poll_interval": self.poll_interval,
            "watchers": len(self._watchers),
            "watcher_paths": list(self._watchers.keys()),
            "integration_pollers": len(self._integration_pollers),
            "events_processed": self._stats["events_processed"],
            "poll_cycles": self._stats["poll_cycles"],
            "errors": self._stats["errors"],
            "pending_notifications": len(self._notification_buffer)
        }

    def list_watchers(self) -> List[Dict[str, Any]]:
        """List all file watchers."""
        return [
            {
                "path": w.path,
                "recursive": w.recursive,
                "files_tracked": len(w._snapshot),
                "ignore_patterns": w.ignore_patterns
            }
            for w in self._watchers.values()
        ]
