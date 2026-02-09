"""Tests for ActivityWatch integration setup."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.activitywatch.api import ActivityWatchApiConnectionError
from custom_components.activitywatch.const import DOMAIN

from .conftest import MOCK_BUCKETS, MOCK_CONFIG, MOCK_WINDOW_EVENT


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests in this module."""
    yield


async def test_setup_entry_success(hass: HomeAssistant) -> None:
    """Test successful setup of a config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test-PC",
        data=MOCK_CONFIG,
        entry_id="test_init_entry",
    )
    entry.add_to_hass(hass)

    with patch("custom_components.activitywatch.ActivityWatchApiClient") as mock_cls:
        mock_client = AsyncMock()
        mock_client.async_validate_connection = AsyncMock(return_value=True)
        mock_client.async_find_buckets = AsyncMock(
            side_effect=lambda t: [
                bid for bid, info in MOCK_BUCKETS.items() if t in info["type"]
            ]
        )
        mock_client.async_get_events = AsyncMock(return_value=[MOCK_WINDOW_EVENT])
        mock_cls.return_value = mock_client

        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state == ConfigEntryState.LOADED
    assert entry.runtime_data is not None


async def test_setup_entry_connection_error(hass: HomeAssistant) -> None:
    """Test that connection error raises ConfigEntryNotReady."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test-PC",
        data=MOCK_CONFIG,
        entry_id="test_init_conn_err",
    )
    entry.add_to_hass(hass)

    with patch("custom_components.activitywatch.ActivityWatchApiClient") as mock_cls:
        mock_client = AsyncMock()
        mock_client.async_validate_connection = AsyncMock(
            side_effect=ActivityWatchApiConnectionError("Cannot connect")
        )
        mock_cls.return_value = mock_client

        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state == ConfigEntryState.SETUP_RETRY


async def test_unload_entry(hass: HomeAssistant) -> None:
    """Test unloading a config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test-PC",
        data=MOCK_CONFIG,
        entry_id="test_init_unload",
    )
    entry.add_to_hass(hass)

    with patch("custom_components.activitywatch.ActivityWatchApiClient") as mock_cls:
        mock_client = AsyncMock()
        mock_client.async_validate_connection = AsyncMock(return_value=True)
        mock_client.async_find_buckets = AsyncMock(
            side_effect=lambda t: [
                bid for bid, info in MOCK_BUCKETS.items() if t in info["type"]
            ]
        )
        mock_client.async_get_events = AsyncMock(return_value=[MOCK_WINDOW_EVENT])
        mock_cls.return_value = mock_client

        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert entry.state == ConfigEntryState.LOADED

        await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state == ConfigEntryState.NOT_LOADED
