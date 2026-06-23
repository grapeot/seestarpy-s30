# CLAUDE.md — Onboarding for AI Assistants

## What is this project?

**seestarpy** is a Python SDK for controlling ZWO Seestar smart
telescopes over TCP (S50, S30 / S30 Pro, and related models).  The Seestar
exposes a JSON-RPC API on port 4700 and a binary image streaming protocol
on ports 4800/4804.  This library wraps both into a clean Python interface.

- **Repo**: https://github.com/grapeot/seestarpy-s30
- **Docs**: https://grapeot.github.io/seestarpy-s30/
- **Upstream**: https://github.com/astronomyk/seestarpy
- **Python**: >= 3.11, built with Hatchling
- **Original author**: Kieran Leschinski

## Repository layout

```
src/seestarpy/
  __init__.py          Imports all submodules
  connection.py        TCP socket, send_command(), DEFAULT_IP/PORT, mDNS discovery
  raw.py               59 low-level JSON-RPC wrappers (getters, setters, scope control)
  ui.py                High-level convenience functions (open, close, goto) with multi-IP support
  status.py            ASCII status dashboard (status_bar())
  plan.py              Observation plan commands (set_view_plan, stop, get status)
  stack.py             Batch stacking commands (set/start/stop/clear/status)
  stream.py            Binary image streaming (ports 4800/4804), matplotlib live display
  wide.py              S30 / S30 Pro dual-camera helpers (SecondView, wide_cam)
  postprocess.py       Bayer demosaic options for preview save/display
  data.py              SMB file operations (list/download FITS from Seestar storage)
  cli.py               Click-based CLI entry point (`seestar` command)
  coordintate_utils.py RA/Dec to Alt/Az conversion
  events/              Async event listener system (port 4700 persistent connection)
    event_listener.py  Background thread + asyncio, heartbeat, WebSocket broadcast
    event_definitions.py  Dataclasses for 20+ event types
    event_stream.py    Global LATEST_STATE dict, event routing
    event_watcher.py   Higher-level state transition watcher
  dashboards/          HTML dashboards for WebSocket event display
```

## Network architecture

The Seestar exposes five TCP ports:

| Port | Protocol | Purpose | Module |
|------|----------|---------|--------|
| 4700 | JSON-RPC (`\r\n` terminated) | Command & control | `connection.py`, `raw.py` |
| 4554 | RTSP (H.264) | Live video — telephoto | `stream.build_rtsp_url()` |
| 4555 | RTSP (H.264) | Live video — wide camera | `stream.build_rtsp_url()` |
| 4800 | Custom binary | Live stacked images — telephoto | `stream.py` |
| 4804 | Custom binary | Live stacked images — wide camera | `stream.py` |

### JSON-RPC (port 4700)

`connection.send_command()` opens a short-lived TCP socket, sends
`{"id":1, "method":"...", "params":{...}}\r\n`, reads a `\r\n`-terminated
JSON response, and closes.  `DEFAULT_IP` is auto-discovered via mDNS
(`seestar.local`).  `VERBOSE_LEVEL=1` prints send/receive to stdout.

### Binary image stream (ports 4800/4804)

Custom framing: 34-byte header (magic `0x03C3`, big-endian) + image payload.
Two payload formats exist:

- **Stacked frames** (img_type=5): ZIP-compressed 16-bit RGB (48bpp).
  Decompress by finding `PK\x03\x04`, parsing the ZIP local-file header,
  then `zlib.decompress(data, -15)`.
- **Preview frames** (img_type=1): Raw 16-bit Bayer, or ZIP-compressed Bayer/RGB on S30.
- **Ack frames** (img_type=0): Tiny keepalives, skip them.

The same socket carries both binary frames AND JSON-RPC heartbeat responses.
The reader syncs on the magic number and skips JSON lines starting with `{`.

## Key patterns

- **All functions in `raw.py`** call `send_command()` which uses the global
  `connection.DEFAULT_IP`.  Set it before calling anything.
- **`ui.py` functions** use the `@multiple_ips` decorator — pass `ips=` to
  broadcast to multiple Seestars.
- **`stream.py` functions** take `ip=None` which defaults to `DEFAULT_IP`.
- **`plan.py` and `stack.py`** also use `send_command()` via `DEFAULT_IP`.
- **Events** use a persistent async TCP connection in a background thread,
  not the fire-and-forget `send_command()`.

## Testing

```bash
pytest --ignore=tests/integration          # unit tests (CI runs this)
pytest -m integration                      # requires live Seestar
pytest -m sequence                         # multi-step observation sequences
```

Tests live in `tests/`.  Integration tests need a Seestar on the network and
are auto-skipped when none is reachable.

**CI:** GitHub Actions runs unit tests on every push/PR
(``.github/workflows/unit-tests.yml``).  Integration tests are excluded.

## Documentation

Sphinx with `sphinx_rtd_theme`.  Build locally:

```bash
pip install -e ".[docs,image]"
sphinx-build -b html docs docs/_build/html
```

Published to **GitHub Pages** on every push to `master`
(``.github/workflows/docs.yml`` → https://grapeot.github.io/seestarpy-s30/).

## Firmware protocol notes

These were reverse-engineered from the Seestar Android app v3.0.2
(decompiled with JADX) and confirmed via live traffic capture (PCAPdroid):

- **Observation plans**: The app stores plans in local SQLite.  Only
  `set_view_plan` is sent to firmware (with full target list).  Stop via
  `stop_func {"name":"ViewPlan"}`.  `get_view_plan` returns error 103.
- **Batch stacking**: `set_batch_stack_setting` → `start_batch_stack` →
  poll `iscope_get_app_state()["BatchStack"]` → `clear_app_state`.
- **Image streaming**: See `docs/info/image_stream_protocol.rst` for the
  full binary protocol spec.

## Development environment

- Package manager: `uv`
- Platform: Windows 11, bash shell
- The owner has 3 Seestar S50s on the local network:
  `seestar.local` (.246), `seestar-2.local` (.83), `seestar-3.local` (.84)

## Reference files (uncommitted)

These are in the working tree but not tracked in git:

- `decompiled_api_commands.txt` — Full list of firmware API commands
- `claude_found_the_plan_methods.md` — Plan API reference from decompiled app
- `seestar_alp_methods.md` — Telescope control method reference
- `.claude/captured_traffic_all.txt` — Full PCAPdroid traffic dump
