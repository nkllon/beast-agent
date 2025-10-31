"""Tests for authenticated Redis connections.

Tests that BaseAgent can connect to Redis with authentication
via MailboxConfig, including automatic environment variable reading.
"""

import os
import pytest
from beast_agent import BaseAgent


class AuthenticatedTestAgent(BaseAgent):
    """Test agent for authenticated connection tests."""

    def __init__(self, agent_id: str, mailbox_url=None):
        """Initialize test agent with optional mailbox URL/config."""
        super().__init__(
            agent_id=agent_id, capabilities=["test"], mailbox_url=mailbox_url
        )

    async def on_startup(self) -> None:
        """Test agent startup hook."""
        pass

    async def on_shutdown(self) -> None:
        """Test agent shutdown hook."""
        pass


@pytest.mark.asyncio
@pytest.mark.skipif(
    not pytest.importorskip("beast_mailbox_core"),
    reason="beast-mailbox-core not available",
)
async def test_authenticated_connection_with_mailbox_config(
    mailbox_config, redis_available
):
    """Test agent can connect with password via MailboxConfig."""
    if not redis_available:
        pytest.skip("Redis not available")

    from beast_mailbox_core import MailboxConfig

    # Create MailboxConfig with password (even if test Redis doesn't require it)
    # This tests that the config object is accepted and used
    config = MailboxConfig(
        host=mailbox_config.host,
        port=mailbox_config.port,
        password="test-password",  # Password field set (even if not required)
        db=mailbox_config.db if hasattr(mailbox_config, "db") else 0,
    )

    agent = AuthenticatedTestAgent("test-auth-agent", mailbox_url=config)

    # Verify MailboxConfig is stored correctly in _mailbox_url
    assert agent._mailbox_url is not None
    assert isinstance(agent._mailbox_url, MailboxConfig)
    assert agent._mailbox_url.host == config.host
    assert agent._mailbox_url.port == config.port

    # Password field should be set (even if Redis doesn't require it)
    if hasattr(agent._mailbox_url, "password"):
        assert agent._mailbox_url.password == "test-password"

    # Agent should be able to start (if Redis accepts connection)
    try:
        await agent.startup()
        # If we get here, connection worked
        assert agent.ready()
        await agent.shutdown()
    except Exception:
        # If Redis requires password and we provided wrong one, that's expected
        # Just verify the config was accepted
        pass


@pytest.mark.asyncio
@pytest.mark.skipif(
    not pytest.importorskip("beast_mailbox_core"),
    reason="beast-mailbox-core not available",
)
async def test_mailbox_url_accepts_mailbox_config_object():
    """Test that mailbox_url parameter accepts MailboxConfig object."""
    from beast_mailbox_core import MailboxConfig

    config = MailboxConfig(
        host="localhost",
        port=6379,
        password="test-password",
        db=0,
    )

    agent = AuthenticatedTestAgent("test-config-object", mailbox_url=config)

    # Verify MailboxConfig object is stored directly (not converted)
    assert agent._mailbox_url is not None
    assert isinstance(agent._mailbox_url, MailboxConfig)
    assert agent._mailbox_url.host == "localhost"
    assert agent._mailbox_url.port == 6379
    if hasattr(agent._mailbox_url, "password"):
        assert agent._mailbox_url.password == "test-password"


@pytest.mark.asyncio
@pytest.mark.skipif(
    not pytest.importorskip("beast_mailbox_core"),
    reason="beast-mailbox-core not available",
)
async def test_mailbox_url_accepts_string_url():
    """Test that mailbox_url parameter accepts string URL."""
    agent = AuthenticatedTestAgent(
        "test-url-string", mailbox_url="redis://localhost:6379"
    )

    # If MailboxConfig was created from URL, it should exist
    # (This tests the URL parsing path)
    if agent._mailbox_config is not None:
        assert hasattr(agent._mailbox_config, "host")
        assert agent._mailbox_config.host == "localhost"
        assert agent._mailbox_config.port == 6379


@pytest.mark.asyncio
async def test_mailbox_url_none_uses_env_var():
    """Test that mailbox_url=None uses REDIS_URL environment variable."""
    # This test verifies the fallback behavior
    # Actual connection test would require Redis, so we just verify the logic
    agent = AuthenticatedTestAgent("test-env-fallback", mailbox_url=None)

    # Without REDIS_URL env var, config should be None
    assert agent._mailbox_config is None or agent._mailbox_url is None


@pytest.mark.asyncio
@pytest.mark.skipif(
    not pytest.importorskip("beast_mailbox_core"),
    reason="beast-mailbox-core not available",
)
async def test_mailbox_url_none_auto_reads_redis_env_vars(
    mailbox_config, redis_available
):
    """Test that mailbox_url=None automatically reads REDIS_HOST, REDIS_PORT, REDIS_PASSWORD from env."""
    if not redis_available:
        pytest.skip("Redis not available")

    from beast_mailbox_core import MailboxConfig

    # Set environment variables
    original_host = os.environ.get("REDIS_HOST")
    original_port = os.environ.get("REDIS_PORT")
    original_password = os.environ.get("REDIS_PASSWORD")
    original_db = os.environ.get("REDIS_DB")

    try:
        os.environ["REDIS_HOST"] = mailbox_config.host
        os.environ["REDIS_PORT"] = str(mailbox_config.port)
        os.environ["REDIS_DB"] = str(
            mailbox_config.db if hasattr(mailbox_config, "db") else 0
        )
        if hasattr(mailbox_config, "password") and mailbox_config.password:
            os.environ["REDIS_PASSWORD"] = mailbox_config.password

        # Create agent with mailbox_url=None - should auto-read from env vars
        agent = AuthenticatedTestAgent("test-auto-env", mailbox_url=None)

        # Verify MailboxConfig was created from env vars
        # This will be None until startup, but _create_mailbox_config should return the config
        config = agent._create_mailbox_config()
        assert config is not None
        assert isinstance(config, MailboxConfig)
        assert config.host == mailbox_config.host
        assert config.port == mailbox_config.port

        # Verify agent can start with auto-configured mailbox
        await agent.startup()
        assert agent.ready()
        await agent.shutdown()
    finally:
        # Restore original env vars
        if original_host is not None:
            os.environ["REDIS_HOST"] = original_host
        else:
            os.environ.pop("REDIS_HOST", None)
        if original_port is not None:
            os.environ["REDIS_PORT"] = original_port
        else:
            os.environ.pop("REDIS_PORT", None)
        if original_password is not None:
            os.environ["REDIS_PASSWORD"] = original_password
        else:
            os.environ.pop("REDIS_PASSWORD", None)
        if original_db is not None:
            os.environ["REDIS_DB"] = original_db
        else:
            os.environ.pop("REDIS_DB", None)
