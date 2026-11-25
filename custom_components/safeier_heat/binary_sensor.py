"""Binary sensor: heating on/off."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SafeierConfigEntry
from .entity import SafeierEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: SafeierConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([SafeierHeating(entry.runtime_data)])


class SafeierHeating(SafeierEntity, BinarySensorEntity):
    _attr_translation_key = "heating"
    _attr_device_class = BinarySensorDeviceClass.HEAT

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "heating")

    @property
    def is_on(self) -> bool | None:
        data = self.coordinator.data
        return None if data is None else data.heating
