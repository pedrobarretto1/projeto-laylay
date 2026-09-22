from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey, X25519PublicKey,
)
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from mcp.server import MCPServer
from pydantic import BaseModel, Field, ValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse

SERVICE_VERSION = "0.5.2"
BRIDGE_TOKEN = os.environ.get("BRIDGE_RECEIPT_TOKEN", "")
MCP_ACCESS_TOKEN = os.environ.get("MCP_ACCESS_TOKEN", "")
GITHUB_COMMAND_REPO = os.environ.get(
    "GITHUB_COMMAND_REPO", "pedrobarretto1/projeto-laylay"
)
GITHUB_COMMAND_AUTHOR = os.environ.get(
    "GITHUB_COMMAND_AUTHOR", "pedrobarretto1"
)
ENCRYPTED_PROTOCOL = "laylay-bridge-encrypted-v1"
ISSUE_TITLE_PREFIX = "[LAYLAY-BRIDGE-ENC]"
ISSUE_MAX_AGE_SECONDS = 600
REQUEST_RE = re.compile(r"^[A-Za-z0-9_-]{8,128}$")
PROTOCOL = "laylay-bridge-command-v1"
ACTIONS = {
    "ping",
    "system_info",
    "access_info",
    "list_files",
    "find_files",
    "search_text",
    "stat_path",
    "read_text",
    "read_text_range",
    "write_text",
    "patch_text",
    "create_directory",
    "move_path",
    "delete_file",
    "check_python_syntax",
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

def _b64u_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64u_decode(value: str) -> bytes:
    raw = str(value or "").encode("ascii")
    raw += b"=" * (-len(raw) % 4)
    return base64.urlsafe_b64decode(raw)


def _command_private_key() -> X25519PrivateKey:
    if not BRIDGE_TOKEN:
        raise RuntimeError("BRIDGE_RECEIPT_TOKEN is not configured")
    seed = hashlib.sha256(
        b"laylay-github-command-private-v1\x00"
        + BRIDGE_TOKEN.encode("utf-8")
    ).digest()
    return X25519PrivateKey.from_private_bytes(seed)


def _command_public_key_b64() -> str:
    raw = _command_private_key().public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return _b64u_encode(raw)


def _decrypt_envelope(envelope: dict[str, Any]) -> Command:
    if envelope.get("protocol") != ENCRYPTED_PROTOCOL:
        raise ValueError("invalid encrypted protocol")
    request_id = str(envelope.get("request_id") or "")
    if not REQUEST_RE.fullmatch(request_id):
        raise ValueError("invalid request_id")

    ephemeral_raw = _b64u_decode(str(envelope.get("ephemeral_public_key") or ""))
    nonce = _b64u_decode(str(envelope.get("nonce") or ""))
    ciphertext = _b64u_decode(str(envelope.get("ciphertext") or ""))
    if len(ephemeral_raw) != 32:
        raise ValueError("invalid ephemeral public key")
    if len(nonce) != 12:
        raise ValueError("invalid nonce")
    if not ciphertext or len(ciphertext) > 131072:
        raise ValueError("invalid ciphertext size")

    shared = _command_private_key().exchange(
        X25519PublicKey.from_public_bytes(ephemeral_raw)
    )
    key = HKDF(
        algorithm=SHA256(),
        length=32,
        salt=None,
        info=b"laylay-github-command-v1\x00" + request_id.encode("ascii"),
    ).derive(shared)
    plaintext = AESGCM(key).decrypt(
        nonce,
        ciphertext,
        request_id.encode("ascii"),
    )
    decoded = json.loads(plaintext.decode("utf-8"))
    if not isinstance(decoded, dict):
        raise ValueError("decrypted payload must be an object")
    command = Command.model_validate(decoded)
    if command.request_id != request_id:
        raise ValueError("request_id mismatch")
    return command


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
    if command.request_id in receipts:
        return {
            "request_id": command.request_id,
            "completed": True,
        }, True
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
async def bridge_access_info(device: str) -> dict[str, Any]:
    """Return the active file access policy for a device."""
    return await _send_and_wait(device, "access_info", {})


@mcp.tool()
async def bridge_list_files(device: str, path: str = ".") -> dict[str, Any]:
    """List files inside the authorized workspace on a device."""
    return await _send_and_wait(device, "list_files", {"path": path})


@mcp.tool()
async def bridge_find_files(
    device: str,
    pattern: str,
    path: str = ".",
    max_results: int = 100,
) -> dict[str, Any]:
    """Find files recursively inside the authorized workspace."""
    return await _send_and_wait(
        device,
        "find_files",
        {"pattern": pattern, "path": path, "max_results": max_results},
    )


@mcp.tool()
async def bridge_search_text(
    device: str,
    query: str,
    path: str = ".",
    file_glob: str = "*.py",
    max_results: int = 100,
    case_sensitive: bool = False,
) -> dict[str, Any]:
    """Search text recursively inside the authorized workspace."""
    return await _send_and_wait(
        device,
        "search_text",
        {
            "query": query,
            "path": path,
            "file_glob": file_glob,
            "max_results": max_results,
            "case_sensitive": case_sensitive,
        },
    )


@mcp.tool()
async def bridge_stat_path(device: str, path: str = ".") -> dict[str, Any]:
    """Return metadata and SHA-256 for a path inside the workspace."""
    return await _send_and_wait(device, "stat_path", {"path": path})


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
async def bridge_read_text_range(
    device: str,
    path: str,
    start_line: int = 1,
    max_lines: int = 200,
) -> dict[str, Any]:
    """Read a line range from a UTF-8 text file inside the workspace."""
    return await _send_and_wait(
        device,
        "read_text_range",
        {"path": path, "start_line": start_line, "max_lines": max_lines},
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
async def bridge_patch_text(
    device: str,
    path: str,
    old_string: str,
    new_string: str,
    expected_replacements: int = 1,
    expected_sha256: str = "",
) -> dict[str, Any]:
    """Apply a guarded text replacement inside the authorized workspace."""
    return await _send_and_wait(
        device,
        "patch_text",
        {
            "path": path,
            "old_string": old_string,
            "new_string": new_string,
            "expected_replacements": expected_replacements,
            "expected_sha256": expected_sha256,
        },
    )


@mcp.tool()
async def bridge_create_directory(device: str, path: str) -> dict[str, Any]:
    """Create a directory inside the authorized workspace."""
    return await _send_and_wait(device, "create_directory", {"path": path})


@mcp.tool()
async def bridge_move_path(
    device: str,
    source: str,
    destination: str,
    expected_source_sha256: str = "",
) -> dict[str, Any]:
    """Move or rename a path inside the authorized workspace."""
    return await _send_and_wait(
        device,
        "move_path",
        {
            "source": source,
            "destination": destination,
            "expected_source_sha256": expected_source_sha256,
        },
    )


@mcp.tool()
async def bridge_delete_file(
    device: str,
    path: str,
    expected_sha256: str = "",
) -> dict[str, Any]:
    """Delete one file inside the workspace, optionally guarded by SHA-256."""
    return await _send_and_wait(
        device,
        "delete_file",
        {"path": path, "expected_sha256": expected_sha256},
    )


@mcp.tool()
async def bridge_check_python_syntax(
    device: str,
    path: str,
) -> dict[str, Any]:
    """Validate Python syntax without executing the file."""
    return await _send_and_wait(
        device,
        "check_python_syntax",
        {"path": path},
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

@mcp.custom_route("/command-key", methods=["GET"])
async def command_key(_: Request) -> JSONResponse:
    try:
        public_key = _command_public_key_b64()
    except Exception as exc:
        return JSONResponse(
            {"detail": f"command key unavailable: {type(exc).__name__}"},
            status_code=503,
        )
    return JSONResponse(
        {
            "protocol": ENCRYPTED_PROTOCOL,
            "curve": "X25519",
            "kdf": "HKDF-SHA256",
            "aead": "AES-256-GCM",
            "public_key": public_key,
        }
    )


@mcp.custom_route("/github/issue/{issue_number:int}", methods=["POST"])
async def github_issue_dispatch(request: Request) -> JSONResponse:
    issue_number = int(request.path_params.get("issue_number") or 0)
    if issue_number <= 0:
        return JSONResponse({"detail": "invalid issue number"}, status_code=400)

    url = (
        "https://api.github.com/repos/"
        + GITHUB_COMMAND_REPO
        + f"/issues/{issue_number}"
    )
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"LaylayBridgeRelay/{SERVICE_VERSION}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            issue = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return JSONResponse(
            {"detail": "github issue lookup failed", "status": exc.code},
            status_code=502,
        )
    except Exception as exc:
        return JSONResponse(
            {"detail": f"github issue lookup failed: {type(exc).__name__}"},
            status_code=502,
        )

    if not isinstance(issue, dict) or "pull_request" in issue:
        return JSONResponse({"detail": "invalid issue"}, status_code=400)
    if str(issue.get("state") or "") != "open":
        return JSONResponse({"detail": "issue is not open"}, status_code=409)
    if str((issue.get("user") or {}).get("login") or "") != GITHUB_COMMAND_AUTHOR:
        return JSONResponse({"detail": "issue author not allowed"}, status_code=403)
    if not str(issue.get("title") or "").startswith(ISSUE_TITLE_PREFIX):
        return JSONResponse({"detail": "invalid issue title"}, status_code=400)

    created_at = str(issue.get("created_at") or "")
    try:
        created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        age = (datetime.now(timezone.utc) - created).total_seconds()
    except Exception:
        return JSONResponse({"detail": "invalid issue timestamp"}, status_code=400)
    if age < -60 or age > ISSUE_MAX_AGE_SECONDS:
        return JSONResponse({"detail": "issue outside dispatch window"}, status_code=409)

    try:
        envelope = json.loads(str(issue.get("body") or ""))
        if not isinstance(envelope, dict):
            raise ValueError("issue body must be an object")
        command = _decrypt_envelope(envelope)
        if command.request_id in receipts:
            return JSONResponse(
                {
                    "queued": False,
                    "completed": True,
                    "request_id": command.request_id,
                }
            )
        _, existing = _queue_payload(command)
    except ValidationError as exc:
        return JSONResponse({"detail": str(exc)}, status_code=422)
    except Exception as exc:
        return JSONResponse(
            {"detail": f"invalid encrypted command: {type(exc).__name__}"},
            status_code=400,
        )

    print(
        "GITHUB_COMMAND_QUEUED "
        + json.dumps(
            {
                "issue": issue_number,
                "request_id": command.request_id,
                "device": command.device,
                "action": command.action,
            },
            sort_keys=True,
        ),
        flush=True,
    )
    return JSONResponse(
        {
            "queued": True,
            "existing": existing,
            "request_id": command.request_id,
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