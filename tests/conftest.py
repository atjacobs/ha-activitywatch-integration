"""Root conftest for tests."""

import pycares
import pytest


@pytest.fixture(autouse=True, scope="session")
def _warm_pycares():
    """Pre-warm pycares to avoid the daemon thread appearing during tests.

    pycares lazily creates a singleton daemon thread (_run_safe_shutdown_loop)
    for safe channel destruction. If this thread is created during a test,
    the pytest-homeassistant-custom-component thread check fails.
    Triggering it here in session scope ensures it exists before any test
    captures its thread baseline.
    """
    channel = pycares.Channel()
    del channel
