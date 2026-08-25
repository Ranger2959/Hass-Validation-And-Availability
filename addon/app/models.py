"""Home Assistant device registry models."""

from pydantic import BaseModel


class HomeAssistantError(Exception):
    """Raised when a Home Assistant WebSocket call fails."""


class HassDevice(BaseModel):
    id: str
    name: str | None = None
    name_by_user: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    model_id: str | None = None
    sw_version: str | None = None
    hw_version: str | None = None
    serial_number: str | None = None
    via_device_id: str | None = None
    area_id: str | None = None
    entry_type: str | None = None
    disabled_by: str | None = None
    configuration_url: str | None = None
    config_entries: list[str] = []
    identifiers: list[list[str]] = []
    connections: list[list[str]] = []
    labels: list[str] = []


class Device(BaseModel):
    id: str
    name: str
