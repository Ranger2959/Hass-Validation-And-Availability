"""Device Board -- FastAPI panel server for Home Assistant."""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
import uvicorn
from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
import ha_api
import ha_data
import ha_monitor
import models

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
_LOGGER = logging.getLogger(__name__)

_INDEX_PATH = "/app/index.html"
_ICON_PATH = "/app/icon.png"

api_router = APIRouter(prefix="/api")

@api_router.get("/devices")
async def list_devices() -> list[models.Device]:
    try:
        return await ha_api.get_devices()
    except Exception as exc:
        _LOGGER.error("Failed to fetch devices from Home Assistant: %s", exc)
        raise HTTPException(status_code=502, detail=f"Home Assistant request failed: {exc}")


@api_router.post("/devices/{device_id}/save")
async def save_device(device_id: str, body: models.SaveDevice) -> dict:
    if body.update_area:
        try:
            await ha_api.update_device_area(device_id, body.area_id)
        except models.HomeAssistantError as exc:
            _LOGGER.error("Failed to update device area: %s", exc)
            raise HTTPException(status_code=502, detail=str(exc))
        except Exception as exc:
            _LOGGER.error("Failed to update device: %s", exc)
            raise HTTPException(
                status_code=502,
                detail=f"Home Assistant request failed: {exc}",
            )
    before = ha_data._load_data()
    prev_entity = next(
        (
            v.monitored_entity_id
            for v in before.validated_devices
            if v.device_id == device_id
        ),
        None,
    )
    ignored, validated_devices = ha_data.save_device_state(
        device_id,
        body.is_included,
        body.is_area_validated,
        body.area_id,
        body.monitored_entity_id,
    )
    ha_monitor.refresh()
    if body.monitored_entity_id and body.monitored_entity_id != prev_entity:
        await ha_monitor.check_entity(body.monitored_entity_id)
    return {
        "ignoredDevices": ignored,
        "validatedDevices": validated_devices,
    }


@api_router.get("/areas")
async def list_areas() -> list[models.HassArea]:
    try:
        return await ha_api.get_areas()
    except Exception as exc:
        _LOGGER.error("Failed to fetch areas from Home Assistant: %s", exc)
        raise HTTPException(status_code=502, detail=f"Home Assistant request failed: {exc}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(ha_monitor.monitor())
    _LOGGER.info("Selected-entity monitor started")
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


app = FastAPI(lifespan=lifespan)
app.include_router(api_router)

@app.get("/icon.png")
async def handle_icon() -> FileResponse:
    return FileResponse(_ICON_PATH)

@app.get("/{tail:path}")
@app.get("/")
async def _serve_index(request: Request):
    tail = request.path_params.get("tail", "")
    if tail:
        app_dir = os.path.realpath(os.path.dirname(_INDEX_PATH))
        static_path = os.path.realpath(os.path.join(app_dir, tail))
        if static_path.startswith(app_dir + os.sep) and os.path.isfile(static_path):
            return FileResponse(static_path)
    ingress_path = request.headers.get("X-Ingress-Path", "").rstrip("/")
    with open(_INDEX_PATH, "r") as f:
        html = f.read()
    return HTMLResponse(html.replace("{{BASE}}", ingress_path))

def main() -> None:
    port = int(os.environ.get("INGRESS_PORT", "8099"))
    _LOGGER.info("Starting Device Board on port %d", port)
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
