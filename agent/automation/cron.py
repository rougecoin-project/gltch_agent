"""
GLTCH Cron Scheduler
Schedule recurring tasks and agent actions
"""

import asyncio
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Callable, Awaitable, Any
from enum import Enum
import re


class CronStatus(Enum):
    """Cron job status"""
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"
    ERROR = "error"


@dataclass
class CronConfig:
    """Cron scheduler configuration"""
    enabled: bool = True
    max_concurrent_jobs: int = 5
    default_timezone: str = "UTC"
    job_timeout: int = 300  # seconds
    persist_jobs: bool = True
    jobs_file: str = ".gltch/cron_jobs.yaml"


@dataclass
class CronJob:
    """Scheduled cron job"""
    id: str
    name: str
    schedule: str  # Cron expression: "*/5 * * * *" or "@hourly"
    action: str    # Action to execute (e.g., "send_message", "run_tool")
    params: Dict[str, Any] = field(default_factory=dict)
    
    # Optional settings
    channel: Optional[str] = None
    session_id: Optional[str] = None
    enabled: bool = True
    status: CronStatus = CronStatus.ACTIVE
    
    # Execution tracking
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
    
    def __post_init__(self):
        self.next_run = self._calculate_next_run()
    
    def _calculate_next_run(self) -> Optional[datetime]:
        """Calculate next run time from cron expression"""
        try:
            from croniter import croniter
            cron = croniter(self.schedule, datetime.now())
            return cron.get_next(datetime)
        except ImportError:
            # Fallback: simple interval parsing
            return self._parse_simple_schedule()
        except Exception:
            return None
    
    def _parse_simple_schedule(self) -> Optional[datetime]:
        """Parse simple schedule formats like @hourly, @daily"""
        now = datetime.now()
        
        aliases = {
            "@hourly": 3600,
            "@daily": 86400,
            "@weekly": 604800,
            "@monthly": 2592000,
        }
        
        if self.schedule in aliases:
            from datetime import timedelta
            return now + timedelta(seconds=aliases[self.schedule])
        
        # Try to parse as interval: "every 5m", "every 1h"
        match = re.match(r'every\s+(\d+)([smhd])', self.schedule, re.IGNORECASE)
        if match:
            from datetime import timedelta
            value = int(match.group(1))
            unit = match.group(2).lower()
            
            multipliers = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
            seconds = value * multipliers.get(unit, 60)
            return now + timedelta(seconds=seconds)
        
        return None


