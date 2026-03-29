"""
GLTCH GitHub Integration
Monitor repos, issues, PRs, and notifications via GitHub REST API.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional

from agent.integrations.base import Integration, IntegrationStatus


GITHUB_API = "https://api.github.com"


class GitHubIntegration(Integration):
    """
    GitHub integration using REST API (no PyGithub dependency).

    Features:
    - Monitor repos for new issues, PRs, commits
    - Check notifications
    - List repos and activity
    """

    def __init__(self):
        super().__init__("github")
        self._watched_repos: List[str] = []
        self._last_notification_id: Optional[str] = None
        self._headers: Dict[str, str] = {}

    def connect(self, token: str, **kwargs) -> bool:
        """Connect with a GitHub personal access token."""
        self.token = token
        self._headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GLTCH-Agent"
        }

        try:
            user = self._http_get(f"{GITHUB_API}/user", self._headers)
            self.status = IntegrationStatus.CONNECTED
            self.last_error = None
            self._username = user.get("login", "unknown")
            return True
        except Exception as e:
            self.status = IntegrationStatus.ERROR
            self.last_error = str(e)
            return False

    def disconnect(self) -> None:
        """Disconnect from GitHub."""
        self.token = None
        self._headers = {}
        self.status = IntegrationStatus.DISCONNECTED

    def poll(self) -> List[Dict[str, Any]]:
        """Poll for new notifications."""
        if self.status != IntegrationStatus.CONNECTED:
            return []

        try:
            self._poll_count += 1
            self.last_poll = datetime.now().isoformat(timespec="seconds")

            params = ""
            if self._last_notification_id:
                params = f"?since={self.last_poll}"

            notifications = self._http_get(
                f"{GITHUB_API}/notifications{params}",
                self._headers
            )

            events = []
            for notif in notifications[:10]:
                events.append({
                    "type": "github_notification",
                    "source": "github",
                    "repo": notif.get("repository", {}).get("full_name", ""),
                    "reason": notif.get("reason", ""),
                    "title": notif.get("subject", {}).get("title", ""),
                    "url": notif.get("subject", {}).get("url", ""),
                    "unread": notif.get("unread", False)
                })

            if notifications:
                self._last_notification_id = notifications[0].get("id")

            return events

        except Exception as e:
            self.last_error = str(e)
            return []

    def send(self, target: str, message: str, **kwargs) -> bool:
        """
        Send to GitHub (create issue comment, etc.)+

        target: "owner/repo#123" format for issue comments
        """
        if self.status != IntegrationStatus.CONNECTED:
            return False

        try:
            # Parse target: owner/repo#123
            if "#" in target:
                repo, issue_num = target.rsplit("#", 1)
                url = f"{GITHUB_API}/repos/{repo}/issues/{issue_num}/comments"
                self._http_post(url, {"body": message}, self._headers)
                return True
            return False
        except Exception as e:
            self.last_error = str(e)
            return False

    # ── GitHub-specific methods ──

    def list_repos(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List user's repos."""
        if self.status != IntegrationStatus.CONNECTED:
            return []

        try:
            repos = self._http_get(
                f"{GITHUB_API}/user/repos?sort=updated&per_page={limit}",
                self._headers
            )
            return [
                {
                    "name": r["full_name"],
                    "description": r.get("description", ""),
                    "stars": r.get("stargazers_count", 0),
                    "language": r.get("language", ""),
                    "updated": r.get("updated_at", ""),
                    "private": r.get("private", False)
                }
                for r in repos
            ]
        except Exception:
            return []

    def get_repo_activity(self, repo: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent activity for a repo."""
        if self.status != IntegrationStatus.CONNECTED:
            return []

        try:
            events = self._http_get(
                f"{GITHUB_API}/repos/{repo}/events?per_page={limit}",
                self._headers
            )
            return [
                {
                    "type": e.get("type", ""),
                    "actor": e.get("actor", {}).get("login", ""),
                    "created_at": e.get("created_at", ""),
                    "payload_action": e.get("payload", {}).get("action", "")
                }
                for e in events
            ]
        except Exception:
            return []

    def watch_repo(self, repo: str) -> None:
        """Add a repo to the watch list."""
        if repo not in self._watched_repos:
            self._watched_repos.append(repo)

    def unwatch_repo(self, repo: str) -> None:
        """Remove a repo from the watch list."""
        if repo in self._watched_repos:
            self._watched_repos.remove(repo)

    def get_status(self) -> Dict[str, Any]:
        """Extended status with GitHub-specific info."""
        status = super().get_status()
        status["username"] = getattr(self, "_username", None)
        status["watched_repos"] = self._watched_repos
        return status
