from __future__ import annotations

import asyncio
import hmac
import json
import os
import re
import secrets
import time
from datetime import datetime, timezone
from typing import Any

from mcp.server import MCPServer
from pydantic import BaseModel, Field, ValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse

SERVICE_VERSION = "0.3.0"
BRIDGE_TOKEN = os.environ.get("BRIDGE_RECEIPT_TOKEN", "")
MCP_ACCESS_TOKEN = os.environ.get("MCP_ACCESS_TOKEN", "")
REQUEST_RE = re.compile(r"^[A-Za-z0-9_-]{8,128}$")
PROTOCOL = "laylay-bridge-command-v1"
ACTIONS = {
    "ping",
    "system_info",
    "list_files",
    "read_text",
    "write_text",
    "run_readonly",
}
commands: dict[str, dict[str, Any]] = {}
receipts: dict[str, dict[str, Any]] = {}
devices_seen: dict[str, dict[str, Any]] = {}


class Receipt(BaseModel):
    device: str
    action: str
    executed: bool
    confirmed: bool | None = None
    data: dict[str, Any] = Field(default_factory=dict)


class Command(BaseModel):
    protocol: str = PROTOCOL
    request_id: str
    device: str = "*"
    action: str
    args: dict[str, Any] = Field(default_factory=dict)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _trim(mapping: dict[str, Any], limit: int = 500) -> None:
    while len(mapping) > limit:
        mapping.pop(next(iter(mapping)))
def _bridge_authorized(request: Request) -> bool:
    supplied = request.headers.get("x-bridge-token", "")
    return bool(BRIDGE_TOKEN) and hmac.compare_digest(supplied, BRIDGE_TOKEN)


def _queue_payload(command: Command) -> tuple[dict[str, Any], bool]:
    if command.protocol != PROTOCOL:
        raise ValueError("invalid protocol")
    if not REQUEST_RE.fullmatch(command.request_id):
        raise ValueError("invalid request_id")
    if command.action not in ACTIONS:
        raise ValueError("invalid action")

    payload = command.model_dump()
    existing = commands.get(command.request_id)
    if existing is not None:
        comparable = dict(existing)
        comparable.pop("queued_at", None)
        if comparable != payload:
            raise RuntimeError("request_id already queued")
        return existing, True
    payload["queued_at"] = _utcnow()
    commands[command.request_id] = payload
    _trim(commands)
    return payload, False
async def _send_and_wait(
    device: str,
    action: str,
    args: dict[str, Any] | None = None,
    timeout_seconds: float = 20.0,
) -> dict[str, Any]:
    device = str(device or "").strip()
    if not device:
        raise ValueError("device is required")
    if action not in ACTIONS:
        raise ValueError(f"unsupported action: {action}")

    request_id = "mcp_" + secrets.token_hex(12)
    command = Command(
        request_id=request_id,
        device=device,
        action=action,
        args=dict(args or {}),
    )
    _queue_payload(command)
    deadline = time.monotonic() + max(2.0, min(float(timeout_seconds), 60.0))

    while time.monotonic() < deadline:
        result = receipts.get(request_id)
        if result is not None:
            return result
        await asyncio.sleep(0.25)
    commands.pop(request_id, None)
    return {
        "device": device,
        "action": action,
        "executed": False,
        "confirmed": False,
        "request_id": request_id,
        "data": {
            "error_type": "TimeoutError",
            "error": f"No receipt within {timeout_seconds:.1f}s",
        },
    }


mcp = MCPServer(
    "Laylay Bridge Relay",
    version=SERVICE_VERSION,
    instructions=(
        "Remote bridge for authorized Windows development devices. "
        "Use bridge_devices first, then target a specific device. "
        "File operations remain confined to each device workspace."
    ),
)


@mcp.tool()
def bridge_devices() -> dict[str, Any]:
    """List devices that have polled the relay and their recent online state."""
    now = time.time()
    items: list[dict[str, Any]] = []
    for name, info in sorted(devices_seen.items()):
        age = max(0.0, now - float(info["seen_epoch"]))
        items.append(
            {
                "device": name,
                "last_seen": info["last_seen"],
                "seconds_ago": round(age, 1),
                "online": age <= 15.0,
            }
        )
    return {"devices": items, "relay_version": SERVICE_VERSION}


@mcp.tool()
async def bridge_ping(device: str) -> dict[str, Any]:
    """Ping one authorized Laylay Dev Bridge device."""
    return await _send_and_wait(device, "ping")


@mcp.tool()
async def bridge_system_info(device: str) -> dict[str, Any]:
    """Return basic OS, Python and workspace information from a device."""
    return await _send_and_wait(device, "system_info")


@mcp.tool()
async def bridge_list_files(device: str, path: str = ".") -> dict[str, Any]:
    """List files inside the authorized workspace on a device."""
    return await _send_and_wait(device, "list_files", {"path": path})
@mcp.tool()
async def bridge_read_text(
    device: str,
    path: str,
    max_chars: int = 20000,
) -> dict[str, Any]:
    """Read a UTF-8 text file inside the authorized workspace."""
    return await _send_and_wait(
        device,
        "read_text",
        {"path": path, "max_chars": max_chars},
    )


