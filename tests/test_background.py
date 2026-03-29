"""Tests for GLTCH Background Daemon"""
import os
import time
import pytest
from agent.automation.background import BackgroundDaemon, FileWatcher, BGEvent, EventType


@pytest.fixture
def daemon():
    """Create a background daemon for testing."""
    d = BackgroundDaemon(poll_interval=0.5)
    yield d
    if d.is_running:
        d.stop()


@pytest.fixture
def watch_dir(tmp_path):
    """Create a temp directory for file watching."""
    d = tmp_path / "watched"
    d.mkdir()
    return d


def test_daemon_start_stop(daemon):
    """Test daemon lifecycle."""
    assert not daemon.is_running
    daemon.start()
    assert daemon.is_running
    daemon.stop()
    assert not daemon.is_running


def test_add_watcher(daemon, watch_dir):
    """Test adding a file watcher."""
    assert daemon.add_watcher(str(watch_dir)) is True
    assert len(daemon.list_watchers()) == 1
    assert daemon.list_watchers()[0]["path"] == str(watch_dir)


def test_add_watcher_invalid_path(daemon):
    """Test adding watcher for invalid path."""
    assert daemon.add_watcher("/nonexistent/path") is False


def test_remove_watcher(daemon, watch_dir):
    """Test removing a file watcher."""
    daemon.add_watcher(str(watch_dir))
    assert daemon.remove_watcher(str(watch_dir)) is True
    assert len(daemon.list_watchers()) == 0


def test_file_watcher_detect_creation(watch_dir):
    """Test that FileWatcher detects new files."""
    watcher = FileWatcher(path=str(watch_dir))
    # Take initial baseline snapshot
    watcher._snapshot = watcher.take_snapshot()
    assert len(watcher._snapshot) == 0  # empty dir
    
    # Create a new file
    (watch_dir / "new_file.txt").write_text("hello")
    
    events = watcher.detect_changes()
    assert len(events) == 1
    assert events[0].type == EventType.FILE_CREATED
    assert "new_file.txt" in events[0].message


def test_file_watcher_detect_deletion(watch_dir):
    """Test that FileWatcher detects deleted files."""
    test_file = watch_dir / "to_delete.txt"
    test_file.write_text("goodbye")
    
    watcher = FileWatcher(path=str(watch_dir))
    watcher._snapshot = watcher.take_snapshot()
    
    test_file.unlink()
    
    events = watcher.detect_changes()
    assert len(events) == 1
    assert events[0].type == EventType.FILE_DELETED


def test_file_watcher_detect_modification(watch_dir):
    """Test that FileWatcher detects modified files."""
    test_file = watch_dir / "modify_me.txt"
    test_file.write_text("original")
    
    watcher = FileWatcher(path=str(watch_dir))
    watcher._snapshot = watcher.take_snapshot()
    
    time.sleep(0.1)  # Ensure mtime changes
    test_file.write_text("modified")
    
    events = watcher.detect_changes()
    assert len(events) == 1
    assert events[0].type == EventType.FILE_CHANGED


def test_file_watcher_ignore_patterns(watch_dir):
    """Test that ignored patterns are skipped."""
    watcher = FileWatcher(path=str(watch_dir), ignore_patterns=["*.pyc", "__pycache__"])
    watcher._snapshot = watcher.take_snapshot()
    
    (watch_dir / "test.pyc").write_bytes(b"bytecode")
    
    events = watcher.detect_changes()
    assert len(events) == 0  # Should be ignored


def test_event_queue(daemon):
    """Test pushing and retrieving events."""
    event = BGEvent(
        type=EventType.CUSTOM,
        source="test",
        message="test event"
    )
    daemon.push_event(event)
    
    # Process it
    daemon.start()
    time.sleep(1)  # Wait for poll cycle
    daemon.stop()
    
    notifications = daemon.get_pending_notifications()
    assert len(notifications) >= 1
    assert notifications[0].message == "test event"


def test_notification_buffer_cleared(daemon):
    """Test that getting notifications clears the buffer."""
    daemon.start()
    time.sleep(0.2)
    
    event = BGEvent(type=EventType.CUSTOM, source="test", message="hello")
    daemon.push_event(event)
    time.sleep(1)
    daemon.stop()
    
    first = daemon.get_pending_notifications()
    second = daemon.get_pending_notifications()
    assert len(second) == 0  # Buffer should be cleared


def test_daemon_status(daemon):
    """Test status reporting."""
    status = daemon.get_status()
    assert status["running"] is False
    assert status["watchers"] == 0
    
    daemon.start()
    time.sleep(0.2)
    
    status = daemon.get_status()
    assert status["running"] is True
    assert status["started_at"] is not None
    daemon.stop()
