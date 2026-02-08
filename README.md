# Home Assistant Integration Development Guide

## ActivityWatch Integration for Official Repository

This guide covers development standards and workflows for building the ActivityWatch integration following Home Assistant's official guidelines.

---

## Project Structure

```
activitywatch/
├── __init__.py           # Integration setup, platforms, unload
├── config_flow.py        # UI-based configuration flow
├── const.py              # Constants (domain, update interval, etc.)
├── coordinator.py        # DataUpdateCoordinator for API polling
├── sensor.py             # Sensor platform entities
├── manifest.json         # Integration metadata
├── strings.json          # Translatable UI strings
└── tests/
    ├── __init__.py
    ├── conftest.py       # Test fixtures
    ├── test_config_flow.py
    ├── test_init.py
    └── test_sensor.py
```

---

## Development Environment Setup

### 1. Create Project Structure

```bash
# Create project directory
mkdir -p ~/ha-activitywatch-integration
cd ~/ha-activitywatch-integration

# Create virtualenv (use Python 3.12, matching HA 2024.x+)
python3.12 -m venv venv

# Activate virtualenv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel
```

### 2. Create Development Requirements

Create `requirements-dev.txt` (for local development):

```txt
# Home Assistant
homeassistant>=2024.1.0

# Testing
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-asyncio>=0.21.0
pytest-homeassistant-custom-component>=0.13.0

# Code quality
ruff>=0.1.0
mypy>=1.7.0
pre-commit>=3.5.0

# ActivityWatch API client
aw-client>=0.5.13

# Type stubs
types-aiohttp
```

**Note:** The integration's runtime dependencies go in `manifest.json`, not requirements.txt. The `requirements-dev.txt` is only for your development environment.

Install dependencies:

```bash
pip install -r requirements-dev.txt
```

### 3. Project Layout

```bash
# Create integration directory structure
mkdir -p custom_components/activitywatch
mkdir -p tests/components/activitywatch

# Your working tree should look like:
# ~/ha-activitywatch-integration/
# ├── venv/                    # Virtual environment (don't commit)
# ├── requirements-dev.txt     # Development dependencies
# ├── custom_components/
# │   └── activitywatch/
# │       ├── __init__.py
# │       ├── config_flow.py
# │       ├── const.py
# │       ├── coordinator.py
# │       ├── sensor.py
# │       ├── manifest.json
# │       └── strings.json
# └── tests/
#     └── components/
#         └── activitywatch/
#             ├── __init__.py
#             ├── conftest.py
#             ├── test_config_flow.py
#             ├── test_init.py
#             └── test_sensor.py
```

### 4. Git Configuration

Create `.gitignore`:

```gitignore
# Virtual environment
venv/
env/
.venv/

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg-info/
dist/
build/

# Testing
.coverage
.pytest_cache/
htmlcov/
.tox/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db
```

Initialize git:

```bash
git init
git add .
git commit -m "Initial project structure"
```

### 5. Pre-commit Hooks (Optional but Recommended)

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.15
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.1
    hooks:
      - id: mypy
        additional_dependencies: [types-aiohttp]
        args: [--ignore-missing-imports]
```

Install hooks:

```bash
pre-commit install
```

Now ruff and mypy run automatically on `git commit`!

### 6. Configure Python Path

For testing to work, HA needs to find your custom component. Create `pytest.ini`:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto

# Add custom_components to Python path
pythonpath = .
```

### 7. Sync to Production HA Server

Use rsync for rapid iteration:

```bash
# Create sync script: ~/ha-activitywatch-integration/sync-to-ha.sh
#!/bin/bash
rsync -av --delete \
  ~/ha-activitywatch-integration/custom_components/activitywatch/ \
  homeassistant@YOUR_HA_SERVER:/config/custom_components/activitywatch/

# Restart HA
ssh homeassistant@YOUR_HA_SERVER "ha core restart"
echo "✓ Synced and restarted Home Assistant"
```

