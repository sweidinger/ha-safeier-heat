"""Config flow: Bluetooth discovery of 'vm-*' sock batteries."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_ADDRESS, CONF_NAME

from .const import DOMAIN


SERVICE_UUID = "0000af30-0000-1000-8000-00805f9b34fb"


def _is_sock(info: BluetoothServiceInfoBleak) -> bool:
    # The 'vm-…' name is only in the scan response, so passive scanners never
    # see it. The advertised AF30 service is what the vendor app filters on.
    return SERVICE_UUID in info.service_uuids or (info.name or "").lower().startswith("vm-")


class SafeierConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._discovery: BluetoothServiceInfoBleak | None = None
        self._found: dict[str, str] = {}

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()
        if not _is_sock(discovery_info):
            return self.async_abort(reason="not_supported")
        self._discovery = discovery_info
        self.context["title_placeholders"] = {"name": discovery_info.address[-5:]}
        return await self.async_step_confirm()

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        assert self._discovery
        if user_input is not None:
            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data={CONF_ADDRESS: self._discovery.address},
            )
        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema(
                {vol.Required(CONF_NAME, default=f"Heizsocke {self._discovery.address[-5:]}"): str}
            ),
            description_placeholders={"address": self._discovery.address},
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=user_input[CONF_NAME], data={CONF_ADDRESS: address}
            )

        current = self._async_current_ids()
        for info in async_discovered_service_info(self.hass, connectable=True):
            if _is_sock(info) and info.address not in current:
                self._found[info.address] = info.address if info.name == info.address else f"{info.name} ({info.address})"
        if not self._found:
            return self.async_abort(reason="no_devices_found")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): vol.In(self._found),
                    vol.Required(CONF_NAME, default="Heizsocke"): str,
                }
            ),
        )