class CronScheduler:
    """
    Manages scheduled cron jobs
    
    Supports standard cron expressions and simple interval formats:
    - "*/5 * * * *" - Every 5 minutes
    - "@hourly" - Every hour
    - "every 30m" - Every 30 minutes
    """
    
    def __init__(self, config: Optional[CronConfig] = None):
        self.config = config or CronConfig()
        self.jobs: Dict[str, CronJob] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._handlers: Dict[str, Callable[..., Awaitable[Any]]] = {}
    
    def register_handler(
        self, 
        action: str, 
        handler: Callable[..., Awaitable[Any]]
    ) -> None:
        """Register a handler for a cron action"""
        self._handlers[action] = handler
    
    def add_job(self, job: CronJob) -> bool:
        """Add a cron job"""
        if job.id in self.jobs:
            return False
        
        self.jobs[job.id] = job
        self._save_jobs()
        return True
    
    def remove_job(self, job_id: str) -> bool:
        """Remove a cron job"""
        if job_id in self.jobs:
            del self.jobs[job_id]
            self._save_jobs()
            return True
        return False
    
    def get_job(self, job_id: str) -> Optional[CronJob]:
        """Get a cron job by ID"""
        return self.jobs.get(job_id)
    
    def list_jobs(self) -> List[CronJob]:
        """List all cron jobs"""
        return list(self.jobs.values())
    
    def pause_job(self, job_id: str) -> bool:
        """Pause a cron job"""
        job = self.jobs.get(job_id)
        if job:
            job.status = CronStatus.PAUSED
            self._save_jobs()
            return True
        return False
    
    def resume_job(self, job_id: str) -> bool:
        """Resume a paused cron job"""
        job = self.jobs.get(job_id)
        if job:
            job.status = CronStatus.ACTIVE
            job.next_run = job._calculate_next_run()
            self._save_jobs()
            return True
        return False
    
    async def start(self) -> None:
        """Start the cron scheduler"""
        if self._running:
            return
        
        self._running = True
        self._load_jobs()
        self._task = asyncio.create_task(self._run_loop())
        print("✓ Cron scheduler started")
    
    async def stop(self) -> None:
        """Stop the cron scheduler"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._save_jobs()
        print("✓ Cron scheduler stopped")
    
    async def _run_loop(self) -> None:
        """Main scheduler loop"""
        while self._running:
            now = datetime.now()
            
            # Check each job
            for job in self.jobs.values():
                if not job.enabled or job.status != CronStatus.ACTIVE:
                    continue
                
                if job.next_run and now >= job.next_run:
                    # Execute job
                    asyncio.create_task(self._execute_job(job))
            
            # Sleep until next check
            await asyncio.sleep(1)
    
    async def _execute_job(self, job: CronJob) -> None:
        """Execute a cron job"""
        handler = self._handlers.get(job.action)
        if not handler:
            job.last_error = f"No handler for action: {job.action}"
            job.error_count += 1
            job.status = CronStatus.ERROR
            return
        
        try:
            # Execute with timeout
            await asyncio.wait_for(
                handler(job.params, job.channel, job.session_id),
                timeout=self.config.job_timeout
            )
            
            job.last_run = datetime.now()
            job.run_count += 1
            job.last_error = None
            job.next_run = job._calculate_next_run()
            
        except asyncio.TimeoutError:
            job.last_error = "Job timed out"
            job.error_count += 1
        except Exception as e:
            job.last_error = str(e)
            job.error_count += 1
        
        self._save_jobs()
    
    async def run_now(self, job_id: str) -> bool:
        """Run a job immediately"""
        job = self.jobs.get(job_id)
        if not job:
            return False
        
        await self._execute_job(job)
        return True
    
    def _load_jobs(self) -> None:
        """Load jobs from file"""
        if not self.config.persist_jobs:
            return
        
        try:
            import yaml
            with open(self.config.jobs_file, 'r') as f:
                data = yaml.safe_load(f)
                if data and 'jobs' in data:
                    for job_data in data['jobs']:
                        job = CronJob(**job_data)
                        self.jobs[job.id] = job
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"Error loading cron jobs: {e}")
    
    def _save_jobs(self) -> None:
        """Save jobs to file"""
        if not self.config.persist_jobs:
            return
        
        try:
            import yaml
            from dataclasses import asdict
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config.jobs_file), exist_ok=True)
            
            jobs_data = []
            for job in self.jobs.values():
                job_dict = asdict(job)
                # Convert datetime to string
                for key in ['last_run', 'next_run']:
                    if job_dict[key]:
                        job_dict[key] = job_dict[key].isoformat()
                # Convert enum to string
                job_dict['status'] = job_dict['status'].value
                jobs_data.append(job_dict)
            
            with open(self.config.jobs_file, 'w') as f:
                yaml.dump({'jobs': jobs_data}, f)
        except Exception as e:
            print(f"Error saving cron jobs: {e}")
    
    def get_status(self) -> dict:
        """Get scheduler status"""
        return {
            "enabled": self.config.enabled,
            "running": self._running,
            "total_jobs": len(self.jobs),
            "active_jobs": sum(1 for j in self.jobs.values() if j.status == CronStatus.ACTIVE),
            "paused_jobs": sum(1 for j in self.jobs.values() if j.status == CronStatus.PAUSED),
            "error_jobs": sum(1 for j in self.jobs.values() if j.status == CronStatus.ERROR),
        }
    
    @classmethod
    def from_env(cls) -> 'CronScheduler':
        """Create scheduler from environment variables"""
        config = CronConfig(
            enabled=os.getenv('GLTCH_CRON_ENABLED', 'true').lower() == 'true',
            max_concurrent_jobs=int(os.getenv('GLTCH_CRON_MAX_JOBS', '5')),
            job_timeout=int(os.getenv('GLTCH_CRON_TIMEOUT', '300')),
        )
        return cls(config)
