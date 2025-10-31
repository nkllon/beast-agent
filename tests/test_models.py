"""Tests for pydantic models."""

import os
import pytest
from pydantic import ValidationError

from beast_agent.models import AgentConfig


def test_agent_config_defaults():
    """Test AgentConfig with default values."""
    config = AgentConfig()

    assert config.log_level == "INFO"
    assert config.heartbeat_interval == 30


def test_agent_config_custom_values():
    """Test AgentConfig with custom values."""
    config = AgentConfig(log_level="DEBUG", heartbeat_interval=60)

    assert config.log_level == "DEBUG"
    assert config.heartbeat_interval == 60


def test_agent_config_validate_log_level():
    """Test log level validation."""
    # Valid levels
    for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        config = AgentConfig(log_level=level)
        assert config.log_level == level

    # Case insensitive
    config = AgentConfig(log_level="debug")
    assert config.log_level == "DEBUG"

    # Invalid level
    with pytest.raises(ValidationError) as exc_info:
        AgentConfig(log_level="INVALID")
    assert "log_level must be one of" in str(exc_info.value)


def test_agent_config_validate_heartbeat_interval():
    """Test heartbeat interval validation."""
    # Valid interval
    config = AgentConfig(heartbeat_interval=30)
    assert config.heartbeat_interval == 30

    # Minimum is 1
    config = AgentConfig(heartbeat_interval=1)
    assert config.heartbeat_interval == 1

    # Invalid: less than 1
    with pytest.raises(ValidationError) as exc_info:
        AgentConfig(heartbeat_interval=0)
    assert "greater than or equal to 1" in str(exc_info.value).lower()

    with pytest.raises(ValidationError) as exc_info:
        AgentConfig(heartbeat_interval=-1)
    assert "greater than or equal to 1" in str(exc_info.value).lower()


def test_agent_config_from_env():
    """Test loading config from environment variables."""
    # Set env vars
    os.environ["AGENT_LOG_LEVEL"] = "DEBUG"
    os.environ["AGENT_HEARTBEAT_INTERVAL"] = "45"

    try:
        config = AgentConfig.from_env()
        assert config.log_level == "DEBUG"
        assert config.heartbeat_interval == 45
    finally:
        # Cleanup
        os.environ.pop("AGENT_LOG_LEVEL", None)
        os.environ.pop("AGENT_HEARTBEAT_INTERVAL", None)


def test_agent_config_from_env_defaults():
    """Test from_env uses defaults when env vars not set."""
    # Ensure env vars are not set
    os.environ.pop("AGENT_LOG_LEVEL", None)
    os.environ.pop("AGENT_HEARTBEAT_INTERVAL", None)

    config = AgentConfig.from_env()
    assert config.log_level == "INFO"
    assert config.heartbeat_interval == 30


def test_agent_config_from_dict():
    """Test creating config from dictionary."""
    data = {"log_level": "WARNING", "heartbeat_interval": 60}
    config = AgentConfig.from_dict(data)

    assert config.log_level == "WARNING"
    assert config.heartbeat_interval == 60


def test_agent_config_to_dict():
    """Test converting config to dictionary."""
    config = AgentConfig(log_level="ERROR", heartbeat_interval=90)
    data = config.to_dict()

    assert data["log_level"] == "ERROR"
    assert data["heartbeat_interval"] == 90


def test_agent_config_get_log_level_int():
    """Test getting log level as integer constant."""
    import logging

    config = AgentConfig(log_level="DEBUG")
    assert config.get_log_level_int() == logging.DEBUG

    config = AgentConfig(log_level="INFO")
    assert config.get_log_level_int() == logging.INFO

    config = AgentConfig(log_level="WARNING")
    assert config.get_log_level_int() == logging.WARNING

    config = AgentConfig(log_level="ERROR")
    assert config.get_log_level_int() == logging.ERROR

    config = AgentConfig(log_level="CRITICAL")
    assert config.get_log_level_int() == logging.CRITICAL


def test_agent_config_reject_unknown_fields():
    """Test that config rejects unknown fields."""
    with pytest.raises(ValidationError) as exc_info:
        AgentConfig(unknown_field="value")
    assert "Extra inputs are not permitted" in str(
        exc_info.value
    ) or "unknown_field" in str(exc_info.value)


def test_agent_config_immutable():
    """Test that config is immutable after creation."""
    config = AgentConfig(log_level="INFO", heartbeat_interval=30)

    # Pydantic frozen models raise ValidationError on assignment
    with pytest.raises((ValidationError, TypeError)):
        config.log_level = "DEBUG"
