"""
GLTCH Multi-Agent Router
Route messages to different agent profiles or backends
"""

import asyncio
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List, Callable, Awaitable, Any, Pattern
from enum import Enum


class RoutingStrategy(Enum):
    """Routing strategies"""
    ROUND_ROBIN = "round_robin"
    RANDOM = "random"
    LEAST_LOADED = "least_loaded"
    AFFINITY = "affinity"  # Sticky sessions
    RULE_BASED = "rule_based"


@dataclass
class AgentProfile:
    """Agent profile for routing"""
    id: str
    name: str
    endpoint: str  # URL or identifier
    
    # Capabilities
    capabilities: List[str] = field(default_factory=list)
    languages: List[str] = field(default_factory=lambda: ["en"])
    specialties: List[str] = field(default_factory=list)
    
    # Load/health
    enabled: bool = True
    weight: int = 1  # For weighted routing
    max_concurrent: int = 10
    current_load: int = 0
    
    # Stats
    total_requests: int = 0
    total_errors: int = 0
    avg_latency_ms: float = 0.0
    last_used: Optional[datetime] = None
    last_error: Optional[str] = None
    
    @property
    def is_available(self) -> bool:
        return self.enabled and self.current_load < self.max_concurrent


@dataclass
class RoutingRule:
    """Rule for message routing"""
    id: str
    name: str
    priority: int = 0  # Higher = checked first
    
    # Conditions
    channel_pattern: Optional[str] = None
    user_pattern: Optional[str] = None
    content_pattern: Optional[str] = None
    session_pattern: Optional[str] = None
    
    # Target
    target_agent: str = ""  # Agent profile ID
    
    # Compiled patterns
    _channel_re: Optional[Pattern] = None
    _user_re: Optional[Pattern] = None
    _content_re: Optional[Pattern] = None
    _session_re: Optional[Pattern] = None
    
    def __post_init__(self):
        if self.channel_pattern:
            self._channel_re = re.compile(self.channel_pattern, re.IGNORECASE)
        if self.user_pattern:
            self._user_re = re.compile(self.user_pattern, re.IGNORECASE)
        if self.content_pattern:
            self._content_re = re.compile(self.content_pattern, re.IGNORECASE)
        if self.session_pattern:
            self._session_re = re.compile(self.session_pattern, re.IGNORECASE)
    
    def matches(
        self,
        channel: str,
        user: str,
        content: str,
        session_id: str
    ) -> bool:
        """Check if rule matches the message"""
        if self._channel_re and not self._channel_re.search(channel):
            return False
        if self._user_re and not self._user_re.search(user):
            return False
        if self._content_re and not self._content_re.search(content):
            return False
        if self._session_re and not self._session_re.search(session_id):
            return False
        return True


