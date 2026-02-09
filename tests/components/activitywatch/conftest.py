"""Fixtures for ActivityWatch tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.activitywatch.const import (
    CONF_API_KEY,
    CONF_DEVICE_NAME,
    CONF_HOST,
    CONF_PORT,
    DOMAIN,
)

MOCK_CONFIG = {
    CONF_HOST: "localhost",
    CONF_PORT: 5600,
    CONF_DEVICE_NAME: "Test-PC",
}

MOCK_CONFIG_WITH_KEY = {
    **MOCK_CONFIG,
    CONF_API_KEY: "test-api-key",
}

MOCK_WINDOW_EVENT = {
    "id": 1,
    "timestamp": "2024-01-15T10:00:00.000000+00:00",
    "duration": 120.5,
    "data": {
        "app": "Code",
        "title": "main.py - Visual Studio Code",
        "url": "",
        "$category": ["Work", "Engineering"],
    },
}

MOCK_WINDOW_EVENT_2 = {
    "id": 2,
    "timestamp": "2024-01-15T10:02:00.000000+00:00",
    "duration": 60.0,
    "data": {
        "app": "Firefox",
        "title": "GitHub - Pull Requests",
        "url": "https://github.com",
        "$category": ["Work", "Communication"],
    },
}

MOCK_WINDOW_EVENT_NO_CATEGORY = {
    "id": 3,
    "timestamp": "2024-01-15T10:03:00.000000+00:00",
    "duration": 30.0,
    "data": {
        "app": "Notepad",
        "title": "Untitled",
    },
}

MOCK_AFK_EVENT_ACTIVE = {
    "id": 10,
    "timestamp": "2024-01-15T10:00:00.000000+00:00",
    "duration": 300.0,
    "data": {"status": "not-afk"},
}

MOCK_AFK_EVENT_AFK = {
    "id": 11,
    "timestamp": "2024-01-15T09:55:00.000000+00:00",
    "duration": 600.0,
    "data": {"status": "afk"},
}

MOCK_BUCKETS = {
    "aw-watcher-window_test-hostname": {
        "id": "aw-watcher-window_test-hostname",
        "type": "aw-watcher-window",
        "hostname": "test-hostname",
    },
    "aw-watcher-afk_test-hostname": {
        "id": "aw-watcher-afk_test-hostname",
        "type": "aw-watcher-afk",
        "hostname": "test-hostname",
    },
}

MOCK_SERVER_INFO = {
    "hostname": "test-hostname",
    "version": "0.12.0",
    "testing": False,
}


@pytest.fixture
def mock_api_client() -> AsyncMock:
    """Create a mock API client with realistic return data."""
    client = AsyncMock()
    client.async_validate_connection = AsyncMock(return_value=True)
    client.async_get_info = AsyncMock(return_value=MOCK_SERVER_INFO)
    client.async_get_buckets = AsyncMock(return_value=MOCK_BUCKETS)
    client.async_get_events = AsyncMock(return_value=[MOCK_WINDOW_EVENT])
    client.async_find_buckets = AsyncMock(
        side_effect=lambda t: [
            bid for bid, info in MOCK_BUCKETS.items() if t in info["type"]
        ]
    )
    client.async_query = AsyncMock(return_value=[[]])
    return client


@pytest.fixture
def mock_api_client_patch(mock_api_client: AsyncMock):
    """Patch the API client constructor to return the mock."""
    with patch(
        "custom_components.activitywatch.api.ActivityWatchApiClient",
        return_value=mock_api_client,
    ) as mock_cls:
        mock_cls.return_value = mock_api_client
        yield mock_cls


@pytest.fixture
def mock_config_entry(hass: HomeAssistant):
    """Create a mock config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test-PC",
        data=MOCK_CONFIG,
        entry_id="test_entry_id",
    )
    entry.add_to_hass(hass)
    return entry
