"""Home Assistant registry clients over the WebSocket API."""

import asyncio
import json
import logging
from typing import Any

import websockets

import ha_config
from models import (
    Device,
    HassManifest,
    HassArea,
    HassConfigEntry,
    HassDevice,
    HassFloor,
    HomeAssistantError,
)

_LOGGER = logging.getLogger(__name__)

_WS_URL = ha_config._HA_WS_URL
_TOKEN = ha_config._token()


async def _send_command(payload: dict) -> Any:
    async with websockets.connect(_WS_URL) as ws:
        msg = json.loads(await ws.recv())
        if msg.get("type") != "auth_required":
            raise HomeAssistantError(
                f"Unexpected auth message: {msg.get('type')}"
            )
        await ws.send(json.dumps({"type": "auth", "access_token": _TOKEN}))
        msg = json.loads(await ws.recv())
        if msg.get("type") != "auth_ok":
            raise HomeAssistantError(
                f"Authentication failed: {msg.get('type')}"
            )
        await ws.send(json.dumps(payload))
        while True:
            msg = json.loads(await ws.recv())
            if msg.get("id") == payload.get("id"):
                break
        if not msg.get("success"):
            raise HomeAssistantError(
                msg.get("message", "unknown Home Assistant error")
            )
        return msg.get("result")


async def get_hass_devices() -> list[HassDevice]:
    result = await _send_command(
        {"id": 1, "type": "config/device_registry/list"}
    )
    return [HassDevice(**d) for d in result]


async def get_areas() -> list[HassArea]:
    result = await _send_command(
        {"id": 2, "type": "config/area_registry/list"}
    )
    return [HassArea.model_validate(d) for d in result]


async def get_floors() -> list[HassFloor]:
    result = await _send_command(
        {"id": 3, "type": "config/floor_registry/list"}
    )
    return [HassFloor.model_validate(d) for d in result]


async def get_config_entries() -> list[HassConfigEntry]:
    result = await _send_command(
        {"id": 4, "type": "config_entries/get"}
    )
    return [HassConfigEntry.model_validate(e) for e in result]


async def get_integration_names() -> dict[str, HassManifest]:
    result = await _send_command({"id": 5, "type": "manifest/list"})
    manifests: dict[str, HassManifest] = {}
    for domain, manifest in result.items():
        try:
            manifests[domain] = HassManifest.model_validate(
                {**manifest, "domain": domain}
            )
        except Exception:
            _LOGGER.warning(
                "Skipping unparseable manifest for domain %s", domain
            )
    return manifests


async def get_devices_with_location() -> list[Device]:
    devices, areas, floors, entries, manifests = await asyncio.gather(
        get_hass_devices(),
        get_areas(),
        get_floors(),
        get_config_entries(),
        get_integration_names(),
    )
    _LOGGER.info(entries)
    area_by_id = {area.area_id: area for area in areas}
    floor_by_id = {floor.floor_id: floor for floor in floors}
    entry_by_id = {entry.entry_id: entry for entry in entries}
    result = []
    for device in devices:
        area = area_by_id.get(device.area_id) if device.area_id else None
        floor = (
            floor_by_id.get(area.floor_id)
            if area and area.floor_id
            else None
        )
        entry = (
            entry_by_id[device.config_entries[0]]
            if device.config_entries
            and device.config_entries[0] in entry_by_id
            else None
        )
        domain = entry.domain if entry else None
        manifest = manifests.get(domain) if domain else None
        result.append(
            Device(
                id=device.id,
                name=device.name_by_user or device.name or "Unnamed device",
                area_name=area.name if area else "Unassigned",
                floor_name=floor.name if floor else "Unassigned",
                integration_name=(
                    manifest.name
                    if manifest
                    else domain or "Unknown"
                ),
            )
        )
    return result


async def get_devices() -> list[Device]:
    return await get_devices_with_location()