Make it executable:

```bash
chmod +x sync-to-ha.sh
```

---

## Coding Standards (Official HA Requirements)

### Type Hints (REQUIRED)

All functions must have complete type hints:

```python
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import Entity

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Set up ActivityWatch from a config entry."""
    ...
```

### Async/Await (REQUIRED)

- All I/O operations must be async
- Use `asyncio` for concurrency
- Never block the event loop with sync I/O

```python
# GOOD
async def async_update_data() -> dict[str, Any]:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

# BAD - blocks event loop
def update_data() -> dict[str, Any]:
    response = requests.get(url)
    return response.json()
```

### Code Style

**Formatter: Ruff** (replaces Black/isort)

```bash
# Format code
ruff format .

# Check and fix linting issues
ruff check . --fix
```

**Linter Configuration:**

- Line length: 88 characters
- Use double quotes for strings
- Import ordering: stdlib → third-party → homeassistant → local

**Type Checker: mypy**

```bash
# Type check the integration
mypy homeassistant/components/activitywatch
```

### Common Patterns

**1. DataUpdateCoordinator (for polling)**

```python
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

class ActivityWatchCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Manage ActivityWatch data updates."""

    def __init__(self, hass: HomeAssistant, api_client: ActivityWatchAPI) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="ActivityWatch",
            update_interval=timedelta(minutes=5),
        )
        self.api = api_client

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from ActivityWatch API."""
        try:
            return await self.api.get_current_window()
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
```

**2. Config Flow (UI setup)**

```python
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

class ActivityWatchConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ActivityWatch."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Validate input
            try:
                await self._test_connection(user_input[CONF_HOST])
            except ConnectionError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=user_input[CONF_HOST],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST, default="localhost:5600"): str,
            }),
            errors=errors,
        )
```

**3. Sensor Entity**

```python
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

class ActivityWatchSensor(CoordinatorEntity, SensorEntity):
    """Representation of an ActivityWatch sensor."""

    def __init__(
        self,
        coordinator: ActivityWatchCoordinator,
        name: str,
        key: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = name
        self._attr_unique_id = f"activitywatch_{key}"
        self._key = key

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        return self.coordinator.data.get(self._key)
```

---

## Testing Requirements (CRITICAL)

### Test Coverage: >90% Required

```bash
# Run tests with coverage
pytest --cov=homeassistant/components/activitywatch --cov-report=term-missing

# Must show >90% coverage:
# homeassistant/components/activitywatch/__init__.py    95%
# homeassistant/components/activitywatch/config_flow.py 92%
# homeassistant/components/activitywatch/sensor.py      94%
```

### Test Structure

**conftest.py** - Fixtures

```python
from unittest.mock import patch
import pytest
from homeassistant.core import HomeAssistant

@pytest.fixture
def mock_activitywatch_api():
    """Mock ActivityWatch API."""
    with patch("homeassistant.components.activitywatch.ActivityWatchAPI") as mock:
        mock.return_value.get_current_window.return_value = {
            "app": "firefox",
            "title": "Home Assistant",
            "duration": 120.5,
        }
        yield mock
```

**test_config_flow.py** - Test UI setup

```python
from homeassistant import config_entries
from homeassistant.const import CONF_HOST

async def test_form(hass: HomeAssistant, mock_activitywatch_api) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "localhost:5600"},
    )
    assert result2["type"] == "create_entry"
    assert result2["title"] == "localhost:5600"
```

**test_sensor.py** - Test entities

```python
async def test_sensor_values(
    hass: HomeAssistant,
    mock_activitywatch_api,
    config_entry: ConfigEntry,
) -> None:
    """Test sensor reports correct values."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.activitywatch_current_app")
    assert state is not None
    assert state.state == "firefox"
```

### Running Tests

