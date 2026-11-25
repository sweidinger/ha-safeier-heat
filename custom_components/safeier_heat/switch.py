"""Switches: heating on/off, quick heating."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SafeierConfigEntry
from .entity import SafeierEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: SafeierConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    async_add_entities([SafeierHeatingSwitch(coordinator), SafeierFlashSwitch(coordinator)])


class SafeierHeatingSwitch(SafeierEntity, SwitchEntity):
    _attr_translation_key = "heating"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "heating_switch")

    @property
    def is_on(self) -> bool | None:
        data = self.coordinator.data
        return None if data is None else data.heating

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_set(heating=True)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set(heating=False, flash=False)


class SafeierFlashSwitch(SafeierEntity, SwitchEntity):
    _attr_translation_key = "flash_heating"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "flash_heating")

    @property
    def is_on(self) -> bool | None:
        data = self.coordinator.data
        return None if data is None else data.flash_heating

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_set(heating=True, flash=True)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set(flash=False)
