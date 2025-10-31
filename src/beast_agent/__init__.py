"""Beast Agent - Base agent class for all Beast Mode agents."""

from beast_agent.base_agent import BaseAgent
from beast_agent.models import AgentConfig
from beast_agent.types import AgentState, HealthStatus
from beast_agent.decorators import capability

__version__ = "0.1.0"
__all__ = ["BaseAgent", "AgentState", "HealthStatus", "AgentConfig", "capability"]

