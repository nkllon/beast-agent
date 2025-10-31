"""Example: Agent connecting to authenticated Redis cluster.

This example shows how to connect to a Redis cluster that requires
authentication using MailboxConfig instead of a URL string.
"""

import asyncio
import os
from beast_agent import BaseAgent
from beast_mailbox_core import MailboxConfig


class AuthenticatedAgent(BaseAgent):
    """Agent that connects to an authenticated Redis cluster."""

    def __init__(self):
        # Load Redis configuration from environment variables
        # For production, use secrets management instead of env vars
        mailbox_config = MailboxConfig(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            password=os.getenv("REDIS_PASSWORD"),  # Required for authenticated clusters
            db=int(os.getenv("REDIS_DB", "0")),
            stream_prefix="mailbox",
            enable_recovery=True,
        )

        super().__init__(
            agent_id="authenticated-agent",
            capabilities=["example"],
            mailbox_url=mailbox_config,  # Pass MailboxConfig object, not URL string
        )

    async def on_startup(self) -> None:
        """Called after mailbox connection is established."""
        self._logger.info("Connected to authenticated Redis cluster!")
        self._logger.info(f"Agent {self.agent_id} is ready and registered on cluster")

    async def on_shutdown(self) -> None:
        """Called before mailbox disconnection."""
        self._logger.info("Disconnecting from cluster...")


async def main():
    """Run the authenticated agent."""
    # Set environment variables (or use secrets management in production)
    # os.environ["REDIS_HOST"] = "your-redis-host"
    # os.environ["REDIS_PORT"] = "6379"
    # os.environ["REDIS_PASSWORD"] = "your-redis-password"

    agent = AuthenticatedAgent()

    # Start agent (connects to Redis and registers on cluster)
    await agent.startup()

    # Agent is now online and registered
    # Other agents can discover you via: beast:agents:all set in Redis
    # Your agent info is at: beast:agents:authenticated-agent

    # Keep agent running
    try:
        agent._logger.info("Agent running... Press Ctrl+C to stop")
        await asyncio.sleep(3600)  # Run for 1 hour, or use your own loop
    except KeyboardInterrupt:
        agent._logger.info("Shutting down...")
    finally:
        await agent.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
