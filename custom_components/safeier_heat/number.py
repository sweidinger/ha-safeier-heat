"""Number: heating setpoint."""

from __future__ import annotations

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SafeierConfigEntry
from .const import SETPOINT_MAX, SETPOINT_MIN
from .entity import SafeierEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: SafeierConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([SafeierSetpoint(entry.runtime_data)])


class SafeierSetpoint(SafeierEntity, NumberEntity):
    _attr_translation_key = "setpoint"
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_native_min_value = SETPOINT_MIN
    _attr_native_max_value = SETPOINT_MAX
    _attr_native_step = 5
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "setpoint_number")

    @property
    def native_value(self) -> float | None:
        data = self.coordinator.data
        return None if data is None else data.setpoint

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set(setpoint=int(value))
