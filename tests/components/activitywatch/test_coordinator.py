"""Tests for ActivityWatch coordinator."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.activitywatch.api import (
    ActivityWatchApiConnectionError,
    ActivityWatchApiError,
)
from custom_components.activitywatch.const import (
    EVENT_ACTIVITY_SWITCH,
)
from custom_components.activitywatch.coordinator import ActivityWatchCoordinator

from .conftest import (
    MOCK_AFK_EVENT_ACTIVE,
    MOCK_WINDOW_EVENT,
    MOCK_WINDOW_EVENT_2,
)


async def test_data_fetch(hass: HomeAssistant, mock_api_client: AsyncMock) -> None:
    """Test successful data fetch."""
    coordinator = ActivityWatchCoordinator(
        hass, client=mock_api_client, device_name="Test-PC"
    )
    coordinator.window_bucket = "aw-watcher-window_test-hostname"
    coordinator.afk_bucket = "aw-watcher-afk_test-hostname"

    # Set up mock to return different data per bucket
    async def mock_get_events(bucket_id, limit=1):
        if "window" in bucket_id:
            return [MOCK_WINDOW_EVENT]
        if "afk" in bucket_id:
            return [MOCK_AFK_EVENT_ACTIVE]
        return []

    mock_api_client.async_get_events = AsyncMock(side_effect=mock_get_events)

    data = await coordinator._async_update_data()

    assert data.window_event == MOCK_WINDOW_EVENT
    assert data.afk_event == MOCK_AFK_EVENT_ACTIVE


async def test_connection_failure_raises_update_failed(
    hass: HomeAssistant, mock_api_client: AsyncMock
) -> None:
    """Test that connection failure raises UpdateFailed."""
    coordinator = ActivityWatchCoordinator(
        hass, client=mock_api_client, device_name="Test-PC"
    )
    coordinator.window_bucket = "aw-watcher-window_test-hostname"

    mock_api_client.async_get_events = AsyncMock(
        side_effect=ActivityWatchApiConnectionError("Connection refused")
    )

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


async def test_api_error_raises_update_failed(
    hass: HomeAssistant, mock_api_client: AsyncMock
) -> None:
    """Test that API error raises UpdateFailed."""
    coordinator = ActivityWatchCoordinator(
        hass, client=mock_api_client, device_name="Test-PC"
    )
    coordinator.window_bucket = "aw-watcher-window_test-hostname"

    mock_api_client.async_get_events = AsyncMock(
        side_effect=ActivityWatchApiError("HTTP 500")
    )

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


async def test_bucket_discovery(
    hass: HomeAssistant, mock_api_client: AsyncMock
) -> None:
    """Test bucket discovery during setup."""
    coordinator = ActivityWatchCoordinator(
        hass, client=mock_api_client, device_name="Test-PC"
    )

    await coordinator.async_setup()

    assert coordinator.window_bucket == "aw-watcher-window_test-hostname"
    assert coordinator.afk_bucket == "aw-watcher-afk_test-hostname"


async def test_window_switch_event_fired(
    hass: HomeAssistant, mock_api_client: AsyncMock
) -> None:
    """Test that window switch events are fired."""
    coordinator = ActivityWatchCoordinator(
        hass, client=mock_api_client, device_name="Test-PC"
    )
    coordinator.window_bucket = "aw-watcher-window_test-hostname"

    events_fired = []

    async def capture_event(event):
        events_fired.append(event)

    hass.bus.async_listen(EVENT_ACTIVITY_SWITCH, capture_event)

    # First poll — should NOT fire (sets baseline)
    mock_api_client.async_get_events = AsyncMock(return_value=[MOCK_WINDOW_EVENT])
    await coordinator._async_update_data()
    await hass.async_block_till_done()
    assert len(events_fired) == 0

    # Second poll with different app — SHOULD fire
    mock_api_client.async_get_events = AsyncMock(return_value=[MOCK_WINDOW_EVENT_2])
    await coordinator._async_update_data()
    await hass.async_block_till_done()
    assert len(events_fired) == 1
    assert events_fired[0].data["app"] == "Firefox"
    assert events_fired[0].data["device_id"] == "Test-PC"
    assert events_fired[0].data["type"] == "window_switch"


async def test_no_event_on_first_poll(
    hass: HomeAssistant, mock_api_client: AsyncMock
) -> None:
    """Test that no event is fired on the first poll."""
    coordinator = ActivityWatchCoordinator(
        hass, client=mock_api_client, device_name="Test-PC"
    )
    coordinator.window_bucket = "aw-watcher-window_test-hostname"

    events_fired = []
    hass.bus.async_listen(EVENT_ACTIVITY_SWITCH, lambda e: events_fired.append(e))

    mock_api_client.async_get_events = AsyncMock(return_value=[MOCK_WINDOW_EVENT])
    await coordinator._async_update_data()
    await hass.async_block_till_done()

    assert len(events_fired) == 0


async def test_no_event_when_same_app(
    hass: HomeAssistant, mock_api_client: AsyncMock
) -> None:
    """Test that no event fires when the same app is active."""
    coordinator = ActivityWatchCoordinator(
        hass, client=mock_api_client, device_name="Test-PC"
    )
    coordinator.window_bucket = "aw-watcher-window_test-hostname"

    events_fired = []
    hass.bus.async_listen(EVENT_ACTIVITY_SWITCH, lambda e: events_fired.append(e))

    mock_api_client.async_get_events = AsyncMock(return_value=[MOCK_WINDOW_EVENT])
    await coordinator._async_update_data()
    await coordinator._async_update_data()
    await hass.async_block_till_done()

    assert len(events_fired) == 0
