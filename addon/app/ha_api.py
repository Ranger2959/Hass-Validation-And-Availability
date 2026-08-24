"""HA data fetchers -- WebSocket access to the device/area/floor registries.

Home Assistant does not expose its registries through the REST API (there are
no /api/devices, /api/areas or /api/floors endpoints), so we use the WebSocket
API (config/*_registry/list) -- the same mechanism the HA frontend uses.
"""

import asyncio
import logging

import aiohttp

from ha_config import _HA_WS_URL, _token

_LOGGER = logging.getLogger(__name__)


async def _ws_call(command: str):
    """Open one WebSocket connection, authenticate, and run a single command."""
    token = _token()
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(_HA_WS_URL, heartbeat=30) as ws:
            msg = await ws.receive_json()
            if msg.get("type") != "auth_required":
                raise RuntimeError(f"Unexpected first WebSocket message: {msg}")
            await ws.send_json({"type": "auth", "access_token": token})
            msg = await ws.receive_json()
            if msg.get("type") != "auth_ok":
                raise RuntimeError(f"WebSocket authentication failed: {msg}")
            await ws.send_json({"id": 1, "type": command})
            while True:
                msg = await ws.receive_json()
                if msg.get("id") != 1:
                    continue  # ignore events / pongs
                if msg.get("type") == "result":
                    return msg.get("result")
                raise RuntimeError(f"Home Assistant error: {msg.get('message')}")


async def get_device_board() -> list[dict]:
    """Fetch all devices joined with their area and floor."""
    devices, areas, floors = await asyncio.gather(
        _ws_call("config/device_registry/list"),
        _ws_call("config/area_registry/list"),
        _ws_call("config/floor_registry/list"),
    )

    areas_by_id = {a["id"]: a for a in areas}
    floors_by_id = {f["id"]: f for f in floors}

    rows = []
    for dev in devices:
        area = areas_by_id.get(dev.get("area_id") or "")
        floor = None
        if area is not None and area.get("floor_id"):
            floor = floors_by_id.get(area["floor_id"])

        name = dev.get("name_by_user") or dev.get("name") or "Unnamed device"
        floor_name = floor["name"] if floor else ""
        area_name = area["name"] if area else ""
        location = " / ".join(part for part in (floor_name, area_name) if part)

        rows.append(
            {
                "id": dev["id"],
                "name": name,
                "manufacturer": dev.get("manufacturer") or "",
                "model": dev.get("model") or "",
                "floor": floor_name,
                "area": area_name,
                "location": location,
            }
        )

    rows.sort(key=lambda r: (r["floor"] or "~", r["area"] or "~", r["name"].lower()))
    _LOGGER.info(
        "Fetched %d devices, %d areas, %d floors",
        len(devices),
        len(areas),
        len(floors),
    )
    return rows