```bash
# All tests
pytest tests/components/activitywatch/

# Specific test file
pytest tests/components/activitywatch/test_config_flow.py

# Single test
pytest tests/components/activitywatch/test_config_flow.py::test_form

# With coverage
pytest --cov --cov-report=html
```

---

## Manifest.json Requirements

```json
{
  "domain": "activitywatch",
  "name": "ActivityWatch",
  "codeowners": ["@yourgithub"],
  "config_flow": true,
  "documentation": "https://www.home-assistant.io/integrations/activitywatch",
  "iot_class": "local_polling",
  "requirements": ["aw-client==0.5.13"],
  "version": "1.0.0"
}
```

**Key fields:**

- `iot_class`: Must be one of: `local_polling`, `cloud_polling`, `local_push`, `cloud_push`
- `requirements`: PyPI packages (must be on PyPI for official integration)
- `config_flow`: true (YAML-only configs not accepted for new integrations)

---

## Quality Checklist

Before submitting PR to HA core:

- [ ] All type hints present (`mypy` passes)
- [ ] Code formatted with `ruff format`
- [ ] No linting issues (`ruff check`)
- [ ] Test coverage >90%
- [ ] All tests pass (`pytest`)
- [ ] Config flow implemented (no YAML)
- [ ] All strings in `strings.json`
- [ ] Unique IDs for all entities
- [ ] Coordinator used for polling
- [ ] No blocking I/O in event loop
- [ ] Error handling for network failures
- [ ] Logs use proper levels (debug/info/warning/error)

---

## Development Workflow

### Daily Setup

```bash
cd ~/ha-activitywatch-integration
source venv/bin/activate  # Always activate first!
```

### Iteration Cycle

1. **Edit code locally** in `custom_components/activitywatch/`
2. **Run tests**: `pytest tests/components/activitywatch/`
3. **Check types**: `mypy custom_components/activitywatch`
4. **Format**: `ruff format . && ruff check . --fix`
5. **Sync to HA server**: `./sync-to-ha.sh`
6. **Test in UI**: Check logs, test sensors, verify config flow
7. **Repeat**

### Logging Best Practices

```python
import logging

_LOGGER = logging.getLogger(__name__)

# DEBUG: Detailed diagnostic info
_LOGGER.debug("Fetched data: %s", data)

# INFO: Notable events (setup, updates)
_LOGGER.info("ActivityWatch integration setup complete")

# WARNING: Recoverable issues
_LOGGER.warning("Failed to fetch data, retrying: %s", err)

# ERROR: Failures that prevent functionality
_LOGGER.error("Cannot connect to ActivityWatch: %s", err)
```

---

## Common Pitfalls

1. **Blocking I/O**: Never use `requests`, always `aiohttp`
2. **Missing type hints**: Will fail CI checks
3. **Low test coverage**: Must be >90%
4. **YAML config**: Not accepted for new integrations
5. **Hardcoded strings**: Must be in `strings.json` for translation
6. **No unique IDs**: Entities won't be configurable in UI
7. **Direct API calls in entities**: Use DataUpdateCoordinator

---

## Resources

- [HA Developer Docs](https://developers.home-assistant.io/)
- [Integration Development](https://developers.home-assistant.io/docs/creating_component_index)
- [Code Review Checklist](https://developers.home-assistant.io/docs/development_checklist)
- [Style Guide](https://developers.home-assistant.io/docs/development_guidelines)
- [Example Integrations](https://github.com/home-assistant/core/tree/dev/homeassistant/components)

---

## Quick Command Reference

```bash
# Initial Setup
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt

# Daily Work (always activate venv first!)
source venv/bin/activate

# Format & Lint
ruff format .
ruff check . --fix

# Type Check
mypy custom_components/activitywatch

# Test
pytest tests/components/activitywatch/ --cov --cov-report=term-missing

# Sync to Production
./sync-to-ha.sh

# Deactivate when done
deactivate
```
