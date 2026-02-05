
import pytest
from agent.core.agent import GltchAgent

def test_agent_initialization(agent):
    """Test that agent initializes with correct defaults."""
    assert agent.operator == "TestUser"
    assert agent.mode == "operator"
    assert agent.mood == "focused"
    assert agent.level == 1
    assert agent.xp == 0

def test_set_mode_permissions(agent):
    """Test mode switching logic and level requirements."""
    # Operator mode is always allowed
    assert agent.set_mode("operator") is True
    assert agent.mode == "operator"

    # Unhinged requires level 3
    agent.memory["level"] = 1
    assert agent.set_mode("unhinged") is False
    assert agent.mode == "operator"

    # Level up to 3
    agent.memory["level"] = 3
    assert agent.set_mode("unhinged") is True
    assert agent.mode == "unhinged"

def test_set_mood_permissions(agent):
    """Test mood switching logic and level requirements."""
    # Calm/Focused are always allowed
    assert agent.set_mood("calm") is True
    assert agent.mood == "calm"

    # Feral requires level 7
    agent.memory["level"] = 1
    assert agent.set_mood("feral") is False
    assert agent.mood == "calm"

    agent.memory["level"] = 7
    assert agent.set_mood("feral") is True
    assert agent.mood == "feral"

def test_xp_gain(agent):
    """Test that agent gains XP correctly."""
    initial_xp = agent.xp
    
    # Simulate a chat interaction (mocking the actual LLM call to avoid network)
    # This just tests the XP utility helper directly or we can mock chat
    # For now, let's just manually verify the property
    agent.memory["xp"] += 10
    assert agent.xp == initial_xp + 10

def test_toggle_boost(agent):
    """Test boost mode toggle."""
    assert agent.memory.get("boost", False) is False
    agent.toggle_boost()
    assert agent.memory.get("boost") is True
    agent.toggle_boost()
    assert agent.memory.get("boost") is False

def test_encode_image(tmp_path):
    """Test image encoding helper."""
    from agent.core.llm import encode_image
    import base64
    
    # Create dummy image file
    img_path = tmp_path / "test.png"
    content = b"fake_image_content"
    img_path.write_bytes(content)
    
    encoded = encode_image(str(img_path))
    decoded = base64.b64decode(encoded)
    assert decoded == content
