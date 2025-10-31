"""Pytest configuration and fixtures for beast-agent tests.

Based on proven patterns from beast-mailbox-core.
"""

import atexit
import subprocess
import time
from typing import Optional, Tuple

import pytest


def _stop_docker_container(container_name: str) -> None:
    """Stop and remove a Docker container.

    This ensures containers are properly cleaned up after tests.
    Containers should never be left running after test sessions.
    """
    try:
        subprocess.run(
            ["docker", "stop", container_name],
            capture_output=True,
            check=False,
            timeout=10,
        )
        subprocess.run(
            ["docker", "rm", container_name],
            capture_output=True,
            check=False,
            timeout=10,
        )
    except Exception:
        pass  # Container might not exist or already removed


@pytest.fixture(scope="session")
def redis_docker() -> Tuple[str, int]:
    """Start Redis in Docker for testing.

    Automatically starts Redis container and stops it after tests.
    If Docker is not available, tests will be skipped.

    Returns:
        Tuple of (host, port) for Redis connection

    Based on proven pattern from beast-mailbox-core.
    """
    container_name = "beast-agent-test-redis"

    # Check if container already exists and is running
    result = subprocess.run(
        [
            "docker",
            "ps",
            "--filter",
            f"name={container_name}",
            "--format",
            "{{.Names}}",
        ],
        capture_output=True,
        text=True,
    )

    if container_name in result.stdout:
        # Container already running - use it (but register cleanup for test session end)
        atexit.register(_stop_docker_container, container_name)
        yield "localhost", 6379
        return

    # Try to start existing stopped container
    result = subprocess.run(
        ["docker", "start", container_name],
        capture_output=True,
    )

    if result.returncode == 0:
        # Started existing container
        time.sleep(1)  # Wait for Redis to be ready
        # Register cleanup for test session end
        atexit.register(_stop_docker_container, container_name)
        yield "localhost", 6379
        return

    # Create and start new container
    try:
        result = subprocess.run(
            [
                "docker",
                "run",
                "-d",
                "--name",
                container_name,
                "-p",
                "6379:6379",
                "redis:latest",
            ],
            capture_output=True,
            check=True,
            text=True,
        )

        # Wait for Redis to be ready
        time.sleep(2)

        # Verify container is actually running (not just created)
        check_result = subprocess.run(
            [
                "docker",
                "ps",
                "--filter",
                f"name={container_name}",
                "--format",
                "{{.Names}}",
            ],
            capture_output=True,
            text=True,
        )

        if container_name not in check_result.stdout:
            # Container was created but not running (likely port conflict)
            _stop_docker_container(container_name)
            pytest.skip(f"Could not start Redis container - port 6379 may be in use")

        # Register cleanup for test session end
        atexit.register(_stop_docker_container, container_name)

        yield "localhost", 6379

        # Explicit cleanup (in addition to atexit)
        _stop_docker_container(container_name)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        # Docker not available or failed to start
        error_msg = str(e) if hasattr(e, "stderr") and e.stderr else str(e)
        pytest.skip(
            f"Docker not available or Redis container failed to start: {error_msg}"
        )


@pytest.fixture(scope="session")
def redis_available(redis_docker: Tuple[str, int]) -> bool:
    """Check if Redis is available for testing.

    Uses the redis_docker fixture to ensure Redis is running.
    Returns True if Redis is available, False otherwise.

    Args:
        redis_docker: Tuple of (host, port) from redis_docker fixture

    Returns:
        True if Redis is available and accessible
    """
    try:
        import redis

        client = redis.Redis(host=redis_docker[0], port=redis_docker[1], db=15)
        client.ping()
        client.close()
        return True
    except Exception:
        return False


@pytest.fixture(scope="session")
def mailbox_core_available() -> bool:
    """Check if beast-mailbox-core is available for testing.

    Returns:
        True if beast-mailbox-core is installed and importable
    """
    try:
        import beast_mailbox_core

        return True
    except ImportError:
        return False


@pytest.fixture
def mailbox_config(redis_docker: Tuple[str, int], mailbox_core_available: bool):
    """Create MailboxConfig for integration tests.

    Uses the redis_docker fixture to configure mailbox with test Redis.
    Skips if beast-mailbox-core is not available.

    Args:
        redis_docker: Tuple of (host, port) from redis_docker fixture
        mailbox_core_available: Whether beast-mailbox-core is available

    Returns:
        MailboxConfig instance configured for testing

    Raises:
        pytest.SkipTest: If beast-mailbox-core is not available
    """
    if not mailbox_core_available:
        pytest.skip("beast-mailbox-core not available - install for integration tests")

    from beast_mailbox_core import MailboxConfig

    return MailboxConfig(
        host=redis_docker[0],
        port=redis_docker[1],
        db=15,  # Use separate DB for tests
        stream_prefix="test:mailbox",
        enable_recovery=True,
        recovery_min_idle_time=0,  # Immediate recovery for tests
    )
