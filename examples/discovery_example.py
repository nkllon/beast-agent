"""Example: Agent discovery and multi-agent communication.

This example shows how to:
- Discover other agents on the cluster
- Get agent metadata and capabilities
- Find agents by capability
- Send messages to discovered agents
"""

import asyncio
import os
from beast_agent import BaseAgent
from beast_mailbox_core import MailboxConfig


class DiscoveryAgent(BaseAgent):
    """Agent that demonstrates cluster discovery."""

    def __init__(self):
        # Load Redis configuration from environment variables
        mailbox_config = MailboxConfig(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            password=os.getenv(
                "REDIS_PASSWORD"
            ),  # Optional, for authenticated clusters
            db=int(os.getenv("REDIS_DB", "0")),
        )

        super().__init__(
            agent_id="discovery-example-agent",
            capabilities=["discover", "communicate", "example"],
            mailbox_url=mailbox_config,
        )

    async def on_startup(self) -> None:
        """Called after mailbox connection is established."""
        self._logger.info("Discovery agent starting up...")

        # Register handler for incoming messages
        self.register_handler("HELP_REQUEST", self.handle_help_request)
        self.register_handler("CHAT_MESSAGE", self.handle_chat)

        # Discover all agents on the cluster
        all_agents = await self.discover_agents()
        self._logger.info(f"Found {len(all_agents)} agents on cluster: {all_agents}")

        # Get info about specific agents (if they exist)
        for agent_id in all_agents:
            if agent_id != self.agent_id:  # Skip ourselves
                agent_info = await self.get_agent_info(agent_id)
                if agent_info:
                    self._logger.info(
                        f"Agent {agent_id} capabilities: {agent_info.get('capabilities', [])}"
                    )

        # Find agents with specific capabilities
        help_agents = await self.find_agents_by_capability("help")
        self._logger.info(f"Found {len(help_agents)} agents with 'help' capability")

        # Find agents with 'communicate' capability
        comm_agents = await self.find_agents_by_capability("communicate")
        self._logger.info(
            f"Found {len(comm_agents)} agents with 'communicate' capability"
        )

        # Send a message to the first discovered agent (if any)
        if all_agents and len(all_agents) > 1:
            other_agent_id = next(
                (aid for aid in all_agents if aid != self.agent_id), None
            )
            if other_agent_id:
                self._logger.info(f"Sending greeting to {other_agent_id}")
                await self.send_message(
                    target=other_agent_id,
                    message_type="CHAT_MESSAGE",
                    content={
                        "message": "Hello from discovery agent!",
                        "sender": self.agent_id,
                    },
                )

    async def handle_help_request(self, content: dict) -> None:
        """Handle help request from another agent."""
        sender = content.get("sender", "unknown")
        request = content.get("request", "")
        self._logger.info(f"Received help request from {sender}: {request}")

        # Send response back
        await self.send_message(
            target=sender,
            message_type="HELP_RESPONSE",
            content={
                "response": "I can help!",
                "agent_id": self.agent_id,
                "capabilities": self.capabilities,
            },
        )

    async def handle_chat(self, content: dict) -> None:
        """Handle chat message from another agent."""
        sender = content.get("sender", "unknown")
        message = content.get("message", "")
        self._logger.info(f"Received chat from {sender}: {message}")

    async def on_shutdown(self) -> None:
        """Called before mailbox disconnection."""
        self._logger.info("Discovery agent shutting down...")


async def main():
    """Run the discovery agent."""
    # Set environment variables (or use secrets management in production)
    # os.environ["REDIS_HOST"] = "your-redis-host"
    # os.environ["REDIS_PORT"] = "6379"
    # os.environ["REDIS_PASSWORD"] = "your-redis-password"

    agent = DiscoveryAgent()

    # Start agent (connects to Redis and registers on cluster)
    await agent.startup()

    # Agent is now online and registered
    # Other agents can discover you via: beast:agents:all set in Redis
    # Your agent info is at: beast:agents:discovery-example-agent

    # Keep agent running
    try:
        agent._logger.info("Discovery agent running... Press Ctrl+C to stop")
        await asyncio.sleep(3600)  # Run for 1 hour, or use your own loop
    except KeyboardInterrupt:
        agent._logger.info("Shutting down...")
    finally:
        await agent.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
