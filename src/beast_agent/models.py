"""Pydantic models for beast-agent configuration and messages."""

import logging
import os
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AgentConfig(BaseModel):
    """Configuration model for BaseAgent instances.

    This model validates agent configuration from environment variables
    or constructor arguments, ensuring type safety and validation.

    Attributes:
        log_level: Python logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        heartbeat_interval: Heartbeat interval in seconds (must be > 0)
    """

    log_level: str = Field(
        default="INFO",
        description="Python logging level",
    )
    heartbeat_interval: int = Field(
        default=30,
        ge=1,
        description="Heartbeat interval in seconds (minimum: 1)",
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log_level is a valid logging level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        upper_v = v.upper()
        if upper_v not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}, got {v}")
        return upper_v

    @classmethod
    def from_env(cls) -> "AgentConfig":
        """Load configuration from environment variables.

        Environment variables:
            AGENT_LOG_LEVEL: Logging level (default: INFO)
            AGENT_HEARTBEAT_INTERVAL: Heartbeat interval in seconds (default: 30)

        Returns:
            AgentConfig instance loaded from environment
        """
        return cls(
            log_level=os.getenv("AGENT_LOG_LEVEL", "INFO"),
            heartbeat_interval=int(os.getenv("AGENT_HEARTBEAT_INTERVAL", "30")),
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentConfig":
        """Create AgentConfig from dictionary.

        Args:
            data: Dictionary with config values

        Returns:
            AgentConfig instance

        Raises:
            pydantic.ValidationError: If data is invalid
        """
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert AgentConfig to dictionary.

        Returns:
            Dictionary representation of configuration
        """
        return self.model_dump()

    def get_log_level_int(self) -> int:
        """Get log level as Python logging constant.

        Returns:
            Integer log level constant (e.g., logging.INFO)
        """
        return getattr(logging, self.log_level)

    model_config = ConfigDict(
        frozen=True,  # Immutable after creation
        extra="forbid",  # Reject unknown fields
    )
