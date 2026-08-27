import json
import os
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


def validate_device(
    device_id: str, area_id: str | None
) -> list[ValidatedDevice]:
    data = _load_data()
    if not any(v.device_id == device_id for v in data.validated_devices):
        data.validated_devices.append(
            ValidatedDevice(device_id=device_id, area_id=area_id)
        )
        _save_data(data)
    return data.validated_devices


def unvalidate_device(device_id: str) -> list[ValidatedDevice]:
    data = _load_data()
    remaining = [v for v in data.validated_devices if v.device_id != device_id]
    if len(remaining) != len(data.validated_devices):
        data.validated_devices = remaining
        _save_data(data)
    return data.validated_devices
