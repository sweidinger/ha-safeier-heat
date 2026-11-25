"""Select: auto-off timer."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SafeierConfigEntry
from .const import TIMER_OPTIONS
from .entity import SafeierEntity

OPTIONS = {"off": 0, "20": 20, "40": 40, "60": 60, "90": 90}


async def async_setup_entry(
    hass: HomeAssistant, entry: SafeierConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([SafeierTimer(entry.runtime_data)])


class SafeierTimer(SafeierEntity, SelectEntity):
    _attr_translation_key = "timer"
    _attr_options = list(OPTIONS)

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "timer")

    @property
    def current_option(self) -> str | None:
        data = self.coordinator.data
        if data is None:
            return None
        if data.timer_min in TIMER_OPTIONS and data.timer_min:
            return str(data.timer_min)
        return "off"

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.async_set(timer_min=OPTIONS[option])
