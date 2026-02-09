"""Async API client for ActivityWatch."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)


class ActivityWatchApiError(Exception):
    """General API error."""


class ActivityWatchApiConnectionError(ActivityWatchApiError):
    """Connection error."""


class ActivityWatchApiClient:
    """Async client for the ActivityWatch REST API."""

    def __init__(
        self,
        host: str,
        port: int,
        session: aiohttp.ClientSession,
        api_key: str | None = None,
    ) -> None:
        """Initialize the API client."""
        self._base_url = f"http://{host}:{port}"
        self._session = session
        self._api_key = api_key

    def _headers(self) -> dict[str, str]:
        """Build request headers."""
        headers: dict[str, str] = {"Accept": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """Make a GET request."""
        url = f"{self._base_url}/api/0{path}"
        try:
            async with self._session.get(
                url, headers=self._headers(), params=params
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise ActivityWatchApiError(
                        f"HTTP {resp.status} from {path}: {text}"
                    )
                return await resp.json()
        except aiohttp.ClientError as err:
            raise ActivityWatchApiConnectionError(
                f"Cannot connect to ActivityWatch at {self._base_url}: {err}"
            ) from err

    async def _post(self, path: str, data: Any = None) -> Any:
        """Make a POST request."""
        url = f"{self._base_url}/api/0{path}"
        try:
            async with self._session.post(
                url, headers=self._headers(), json=data
            ) as resp:
                if resp.status not in (200, 201):
                    text = await resp.text()
                    raise ActivityWatchApiError(
                        f"HTTP {resp.status} from {path}: {text}"
                    )
                return await resp.json()
        except aiohttp.ClientError as err:
            raise ActivityWatchApiConnectionError(
                f"Cannot connect to ActivityWatch at {self._base_url}: {err}"
            ) from err

    async def async_get_info(self) -> dict[str, Any]:
        """Get server info."""
        return await self._get("/info")

    async def async_get_buckets(self) -> dict[str, Any]:
        """Get all buckets."""
        return await self._get("/buckets/")

    async def async_get_events(
        self, bucket_id: str, limit: int = 1
    ) -> list[dict[str, Any]]:
        """Get events from a bucket."""
        return await self._get(f"/buckets/{bucket_id}/events", {"limit": str(limit)})

    async def async_query(self, query: list[str], timeperiods: list[str]) -> list[Any]:
        """Execute an AW query."""
        return await self._post("/query/", {"query": query, "timeperiods": timeperiods})

    async def async_find_buckets(self, bucket_type: str) -> list[str]:
        """Find bucket IDs matching a type pattern."""
        buckets = await self.async_get_buckets()
        return [
            bid for bid, info in buckets.items() if bucket_type in info.get("type", "")
        ]

    async def async_validate_connection(self) -> bool:
        """Validate that the server is reachable."""
        await self.async_get_info()
        return True
