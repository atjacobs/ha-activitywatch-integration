"""Tests for ActivityWatch sensor platform."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.activitywatch.const import DOMAIN
from custom_components.activitywatch.coordinator import (
    ActivityWatchCoordinator,
    ActivityWatchData,
)
from custom_components.activitywatch.sensor import ActivityWatchCurrentActivitySensor

from .conftest import MOCK_CONFIG, MOCK_WINDOW_EVENT, MOCK_WINDOW_EVENT_NO_CATEGORY


@pytest.fixture
def coordinator(hass: HomeAssistant, mock_api_client: AsyncMock):
    """Create a coordinator with mock data."""
    coord = ActivityWatchCoordinator(
        hass, client=mock_api_client, device_name="Test-PC"
    )
    data = ActivityWatchData()
    data.window_event = MOCK_WINDOW_EVENT
    coord.data = data
    return coord


@pytest.fixture
def mock_entry(hass: HomeAssistant):
    """Create a minimal mock config entry for sensor tests."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test-PC",
        data=MOCK_CONFIG,
        entry_id="test_sensor_entry",
    )
    entry.add_to_hass(hass)
    return entry


def test_state_returns_category(
    coordinator: ActivityWatchCoordinator, mock_entry
) -> None:
    """Test that state returns the top-level category."""
    sensor = ActivityWatchCurrentActivitySensor(coordinator, mock_entry)
    assert sensor.native_value == "Work"


def test_state_returns_uncategorized_when_no_category(
    hass: HomeAssistant, mock_api_client: AsyncMock, mock_entry
) -> None:
    """Test that state returns Uncategorized when no category."""
    coord = ActivityWatchCoordinator(
        hass, client=mock_api_client, device_name="Test-PC"
    )
    data = ActivityWatchData()
    data.window_event = MOCK_WINDOW_EVENT_NO_CATEGORY
    coord.data = data

    sensor = ActivityWatchCurrentActivitySensor(coord, mock_entry)
    assert sensor.native_value == "Uncategorized"


def test_state_returns_none_when_no_data(
    hass: HomeAssistant, mock_api_client: AsyncMock, mock_entry
) -> None:
    """Test that state returns None when no data available."""
    coord = ActivityWatchCoordinator(
        hass, client=mock_api_client, device_name="Test-PC"
    )
    data = ActivityWatchData()
    coord.data = data

    sensor = ActivityWatchCurrentActivitySensor(coord, mock_entry)
    assert sensor.native_value is None


def test_attributes(coordinator: ActivityWatchCoordinator, mock_entry) -> None:
    """Test sensor attributes."""
    sensor = ActivityWatchCurrentActivitySensor(coordinator, mock_entry)
    attrs = sensor.extra_state_attributes

    assert attrs["app_name"] == "Code"
    assert attrs["window_title"] == "main.py - Visual Studio Code"
    assert attrs["url"] == ""
    assert attrs["sub_categories"] == ["Work", "Engineering"]
    assert attrs["duration"] == 120


def test_unique_id(coordinator: ActivityWatchCoordinator, mock_entry) -> None:
    """Test unique ID format."""
    sensor = ActivityWatchCurrentActivitySensor(coordinator, mock_entry)
    assert sensor.unique_id == "test_sensor_entry_current_activity"


def test_device_info(coordinator: ActivityWatchCoordinator, mock_entry) -> None:
    """Test device info."""
    sensor = ActivityWatchCurrentActivitySensor(coordinator, mock_entry)
    device_info = sensor.device_info
    assert device_info is not None
    assert device_info["name"] == "Test-PC"
    assert device_info["manufacturer"] == "ActivityWatch"
