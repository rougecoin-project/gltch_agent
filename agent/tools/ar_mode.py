"""
GLTCH AR Mode
Augmented Reality overlay and spatial computing features
"""

import asyncio
import os
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List, Any, Tuple
from enum import Enum


class ARContentType(Enum):
    """AR content types"""
    TEXT = "text"
    IMAGE = "image"
    MODEL_3D = "model_3d"
    VIDEO = "video"
    WIDGET = "widget"
    HOLOGRAM = "hologram"


class ARAnchorType(Enum):
    """AR anchor types"""
    WORLD = "world"       # Fixed in physical space
    SCREEN = "screen"     # Fixed to screen
    FOLLOW = "follow"     # Follows user gaze
    FACE = "face"         # Face tracking
    HAND = "hand"         # Hand tracking


@dataclass
class AROverlay:
    """AR overlay object"""
    id: str
    content_type: ARContentType
    content: str  # Text, URL, or serialized data
    
    # Positioning
    anchor_type: ARAnchorType = ARAnchorType.SCREEN
    position: Tuple[float, float, float] = (0, 0, 0)  # x, y, z
    rotation: Tuple[float, float, float] = (0, 0, 0)  # pitch, yaw, roll
    scale: float = 1.0
    
    # Appearance
    opacity: float = 1.0
    style: Dict[str, Any] = field(default_factory=dict)
    
    # Behavior
    interactive: bool = False
    clickable: bool = False
    persistent: bool = False
    
    # Timing
    duration_ms: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None


@dataclass
class ARScene:
    """AR scene containing multiple overlays"""
    id: str
    name: str
    overlays: List[AROverlay] = field(default_factory=list)
    
    # Scene settings
    lighting: str = "auto"  # auto, bright, dim, dark
    occlusion: bool = True
    physics: bool = False
    
    # State
    active: bool = False
    created_at: datetime = field(default_factory=datetime.now)