class MultiAgentRouter:
    """
    Routes messages to different agent profiles
    
    Supports:
    - Multiple agent backends (local, remote, specialized)
    - Load balancing strategies
    - Rule-based routing
    - Session affinity
    """
    
    def __init__(self, strategy: RoutingStrategy = RoutingStrategy.RULE_BASED):
        self.strategy = strategy
        self.agents: Dict[str, AgentProfile] = {}
        self.rules: List[RoutingRule] = []
        self.default_agent: Optional[str] = None
        
        # Session affinity mapping
        self._session_affinity: Dict[str, str] = {}  # session_id -> agent_id
        
        # Round-robin state
        self._rr_index = 0
    
    def register_agent(self, profile: AgentProfile) -> None:
        """Register an agent profile"""
        self.agents[profile.id] = profile
        
        # Set as default if first agent
        if self.default_agent is None:
            self.default_agent = profile.id
    
    def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            
            # Clear affinity mappings for this agent
            self._session_affinity = {
                k: v for k, v in self._session_affinity.items()
                if v != agent_id
            }
            
            # Update default if needed
            if self.default_agent == agent_id:
                self.default_agent = next(iter(self.agents.keys()), None)
            
            return True
        return False
    
    def add_rule(self, rule: RoutingRule) -> None:
        """Add a routing rule"""
        self.rules.append(rule)
        # Sort by priority (highest first)
        self.rules.sort(key=lambda r: r.priority, reverse=True)
    
    def remove_rule(self, rule_id: str) -> bool:
        """Remove a routing rule"""
        for i, rule in enumerate(self.rules):
            if rule.id == rule_id:
                del self.rules[i]
                return True
        return False
    
    def set_default_agent(self, agent_id: str) -> bool:
        """Set the default agent"""
        if agent_id in self.agents:
            self.default_agent = agent_id
            return True
        return False
    
    def route(
        self,
        channel: str,
        user: str,
        content: str,
        session_id: str
    ) -> Optional[AgentProfile]:
        """
        Route a message to an agent
        
        Returns the selected agent profile
        """
        # Check session affinity first
        if self.strategy == RoutingStrategy.AFFINITY:
            if session_id in self._session_affinity:
                agent_id = self._session_affinity[session_id]
                agent = self.agents.get(agent_id)
                if agent and agent.is_available:
                    return agent
        
        # Rule-based routing
        if self.strategy in (RoutingStrategy.RULE_BASED, RoutingStrategy.AFFINITY):
            for rule in self.rules:
                if rule.matches(channel, user, content, session_id):
                    agent = self.agents.get(rule.target_agent)
                    if agent and agent.is_available:
                        self._update_affinity(session_id, agent.id)
                        return agent
        
        # Strategy-based selection
        available = [a for a in self.agents.values() if a.is_available]
        if not available:
            # Fallback to any enabled agent
            available = [a for a in self.agents.values() if a.enabled]
        
        if not available:
            return None
        
        selected: Optional[AgentProfile] = None
        
        if self.strategy == RoutingStrategy.ROUND_ROBIN:
            selected = available[self._rr_index % len(available)]
            self._rr_index += 1
        
        elif self.strategy == RoutingStrategy.RANDOM:
            import random
            selected = random.choice(available)
        
        elif self.strategy == RoutingStrategy.LEAST_LOADED:
            selected = min(available, key=lambda a: a.current_load / a.max_concurrent)
        
        else:
            # Default: use default agent or first available
            if self.default_agent and self.default_agent in self.agents:
                agent = self.agents[self.default_agent]
                if agent.is_available:
                    selected = agent
            if not selected:
                selected = available[0]
        
        if selected:
            self._update_affinity(session_id, selected.id)
        
        return selected
    
    def _update_affinity(self, session_id: str, agent_id: str) -> None:
        """Update session affinity"""
        if self.strategy == RoutingStrategy.AFFINITY:
            self._session_affinity[session_id] = agent_id
    
    def record_request(
        self,
        agent_id: str,
        latency_ms: float,
        success: bool,
        error: Optional[str] = None
    ) -> None:
        """Record request metrics for an agent"""
        agent = self.agents.get(agent_id)
        if not agent:
            return
        
        agent.total_requests += 1
        agent.last_used = datetime.now()
        
        # Update rolling average latency
        agent.avg_latency_ms = (
            (agent.avg_latency_ms * (agent.total_requests - 1) + latency_ms)
            / agent.total_requests
        )
        
        if not success:
            agent.total_errors += 1
            agent.last_error = error
    
    def increment_load(self, agent_id: str) -> None:
        """Increment agent load"""
        if agent_id in self.agents:
            self.agents[agent_id].current_load += 1
    
    def decrement_load(self, agent_id: str) -> None:
        """Decrement agent load"""
        if agent_id in self.agents:
            self.agents[agent_id].current_load = max(0, self.agents[agent_id].current_load - 1)
    
    def get_agent(self, agent_id: str) -> Optional[AgentProfile]:
        """Get agent by ID"""
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[AgentProfile]:
        """List all agents"""
        return list(self.agents.values())
    
    def list_available_agents(self) -> List[AgentProfile]:
        """List available agents"""
        return [a for a in self.agents.values() if a.is_available]
    
    def list_rules(self) -> List[RoutingRule]:
        """List all routing rules"""
        return self.rules.copy()
    
    def get_status(self) -> dict:
        """Get router status"""
        return {
            "strategy": self.strategy.value,
            "total_agents": len(self.agents),
            "available_agents": len(self.list_available_agents()),
            "total_rules": len(self.rules),
            "default_agent": self.default_agent,
            "active_sessions": len(self._session_affinity),
        }
    
    def get_agent_stats(self) -> List[dict]:
        """Get stats for all agents"""
        return [
            {
                "id": a.id,
                "name": a.name,
                "enabled": a.enabled,
                "available": a.is_available,
                "current_load": a.current_load,
                "max_concurrent": a.max_concurrent,
                "total_requests": a.total_requests,
                "total_errors": a.total_errors,
                "avg_latency_ms": round(a.avg_latency_ms, 2),
                "error_rate": round(a.total_errors / a.total_requests * 100, 2) if a.total_requests > 0 else 0,
            }
            for a in self.agents.values()
        ]
