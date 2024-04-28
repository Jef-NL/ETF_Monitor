"""Platform for sensor integration."""

from __future__ import annotations

import logging
import os

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import CURRENCY_EURO
from homeassistant.core import Event, HomeAssistant, State, callback
from homeassistant.exceptions import NoEntitySpecifiedError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.yaml import load_yaml_dict, save_yaml

from .const import (
    ASSET_LIST_TOP_FIELD,
    CONF_FILE_OPTION_FIELD,
    DEFAULT_CONFIG_NAME,
    DEFAULT_POLLING_RATE_S,
    DOMAIN,
    MIN_POLLING_RATE_S,
    POLL_RATE_FIELD,
)
from .coordinator import ETFUpdateCoordinator
from .EtfMonitor import ETFEntry, ETFList

_logger = logging.getLogger(DOMAIN)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the sensor platform."""

    # Load ETFs from the configuration file
    etf_conf = {}
    conf_path = hass.config.path(
        config.get(CONF_FILE_OPTION_FIELD, DEFAULT_CONFIG_NAME)
    )
    if os.path.exists(conf_path):
        etf_conf = load_yaml_dict(conf_path)
        _logger.info("Loaded configuration: %s", etf_conf)
    else:
        save_yaml(conf_path, {ASSET_LIST_TOP_FIELD: []})
        _logger.warning(
            "ETF Configuration was not found. Created a new configuration to be filled '%s'. Not loaded the Integration.",
            conf_path,
        )
        return

    # Create entry per ETF
    entries = await ETFList.entries_from_dict(etf_conf)
    if entries is None or not entries.etfs:
        _logger.error("Failed to load entries. Not loading the integration.")
        return

    # Setup the update coordinator
    coordinator = ETFUpdateCoordinator(
        hass,
        _logger,
        entries,
        max(config.get(POLL_RATE_FIELD, DEFAULT_POLLING_RATE_S), MIN_POLLING_RATE_S),
    )
    await coordinator.async_config_entry_first_refresh()

    # Create the sensor entries
    sensor_entities = []
    for etf in entries.etfs:
        sensor_entities.append(
            MonitorSensorEntity(
                coordinator=coordinator, idx=etf.name, name=etf.name, entry=etf
            )
        )
        sensor_entities.append(
            CalculateSensorEntity(
                hass=hass, name=etf.name + " Gain", entry=etf, tracking=etf.name
            )
        )

    # Add configured entities
    async_add_entities(sensor_entities)


class MonitorSensorEntity(CoordinatorEntity, SensorEntity):
    """Live ETF monitoring sensor."""

    def __init__(self, coordinator, idx, name: str, entry: ETFEntry) -> None:
        """Initialize etf_monitor Sensor."""
        super().__init__(coordinator, context=idx)
        self.idx = idx
        self._attr_name = name
        self._etf_entry = entry
        self._attr_extra_state_attributes = entry.__dict__
        self._state_value: float = self.coordinator.data.get(self.idx, 0)

    async def async_added_to_hass(self) -> None:
        """Assign entity ID to the ETF entry."""
        await super().async_added_to_hass()  # Used by coordinator
        self._etf_entry.entity_id = self.entity_id

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        _logger.debug(
            "Value update for %s : %f", self.entity_id, self.coordinator.data[self.idx]
        )
        self._state_value = self.coordinator.data.get(self.idx, 0)
        self.async_write_ha_state()

    @property
    def name(self):
        """Return name of entity."""
        return self._attr_name

    @property
    def state(self):
        """Return last entity state."""
        return f"{self._state_value:.2f}"

    @property
    def unit_of_measurement(self):
        """Default unit of measurement."""
        return CURRENCY_EURO

    @property
    def unique_id(self):
        """Entity unique ID."""
        return self._etf_entry.isin


class CalculateSensorEntity(SensorEntity):
    """Connected entity to the ETF, updating the depot status calculations."""

    def __init__(
        self, hass: HomeAssistant, name: str, entry: ETFEntry, tracking: str
    ) -> None:
        """Initialize etf_monitor Sensor."""
        super().__init__()
        self._attr_name = name
        self._etf_entry = entry
        self._state_value: float = 0.0
        self._unsub = None
        self._tracking_entity = (
            f"sensor.{tracking.lower().replace(' ', '_').replace('-', '_')}"
        )

    async def async_added_to_hass(self) -> None:
        """Update attributes and link value events on add event."""
        self._unsub = async_track_state_change_event(
            hass=self.hass,
            entity_ids=[self._tracking_entity],
            action=self._value_event,
        )
        self._state_value = await self._etf_entry.calulate_gain()
        await self._set_extra_attributes()

    async def _value_event(self, event: Event):
        """Respond to Callback of entity on update."""
        try:
            new_state: State = event.data["new_state"]
            self._state_value = await self._etf_entry.calulate_gain(
                float(new_state.state)
            )
            self.async_write_ha_state()
        except NoEntitySpecifiedError:
            ...  # Ignore exceptions raised
        except RuntimeError:
            ...  # Ignore exceptions raised
        except ValueError:
            ...  # Entry failed setup, value is invalid

    async def _set_extra_attributes(self):
        """Set extra state attribites."""
        shares = await self._etf_entry.get_shares_amount()
        self._attr_extra_state_attributes = {
            "shares": shares,
            "current_value": await self._etf_entry.get_shares_value(shares),
        }

    @property
    def name(self):
        """Return name of entity."""
        return self._attr_name

    @property
    def state(self):
        """Return last entity state."""
        return f"{self._state_value:.2f}"

    @property
    def unit_of_measurement(self):
        """Default unit of measurement."""
        return CURRENCY_EURO

    @property
    def unique_id(self):
        """Entity unique ID."""
        return f"{self._etf_entry.isin}_gain"
