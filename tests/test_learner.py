"""Tests for GLTCH Learner"""
import os
import json
import pytest
from agent.memory.learner import Learner


@pytest.fixture
def learner(tmp_path):
    """Create a learner with temp storage."""
    patterns_file = str(tmp_path / "test_patterns.json")
    return Learner(patterns_file=patterns_file)


def test_extract_corrections_dont_say(learner):
    """Test correction extraction: 'don't say X, say Y'."""
    corrections = learner.extract_corrections("don't say color, say colour")
    assert len(corrections) >= 1


def test_extract_corrections_use_not(learner):
    """Test correction extraction: 'use X not Y'."""
    corrections = learner.extract_corrections("use tabs not spaces")
    assert len(corrections) >= 1


def test_extract_preferences_prefers(learner):
    """Test preference extraction: 'I prefer X'."""
    preferences = learner.extract_preferences("I prefer dark mode for everything")
    assert len(preferences) >= 1
    assert any(p["type"] == "prefers" for p in preferences)


def test_extract_preferences_dislikes(learner):
    """Test preference extraction: 'I hate X'."""
    preferences = learner.extract_preferences("I hate verbose error messages")
    assert len(preferences) >= 1
    assert any(p["type"] == "dislikes" for p in preferences)


def test_extract_preferences_favorite(learner):
    """Test preference extraction: 'my go-to is X'."""
    preferences = learner.extract_preferences("my go-to editor is neovim")
    assert len(preferences) >= 1
    assert any(p["type"] == "favorite" for p in preferences)


def test_analyze_conversation(learner):
    """Test full conversation analysis."""
    result = learner.analyze_conversation(
        user_message="I prefer python for scripting, don't say py, say python",
        assistant_response="got it, python is great for scripting tasks",
        operator="CyberDreadx"
    )
    
    assert learner.data["stats"]["conversations_analyzed"] == 1
    assert learner.data["stats"]["last_analysis"] is not None


def test_style_detection_casual(learner):
    """Test casual style detection."""
    learner.analyze_conversation(
        user_message="lol bruh idk what this code does tbh",
        assistant_response="let me check that for you"
    )
    assert learner.data["style"]["formality"] == "casual"


def test_style_detection_formal(learner):
    """Test formal style detection."""
    learner.analyze_conversation(
        user_message="Could you please analyze this code? I would like a detailed breakdown.",
        assistant_response="of course, here's the analysis"
    )
    assert learner.data["style"]["formality"] == "formal"


def test_topic_tracking(learner):
    """Test topic interest tracking."""
    learner.analyze_conversation(
        user_message="how do I set up docker with nginx reverse proxy",
        assistant_response="here's how to configure docker and nginx"
    )
    topics = learner.data["style"].get("topics", {})
    assert "devops" in topics


def test_operator_profile_empty(learner):
    """Test that empty learner returns empty profile."""
    profile = learner.get_operator_profile()
    assert profile == ""


def test_operator_profile_with_data(learner):
    """Test profile generation with learned data."""
    learner._add_preference("prefers", "dark mode")
    learner._add_correction("colour", "color", "spelling preference")
    
    profile = learner.get_operator_profile()
    assert "dark mode" in profile
    assert "PREFERENCES" in profile


def test_preference_confidence_growth(learner):
    """Test that repeated preferences increase confidence."""
    learner._add_preference("prefers", "vim")
    initial = learner.data["preferences"][0]["confidence"]
    
    learner._add_preference("prefers", "vim")
    grown = learner.data["preferences"][0]["confidence"]
    
    assert grown > initial


def test_decay_old_patterns(learner):
    """Test pattern decay."""
    learner._add_preference("prefers", "test_item")
    # Manually age the pattern
    learner.data["preferences"][0]["last_seen"] = "2020-01-01T00:00:00"
    
    decayed = learner.decay_old_patterns(days_threshold=1)
    assert decayed >= 1


def test_persistence(tmp_path):
    """Test learner persistence."""
    pf = str(tmp_path / "persist_patterns.json")
    
    lr1 = Learner(patterns_file=pf)
    lr1._add_preference("prefers", "python")
    
    lr2 = Learner(patterns_file=pf)
    assert len(lr2.data["preferences"]) == 1
    assert lr2.data["preferences"][0]["value"] == "python"


def test_time_pattern_tracking(learner):
    """Test time-of-day tracking."""
    learner.analyze_conversation(
        user_message="hello",
        assistant_response="hey"
    )
    time_patterns = learner.data["style"].get("time_patterns", {})
    assert len(time_patterns) > 0


def test_stats(learner):
    """Test stats reporting."""
    learner.analyze_conversation("hello", "hey")
    learner.analyze_conversation("test", "ok")
    
    stats = learner.get_stats()
    assert stats["conversations_analyzed"] == 2
    assert stats["last_analysis"] is not None
