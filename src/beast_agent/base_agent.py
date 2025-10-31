"""Base agent class for all Beast Mode agents."""

import json
import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

from beast_agent.models import AgentConfig
from beast_agent.types import AgentState, HealthStatus

if TYPE_CHECKING:
    from beast_mailbox_core import (
        RedisMailboxService,
        MailboxMessage,
        MailboxConfig,
        RecoveryMetrics,
    )


class BaseAgent(ABC):
    """
    Base class for all Beast Mode agents.

    This abstract base class provides standardized lifecycle, messaging,
    discovery, and capability management for all Beast Mode agents.

    Attributes:
        agent_id: Unique identifier for this agent instance
        capabilities: List of capability names this agent provides
        state: Current agent lifecycle state
        config: Agent configuration (AgentConfig pydantic model)
    """

    def __init__(
        self,
        agent_id: str,
        capabilities: List[str],
        mailbox_url: Optional[Any] = None,
        config: Optional[AgentConfig] = None,
    ):
        """
        Initialize agent with ID, capabilities, and configuration.

        Args:
            agent_id: Unique identifier for this agent instance
            capabilities: List of capability names this agent provides
            mailbox_url: Redis connection configuration. Accepts:
                - str: Redis URL string (e.g., "redis://localhost:6379") for unauthenticated connections
                - MailboxConfig: Advanced configuration object with authentication support (recommended for production)
                - None: Uses REDIS_URL environment variable
            config: Agent configuration (uses AgentConfig.from_env() if None)

        Raises:
            pydantic.ValidationError: If config validation fails
        """
        self.agent_id = agent_id
        self.capabilities = capabilities

        # Validate and load configuration
        if config is None:
            self.config = self._load_config()
        else:
            # Config is already validated (pydantic model)
            self.config = config

        self._state = AgentState.INITIALIZING
        self._handlers: Dict[str, Callable] = {}
        self._error_count = 0
        self._last_heartbeat = datetime.now()
        self._logger = self._setup_logging()

        # Mailbox connection (lazy initialization in startup)
        # Only set mailbox_url if explicitly provided or REDIS_URL is set
        # If None and no env var, agent operates without mailbox
        if mailbox_url is None:
            mailbox_url = os.getenv("REDIS_URL")  # May be None

        self._mailbox_url = mailbox_url
        self._mailbox: Optional["RedisMailboxService"] = None
        self._mailbox_config: Optional["MailboxConfig"] = None

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
            # Use validated log level from config
            logger.setLevel(self.config.get_log_level_int())
        return logger

    def _load_config(self) -> AgentConfig:
        """Load and validate configuration from environment variables.

        Returns:
            AgentConfig instance validated with pydantic

        Raises:
            pydantic.ValidationError: If environment variables contain invalid values
        """
        return AgentConfig.from_env()

    def _create_mailbox_config(self) -> Optional["MailboxConfig"]:
        """Create MailboxConfig from URL or env vars.

        Returns:
            MailboxConfig instance configured for mailbox connection, or None if not available

        Note:
            Returns None if beast-mailbox-core is not installed or if mailbox is not configured.
            This allows agents to function without mailbox for basic operations.
        """
        try:
            from beast_mailbox_core import MailboxConfig

            # If mailbox_url is already a MailboxConfig instance, return it
            if isinstance(self._mailbox_url, MailboxConfig):
                return self._mailbox_url

            # Parse URL string (simple implementation - could be enhanced)
            # For now, assume redis://host:port format
            if self._mailbox_url is None:
                return None

            url = self._mailbox_url
            if url.startswith("redis://"):
                url = url[8:]  # Remove redis:// prefix

            # Parse host and port
            if ":" in url:
                host, port_str = url.rsplit(":", 1)
                port = int(port_str) if port_str.isdigit() else 6379
            else:
                host = url if url else "localhost"
                port = 6379

            return MailboxConfig(
                host=host,
                port=port,
                db=0,
                stream_prefix="mailbox",
            )
        except ImportError:
            # beast-mailbox-core not installed - mailbox features unavailable
            return None

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

        # Initialize mailbox service (if available and configured)
        self._mailbox_config = self._create_mailbox_config()

        if self._mailbox_config is not None:
            # Mailbox config available - try to start mailbox service
            try:
                from beast_mailbox_core import RedisMailboxService

                # Create mailbox service
                self._mailbox = RedisMailboxService(
                    agent_id=self.agent_id,
                    config=self._mailbox_config,
                    recovery_callback=(
                        self._handle_recovery
                        if hasattr(self, "_handle_recovery")
                        else None
                    ),
                )

                # Register mailbox message handler
                self._mailbox.register_handler(self._mailbox_message_handler)

                # Start mailbox service (connects to Redis)
                result = await self._mailbox.start()

                if not result:
                    self._logger.error(
                        f"Failed to start mailbox service for agent {self.agent_id}"
                    )
                    self._state = AgentState.ERROR
                    return

                self._logger.info(f"Mailbox service started for agent {self.agent_id}")

                # Register agent name on the cluster for discovery
                await self._register_agent_name()
            except ImportError:
                self._logger.warning(
                    "beast-mailbox-core not installed - continuing without mailbox"
                )
                # Continue without mailbox - agent can function without it
            except Exception as e:
                self._logger.error(
                    f"Error starting mailbox service: {e}", exc_info=True
                )
                self._state = AgentState.ERROR
                raise
        else:
            # Mailbox not configured - agent operates without mailbox
            self._logger.debug("Mailbox not configured - operating without mailbox")

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

        # Unregister agent name from cluster
        await self._unregister_agent_name()

        # Stop mailbox service
        if self._mailbox:
            try:
                await self._mailbox.stop()
                self._logger.info(f"Mailbox service stopped for agent {self.agent_id}")
            except Exception as e:
                self._logger.error(
                    f"Error stopping mailbox service: {e}", exc_info=True
                )

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
        # Get message queue size from mailbox if available
        message_queue_size = 0
        if self._mailbox and hasattr(self._mailbox, "_client"):
            try:
                # Try to get pending count from mailbox
                # This is a simplified implementation - actual implementation
                # would depend on mailbox-core API for pending message count
                pass
            except Exception:
                pass

        return HealthStatus(
            healthy=(self._state in [AgentState.READY, AgentState.RUNNING]),
            state=self._state,
            last_heartbeat=self._last_heartbeat,
            message_queue_size=message_queue_size,
            error_count=self._error_count,
            metadata={
                "agent_id": self.agent_id,
                "capabilities": self.capabilities,
                "mailbox_connected": self._mailbox is not None,
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
    ) -> str:
        """
        Send message to target agent via mailbox.

        Args:
            target: Target agent ID
            message_type: Message type (e.g., "HELP_REQUEST")
            content: Message content dictionary

        Returns:
            Message ID from mailbox service

        Raises:
            RuntimeError: If mailbox is not initialized
        """
        if not self._mailbox:
            raise RuntimeError("Mailbox not initialized. Call startup() first.")

        try:
            message_id = await self._mailbox.send_message(
                recipient=target,
                payload={"type": message_type, "content": content},
                message_type="direct_message",
            )

            self._logger.debug(f"Sent {message_type} to {target}: {message_id}")
            return message_id
        except Exception as e:
            self._error_count += 1
            self._logger.error(f"Error sending message to {target}: {e}", exc_info=True)
            raise

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

    async def _mailbox_message_handler(self, mailbox_message: "MailboxMessage") -> None:
        """Wrapper to route MailboxMessage to BaseAgent handlers.

        This method receives MailboxMessage from RedisMailboxService and routes
        it to the appropriate BaseAgent handler based on message type.

        Args:
            mailbox_message: MailboxMessage from mailbox service
        """
        try:
            # Extract payload (assumed to contain {"type": str, "content": dict})
            payload = mailbox_message.payload
            message_type = payload.get("type")

            # Route to registered handler
            if message_type in self._handlers:
                handler = self._handlers[message_type]
                # Pass content to handler (not full message dict)
                content = payload.get("content", {})
                await handler(content)
                self._last_heartbeat = datetime.now()
            else:
                self._logger.warning(
                    f"No handler registered for message type: {message_type} "
                    f"(from {mailbox_message.sender})"
                )
        except Exception as e:
            self._error_count += 1
            self._logger.error(
                f"Error handling mailbox message from {mailbox_message.sender}: {e}",
                exc_info=True,
            )

    async def _handle_recovery(self, metrics: "RecoveryMetrics") -> None:
        """Handle pending message recovery metrics.

        This is called by RedisMailboxService when recovery operations occur.

        Args:
            metrics: RecoveryMetrics with recovery statistics
        """
        self._logger.info(
            f"Recovery metrics: {metrics.total_recovered} messages recovered "
            f"in {metrics.batches_processed} batches"
        )

    async def _register_agent_name(self) -> None:
        """Register agent name on the cluster for discovery.

        Publishes agent_id to Redis so other agents can discover it.
        Uses the same Redis connection that the mailbox service uses.
        Uses a simple Redis SET with expiration (heartbeat-based).
        """
        if not self._mailbox_config:
            return  # No mailbox, no registration

        try:
            # Use Redis directly to register agent name
            # Key format: beast:agents:{agent_id}
            # Value: JSON with agent metadata
            import redis.asyncio as redis

            # Extract Redis connection info from mailbox config (must match mailbox connection)
            # If mailbox started successfully, these should be production values, not defaults
            if not hasattr(self._mailbox_config, "host") or not hasattr(
                self._mailbox_config, "port"
            ):
                self._logger.warning(
                    "Mailbox config missing host/port - cannot register agent name"
                )
                return

            host = self._mailbox_config.host
            port = self._mailbox_config.port
            db = self._mailbox_config.db if hasattr(self._mailbox_config, "db") else 0

            # Note: host will be from mailbox config - localhost is fine for single-node clusters,
            # but in production multi-node clusters, it will be the actual Redis cluster endpoint
            if host == "localhost":
                self._logger.debug(
                    f"Using localhost Redis (single-node cluster): {host}:{port}"
                )

            # Create Redis connection using exact same config as mailbox
            redis_client = redis.Redis(
                host=host, port=port, db=db, decode_responses=True
            )

            # Register agent name with metadata
            agent_info = {
                "agent_id": self.agent_id,
                "capabilities": self.capabilities,
                "registered_at": datetime.now().isoformat(),
                "state": (
                    self._state.value
                    if hasattr(self._state, "value")
                    else str(self._state)
                ),
            }

            # Set with expiration (heartbeat-based - 60 seconds)
            # Agents should heartbeat to refresh this
            key = f"beast:agents:{self.agent_id}"
            await redis_client.setex(
                key,
                60,  # Expire in 60 seconds (should be refreshed by heartbeat)
                json.dumps(agent_info),
            )

            # Also add to set of all agent IDs for quick discovery
            await redis_client.sadd("beast:agents:all", self.agent_id)

            await redis_client.aclose()

            self._logger.debug(f"Registered agent name on cluster: {self.agent_id}")
        except ImportError:
            # redis package not available - skip registration
            self._logger.debug(
                "redis package not available - skipping agent name registration"
            )
        except Exception as e:
            # Non-fatal - log but don't fail startup
            self._logger.warning(f"Failed to register agent name on cluster: {e}")

    async def _unregister_agent_name(self) -> None:
        """Unregister agent name from the cluster.

        Removes agent_id from Redis discovery registry.
        Uses the same Redis connection that the mailbox service uses.
        """
        if not self._mailbox_config:
            return  # No mailbox, no unregistration

        try:
            import redis.asyncio as redis

            # Extract Redis connection info from mailbox config (must match mailbox connection)
            if not hasattr(self._mailbox_config, "host") or not hasattr(
                self._mailbox_config, "port"
            ):
                self._logger.warning(
                    "Mailbox config missing host/port - cannot unregister agent name"
                )
                return

            host = self._mailbox_config.host
            port = self._mailbox_config.port
            db = self._mailbox_config.db if hasattr(self._mailbox_config, "db") else 0

            # Create Redis connection using exact same config as mailbox
            redis_client = redis.Redis(
                host=host, port=port, db=db, decode_responses=True
            )

            # Remove agent name from discovery
            key = f"beast:agents:{self.agent_id}"
            await redis_client.delete(key)

            # Remove from set of all agents
            await redis_client.srem("beast:agents:all", self.agent_id)

            await redis_client.aclose()

            self._logger.debug(f"Unregistered agent name from cluster: {self.agent_id}")
        except ImportError:
            # redis package not available - skip unregistration
            pass
        except Exception as e:
            # Non-fatal - log but don't fail shutdown
            self._logger.warning(f"Failed to unregister agent name from cluster: {e}")

    async def discover_agents(self) -> List[str]:
        """Discover all active agents on the cluster.

        Returns:
            List of active agent IDs

        Raises:
            RuntimeError: If mailbox is not initialized
        """
        if not self._mailbox_config:
            raise RuntimeError("Mailbox not initialized. Call startup() first.")

        try:
            import redis.asyncio as redis

            host = self._mailbox_config.host
            port = self._mailbox_config.port
            db = self._mailbox_config.db if hasattr(self._mailbox_config, "db") else 0

            redis_client = redis.Redis(
                host=host, port=port, db=db, decode_responses=True
            )

            # Get all agent IDs from the set
            agent_ids = await redis_client.smembers("beast:agents:all")

            await redis_client.aclose()

            return list(agent_ids) if agent_ids else []
        except ImportError:
            self._logger.error("redis package not available for discovery")
            return []
        except Exception as e:
            self._logger.error(f"Failed to discover agents: {e}", exc_info=True)
            return []

    async def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific agent.

        Args:
            agent_id: Agent ID to query

        Returns:
            Agent metadata dictionary (agent_id, capabilities, state, registered_at) or None if not found

        Raises:
            RuntimeError: If mailbox is not initialized
        """
        if not self._mailbox_config:
            raise RuntimeError("Mailbox not initialized. Call startup() first.")

        try:
            import redis.asyncio as redis

            host = self._mailbox_config.host
            port = self._mailbox_config.port
            db = self._mailbox_config.db if hasattr(self._mailbox_config, "db") else 0

            redis_client = redis.Redis(
                host=host, port=port, db=db, decode_responses=True
            )

            # Get agent metadata
            key = f"beast:agents:{agent_id}"
            agent_info_str = await redis_client.get(key)

            await redis_client.aclose()

            if agent_info_str:
                return json.loads(agent_info_str)
            return None
        except ImportError:
            self._logger.error("redis package not available for agent info")
            return None
        except Exception as e:
            self._logger.error(
                f"Failed to get agent info for {agent_id}: {e}", exc_info=True
            )
            return None

    async def find_agents_by_capability(self, capability: str) -> List[Dict[str, Any]]:
        """Find all agents that provide a specific capability.

        Args:
            capability: Capability name to search for

        Returns:
            List of agent metadata dictionaries for agents with the capability

        Raises:
            RuntimeError: If mailbox is not initialized
        """
        if not self._mailbox_config:
            raise RuntimeError("Mailbox not initialized. Call startup() first.")

        matching_agents = []
        agent_ids = await self.discover_agents()

        for agent_id in agent_ids:
            agent_info = await self.get_agent_info(agent_id)
            if agent_info and capability in agent_info.get("capabilities", []):
                matching_agents.append(agent_info)

        return matching_agents
