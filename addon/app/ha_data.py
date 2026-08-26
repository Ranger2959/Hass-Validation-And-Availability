import json
import os

from models import AppData

DATA_DIR = os.environ.get("SUPERVISOR_CONFIG_DIR", "/config")
DATA_PATH = os.path.join(DATA_DIR, "data.json")


def _load_data() -> AppData:
    try:
        with open(DATA_PATH, "r") as f:
            raw = json.load(f)
    except (OSError, ValueError):
        raw = {}
    return AppData.model_validate(raw)


def _save_data(data: AppData) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
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
