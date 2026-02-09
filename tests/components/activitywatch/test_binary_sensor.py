"""Tests for ActivityWatch binary sensor platform."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.activitywatch.binary_sensor import (
    ActivityWatchActiveBinarySensor,
    ActivityWatchCategoryBinarySensor,
)
from custom_components.activitywatch.const import DOMAIN
from custom_components.activitywatch.coordinator import (
    ActivityWatchCoordinator,
    ActivityWatchData,
)

from .conftest import (
    MOCK_AFK_EVENT_ACTIVE,
    MOCK_AFK_EVENT_AFK,
    MOCK_CONFIG,
    MOCK_WINDOW_EVENT,
    MOCK_WINDOW_EVENT_NO_CATEGORY,
)


@pytest.fixture
def mock_entry(hass: HomeAssistant):
    """Create a minimal mock config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test-PC",
        data=MOCK_CONFIG,
        entry_id="test_binary_entry",
    )
    entry.add_to_hass(hass)
    return entry


def _make_coordinator(
    hass: HomeAssistant, mock_api_client: AsyncMock, window_event=None, afk_event=None
) -> ActivityWatchCoordinator:
    """Create a coordinator with specified data."""
    coord = ActivityWatchCoordinator(
        hass, client=mock_api_client, device_name="Test-PC"
    )
    data = ActivityWatchData()
    data.window_event = window_event
    data.afk_event = afk_event
    coord.data = data
    return coord


class TestActiveBinarySensor:
    """Tests for the active/AFK binary sensor."""

    def test_is_on_when_not_afk(
        self, hass: HomeAssistant, mock_api_client: AsyncMock, mock_entry
    ) -> None:
        """Test sensor is ON when user is not AFK."""
        coord = _make_coordinator(
            hass, mock_api_client, afk_event=MOCK_AFK_EVENT_ACTIVE
        )
        sensor = ActivityWatchActiveBinarySensor(coord, mock_entry)
        assert sensor.is_on is True

    def test_is_off_when_afk(
        self, hass: HomeAssistant, mock_api_client: AsyncMock, mock_entry
    ) -> None:
        """Test sensor is OFF when user is AFK."""
        coord = _make_coordinator(hass, mock_api_client, afk_event=MOCK_AFK_EVENT_AFK)
        sensor = ActivityWatchActiveBinarySensor(coord, mock_entry)
        assert sensor.is_on is False

    def test_is_none_when_no_data(
        self, hass: HomeAssistant, mock_api_client: AsyncMock, mock_entry
    ) -> None:
        """Test sensor is None when no data."""
        coord = _make_coordinator(hass, mock_api_client)
        sensor = ActivityWatchActiveBinarySensor(coord, mock_entry)
        assert sensor.is_on is None

    def test_last_active_attribute(
        self, hass: HomeAssistant, mock_api_client: AsyncMock, mock_entry
    ) -> None:
        """Test last_active attribute."""
        coord = _make_coordinator(
            hass, mock_api_client, afk_event=MOCK_AFK_EVENT_ACTIVE
        )
        sensor = ActivityWatchActiveBinarySensor(coord, mock_entry)
        attrs = sensor.extra_state_attributes
        assert attrs["last_active"] == "2024-01-15T10:00:00.000000+00:00"

    def test_unique_id(
        self, hass: HomeAssistant, mock_api_client: AsyncMock, mock_entry
    ) -> None:
        """Test unique ID."""
        coord = _make_coordinator(hass, mock_api_client)
        sensor = ActivityWatchActiveBinarySensor(coord, mock_entry)
        assert sensor.unique_id == "test_binary_entry_active"


class TestCategoryBinarySensor:
    """Tests for category binary sensors."""

    def test_is_on_when_category_matches(
        self, hass: HomeAssistant, mock_api_client: AsyncMock, mock_entry
    ) -> None:
        """Test sensor is ON when category matches."""
        coord = _make_coordinator(hass, mock_api_client, window_event=MOCK_WINDOW_EVENT)
        sensor = ActivityWatchCategoryBinarySensor(coord, mock_entry, "Work")
        assert sensor.is_on is True

    def test_is_on_for_subcategory_match(
        self, hass: HomeAssistant, mock_api_client: AsyncMock, mock_entry
    ) -> None:
        """Test sensor is ON when subcategory matches."""
        coord = _make_coordinator(hass, mock_api_client, window_event=MOCK_WINDOW_EVENT)
        sensor = ActivityWatchCategoryBinarySensor(coord, mock_entry, "Engineering")
        assert sensor.is_on is True

    def test_is_off_when_category_does_not_match(
        self, hass: HomeAssistant, mock_api_client: AsyncMock, mock_entry
    ) -> None:
        """Test sensor is OFF when category doesn't match."""
        coord = _make_coordinator(hass, mock_api_client, window_event=MOCK_WINDOW_EVENT)
        sensor = ActivityWatchCategoryBinarySensor(coord, mock_entry, "Gaming")
        assert sensor.is_on is False

    def test_is_off_when_no_category(
        self, hass: HomeAssistant, mock_api_client: AsyncMock, mock_entry
    ) -> None:
        """Test sensor is OFF when event has no category."""
        coord = _make_coordinator(
            hass, mock_api_client, window_event=MOCK_WINDOW_EVENT_NO_CATEGORY
        )
        sensor = ActivityWatchCategoryBinarySensor(coord, mock_entry, "Work")
        assert sensor.is_on is False

    def test_is_none_when_no_data(
        self, hass: HomeAssistant, mock_api_client: AsyncMock, mock_entry
    ) -> None:
        """Test sensor is None when no data."""
        coord = _make_coordinator(hass, mock_api_client)
        sensor = ActivityWatchCategoryBinarySensor(coord, mock_entry, "Work")
        assert sensor.is_on is None

    def test_case_insensitive_match(
        self, hass: HomeAssistant, mock_api_client: AsyncMock, mock_entry
    ) -> None:
        """Test that category matching is case-insensitive."""
        coord = _make_coordinator(hass, mock_api_client, window_event=MOCK_WINDOW_EVENT)
        sensor = ActivityWatchCategoryBinarySensor(coord, mock_entry, "work")
        assert sensor.is_on is True

    def test_unique_id_slugified(
        self, hass: HomeAssistant, mock_api_client: AsyncMock, mock_entry
    ) -> None:
        """Test that unique ID uses slugified category."""
        coord = _make_coordinator(hass, mock_api_client)
        sensor = ActivityWatchCategoryBinarySensor(coord, mock_entry, "Video Games")
        assert sensor.unique_id == "test_binary_entry_is_video_games"
