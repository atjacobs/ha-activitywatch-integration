"""Config flow for ActivityWatch integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ActivityWatchApiClient, ActivityWatchApiConnectionError
from .const import (
    CONF_API_KEY,
    CONF_DEVICE_NAME,
    CONF_HOST,
    CONF_MONITORED_CATEGORIES,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    DEFAULT_DEVICE_NAME,
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Optional(CONF_API_KEY): str,
        vol.Required(CONF_DEVICE_NAME, default=DEFAULT_DEVICE_NAME): str,
    }
)


class ActivityWatchConfigFlow(ConfigFlow, domain=DOMAIN):  # type: ignore[call-arg]
    """Handle a config flow for ActivityWatch."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._async_abort_entries_match(
                {CONF_HOST: user_input[CONF_HOST], CONF_PORT: user_input[CONF_PORT]}
            )

            session = async_get_clientsession(self.hass)
            client = ActivityWatchApiClient(
                host=user_input[CONF_HOST],
                port=user_input[CONF_PORT],
                session=session,
                api_key=user_input.get(CONF_API_KEY),
            )

            try:
                await client.async_validate_connection()
            except ActivityWatchApiConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during config flow")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=user_input[CONF_DEVICE_NAME],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=USER_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return ActivityWatchOptionsFlow(config_entry)


class ActivityWatchOptionsFlow(OptionsFlow):
    """Handle options flow for ActivityWatch."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            categories_str = user_input.get(CONF_MONITORED_CATEGORIES, "")
            categories = [c.strip() for c in categories_str.split(",") if c.strip()]
            return self.async_create_entry(
                title="",
                data={
                    CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
                    CONF_MONITORED_CATEGORIES: categories,
                },
            )

        current_options = self._config_entry.options
        current_categories = current_options.get(CONF_MONITORED_CATEGORIES, [])
        categories_str = ", ".join(current_categories) if current_categories else ""

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=current_options.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    ): vol.All(
                        int, vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL)
                    ),
                    vol.Optional(
                        CONF_MONITORED_CATEGORIES,
                        default=categories_str,
                    ): str,
                }
            ),
        )
