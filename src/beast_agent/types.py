"""Type definitions for beast-agent."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict


class AgentState(Enum):
    """Agent lifecycle states."""

    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class HealthStatus:
    """Agent health status."""

    healthy: bool
    state: AgentState
    last_heartbeat: datetime
    message_queue_size: int
    error_count: int
    metadata: Dict[str, Any]
