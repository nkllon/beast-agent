"""Example: Simple agent with a single capability."""

import asyncio
from beast_agent import BaseAgent
from beast_agent.decorators import capability


class SimpleAgent(BaseAgent):
    """A simple agent that processes data."""

    def __init__(self):
        super().__init__(
            agent_id="simple-agent", capabilities=["process_data", "echo"]
        )

    async def on_startup(self) -> None:
        """Initialize agent."""
        print(f"SimpleAgent {self.agent_id} starting up...")

    async def on_shutdown(self) -> None:
        """Cleanup agent."""
        print(f"SimpleAgent {self.agent_id} shutting down...")

    @capability("process_data", version="1.0.0")
    async def process_data(self, data: dict) -> dict:
        """Process incoming data."""
        print(f"Processing data: {data}")
        return {"status": "processed", "result": data}

    @capability("echo", version="1.0.0")
    async def echo(self, message: str) -> str:
        """Echo back a message."""
        return f"Echo: {message}"


async def main():
    """Run the simple agent."""
    agent = SimpleAgent()

    # Start the agent
    await agent.startup()

    # Check health
    health = agent.health_check()
    print(f"Agent healthy: {health.healthy}, state: {health.state.value}")

    # Process some data
    result = await agent.process_data({"value": 42})
    print(f"Process result: {result}")

    # Echo a message
    echo = await agent.echo("Hello, Beast Mode!")
    print(echo)

    # Shutdown
    await agent.shutdown()


if __name__ == "__main__":
    asyncio.run(main())

