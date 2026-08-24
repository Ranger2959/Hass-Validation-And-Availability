# Device Board — Home Assistant Add-on

A Home Assistant add-on that adds a **Devices** panel to the sidebar. The panel shows a
table of every device in Home Assistant, with the device name and the floor/area it
belongs to.

## How it works

- Runs as a Docker add-on on the Home Assistant OS supervisor.
- `ingress` + `panel_title` in `addon/config.yaml` register the panel in the HA sidebar;
  the supervisor proxies the panel and the add-on's small HTTP API into the HA frontend.
- Reads the **device**, **area**, and **floor** registries through the Home Assistant
  **WebSocket API** (`config/device_registry/list`, `config/area_registry/list`,
  `config/floor_registry/list`) — the same mechanism the HA frontend and the
  [battery-sentinel](https://github.com/smcneece/battery-sentinel) example add-on use.

> **Note on the REST API:** Home Assistant's
> [REST API docs](https://developers.home-assistant.io/docs/api/rest) do not expose the
> device/area/floor registries (there are no `/api/devices`, `/api/areas`, or
> `/api/floors` endpoints — the registries are only available over the WebSocket API).
> That is why this add-on reads the data over WebSocket instead.

No token or options are needed when installed as an add-on: the supervisor
authenticates the connection to HA on your behalf (`homeassistant_api: true`).

## Installation

1. Push this repository to GitHub, e.g.
   `https://github.com/<you>/Hass-Validation-And-Availability`.
2. Update the `url` field in `repository.yaml` and `addon/config.yaml` to match your
   GitHub URL (and `maintainer` if needed).
3. In Home Assistant go to **Settings → Add-ons → Add-on store**, open the three-dot
   menu and choose **Add add-on repository**, then paste your repository URL.
4. Open the **Device Board** store entry, click **Install**, then **Start**.
5. A **Devices** entry appears in the sidebar — open it to see your device table.

## Running outside Home Assistant OS (plain Docker)

The same app works standalone against any HA instance:

```bash
docker build -t device-board ./addon
docker run --rm -p 8099:8099 \
  -e HA_BASE_URL=http://192.168.1.64:8123 \
  -e HA_TOKEN=<long-lived access token> \
  device-board
```

Then open http://localhost:8099 in a browser.
(Create a token under *Profile → Security → Long-lived access tokens* in HA.)

## Project layout

```
repository.yaml          add-on store manifest
README.md
addon/
  config.yaml            add-on manifest (panel, ingress, architecture)
  Dockerfile             builds the add-on image (base-python + aiohttp)
  run.sh                 entrypoint (with-contenv bashio)
  icon.png               add-on store icon
  app/
    main.py              aiohttp server: serves the panel + /api/devices
    ha_api.py            WebSocket calls to the device/area/floor registries
    ha_config.py         connection mode + auth token resolution
    index.html           the sidebar panel UI
```
