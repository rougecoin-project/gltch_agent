
import pytest
from unittest.mock import MagicMock
from agent.core.agent import GltchAgent

@pytest.fixture
def mock_memory():
    """Return a fresh memory dict for testing."""
    return {
        "chat_history": [],
        "notes": [],
        "missions": [],
        "operator": "TestUser",
        "mode": "operator",
        "mood": "focused",
        "level": 1,
        "xp": 0,
        "api_keys": {},
        "network_active": False
    }

@pytest.fixture
def agent(mock_memory):
    """Return an agent instance with mock memory."""
    # We mock load_memory to return our fixture instead of reading disk
    with pytest.MonkeyPatch.context() as m:
        m.setattr("agent.core.agent.load_memory", lambda: mock_memory)
        # Prevent auto-saving to disk during tests
        m.setattr("agent.core.agent.save_memory", MagicMock())
        
        agent_instance = GltchAgent(memory=mock_memory)
        yield agent_instance
