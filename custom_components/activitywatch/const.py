"""Constants for the ActivityWatch integration."""

from typing import Final

DOMAIN: Final = "activitywatch"

# Config keys
CONF_HOST: Final = "host"
CONF_PORT: Final = "port"
CONF_API_KEY: Final = "api_key"
CONF_DEVICE_NAME: Final = "device_name"

# Options keys
CONF_SCAN_INTERVAL: Final = "scan_interval"
CONF_MONITORED_CATEGORIES: Final = "monitored_categories"

# Defaults
DEFAULT_HOST: Final = "localhost"
DEFAULT_PORT: Final = 5600
DEFAULT_SCAN_INTERVAL: Final = 15
MIN_SCAN_INTERVAL: Final = 5
MAX_SCAN_INTERVAL: Final = 300
DEFAULT_DEVICE_NAME: Final = "ActivityWatch"

# Bucket patterns
BUCKET_WINDOW: Final = "aw-watcher-window"
BUCKET_AFK: Final = "aw-watcher-afk"

# Event
EVENT_ACTIVITY_SWITCH: Final = "activitywatch_event"