class ARMode:
    """
    AR Mode for GLTCH
    
    Provides augmented reality overlay capabilities:
    - Floating text responses
    - 3D model placement
    - Spatial notifications
    - Face/hand tracking overlays
    - Interactive widgets
    
    Works with native apps (macOS/iOS/visionOS/Android)
    """
    
    def __init__(self):
        self._scenes: Dict[str, ARScene] = {}
        self._active_scene: Optional[str] = None
        self._overlays: Dict[str, AROverlay] = {}
        self._connected_devices: Dict[str, dict] = {}
    
    def create_scene(self, name: str, **kwargs) -> ARScene:
        """Create a new AR scene"""
        import uuid
        scene_id = f"scene_{uuid.uuid4().hex[:8]}"
        
        scene = ARScene(
            id=scene_id,
            name=name,
            **kwargs
        )
        
        self._scenes[scene_id] = scene
        return scene
    
    def activate_scene(self, scene_id: str) -> bool:
        """Activate a scene"""
        if scene_id not in self._scenes:
            return False
        
        # Deactivate current scene
        if self._active_scene:
            self._scenes[self._active_scene].active = False
        
        self._scenes[scene_id].active = True
        self._active_scene = scene_id
        
        # Notify connected devices
        self._broadcast_scene_update(scene_id)
        return True
    
    def add_overlay(
        self,
        content_type: ARContentType,
        content: str,
        scene_id: Optional[str] = None,
        **kwargs
    ) -> AROverlay:
        """Add an overlay to a scene"""
        import uuid
        overlay_id = f"overlay_{uuid.uuid4().hex[:8]}"
        
        overlay = AROverlay(
            id=overlay_id,
            content_type=content_type,
            content=content,
            **kwargs
        )
        
        self._overlays[overlay_id] = overlay
        
        # Add to scene
        target_scene = scene_id or self._active_scene
        if target_scene and target_scene in self._scenes:
            self._scenes[target_scene].overlays.append(overlay)
        
        # Notify connected devices
        self._broadcast_overlay_update(overlay)
        
        return overlay
    
    def show_text(
        self,
        text: str,
        position: Tuple[float, float, float] = (0, 0.5, 1),
        duration_ms: int = 5000,
        style: Optional[Dict] = None
    ) -> AROverlay:
        """Show floating text in AR"""
        return self.add_overlay(
            content_type=ARContentType.TEXT,
            content=text,
            position=position,
            duration_ms=duration_ms,
            style=style or {
                "font_size": 24,
                "color": "#00ff00",
                "background": "rgba(0,0,0,0.7)",
                "padding": 16,
                "border_radius": 8
            }
        )
    
    def show_response(
        self,
        response: str,
        mood: Optional[str] = None
    ) -> AROverlay:
        """Show agent response as AR overlay"""
        # Position above user's view
        position = (0, 0.3, 1.5)
        
        # Style based on mood
        mood_colors = {
            "happy": "#00ff00",
            "excited": "#ffff00",
            "curious": "#00ffff",
            "mischievous": "#ff00ff",
            "focused": "#0088ff",
            "neutral": "#ffffff"
        }
        
        color = mood_colors.get(mood, "#00ff00")
        
        return self.show_text(
            text=response,
            position=position,
            duration_ms=10000,
            style={
                "font_size": 20,
                "color": color,
                "background": "rgba(0,0,0,0.8)",
                "padding": 20,
                "border_radius": 12,
                "max_width": 400,
                "animation": "fade_in"
            }
        )
    
    def show_notification(
        self,
        title: str,
        message: str,
        icon: Optional[str] = None
    ) -> AROverlay:
        """Show notification in AR"""
        content = json.dumps({
            "title": title,
            "message": message,
            "icon": icon
        })
        
        return self.add_overlay(
            content_type=ARContentType.WIDGET,
            content=content,
            anchor_type=ARAnchorType.SCREEN,
            position=(0.8, 0.9, 0),  # Top right
            duration_ms=5000,
            style={"type": "notification"}
        )
    
    def show_hologram(
        self,
        model_url: str,
        position: Tuple[float, float, float] = (0, 0, 2),
        scale: float = 1.0,
        animate: bool = True
    ) -> AROverlay:
        """Show 3D hologram model"""
        return self.add_overlay(
            content_type=ARContentType.HOLOGRAM,
            content=model_url,
            anchor_type=ARAnchorType.WORLD,
            position=position,
            scale=scale,
            style={
                "animate": animate,
                "glow": True,
                "color_tint": "#00ff00"
            }
        )
    
    def show_info_panel(
        self,
        data: Dict[str, Any],
        position: Tuple[float, float, float] = (0.5, 0.5, 1)
    ) -> AROverlay:
        """Show information panel widget"""
        return self.add_overlay(
            content_type=ARContentType.WIDGET,
            content=json.dumps(data),
            anchor_type=ARAnchorType.FOLLOW,
            position=position,
            interactive=True,
            style={"type": "info_panel"}
        )
    
    def remove_overlay(self, overlay_id: str) -> bool:
        """Remove an overlay"""
        if overlay_id in self._overlays:
            overlay = self._overlays.pop(overlay_id)
            
            # Remove from scenes
            for scene in self._scenes.values():
                scene.overlays = [o for o in scene.overlays if o.id != overlay_id]
            
            # Notify devices
            self._broadcast_overlay_remove(overlay_id)
            return True
        return False
    
    def clear_overlays(self) -> None:
        """Clear all overlays"""
        self._overlays.clear()
        for scene in self._scenes.values():
            scene.overlays.clear()
        
        self._broadcast_clear()
    
    def register_device(
        self,
        device_id: str,
        device_type: str,
        capabilities: List[str]
    ) -> None:
        """Register a connected AR device"""
        self._connected_devices[device_id] = {
            "type": device_type,
            "capabilities": capabilities,
            "connected_at": datetime.now().isoformat()
        }
    
    def unregister_device(self, device_id: str) -> None:
        """Unregister a device"""
        self._connected_devices.pop(device_id, None)
    
    def _broadcast_scene_update(self, scene_id: str) -> None:
        """Broadcast scene update to devices"""
        # In production, would send via WebSocket
        pass
    
    def _broadcast_overlay_update(self, overlay: AROverlay) -> None:
        """Broadcast overlay update to devices"""
        pass
    
    def _broadcast_overlay_remove(self, overlay_id: str) -> None:
        """Broadcast overlay removal to devices"""
        pass
    
    def _broadcast_clear(self) -> None:
        """Broadcast clear command to devices"""
        pass
    
    def get_scene_data(self, scene_id: Optional[str] = None) -> Dict[str, Any]:
        """Get scene data for rendering"""
        target = scene_id or self._active_scene
        if not target or target not in self._scenes:
            return {"error": "No active scene"}
        
        scene = self._scenes[target]
        return {
            "id": scene.id,
            "name": scene.name,
            "active": scene.active,
            "settings": {
                "lighting": scene.lighting,
                "occlusion": scene.occlusion,
                "physics": scene.physics
            },
            "overlays": [
                {
                    "id": o.id,
                    "type": o.content_type.value,
                    "content": o.content,
                    "position": o.position,
                    "rotation": o.rotation,
                    "scale": o.scale,
                    "opacity": o.opacity,
                    "style": o.style,
                    "interactive": o.interactive
                }
                for o in scene.overlays
            ]
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get AR mode status"""
        return {
            "active_scene": self._active_scene,
            "total_scenes": len(self._scenes),
            "total_overlays": len(self._overlays),
            "connected_devices": len(self._connected_devices),
            "devices": list(self._connected_devices.keys())
        }


# Global instance
ar_mode = ARMode()
