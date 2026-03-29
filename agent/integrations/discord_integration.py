"""
GLTCH Discord Integration
Send/receive messages via Discord REST API (no discord.py dependency).
"""

from datetime import datetime
from typing import Dict, Any, List, Optional

from agent.integrations.base import Integration, IntegrationStatus


DISCORD_API = "https://discord.com/api/v10"


class DiscordIntegration(Integration):
    """
    Discord integration using REST API only.

    Features:
    - Send messages to channels
    - Poll for new messages in monitored channels
    - List guilds and channels

    Uses a bot token — create one at discord.com/developers
    """

    def __init__(self):
        super().__init__("discord")
        self._monitored_channels: List[str] = []
        self._last_message_ids: Dict[str, str] = {}  # channel_id -> last seen message id
        self._headers: Dict[str, str] = {}
        self._bot_user: Optional[Dict[str, Any]] = None

    def connect(self, token: str, **kwargs) -> bool:
        """Connect with a Discord bot token."""
        self.token = token
        self._headers = {
            "Authorization": f"Bot {token}",
            "Content-Type": "application/json",
            "User-Agent": "GLTCH-Agent (https://gltch.app, 1.0)"
        }

        try:
            self._bot_user = self._http_get(f"{DISCORD_API}/users/@me", self._headers)
            self.status = IntegrationStatus.CONNECTED
            self.last_error = None
            return True
        except Exception as e:
            self.status = IntegrationStatus.ERROR
            self.last_error = str(e)
            return False

    def disconnect(self) -> None:
        """Disconnect from Discord."""
        self.token = None
        self._headers = {}
        self._bot_user = None
        self.status = IntegrationStatus.DISCONNECTED

    def poll(self) -> List[Dict[str, Any]]:
        """Poll monitored channels for new messages."""
        if self.status != IntegrationStatus.CONNECTED:
            return []

        events = []
        self._poll_count += 1
        self.last_poll = datetime.now().isoformat(timespec="seconds")

        for channel_id in self._monitored_channels:
            try:
                params = f"?limit=5"
                last_id = self._last_message_ids.get(channel_id)
                if last_id:
                    params += f"&after={last_id}"

                messages = self._http_get(
                    f"{DISCORD_API}/channels/{channel_id}/messages{params}",
                    self._headers
                )

                # Filter out bot's own messages
                bot_id = self._bot_user.get("id", "") if self._bot_user else ""
                for msg in reversed(messages):  # oldest first
                    if msg.get("author", {}).get("id") == bot_id:
                        continue
                    events.append({
                        "type": "discord_message",
                        "source": "discord",
                        "channel_id": channel_id,
                        "author": msg.get("author", {}).get("username", "unknown"),
                        "content": msg.get("content", ""),
                        "message_id": msg.get("id", ""),
                        "timestamp": msg.get("timestamp", "")
                    })

                # Update last seen message
                if messages:
                    self._last_message_ids[channel_id] = messages[0].get("id", "")

            except Exception as e:
                self.last_error = str(e)

        return events

    def send(self, target: str, message: str, **kwargs) -> bool:
        """
        Send a message to a Discord channel.

        target: channel ID
        """
        if self.status != IntegrationStatus.CONNECTED:
            return False

        try:
            self._http_post(
                f"{DISCORD_API}/channels/{target}/messages",
                {"content": message},
                self._headers
            )
            return True
        except Exception as e:
            self.last_error = str(e)
            return False

    # ── Discord-specific methods ──

    def list_guilds(self) -> List[Dict[str, Any]]:
        """List bot's guilds (servers)."""
        if self.status != IntegrationStatus.CONNECTED:
            return []

        try:
            guilds = self._http_get(f"{DISCORD_API}/users/@me/guilds", self._headers)
            return [
                {
                    "id": g["id"],
                    "name": g["name"],
                    "icon": g.get("icon"),
                    "owner": g.get("owner", False)
                }
                for g in guilds
            ]
        except Exception:
            return []

    def list_channels(self, guild_id: str) -> List[Dict[str, Any]]:
        """List channels in a guild."""
        if self.status != IntegrationStatus.CONNECTED:
            return []

        try:
            channels = self._http_get(
                f"{DISCORD_API}/guilds/{guild_id}/channels",
                self._headers
            )
            return [
                {
                    "id": c["id"],
                    "name": c["name"],
                    "type": c.get("type", 0),
                    "position": c.get("position", 0)
                }
                for c in channels
                if c.get("type", 0) == 0  # Text channels only
            ]
        except Exception:
            return []

    def monitor_channel(self, channel_id: str) -> None:
        """Add a channel to the monitoring list."""
        if channel_id not in self._monitored_channels:
            self._monitored_channels.append(channel_id)

    def unmonitor_channel(self, channel_id: str) -> None:
        """Remove a channel from the monitoring list."""
        if channel_id in self._monitored_channels:
            self._monitored_channels.remove(channel_id)

    def get_status(self) -> Dict[str, Any]:
        """Extended status with Discord-specific info."""
        status = super().get_status()
        status["bot_name"] = self._bot_user.get("username") if self._bot_user else None
        status["monitored_channels"] = self._monitored_channels
        return status
