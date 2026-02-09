"""Service handlers for ActivityWatch integration."""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse

from .api import ActivityWatchApiClient, ActivityWatchApiError
from .const import CONF_DEVICE_NAME, DOMAIN

_LOGGER = logging.getLogger(__name__)

SERVICE_QUERY_STATS = "query_stats"
ATTR_DEVICE_ID = "device_id"
ATTR_START_TIME = "start_time"
ATTR_END_TIME = "end_time"
ATTR_CATEGORY = "category"

SERVICE_QUERY_STATS_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_DEVICE_ID): str,
        vol.Optional(ATTR_START_TIME): str,
        vol.Optional(ATTR_END_TIME): str,
        vol.Optional(ATTR_CATEGORY): str,
    }
)


def _find_client_for_device(
    hass: HomeAssistant, device_id: str
) -> ActivityWatchApiClient | None:
    """Find the API client for a given device name."""
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.data.get(CONF_DEVICE_NAME) == device_id:
            coordinator = entry.runtime_data
            return coordinator.client
    return None


async def async_handle_query_stats(call: ServiceCall) -> dict[str, Any]:
    """Handle the query_stats service call."""
    hass = call.hass
    device_id = call.data[ATTR_DEVICE_ID]

    client = _find_client_for_device(hass, device_id)
    if client is None:
        _LOGGER.error("No ActivityWatch entry found for device: %s", device_id)
        return {
            "error": f"Device '{device_id}' not found",
            "total_seconds": 0,
            "top_apps": [],
        }

    now = datetime.now(timezone.utc)
    start_str = call.data.get(ATTR_START_TIME)
    end_str = call.data.get(ATTR_END_TIME)

    if start_str:
        start = start_str
    else:
        start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()

    end = end_str if end_str else now.isoformat()

    timeperiod = f"{start}/{end}"
    category_filter = call.data.get(ATTR_CATEGORY)

    query_lines = [
        'events = query_bucket(find_bucket("aw-watcher-window-"));',
        'events = merge_events_by_keys(events, ["app"]);',
        "RETURN = sort_by_duration(events);",
    ]

    try:
        result = await client.async_query(query_lines, [timeperiod])
    except ActivityWatchApiError as err:
        _LOGGER.error("Query failed: %s", err)
        return {"error": str(err), "total_seconds": 0, "top_apps": []}

    if not result or not isinstance(result, list) or len(result) == 0:
        return {"total_seconds": 0, "top_apps": []}

    events = result[0] if isinstance(result[0], list) else []

    top_apps: list[dict[str, Any]] = []
    total_seconds = 0.0

    for event in events:
        app_name = event.get("data", {}).get("app", "Unknown")
        duration = event.get("duration", 0)

        if category_filter:
            cat = event.get("data", {}).get("$category", [])
            if isinstance(cat, list) and category_filter.lower() not in [
                c.lower() for c in cat
            ]:
                continue

        total_seconds += duration
        top_apps.append({"name": app_name, "seconds": round(duration)})

    return {
        "total_seconds": round(total_seconds),
        "top_apps": top_apps[:10],
    }


def async_register_services(hass: HomeAssistant) -> None:
    """Register ActivityWatch services."""
    if hass.services.has_service(DOMAIN, SERVICE_QUERY_STATS):
        return

    hass.services.async_register(
        DOMAIN,
        SERVICE_QUERY_STATS,
        async_handle_query_stats,
        schema=SERVICE_QUERY_STATS_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )


def async_unregister_services(hass: HomeAssistant) -> None:
    """Unregister ActivityWatch services."""
    if hass.services.has_service(DOMAIN, SERVICE_QUERY_STATS):
        hass.services.async_remove(DOMAIN, SERVICE_QUERY_STATS)
