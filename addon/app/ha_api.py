"""Home Assistant device registry client over the WebSocket API."""

import json
import logging
from typing import Any

import websockets

import ha_config
from models import Device, HassDevice, HomeAssistantError

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


async def get_devices() -> list[Device]:
    hass_devices = await get_hass_devices()
    return [
        Device(id=d.id, name=d.name_by_user or d.name or "Unnamed device")
        for d in hass_devices
    ]
