"""HA data fetchers -- WebSocket access to the device/area/floor registries and the entity registry.

Home Assistant does not expose its registries through the REST API (there are
no /api/devices, /api/areas or /api/floors endpoints), so we use the WebSocket
API (config/*_registry/list) -- the same mechanism the HA frontend uses.
"""

import asyncio
import json
import logging
import os

import aiohttp

from ha_config import _HA_STATES_URL, _HA_WS_URL, _token

_LOGGER = logging.getLogger(__name__)


def _short(value, limit: int = 300) -> str:
    """Return a compact, bounded repr for logging diagnostics."""
    text = repr(value)
    return text if len(text) <= limit else text[:limit] + "…"


def _entries(value, label: str, *id_keys: str) -> list[dict]:
    """Normalize a registry 'list' result into a list of dict entries.

    Recent Home Assistant versions key registry entries by their
    type-specific id field (e.g. area_id, floor_id) instead of a plain
    "id" key; older versions use "id". The candidate keys are tried in
    order and the resolved id is stored under "id" so callers can rely
    on a single key. Unexpected shapes degrade to an empty/partial list
    with a diagnostic log line instead of crashing the whole panel.
    """
    if value is None:
        _LOGGER.warning("%s registry returned a null result", label)
        return []
    if not isinstance(value, list):
        _LOGGER.warning(
            "%s registry returned %s (expected a list): %s",
            label,
            type(value).__name__,
            _short(value),
        )
        return []
    entries = []
    for entry in value:
        if not isinstance(entry, dict):
            if entry is not None:
                _LOGGER.warning(
                    "%s registry entry is not an object, skipping: %s",
                    label,
                    _short(entry),
                )
            continue
        entry_id = None
        for key in id_keys:
            if entry.get(key):
                entry_id = entry[key]
                break
        if entry_id:
            entry.setdefault("id", entry_id)
            entries.append(entry)
        else:
            _LOGGER.warning(
                "%s registry entry has no id (%s), skipping: %s",
                label,
                ", ".join(id_keys),
                _short(entry),
            )
    return entries


async def _ws_call(command: str):
    """Open one WebSocket connection, authenticate, and run a single command."""
    token = _token()
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(_HA_WS_URL, heartbeat=30) as ws:
            msg = await ws.receive_json()
            if msg.get("type") != "auth_required":
                raise RuntimeError(
                    f"Unexpected first WebSocket message: {_short(msg)}"
                )
            await ws.send_json({"type": "auth", "access_token": token})
            msg = await ws.receive_json()
            if msg.get("type") != "auth_ok":
                raise RuntimeError(
                    f"WebSocket authentication failed: {_short(msg)}"
                )
            await ws.send_json({"id": 1, "type": command})
            while True:
                msg = await ws.receive_json()
                if msg.get("id") != 1:
                    continue  # ignore events / pongs
                if msg.get("type") == "result":
                    return msg.get("result")
                raise RuntimeError(
                    f"Home Assistant error: {msg.get('message')} ({msg.get('code')})"
                )


async def _rest_states() -> list[dict]:
    """Fetch all states via REST to resolve entity friendly names."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                _HA_STATES_URL,
                headers={"Authorization": f"Bearer {_token()}"},
            ) as resp:
                if resp.status != 200:
                    body = (await resp.text())[:200]
                    _LOGGER.warning(
                        "States request failed with HTTP %d: %s",
                        resp.status,
                        body,
                    )
                    return []
                data = await resp.json()
        return data if isinstance(data, list) else []
    except Exception as exc:
        _LOGGER.warning("Could not fetch states for entity names: %s", exc)
        return []


VERIFIED_PATH = "/data/verified.json"


def load_verified() -> dict[str, dict[str, str]]:
    """Load saved device_id -> {"floor": ..., "area": ...} verification data."""
    try:
        with open(VERIFIED_PATH, "r") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_verified(verified: dict[str, dict[str, str]]) -> None:
    os.makedirs(os.path.dirname(VERIFIED_PATH), exist_ok=True)
    tmp = VERIFIED_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(verified, f, indent=2)
    os.replace(tmp, VERIFIED_PATH)


async def get_device_board() -> list[dict]:
    """Fetch all devices joined with their area and floor."""
    raw_devices, raw_areas, raw_floors, raw_entity_reg, states = await asyncio.gather(
        _ws_call("config/device_registry/list"),
        _ws_call("config/area_registry/list"),
        _ws_call("config/floor_registry/list"),
        _ws_call("config/entity_registry/list"),
        _rest_states(),
    )
    devices = _entries(raw_devices, "device", "id", "device_id")

    areas = _entries(raw_areas, "area", "area_id", "id")
    floors = _entries(raw_floors, "floor", "floor_id", "id")

    areas_by_id = {a["id"]: a for a in areas}
    floors_by_id = {f["id"]: f for f in floors}

    entity_reg = _entries(raw_entity_reg, "entity", "entity_id", "id")
    entities_by_device: dict[str, list[str]] = {}
    for ent in entity_reg:
        dev_id = ent.get("device_id")
        if dev_id:
            entities_by_device.setdefault(dev_id, []).append(ent["id"])
    _LOGGER.info(states);
    friendly_names: dict[str, str] = {}
    for st in states:
        eid = st.get("entity_id")
        if eid:
            friendly_names[eid] = (st.get("attributes") or {}).get("friendly_name") or eid

    verified = load_verified()

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
        saved = verified.get(dev["id"]) or {}


        rows.append(
            {
                "id": dev["id"],
                "name": name,
                "manufacturer": dev.get("manufacturer") or "",
                "model": dev.get("model") or "",
                "floor": floor_name,
                "area": area_name,
                "location": location,
                "verified_floor": saved.get("floor"),
                "verified_area": saved.get("area"),
                "entities": [
                    {"id": eid, "name": friendly_names.get(eid, eid)}
                    for eid in entities_by_device.get(dev["id"]) or []
                ],
                "verified_entity": saved.get("entity"),
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