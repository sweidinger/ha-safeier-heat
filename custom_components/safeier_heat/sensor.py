"""Sensors: battery %, cell voltage, setpoint."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfElectricPotential, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SafeierConfigEntry
from .entity import SafeierEntity
from .protocol import SockStatus


@dataclass(frozen=True, kw_only=True)
class SafeierSensorDescription(SensorEntityDescription):
    value_fn: Callable[[SockStatus], float | int | str | None]


SENSORS: tuple[SafeierSensorDescription, ...] = (
    SafeierSensorDescription(
        key="battery",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda s: s.battery_percent,
    ),
    SafeierSensorDescription(
        key="voltage",
        translation_key="voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT,
        suggested_unit_of_measurement=UnitOfElectricPotential.VOLT,
        suggested_display_precision=2,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda s: s.voltage_mv or None,
    ),
    SafeierSensorDescription(
        key="setpoint",
        translation_key="setpoint",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda s: s.setpoint,
    ),
    SafeierSensorDescription(
        key="raw",
        translation_key="raw",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda s: s.raw,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: SafeierConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(SafeierSensor(coordinator, d) for d in SENSORS)


class SafeierSensor(SafeierEntity, SensorEntity):
    entity_description: SafeierSensorDescription

    def __init__(self, coordinator, description: SafeierSensorDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self):
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)
