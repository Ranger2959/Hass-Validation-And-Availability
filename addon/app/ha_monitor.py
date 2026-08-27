"""Background monitor for the state of each selected entity."""

import logging

import ha_api
import ha_data

_LOGGER = logging.getLogger(__name__)

_MONITORED: set[str] = set()


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


def _log_if_bad(entity_id: str, state: str | None) -> None:
    if state in ("unavailable", "unknown"):
        _LOGGER.info("Selected entity %s is %s", entity_id, state)


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
