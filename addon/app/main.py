"""Device Board -- aiohttp panel server for Home Assistant."""

import json
import logging
import os

from aiohttp import web

import ha_api

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
_LOGGER = logging.getLogger(__name__)

VERSION = "1.0.0"


async def handle_index(request):
    """Serve the panel UI. When proxied through the supervisor the request
    carries an X-Ingress-Path header (e.g. /hassio/addons/device_board)
    which the frontend uses as the base URL for its API calls."""
    ingress_path = request.headers.get("X-Ingress-Path", "").rstrip("/")
    with open("/app/index.html", "r") as f:
        html = f.read()
    return web.Response(text=html.replace("{{BASE}}", ingress_path), content_type="text/html")


async def handle_icon(request):
    return web.FileResponse("/app/icon.png")


async def handle_api_devices(request):
    try:
        rows = await ha_api.get_device_board()
    except Exception as exc:
        _LOGGER.exception("Failed to fetch device board from Home Assistant")
        return web.Response(
            status=502,
            text=json.dumps(
                {
                    "error": "Could not load devices from Home Assistant: "
                    + str(exc)[:300]
                }
            ),
            content_type="application/json",
        )
    return web.Response(
        text=json.dumps({"devices": rows, "count": len(rows)}),
        content_type="application/json",
    )


async def handle_api_verify(request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    if not isinstance(body, dict):
        body = {}
    device_id = str(body.get("id") or "")
    if not device_id:
        return web.Response(
            status=400,
            text=json.dumps({"error": "Expected JSON body with id, floor and area"}),
            content_type="application/json",
        )
    verified = ha_api.load_verified()
    entry = verified.get(device_id) or {}
    for key in ("floor", "area", "entity"):
        if key in body:
            entry[key] = str(body.get(key) or "")
    verified[device_id] = entry
    try:
        ha_api.save_verified(verified)
    except OSError as exc:
        return web.Response(
            status=500,
            text=json.dumps({"error": "Could not save verification: " + str(exc)[:300]}),
            content_type="application/json",
        )
    return web.Response(text=json.dumps({"ok": True}), content_type="application/json")


def main():
    port = int(os.environ.get("INGRESS_PORT", "8099"))
    app = web.Application()
    app.router.add_get("/", handle_index)
    app.router.add_get("/icon.png", handle_icon)
    app.router.add_get("/api/devices", handle_api_devices)
    app.router.add_post("/api/devices/verify", handle_api_verify)
    app.router.add_get("/{tail:.*}", handle_index)
    _LOGGER.info("Starting Device Board v%s on port %d", VERSION, port)
    web.run_app(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