@mcp.tool()
async def bridge_write_text(
    device: str,
    path: str,
    content: str,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Create or replace a UTF-8 file inside the authorized workspace."""
    return await _send_and_wait(
        device,
        "write_text",
        {"path": path, "content": content, "overwrite": overwrite},
    )


@mcp.tool()
async def bridge_run_readonly(
    device: str,
    command: str,
    cwd: str = ".",
) -> dict[str, Any]:
    """Run one predefined read-only command inside the workspace."""
    return await _send_and_wait(
        device,
        "run_readonly",
        {"command": command, "cwd": cwd},
    )


@mcp.custom_route("/", methods=["GET"])
async def root(_: Request) -> JSONResponse:
    return JSONResponse(
        {"service": "laylay-bridge-relay", "version": SERVICE_VERSION}
    )


@mcp.custom_route("/health", methods=["GET"])
async def health(_: Request) -> JSONResponse:
    online = sum(
        1
        for info in devices_seen.values()
        if time.time() - float(info["seen_epoch"]) <= 15.0
    )
    return JSONResponse(
        {
            "ok": True,
            "version": SERVICE_VERSION,
            "stored_receipts": len(receipts),
            "pending_commands": len(commands),
            "seen_devices": len(devices_seen),
            "online_devices": online,
            "mcp_configured": bool(MCP_ACCESS_TOKEN),
        }
    )
@mcp.custom_route("/command", methods=["POST"])
async def post_command(request: Request) -> JSONResponse:
    if not _bridge_authorized(request):
        return JSONResponse({"detail": "invalid bridge token"}, status_code=401)
    try:
        command = Command.model_validate(await request.json())
        _, existing = _queue_payload(command)
    except ValidationError as exc:
        return JSONResponse({"detail": str(exc)}, status_code=422)
    except ValueError as exc:
        return JSONResponse({"detail": str(exc)}, status_code=400)
    except RuntimeError as exc:
        return JSONResponse({"detail": str(exc)}, status_code=409)

    if command.request_id in receipts:
        return JSONResponse(
            {"queued": False, "completed": True, "request_id": command.request_id}
        )
    return JSONResponse(
        {
            "queued": True,
            "existing": existing,
            "request_id": command.request_id,
        }
    )
@mcp.custom_route("/command/next", methods=["GET"])
async def next_command(request: Request) -> JSONResponse:
    if not _bridge_authorized(request):
        return JSONResponse({"detail": "invalid bridge token"}, status_code=401)
    device = str(request.query_params.get("device") or "").strip()
    if not device or len(device) > 128:
        return JSONResponse({"detail": "invalid device"}, status_code=400)

    now = time.time()
    devices_seen[device] = {
        "last_seen": _utcnow(),
        "seen_epoch": now,
    }
    _trim(devices_seen, 100)

    for payload in commands.values():
        target = str(payload.get("device") or "*")
        if target in {"*", device}:
            return JSONResponse({"command": payload})
    return JSONResponse({"command": None})


@mcp.custom_route("/devices", methods=["GET"])
async def devices_route(request: Request) -> JSONResponse:
    if not _bridge_authorized(request):
        return JSONResponse({"detail": "invalid bridge token"}, status_code=401)
    return JSONResponse(bridge_devices())


@mcp.custom_route("/receipt/{request_id}", methods=["GET", "POST"])
async def receipt_route(request: Request) -> JSONResponse:
    if not _bridge_authorized(request):
        return JSONResponse({"detail": "invalid bridge token"}, status_code=401)
    request_id = str(request.path_params.get("request_id") or "")
    if not REQUEST_RE.fullmatch(request_id):
        return JSONResponse({"detail": "invalid request_id"}, status_code=400)

    if request.method == "GET":
        payload = receipts.get(request_id)
        if payload is None:
            return JSONResponse({"detail": "receipt not found"}, status_code=404)
        return JSONResponse(payload)

    try:
        receipt = Receipt.model_validate(await request.json())
    except ValidationError as exc:
        return JSONResponse({"detail": str(exc)}, status_code=422)
    payload = receipt.model_dump()
    payload["request_id"] = request_id
    payload["received_at"] = _utcnow()
    receipts[request_id] = payload
    commands.pop(request_id, None)
    _trim(receipts)
    print(
        "BRIDGE_RECEIPT "
        + json.dumps(payload, ensure_ascii=False, sort_keys=True),
        flush=True,
    )
    return JSONResponse({"stored": True, "request_id": request_id})


class MCPBearerMiddleware:
    def __init__(self, inner_app: Any):
        self.inner_app = inner_app

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope.get("type") == "http" and str(scope.get("path") or "").startswith("/mcp"):
            headers = {
                key.lower(): value
                for key, value in scope.get("headers", [])
            }
            supplied = headers.get(b"authorization", b"").decode(
                "latin-1",
                errors="replace",
            )
            if not MCP_ACCESS_TOKEN:
                response = JSONResponse(
                    {"detail": "mcp access token is not configured"},
                    status_code=503,
                )
                await response(scope, receive, send)
                return
            expected = "Bearer " + MCP_ACCESS_TOKEN
            if not hmac.compare_digest(supplied, expected):
                response = JSONResponse(
                    {"detail": "unauthorized"},
                    status_code=401,
                    headers={"WWW-Authenticate": "Bearer"},
                )
                await response(scope, receive, send)
                return
        await self.inner_app(scope, receive, send)


_inner_app = mcp.streamable_http_app(
    streamable_http_path="/mcp",
    json_response=True,
    stateless_http=True,
    host="0.0.0.0",
)
app = MCPBearerMiddleware(_inner_app)