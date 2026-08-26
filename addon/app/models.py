"""Home Assistant registry models."""

from pydantic import BaseModel, ConfigDict, Field


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
    identifiers: list[list[str | int]] = []
    connections: list[list[str | int]] = []
    labels: list[str] = []


class Device(BaseModel):
    id: str
    name: str
    area_id: str | None = None
    area_name: str | None = None
    floor_name: str | None = None
    integration_name: str | None = None
    is_ignored: bool = False


class UpdateDeviceArea(BaseModel):
    area_id: str | None = None


class HassArea(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    area_id: str = Field(validation_alias="id", serialization_alias="area_id")
    name: str
    normalized_name: str | None = None
    floor_id: str | None = None
    icon: str | None = None
    picture: str | None = None
    aliases: list[str] = []
    labels: list[str] = []
    humidity_entity_id: str | None = None
    temperature_entity_id: str | None = None


class HassFloor(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    floor_id: str = Field(validation_alias="id", serialization_alias="floor_id")
    name: str
    icon: str | None = None
    level: int | None = None
    aliases: list[str] = []


class HassConfigEntry(BaseModel):
    entry_id: str
    domain: str
    title: str | None = None
    source: str | None = None
    state: str | None = None


class AppData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    ignored_devices: list[str] = Field(
        default_factory=list, alias="ignoredDevices"
    )


class HassManifest(BaseModel):
    domain: str
    name: str
    codeowners: list[str] = []
    documentation: str | None = None
    integration_type: str | None = None
    quality_scale: str | None = None
    is_built_in: bool = False
    overwrites_built_in: bool = False
