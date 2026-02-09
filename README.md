# ActivityWatch Integration for Home Assistant

Track your computer activity in Home Assistant using [ActivityWatch](https://activitywatch.net/), a free and open-source automated time tracker.

This integration connects to your local ActivityWatch instance and exposes your current activity, AFK status, and per-category tracking as Home Assistant entities — enabling automations based on what you're doing at your computer.

## Features

- **Current Activity Sensor** — Shows what app and window you're using right now, with category, title, and duration as attributes
- **Active/AFK Binary Sensor** — Detects whether you're at your computer or away, great for presence-based automations
- **Category Binary Sensors** — Create binary sensors for specific categories (e.g. "Working", "Gaming") to trigger automations when you switch activities
- **Window Switch Events** — Fires `activitywatch_event` on the HA event bus when you switch apps, for granular automations without sensor noise
- **Query Stats Service** — Query historical usage data (e.g. "How long did I code today?") for use in templates and notifications

## Requirements

- A running [ActivityWatch](https://activitywatch.net/) instance accessible over the network from your Home Assistant server
- ActivityWatch's `aw-watcher-window` and `aw-watcher-afk` must be running on the monitored machine

> **Note:** By default, ActivityWatch only listens on `127.0.0.1`. To allow connections from your HA server, start `aw-server` with `--host 0.0.0.0` or set `host = "0.0.0.0"` in your ActivityWatch server config (`~/.config/activitywatch/aw-server/config.toml`).

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Go to **Integrations** > three-dot menu > **Custom repositories**
3. Add this repository URL and select **Integration** as the category
4. Click **Download**
5. Restart Home Assistant

### Manual

1. Copy the `custom_components/activitywatch/` folder into your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant

## Setup

1. Go to **Settings > Devices & Services > Add Integration**
2. Search for **ActivityWatch**
3. Enter:
   - **Host** — IP address or hostname of your ActivityWatch server
   - **Port** — Default is `5600`
   - **API Key** — Optional, for future use
   - **Device Name** — A label for this machine (e.g. "Desktop", "Work Laptop")

## Entities

Once configured, the integration creates a device with the following entities:

| Entity | Type | Description |
|--------|------|-------------|
| `sensor.<device>_current_activity` | Sensor | Current activity category (e.g. "Work", "Uncategorized") |
| `binary_sensor.<device>_active` | Binary Sensor | ON when actively using the computer, OFF when AFK |
| `binary_sensor.<device>_is_<category>` | Binary Sensor | ON when the current activity matches a configured category |

### Sensor Attributes

The current activity sensor includes these attributes:

| Attribute | Description |
|-----------|-------------|
| `app_name` | Active application (e.g. "Firefox", "Code") |
| `window_title` | Title of the active window |
| `url` | URL if available from a browser watcher |
| `sub_categories` | Full category hierarchy (e.g. `["Work", "Engineering"]`) |
| `duration` | Seconds spent in the current event |

## Options

After setup, you can configure options via **Settings > Devices & Services > ActivityWatch > Configure**:

- **Scan Interval** — How often to poll ActivityWatch (5–300 seconds, default: 15)
- **Monitored Categories** — Comma-separated list of categories to create binary sensors for (e.g. `Work, Gaming, Browsing`)

## Services

### `activitywatch.query_stats`

Query historical activity data. Returns a response variable — use it with the **Perform action** step in automations or in Developer Tools > Services.

| Field | Required | Description |
|-------|----------|-------------|
| `device_id` | Yes | The device name you configured |
| `start_time` | No | ISO timestamp, defaults to start of today |
| `end_time` | No | ISO timestamp, defaults to now |
| `category` | No | Filter by category name |

**Example response:**

```json
{
  "total_seconds": 14400,
  "top_apps": [
    {"name": "VS Code", "seconds": 10000},
    {"name": "Slack", "seconds": 4400}
  ]
}
```

## Automation Examples

**Turn on desk lamp when I start working:**

```yaml
automation:
  - trigger:
      - platform: state
        entity_id: binary_sensor.desktop_is_work
        to: "on"
    action:
      - service: light.turn_on
        target:
          entity_id: light.desk_lamp
```

**Send a notification when AFK for more than 30 minutes:**

```yaml
automation:
  - trigger:
      - platform: state
        entity_id: binary_sensor.desktop_active
        to: "off"
        for: "00:30:00"
    action:
      - service: notify.mobile_app
        data:
          message: "You've been away from your desktop for 30 minutes."
```

**Dim lights when watching a video:**

```yaml
automation:
  - trigger:
      - platform: event
        event_type: activitywatch_event
    condition:
      - condition: template
        value_template: "{{ trigger.event.data.app in ['vlc', 'mpv'] }}"
    action:
      - service: light.turn_on
        target:
          entity_id: light.living_room
        data:
          brightness_pct: 20
```
