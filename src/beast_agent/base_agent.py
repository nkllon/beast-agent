"""Base agent class for all Beast Mode agents."""

import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from beast_agent.types import AgentState, HealthStatus


class BaseAgent(ABC):
    """
    Base class for all Beast Mode agents.

    This abstract base class provides standardized lifecycle, messaging,
    discovery, and capability management for all Beast Mode agents.

    Attributes:
        agent_id: Unique identifier for this agent instance
        capabilities: List of capability names this agent provides
        state: Current agent lifecycle state
        config: Agent configuration dictionary
    """

    def __init__(
        self,
        agent_id: str,
        capabilities: List[str],
        mailbox_url: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize agent with ID, capabilities, and configuration.

        Args:
            agent_id: Unique identifier for this agent
            capabilities: List of capability names
            mailbox_url: Optional Redis mailbox URL (defaults to REDIS_URL env var)
            config: Optional configuration dictionary
        """
        self.agent_id = agent_id
        self.capabilities = capabilities
        self.config = config or self._load_config()
        self._state = AgentState.INITIALIZING
        self._handlers: Dict[str, Callable] = {}
        self._error_count = 0
        self._last_heartbeat = datetime.now()
        self._logger = self._setup_logging()

        # Mailbox connection (lazy initialization in startup)
        self._mailbox_url = mailbox_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self._mailbox = None

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for agent."""
        logger = logging.getLogger(f"beast-agent.{self.agent_id}")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                f"%(asctime)s - {self.agent_id} - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment or defaults."""
        return {
            "log_level": os.getenv("AGENT_LOG_LEVEL", "INFO"),
            "heartbeat_interval": int(os.getenv("AGENT_HEARTBEAT_INTERVAL", "30")),
        }

    async def startup(self) -> None:
        """
        Initialize agent and register with mailbox.

        This method:
        1. Connects to beast-mailbox-core
        2. Registers agent with discovery service
        3. Calls user-defined on_startup hook
        4. Transitions to READY state
        """
        self._logger.info(f"Starting agent {self.agent_id}")
        self._state = AgentState.INITIALIZING

        # TODO: Connect to beast-mailbox-core
        # from beast_mailbox_core import MailboxClient
        # self._mailbox = MailboxClient(self._mailbox_url)
        # await self._mailbox.connect()
        # await self._mailbox.register_agent(self.agent_id, self.capabilities)

        await self.on_startup()
        self._state = AgentState.READY
        self._last_heartbeat = datetime.now()
        self._logger.info(f"Agent {self.agent_id} ready")

    @abstractmethod
    async def on_startup(self) -> None:
        """
        Subclass hook for custom startup logic.

        Override this method to add agent-specific initialization.
        """
        pass

    async def shutdown(self) -> None:
        """
        Gracefully shutdown the agent.

        This method:
        1. Transitions to STOPPING state
        2. Calls user-defined on_shutdown hook
        3. Disconnects from mailbox
        4. Transitions to STOPPED state
        """
        self._logger.info(f"Stopping agent {self.agent_id}")
        self._state = AgentState.STOPPING

        await self.on_shutdown()

        # TODO: Disconnect from beast-mailbox-core
        # if self._mailbox:
        #     await self._mailbox.disconnect()

        self._state = AgentState.STOPPED
        self._logger.info(f"Agent {self.agent_id} stopped")

    @abstractmethod
    async def on_shutdown(self) -> None:
        """
        Subclass hook for custom shutdown logic.

        Override this method to add agent-specific cleanup.
        """
        pass

    def health_check(self) -> HealthStatus:
        """
        Return agent health status.

        Returns:
            HealthStatus object with current agent state
        """
        return HealthStatus(
            healthy=(self._state in [AgentState.READY, AgentState.RUNNING]),
            state=self._state,
            last_heartbeat=self._last_heartbeat,
            message_queue_size=0,  # TODO: Get from mailbox
            error_count=self._error_count,
            metadata={
                "agent_id": self.agent_id,
                "capabilities": self.capabilities,
            },
        )

    def ready(self) -> bool:
        """
        Return True if agent is ready to handle messages.

        Returns:
            True if agent state is READY or RUNNING
        """
        return self._state in [AgentState.READY, AgentState.RUNNING]

    def register_handler(self, message_type: str, handler: Callable) -> None:
        """
        Register handler for message type.

        Args:
            message_type: Message type to handle (e.g., "TASK_REQUEST")
            handler: Async callable to handle messages of this type
        """
        self._handlers[message_type] = handler
        self._logger.info(f"Registered handler for {message_type}")

    async def send_message(
        self, target: str, message_type: str, content: Dict[str, Any]
    ) -> None:
        """
        Send message to target agent.

        Args:
            target: Target agent ID
            message_type: Message type (e.g., "HELP_REQUEST")
            content: Message content dictionary
        """
        self._logger.info(f"Sending {message_type} to {target}")
        # TODO: Implement with beast-mailbox-core
        # await self._mailbox.send_message(target, message_type, content)

    async def handle_message(self, message: Dict[str, Any]) -> None:
        """
        Route message to registered handler.

        Args:
            message: Message dictionary with 'type' and 'content' keys
        """
        message_type = message.get("type")
        handler = self._handlers.get(message_type)

        if handler:
            try:
                await handler(message)
                self._last_heartbeat = datetime.now()
            except Exception as e:
                self._error_count += 1
                self._logger.error(f"Error handling {message_type}: {e}")
        else:
            self._logger.warning(f"No handler for message type: {message_type}")

