"""Defines base entities for Google Home"""
from __future__ import annotations
from datetime import timedelta
import logging

from abc import ABC, abstractmethod

from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from homeassistant.core import HomeAssistant, callback

from .api import GlocaltokensApiClient
from .const import DEFAULT_NAME, DOMAIN, MANUFACTURER
from .models import GoogleHomeDevice
from .types import DeviceInfo

_LOGGER: logging.Logger = logging.getLogger(__package__)


class GoogleHomeBaseEntity(CoordinatorEntity, ABC):
    """Base entity base for Google Home sensors"""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        client: GlocaltokensApiClient,
        device_id: str,
        device_name: str,
        device_model: str,
    ):
        super().__init__(coordinator)
        self.client = client
        self.device_id = device_id
        self.device_name = device_name
        self.device_model = device_model

    @property
    @abstractmethod
    def label(self) -> str:
        """Label to use for name and unique id."""

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"{self.device_name} {self.label}"

    @property
    def unique_id(self) -> str:
        """Return a unique ID to use for this entity."""
        return f"{self.device_id}/{self.label}"

    @property
    def device_info(self) -> DeviceInfo:
        return {
            "identifiers": {(DOMAIN, self.device_id)},
            "name": f"{DEFAULT_NAME} {self.device_name}",
            "manufacturer": MANUFACTURER,
            "model": self.device_model,
        }

    def get_device(self) -> GoogleHomeDevice | None:
        """Return the device matched by device name
        from the list of google devices in coordinator_data"""
        matched_devices: list[GoogleHomeDevice] = [
            device
            for device in self.coordinator.data
            if device.device_id == self.device_id
        ]
        return matched_devices[0] if matched_devices else None


class BTDeviceEntity(CoordinatorEntity):
    """Defines the base Google Home entity."""

    def __init__(
        self,
        coordinator: GoogleHomeBTDeviceUpdater,
        name: str,
        icon: str,
        system_id: str,
        item_id: str,
    ):
        """Initialize the Google Home Entity."""
        super().__init__(coordinator)

        self._name = name
        self._unique_id = item_id if item_id else system_id
        self._icon = icon
        self._system_id = system_id
        self._item_id = item_id
        self._attrs = {}

    @property
    def unique_id(self) -> str:
        """Return a unique, Home Assistant friendly identifier for this entity."""
        return self._unique_id

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def icon(self) -> str:
        """Return the icon for the entity."""
        return self._icon

    @property
    def extra_state_attributes(self) -> str:
        """Return the attributes."""
        self._attrs["system"] = self._system_id
        return self._attrs

    @property
    def entity_registry_enabled_default(self) -> any:
        """Return option setting to enable or disable by default."""
        return self.coordinator.add_disabled

    async def async_added_to_hass(self) -> None:
        """When entity is added to HASS."""
        self.async_on_remove(self.coordinator.async_add_listener(self._update_callback))

    @callback
    def _update_callback(self) -> None:
        """Handle device update."""
        self.async_write_ha_state()

    async def _delete_callback(self, device_id):
        """Remove the device when it disappears."""

        if device_id == self._unique_id:
            entity_registry = (
                await self.hass.helpers.entity_registry.async_get_registry()
            )

            if entity_registry.async_is_registered(self.entity_id):
                entity_entry = entity_registry.async_get(self.entity_id)
                entity_registry.async_remove(self.entity_id)
                await cleanup_device_registry(self.hass, entity_entry.device_id)
            else:
                await self.async_remove()


async def cleanup_device_registry(hass: HomeAssistant, device_id):
    """Remove device registry entry if there are no remaining entities."""

    device_registry = await hass.helpers.device_registry.async_get_registry()
    entity_registry = await hass.helpers.entity_registry.async_get_registry()
    if device_id and not hass.helpers.entity_registry.async_entries_for_device(
        entity_registry, device_id, include_disabled_entities=True
    ):
        device_registry.async_remove_device(device_id)


class GoogleHomeBTDeviceUpdater(DataUpdateCoordinator):
    """Class to manage fetching update data from the Google Home API."""

    def __init__(
        self,
        hass,
        name: str,
        polling_interval: int,
    ):
        """Initialize the global Google Home data updater."""

        super().__init__(
            hass=hass,
            logger=_LOGGER,
            name=name,
            update_interval=timedelta(seconds=polling_interval),
        )

    async def _async_update_data(self) -> None:
        """Fetch data from Google Home API."""
