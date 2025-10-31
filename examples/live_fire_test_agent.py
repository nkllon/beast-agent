"""Live-fire test agent for production cluster testing.

This agent connects to the production Redis cluster, discovers other agents,
and tests communication.
"""

import asyncio
import os
from pathlib import Path
from beast_agent import BaseAgent

# Load environment variables from ~/.env if not already set
def load_env_file():
    """Load environment variables from ~/.env file if they exist."""
    env_file = Path.home() / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    # Remove quotes if present
                    value = value.strip().strip('"').strip("'")
                    # Only set if not already in environment
                    if key not in os.environ:
                        os.environ[key] = value

# Load env vars before creating agent
load_env_file()


class LiveFireTestAgent(BaseAgent):
    """Agent for live-fire testing on production cluster."""

    def __init__(self):
        # BaseAgent automatically reads REDIS_HOST, REDIS_PORT, REDIS_PASSWORD from env vars
        super().__init__(
            agent_id="beast-agent-live-fire",
            capabilities=["testing", "discovery", "communication"],
            mailbox_url=None,  # Auto-configures from REDIS_HOST, REDIS_PORT, REDIS_PASSWORD env vars
        )

    async def on_startup(self) -> None:
        """Called after mailbox connection is established."""
        self._logger.info("=== Live-Fire Test Agent Starting ===")
        self._logger.info(f"Agent ID: {self.agent_id}")
        self._logger.info(f"Capabilities: {self.capabilities}")

        # Register message handlers
        self.register_handler("HELP_REQUEST", self.handle_help_request)
        self.register_handler("CHAT_MESSAGE", self.handle_chat_message)
        self.register_handler("PING", self.handle_ping)

        self._logger.info("Message handlers registered")

        # Wait a moment for registration
        await asyncio.sleep(0.5)

        # Discover all agents on the cluster
        self._logger.info("\n=== Discovering Agents on Cluster ===")
        all_agents = await self.discover_agents()

        if not all_agents:
            self._logger.warning("⚠️  No other agents found on cluster")
            self._logger.info("This agent is the only one online")
        else:
            self._logger.info(f"✅ Found {len(all_agents)} agent(s) on cluster:")
            for agent_id in all_agents:
                self._logger.info(f"  - {agent_id}")

            # Get detailed info about each agent
            self._logger.info("\n=== Agent Details ===")
            for agent_id in all_agents:
                if agent_id != self.agent_id:  # Skip ourselves
                    agent_info = await self.get_agent_info(agent_id)
                    if agent_info:
                        self._logger.info(f"\nAgent: {agent_info['agent_id']}")
                        self._logger.info(
                            f"  Capabilities: {', '.join(agent_info.get('capabilities', []))}"
                        )
                        self._logger.info(
                            f"  State: {agent_info.get('state', 'unknown')}"
                        )
                        self._logger.info(
                            f"  Registered: {agent_info.get('registered_at', 'unknown')}"
                        )

            # Try to find agents with specific capabilities
            self._logger.info("\n=== Finding Agents by Capability ===")
            for capability in ["help", "communication", "testing", "discovery"]:
                matching = await self.find_agents_by_capability(capability)
                if matching:
                    self._logger.info(
                        f"  Capability '{capability}': {len(matching)} agent(s)"
                    )
                    for agent_info in matching:
                        self._logger.info(f"    - {agent_info['agent_id']}")

            # Try to send a ping to the first discovered agent
            if all_agents and len(all_agents) > 1:
                other_agent = next(
                    (aid for aid in all_agents if aid != self.agent_id), None
                )
                if other_agent:
                    self._logger.info(
                        f"\n=== Sending Test Message to {other_agent} ==="
                    )
                    try:
                        message_id = await self.send_message(
                            target=other_agent,
                            message_type="PING",
                            content={
                                "message": "Hello from beast-agent live-fire test!",
                                "sender": self.agent_id,
                                "timestamp": asyncio.get_event_loop().time(),
                            },
                        )
                        self._logger.info(f"✅ Message sent! Message ID: {message_id}")
                    except Exception as e:
                        self._logger.error(
                            f"❌ Failed to send message: {e}", exc_info=True
                        )

        self._logger.info("\n=== Live-Fire Test Complete ===")
        self._logger.info("Agent is ready and registered on cluster")
        self._logger.info("Press Ctrl+C to stop")

    async def handle_help_request(self, content: dict) -> None:
        """Handle help request from another agent."""
        sender = content.get("sender", "unknown")
        request = content.get("request", "")
        self._logger.info(f"📨 Received HELP_REQUEST from {sender}: {request}")

        # Send response back
        await self.send_message(
            target=sender,
            message_type="HELP_RESPONSE",
            content={
                "response": "I can help with testing and discovery!",
                "agent_id": self.agent_id,
                "capabilities": self.capabilities,
            },
        )

    async def handle_chat_message(self, content: dict) -> None:
        """Handle chat message from another agent."""
        sender = content.get("sender", "unknown")
        message = content.get("message", "")
        self._logger.info(f"💬 Received CHAT_MESSAGE from {sender}: {message}")

    async def handle_ping(self, content: dict) -> None:
        """Handle ping from another agent."""
        sender = content.get("sender", "unknown")
        message = content.get("message", "")
        self._logger.info(f"🏓 Received PING from {sender}: {message}")

        # Send pong back
        await self.send_message(
            target=sender,
            message_type="PONG",
            content={
                "response": "Pong from beast-agent!",
                "sender": self.agent_id,
                "original_message": message,
            },
        )

    async def on_shutdown(self) -> None:
        """Called before mailbox disconnection."""
        self._logger.info("=== Live-Fire Test Agent Shutting Down ===")


async def main():
    """Run the live-fire test agent."""
    agent = LiveFireTestAgent()

    # Start agent
    await agent.startup()

    # Keep agent running
    try:
        await asyncio.sleep(3600)  # Run for 1 hour, or use your own loop
    except KeyboardInterrupt:
        agent._logger.info("\n=== Shutting down... ===")
    finally:
        await agent.shutdown()
        agent._logger.info("=== Agent stopped ===")


if __name__ == "__main__":
    asyncio.run(main())
