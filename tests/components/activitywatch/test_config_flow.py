"""Tests for ActivityWatch config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.activitywatch.api import ActivityWatchApiConnectionError
from custom_components.activitywatch.const import (
    CONF_API_KEY,
    CONF_MONITORED_CATEGORIES,
    CONF_SCAN_INTERVAL,
    DOMAIN,
)

from .conftest import MOCK_CONFIG, MOCK_CONFIG_WITH_KEY


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests in this module."""
    yield


@pytest.fixture(autouse=True)
def mock_setup_entry():
    """Prevent actual setup of the entry during config flow tests."""
    with patch(
        "custom_components.activitywatch.async_setup_entry",
        return_value=True,
    ):
        yield


async def test_form_displayed(hass: HomeAssistant) -> None:
    """Test that the config form is displayed."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}


async def test_successful_config(hass: HomeAssistant) -> None:
    """Test a successful configuration."""
    with patch(
        "custom_components.activitywatch.config_flow.ActivityWatchApiClient"
    ) as mock_cls:
        mock_client = AsyncMock()
        mock_client.async_validate_connection = AsyncMock(return_value=True)
        mock_cls.return_value = mock_client

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            MOCK_CONFIG,
        )
        await hass.async_block_till_done()

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "Test-PC"
        assert result["data"] == MOCK_CONFIG

        # Unload the entry to clean up
        entry = result["result"]
        await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()


async def test_successful_config_with_api_key(hass: HomeAssistant) -> None:
    """Test a successful configuration with API key."""
    with patch(
        "custom_components.activitywatch.config_flow.ActivityWatchApiClient"
    ) as mock_cls:
        mock_client = AsyncMock()
        mock_client.async_validate_connection = AsyncMock(return_value=True)
        mock_cls.return_value = mock_client

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            MOCK_CONFIG_WITH_KEY,
        )
        await hass.async_block_till_done()

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_API_KEY] == "test-api-key"


async def test_connection_error(hass: HomeAssistant) -> None:
    """Test handling of connection error."""
    with patch(
        "custom_components.activitywatch.config_flow.ActivityWatchApiClient"
    ) as mock_cls:
        mock_client = AsyncMock()
        mock_client.async_validate_connection = AsyncMock(
            side_effect=ActivityWatchApiConnectionError("Connection refused")
        )
        mock_cls.return_value = mock_client

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            MOCK_CONFIG,
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_unknown_error(hass: HomeAssistant) -> None:
    """Test handling of unknown error."""
    with patch(
        "custom_components.activitywatch.config_flow.ActivityWatchApiClient"
    ) as mock_cls:
        mock_client = AsyncMock()
        mock_client.async_validate_connection = AsyncMock(
            side_effect=RuntimeError("Something unexpected")
        )
        mock_cls.return_value = mock_client

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            MOCK_CONFIG,
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "unknown"}


async def test_duplicate_entry(hass: HomeAssistant, mock_config_entry) -> None:
    """Test that duplicate entries are aborted."""
    with patch(
        "custom_components.activitywatch.config_flow.ActivityWatchApiClient"
    ) as mock_cls:
        mock_client = AsyncMock()
        mock_client.async_validate_connection = AsyncMock(return_value=True)
        mock_cls.return_value = mock_client

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            MOCK_CONFIG,
        )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_options_flow(hass: HomeAssistant, mock_config_entry) -> None:
    """Test the options flow."""
    mock_config_entry.runtime_data = None

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_SCAN_INTERVAL: 30,
            CONF_MONITORED_CATEGORIES: "Work, Gaming, Browsing",
        },
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_SCAN_INTERVAL] == 30
    assert result["data"][CONF_MONITORED_CATEGORIES] == [
        "Work",
        "Gaming",
        "Browsing",
    ]
