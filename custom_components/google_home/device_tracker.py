"""Support for Google Wifi Routers as device tracker."""

from homeassistant.components.device_tracker.config_entry import ScannerEntity
from homeassistant.components.device_tracker.const import SOURCE_TYPE_BLUETOOTH
from homeassistant.const import ATTR_NAME
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.const import ATTR_NAME

from .entity import BTDeviceEntity
from .types import GoogleHomeBTDeviceDict
from .const import (
    ATTR_CONNECTIONS,
    ATTR_IDENTIFIERS,
    ATTR_MANUFACTURER,
    ATTR_MODEL,
    DATA_COORDINATOR,
    ICON_BT_DEVICES,
    DEV_CLIENT_MODEL,
    DEV_MANUFACTURER,
    DOMAIN,
    SIGNAL_ADD_DEVICE,
)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the device tracker platforms."""

    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    entities = []

    for device in coordinator.data:
        entity = GoogleHomeDeviceTracker(
            coordinator=coordinator,
            device_name=device.device_name,
            icon=ICON_BT_DEVICES,
            device_id=device.device_id,
        )
        entities.append(entity)

    async_add_entities(entities)

    async def async_new_entities(device_info: GoogleHomeBTDeviceDict):
        """Add new entities when they connect to Google Home."""

        entity = GoogleHomeDeviceTracker(
            coordinator=coordinator,
            icon=ICON_BT_DEVICES,
            device_name=device_info.device_name,
            device_id=device_info.device_id,
            device_class=device_info.device_class,
            mac_address=device_info.mac_address,
            rssi=device.rssi,
            expected_profiles=device.expected_profiles,
        )
        entities = [entity]
        async_add_entities(entities)

    async_dispatcher_connect(hass, SIGNAL_ADD_DEVICE, async_new_entities)


class GoogleHomeDeviceTracker(BTDeviceEntity, ScannerEntity):
    """Defines a Google Home device tracker."""

    def __init__(
        self,
        coordinator,
        icon,
        device_name,
        device_id,
        device_class,
        mac_address,
        rssi,
        expected_profiles,
    ):
        """Initialize the device tracker."""
        super().__init__(
            coordinator=coordinator,
            icon=icon,
            device_name=device_name,
            device_id=device_id,
            device_class=device_class,
            mac_address=mac_address,
            rssi=rssi,
            expected_profiles=expected_profiles,
        )

        self._is_connected = None
        self._mac = mac_address

    @property
    def is_connected(self):
        """Return true if the device is connected."""
        # try:
        #     if self.coordinator.data[self._system_id]["devices"][self._item_id].get(
        #         "connected"
        #     ):
        #         connected_gh = self.coordinator.data[self._system_id]["devices"][
        #             self._item_id
        #         ].get("apId")
        #         if connected_gh:
        #             connected_gh = self.coordinator.data[self._system_id][
        #                 "access_points"
        #             ][connected_gh]["accessPointSettings"]["accessPointOtherSettings"][
        #                 "roomData"
        #             ][
        #                 "name"
        #             ]
        #             self._attrs["connected_gh"] = connected_gh
        #         else:
        #             self._attrs["connected_gh"] = "NA"

        #         self._mac = self.coordinator.data[self._system_id]["devices"][
        #             self._item_id
        #         ].get("macAddress")

        #         self._attrs["mac"] = self._mac if self._mac else "NA"

        #         self._is_connected = True
        #     else:
        #         self._is_connected = False
        # except TypeError:
        #     pass
        # except KeyError:
        #     pass

        self._is_connected = True

        return self._is_connected

    @property
    def source_type(self):
        """Return the source type of the client."""
        return SOURCE_TYPE_BLUETOOTH

    @property
    def device_info(self):
        """Define the device as a device tracker system."""
        if self._mac:
            mac = {(CONNECTION_NETWORK_MAC, self._mac)}
        else:
            mac = {}

        device_info = {
            ATTR_IDENTIFIERS: {(DOMAIN, self._item_id)},
            ATTR_NAME: self._name,
            ATTR_CONNECTIONS: mac,
            ATTR_MANUFACTURER: DEV_MANUFACTURER,
            ATTR_MODEL: DEV_CLIENT_MODEL,
            "via_device": (DOMAIN, self._system_id),
        }

        return device_info
