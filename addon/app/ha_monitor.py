"""Background monitor for the state of each selected entity."""

import logging

import ha_api
import ha_data

_LOGGER = logging.getLogger(__name__)

_MONITORED: set[str] = set()

_BOARD_SENSOR = "sensor.device_board_unavailable_devices"
_UNAVAILABLE_STATES = ("unavailable", "unknown")


def _refresh_monitored() -> set[str]:
    global _MONITORED
    data = ha_data._load_data()
    _MONITORED = {
        v.monitored_entity_id
        for v in data.validated_devices
        if v.monitored_entity_id
    }
    return _MONITORED


def refresh() -> None:
    _refresh_monitored()


async def check_entity(entity_id: str) -> None:
    try:
        states = await ha_api.get_states()
    except Exception as exc:
        _LOGGER.error("Failed to fetch entity states: %s", exc)
        return
    state = next(
        (s.state for s in states if s.entity_id == entity_id),
        None,
    )
    _log_if_bad(entity_id, state)


def _log_if_bad(entity_id: str, state: str | None) -> None:
    if state in _UNAVAILABLE_STATES:
        _LOGGER.info("Selected entity %s is %s", entity_id, state)


def _unavailable_count(state_by_id: dict[str, str]) -> int:
    return sum(
        1
        for entity_id in _MONITORED
        if state_by_id.get(entity_id) in _UNAVAILABLE_STATES
    )


async def update_board_sensor(state_by_id: dict[str, str]) -> None:
    count = _unavailable_count(state_by_id)
    _LOGGER.info("%s = %d", _BOARD_SENSOR, count)
    try:
        await ha_api.update_state(_BOARD_SENSOR, str(count))
    except Exception as exc:
        _LOGGER.error("Failed to update %s: %s", _BOARD_SENSOR, exc)


async def monitor() -> None:
    _refresh_monitored()
    _LOGGER.info("Monitoring %d selected entities", len(_MONITORED))
    try:
        states = await ha_api.get_states()
    except Exception as exc:
        _LOGGER.error("Failed to fetch initial entity states: %s", exc)
        states = []
    state_by_id = {s.entity_id: s.state for s in states}
    for entity_id in _MONITORED:
        _log_if_bad(entity_id, state_by_id.get(entity_id))
    await update_board_sensor(state_by_id)
    try:
        async for event in ha_api.subscribe_events("state_changed"):
            entity_id = event.get("entity_id")
            if entity_id not in _MONITORED:
                continue
            new_state = event.get("new_state")
            _log_if_bad(
                entity_id,
                new_state.get("state") if new_state else None,
            )
    except Exception as exc:
        _LOGGER.error("Entity monitor stopped: %s", exc)
