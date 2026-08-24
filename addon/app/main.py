"""Device Board -- aiohttp panel server for Home Assistant."""

import json
import logging
import os

from aiohttp import web

import ha_api

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
_LOGGER = logging.getLogger(__name__)


async def handle_index(request):
    ingress_path = request.headers.get("X-Ingress-Path", "").rstrip("/")
    with open("/app/index.html", "r") as f:
        html = f.read()
    return web.Response(text=html.replace("{{BASE}}", ingress_path), content_type="text/html")


async def handle_icon(request):
    return web.FileResponse("/app/icon.png")


def main():
    port = int(os.environ.get("INGRESS_PORT", "8099"))
    app = web.Application()
    app.router.add_get("/", handle_index)
    app.router.add_get("/icon.png", handle_icon)
    app.router.add_get("/{tail:.*}", handle_index)
    _LOGGER.info("Starting Device Board on port %d", port)
    web.run_app(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
