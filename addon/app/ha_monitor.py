"""Background monitor for the state of each selected entity."""

import logging

import ha_api
import ha_data

_LOGGER = logging.getLogger(__name__)

_MONITORED: set[str] = set()

_BOARD_SENSOR = "sensor.device_board_unavailable_devices"
_UNAVAILABLE_STATES = ("unavailable", "unknown")
_PUBLISHED: list[str] | None = None


def refresh_monitored() -> set[str]:
    global _MONITORED
    data = ha_data._load_data()
    _MONITORED = {
        v.monitored_entity_id
        for v in data.validated_devices
        if v.monitored_entity_id
    }
    return _MONITORED


def _unavailable_devices(state_by_id: dict[str, str]) -> list[str]:
    return sorted(
        entity_id
        for entity_id in _MONITORED
        if state_by_id.get(entity_id) in _UNAVAILABLE_STATES
    )


async def _resolve_names(entity_ids: list[str]) -> list[str]:
    data = ha_data._load_data()
    device_by_entity = {
        v.monitored_entity_id: v.device_id
        for v in data.validated_devices
        if v.monitored_entity_id
    }
    name_by_device: dict[str, str] = {}
    try:
        devices = await ha_api.get_hass_devices()
    except Exception as exc:
        _LOGGER.error("Failed to load device registry: %s", exc)
        devices = []
    for device in devices:
        name_by_device[device.id] = (
            device.name_by_user or device.name or "Unnamed device"
        )
    return [
        name_by_device.get(device_by_entity.get(entity_id), entity_id)
        for entity_id in entity_ids
    ]


async def update_board_sensor(state_by_id: dict[str, str]) -> None:
    global _PUBLISHED
    unavailable = _unavailable_devices(state_by_id)
    if unavailable == _PUBLISHED:
        return
    names = await _resolve_names(unavailable)
    _LOGGER.info("%s = %d", _BOARD_SENSOR, len(unavailable))
    try:
        await ha_api.update_state(
            _BOARD_SENSOR,
            str(len(unavailable)),
            attributes={"unavailable_devices": ",".join(names)},
        )
    except Exception as exc:
        _LOGGER.error("Failed to update %s: %s", _BOARD_SENSOR, exc)
        return
    _PUBLISHED = unavailable


async def monitor() -> None:
    refresh_monitored()
    _LOGGER.info("Monitoring %d selected entities", len(_MONITORED))
    try:
        states = await ha_api.get_states()
    except Exception as exc:
        _LOGGER.error("Failed to fetch initial entity states: %s", exc)
        states = []
    state_by_id = {s.entity_id: s.state for s in states}
    await update_board_sensor(state_by_id)
    try:
        async for event in ha_api.subscribe_events("state_changed"):
            data = event.get("data", {})
            entity_id = data.get("entity_id")
            if entity_id not in _MONITORED:
                continue
            _LOGGER.info(event)
            new_state = data.get("new_state")
            if new_state:
                state_by_id[entity_id] = new_state.get("state")
            else:
                state_by_id.pop(entity_id, None)
            await update_board_sensor(state_by_id)
    except Exception as exc:
        _LOGGER.error("Entity monitor stopped: %s", exc)
