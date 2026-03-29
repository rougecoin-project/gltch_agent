"""Tests for GLTCH Knowledge Graph"""
import os
import json
import pytest
from agent.memory.knowledge_graph import KnowledgeGraph


@pytest.fixture
def kg(tmp_path):
    """Create a knowledge graph with temp storage."""
    kg_file = str(tmp_path / "test_kg.json")
    return KnowledgeGraph(kg_file=kg_file)


def test_add_entity(kg):
    """Test adding entities."""
    eid = kg.add_entity("python", "language")
    assert eid == "python"
    assert "python" in kg.data["entities"]
    assert kg.data["entities"]["python"]["type"] == "language"
    assert kg.data["entities"]["python"]["mentions"] == 1


def test_add_entity_increments_mentions(kg):
    """Test that re-adding an entity increments mentions."""
    kg.add_entity("python", "language")
    kg.add_entity("python", "language")
    assert kg.data["entities"]["python"]["mentions"] == 2


def test_add_entity_with_aliases(kg):
    """Test adding entities with aliases."""
    kg.add_entity("gltch_agent", "project", aliases=["gltch", "glitch"])
    entity = kg.data["entities"]["gltch_agent"]
    assert "gltch" in entity["aliases"]
    assert "glitch" in entity["aliases"]


def test_get_entity(kg):
    """Test getting entities by name and alias."""
    kg.add_entity("react", "tool", aliases=["reactjs"])
    
    assert kg.get_entity("react") is not None
    assert kg.get_entity("react")["type"] == "tool"
    assert kg.get_entity("reactjs") is not None  # alias lookup


def test_remove_entity(kg):
    """Test removing entities and their relations."""
    kg.add_entity("node", "tool")
    kg.add_entity("express", "tool")
    kg.add_relation("node", "express", "uses")
    
    assert kg.remove_entity("node") is True
    assert "node" not in kg.data["entities"]
    # Relations should be cleaned up
    assert len([r for r in kg.data["relations"] if r["source"] == "node" or r["target"] == "node"]) == 0


def test_add_relation(kg):
    """Test adding relations between entities."""
    kg.add_entity("gltch", "project")
    kg.add_entity("python", "language")
    kg.add_relation("gltch", "python", "uses")
    
    assert len(kg.data["relations"]) == 1
    rel = kg.data["relations"][0]
    assert rel["source"] == "gltch"
    assert rel["target"] == "python"
    assert rel["type"] == "uses"
    assert rel["weight"] == 1


def test_relation_weight_increment(kg):
    """Test that repeated relations increase weight."""
    kg.add_entity("gltch", "project")
    kg.add_entity("python", "language")
    kg.add_relation("gltch", "python", "uses")
    kg.add_relation("gltch", "python", "uses")
    
    assert kg.data["relations"][0]["weight"] == 2


def test_extract_from_conversation(kg):
    """Test entity extraction from conversation text."""
    result = kg.extract_from_conversation(
        user_message="I'm building a project with python and react",
        assistant_response="nice, python and react work well together. check https://reactjs.org",
        operator="CyberDreadx"
    )
    
    assert len(result["entities"]) > 0
    assert kg.data["stats"]["total_extractions"] == 1
    # Should have extracted python and react as languages/tools
    assert kg.get_entity("python") is not None
    assert kg.get_entity("reactjs.org") is not None  # URL domain


def test_get_relevant_context(kg):
    """Test context generation for LLM prompt."""
    kg.add_entity("python", "language")
    kg.add_entity("gltch", "project")
    kg.add_relation("gltch", "python", "uses")
    
    context = kg.get_relevant_context("tell me about gltch")
    assert "gltch" in context.lower()
    assert "KNOWLEDGE" in context


def test_empty_context(kg):
    """Test that empty graph returns empty context."""
    context = kg.get_relevant_context("hello world")
    assert context == ""


def test_search(kg):
    """Test searching entities."""
    kg.add_entity("python", "language")
    kg.add_entity("pytest", "tool")
    kg.add_entity("react", "tool")
    
    results = kg.search("pyt")
    assert len(results) == 2  # python and pytest
    
    results = kg.search("tool")
    assert len(results) == 2  # pytest and react


def test_list_entities(kg):
    """Test listing entities with type filter."""
    kg.add_entity("python", "language")
    kg.add_entity("javascript", "language")
    kg.add_entity("react", "tool")
    
    all_entities = kg.list_entities()
    assert len(all_entities) == 3
    
    langs = kg.list_entities(entity_type="language")
    assert len(langs) == 2


def test_merge_entities(kg):
    """Test merging two entities."""
    kg.add_entity("gltch", "project")
    kg.add_entity("gltch_agent", "project", aliases=["glitch_agent"])
    kg.add_entity("python", "language")
    kg.add_relation("gltch_agent", "python", "uses")
    
    result = kg.merge("gltch", "gltch_agent")
    assert result is True
    assert "gltch_agent" not in kg.data["entities"]
    assert "gltch_agent" in kg.data["entities"]["gltch"]["aliases"]
    # Relation should be repointed
    assert kg.data["relations"][0]["source"] == "gltch"


def test_persistence(tmp_path):
    """Test that knowledge graph persists to disk."""
    kg_file = str(tmp_path / "persist_test.json")
    
    kg1 = KnowledgeGraph(kg_file=kg_file)
    kg1.add_entity("python", "language")
    
    # Load from same file
    kg2 = KnowledgeGraph(kg_file=kg_file)
    assert "python" in kg2.data["entities"]
    assert kg2.data["entities"]["python"]["type"] == "language"


def test_stats(kg):
    """Test stats reporting."""
    kg.add_entity("python", "language")
    kg.add_entity("react", "tool")
    kg.add_relation("react", "python", "related_to")
    
    stats = kg.get_stats()
    assert stats["total_entities"] == 2
    assert stats["total_relations"] == 1
    assert "language" in stats["entity_types"]
    assert "tool" in stats["entity_types"]
