import json
import logging

from models import AppData, ValidatedDevice

_LOGGER = logging.getLogger(__name__)

DATA_PATH = "/data/data.json"


def _load_data() -> AppData:
    try:
        with open(DATA_PATH, "r") as f:
            raw = json.load(f)
            _LOGGER.info(raw)
    except (OSError, ValueError):
        raw = {}
    return AppData.model_validate(raw)


def _save_data(data: AppData) -> None:
    with open(DATA_PATH, "w") as f:
        json.dump(data.model_dump(by_alias=True), f, indent=4)


def save_device_state(
    device_id: str,
    included: bool,
    validated: bool,
    area_id: str | None,
    entity_id: str | None,
) -> tuple[list[str], list[ValidatedDevice]]:
    data = _load_data()
    changed = False
    if device_id in data.ignored_devices and included:
        data.ignored_devices.remove(device_id)
        changed = True
    elif device_id not in data.ignored_devices and not included:
        data.ignored_devices.append(device_id)
        changed = True
    existing = next(
        (v for v in data.validated_devices if v.device_id == device_id),
        None,
    )
    if existing is None and validated:
        data.validated_devices.append(
            ValidatedDevice(
                device_id=device_id, area_id=area_id, entity_id=entity_id
            )
        )
        changed = True
    elif existing is not None and not validated:
        data.validated_devices = [
            v for v in data.validated_devices if v.device_id != device_id
        ]
        changed = True
    elif existing is not None and (
        existing.area_id != area_id or existing.entity_id != entity_id
    ):
        existing.area_id = area_id
        existing.entity_id = entity_id
        changed = True
    if changed:
        _save_data(data)
    return data.ignored_devices, data.validated_devices
