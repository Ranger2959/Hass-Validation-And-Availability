import json
import os

from models import AppData

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


def ignore_device(device_id: str) -> list[str]:
    data = _load_data()
    if device_id not in data.ignored_devices:
        data.ignored_devices.append(device_id)
        _save_data(data)
    return data.ignored_devices


def unignore_device(device_id: str) -> list[str]:
    data = _load_data()
    if device_id in data.ignored_devices:
        data.ignored_devices.remove(device_id)
        _save_data(data)
    return data.ignored_devices
