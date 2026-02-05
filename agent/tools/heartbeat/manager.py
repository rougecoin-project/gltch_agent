"""
Heartbeat Manager
Central orchestrator for all website heartbeats.
"""

import os
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable
from pathlib import Path

from .config import HeartbeatConfig, load_all_configs, HeartbeatTask
from .sandbox import HeartbeatSandbox, SandboxViolation, create_sandbox


class HeartbeatManager:
    """
    Manages heartbeats for all configured websites.
    
    Features:
    - Load configs from heartbeats/ directory
    - Track state per-site in memory
    - Execute heartbeats with sandbox protection
    - Pluggable action handlers
    """
    
    def __init__(self, heartbeats_dir: str = None):
        self.heartbeats_dir = heartbeats_dir
        self.configs: Dict[str, HeartbeatConfig] = {}
        self._action_handlers: Dict[str, Callable] = {}
        
        # Register default handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self) -> None:
        """Register built-in action handlers."""
        # Generic handlers that work for any site
        self._action_handlers["check_feed"] = self._handle_check_feed
        self._action_handlers["update_status"] = self._handle_update_status
        self._action_handlers["log_activity"] = self._handle_log_activity
    
    def register_handler(self, action: str, handler: Callable) -> None:
        """Register a custom action handler."""
        self._action_handlers[action] = handler
    
    def load_configs(self) -> Dict[str, HeartbeatConfig]:
        """Load all heartbeat configs from directory."""
        self.configs = load_all_configs(self.heartbeats_dir)
        return self.configs
    
    def get_config(self, site_id: str) -> Optional[HeartbeatConfig]:
        """Get config for a specific site."""
        if not self.configs:
            self.load_configs()
        return self.configs.get(site_id)
    
    def list_sites(self) -> List[Dict[str, Any]]:
        """List all configured sites with status."""
        if not self.configs:
            self.load_configs()
        
        sites = []
        for site_id, config in self.configs.items():
            state = self.get_state(site_id)
            sites.append({
                "site_id": site_id,
                "display_name": config.display_name,
                "enabled": config.enabled,
                "interval_hours": config.interval_hours,
                "last_heartbeat": state.get("last_heartbeat"),
                "should_run": self.should_run(site_id),
            })
        return sites
    
    def get_state(self, site_id: str) -> Dict[str, Any]:
        """Get heartbeat state for a site from memory."""
        try:
            from agent.memory.store import load_memory
            mem = load_memory()
            all_states = mem.get("heartbeats", {})
            return all_states.get(site_id, {
                "last_heartbeat": None,
                "last_result": None,
                "error_count": 0,
            })
        except Exception:
            return {"last_heartbeat": None, "last_result": None, "error_count": 0}
    
    def update_state(self, site_id: str, updates: Dict[str, Any]) -> None:
        """Update heartbeat state for a site."""
        try:
            from agent.memory.store import load_memory, save_memory
            mem = load_memory()
            
            if "heartbeats" not in mem:
                mem["heartbeats"] = {}
            
            if site_id not in mem["heartbeats"]:
                mem["heartbeats"][site_id] = {}
            
            mem["heartbeats"][site_id].update(updates)
            save_memory(mem)
        except Exception:
            pass
    
    def should_run(self, site_id: str) -> bool:
        """Check if a site's heartbeat should run based on interval."""
        config = self.get_config(site_id)
        if not config or not config.enabled:
            return False
        
        state = self.get_state(site_id)
        last_heartbeat = state.get("last_heartbeat")
        
        if not last_heartbeat:
            return True
        
        try:
            last = datetime.fromisoformat(last_heartbeat)
            now = datetime.now()
            hours_since = (now - last).total_seconds() / 3600
            return hours_since >= config.interval_hours
        except Exception:
            return True
    
    def get_pending_sites(self) -> List[str]:
        """Get list of sites that need heartbeats."""
        if not self.configs:
            self.load_configs()
        
        return [site_id for site_id in self.configs if self.should_run(site_id)]
    
    def run_heartbeat(self, site_id: str, force: bool = False) -> Dict[str, Any]:
        """
        Run heartbeat for a specific site.
        
        Args:
            site_id: Site to run heartbeat for
            force: If True, run even if not due
            
        Returns:
            Result dict with success status and details
        """
        config = self.get_config(site_id)
        if not config:
            return {"success": False, "error": f"Unknown site: {site_id}"}
        
        if not config.enabled:
            return {"success": False, "error": f"Site {site_id} is disabled"}
        
        if not force and not self.should_run(site_id):
            return {"success": False, "error": f"Heartbeat not due yet for {site_id}"}
        
        # Create sandbox for this site
        sandbox = create_sandbox(
            site_id=site_id,
            api_key_name=config.api_key_name,
            max_requests=config.max_requests_per_heartbeat,
            timeout=config.timeout_seconds,
        )
        
        # Register handlers with sandbox
        for action, handler in self._action_handlers.items():
            sandbox.register_handler(action, handler)
        
        results = {
            "site_id": site_id,
            "tasks_run": 0,
            "tasks_succeeded": 0,
            "tasks_failed": 0,
            "errors": [],
        }
        
        # Execute each task
        for task in config.tasks:
            try:
                result = sandbox.execute_task(task.action, task.params)
                results["tasks_run"] += 1
                
                if result.get("success"):
                    results["tasks_succeeded"] += 1
                else:
                    results["tasks_failed"] += 1
                    results["errors"].append(f"{task.action}: {result.get('error')}")
                    
            except SandboxViolation as e:
                results["tasks_run"] += 1
                results["tasks_failed"] += 1
                results["errors"].append(f"{task.action}: BLOCKED - {e}")
                
            except Exception as e:
                results["tasks_run"] += 1
                results["tasks_failed"] += 1
                results["errors"].append(f"{task.action}: {e}")
        
        # Update state
        self.update_state(site_id, {
            "last_heartbeat": datetime.now().isoformat(),
            "last_result": "success" if results["tasks_failed"] == 0 else "partial",
            "error_count": 0 if results["tasks_failed"] == 0 else results["tasks_failed"],
        })
        
        results["success"] = results["tasks_failed"] == 0
        return results
    
    def run_all_pending(self) -> Dict[str, Dict[str, Any]]:
        """Run heartbeats for all pending sites."""
        pending = self.get_pending_sites()
        results = {}
        
        for site_id in pending:
            results[site_id] = self.run_heartbeat(site_id)
        
        return results
    
    # === Default Action Handlers ===
    
    def _handle_check_feed(self, sandbox: HeartbeatSandbox, params: Dict[str, Any]) -> Any:
        """Default handler for check_feed action."""
        # This is a placeholder - sites should override with their own handler
        return {"checked": True, "items": 0}
    
    def _handle_update_status(self, sandbox: HeartbeatSandbox, params: Dict[str, Any]) -> Any:
        """Default handler for update_status action."""
        return {"updated": True}
    
    def _handle_log_activity(self, sandbox: HeartbeatSandbox, params: Dict[str, Any]) -> Any:
        """Default handler for log_activity action."""
        message = params.get("message", "Heartbeat check-in")
        return {"logged": True, "message": message}


# Global manager instance
_manager: Optional[HeartbeatManager] = None


def get_manager() -> HeartbeatManager:
    """Get or create the global heartbeat manager."""
    global _manager
    if _manager is None:
        _manager = HeartbeatManager()
        _manager.load_configs()
    return _manager
