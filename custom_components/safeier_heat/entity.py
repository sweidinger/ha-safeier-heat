"""Base entity."""

from __future__ import annotations

from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import SafeierCoordinator
from .const import DOMAIN


class SafeierEntity(CoordinatorEntity[SafeierCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: SafeierCoordinator, key: str) -> None:
        super().__init__(coordinator)
        address = coordinator.address
        self._attr_unique_id = f"{address}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, address)},
            connections={(CONNECTION_BLUETOOTH, address)},
            name=coordinator.config_entry.title,
            manufacturer="Dongguan Pinguan Sports Technology",
            model="PG-6000A",
        )
