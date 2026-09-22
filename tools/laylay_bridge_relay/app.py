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
from pathlib import Path
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

SERVICE_VERSION = "0.9.1"
BRIDGE_TOKEN = os.environ.get("BRIDGE_RECEIPT_TOKEN", "")
MCP_ACCESS_TOKEN = os.environ.get("MCP_ACCESS_TOKEN", "")
DEVICE_CREDENTIALS_RAW = os.environ.get("DEVICE_CREDENTIALS_JSON", "{}")
CONTROLLER_TOKEN = os.environ.get("CONTROLLER_DISPATCH_TOKEN", "")
DIRECT_DISPATCH_ENABLED = str(
    os.environ.get("DIRECT_DISPATCH_ENABLED", "0")
).strip().casefold() in {"1", "true", "yes", "on"}
GITHUB_WEBHOOK_SECRET = os.environ.get("GITHUB_WEBHOOK_SECRET", "")
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
DIRECT_PROTOCOL = "laylay-bridge-direct-v1"
ACTIONS = {
    "ping",
    "bridge_status",
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
    "copy_file",
    "backup_file",
    "restore_backup",
    "copy_directory",
    "move_path",
    "delete_file",
    "delete_directory",
    "tail_file",
    "read_binary",
    "check_python_syntax",
    "run_readonly",
    "run_named_command",
    "git_diff",
    "git_log",
    "run_tests",
    "process_start",
    "process_sessions",
    "process_output",
    "process_input",
    "process_stop",
    "system_status",
    "list_processes",
    "list_windows",
    "focus_window",
    "capture_screen",
    "ui_profiles",
    "ui_windows",
    "ui_controls",
    "ui_window_action",
    "ui_prepare_invoke",
    "ui_invoke",
    "ui_capture_window",
}
commands: dict[str, dict[str, Any]] = {}
receipts: dict[str, dict[str, Any]] = {}
devices_seen: dict[str, dict[str, Any]] = {}
leases: dict[str, float] = {}


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


class DirectCommand(BaseModel):
    protocol: str = DIRECT_PROTOCOL
    request_id: str
    device: str
    action: str
    args: dict[str, Any] = Field(default_factory=dict)
    controller_token: str
    issued_at: int


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _trim(mapping: dict[str, Any], limit: int = 500) -> None:
    while len(mapping) > limit:
        mapping.pop(next(iter(mapping)))


STATE_PATH = Path(os.environ.get("RELAY_STATE_PATH", "/data/relay_state.json"))


def _save_state() -> None:
    try:
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        temp = STATE_PATH.with_suffix(STATE_PATH.suffix + ".tmp")
        temp.write_text(
            json.dumps(
                {
                    "commands": commands,
                    "receipts": receipts,
                    "leases": leases,
                },
                ensure_ascii=False,
                separators=(",", ":"),
            ),
            encoding="utf-8",
        )
        temp.replace(STATE_PATH)
    except Exception as exc:
        print(
            f"STATE_SAVE_ERROR {type(exc).__name__}: {exc}",
            flush=True,
        )


def _load_state() -> None:
    try:
        if not STATE_PATH.exists():
            return
        data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return
        stored_commands = data.get("commands")
        stored_receipts = data.get("receipts")
        stored_leases = data.get("leases")
        if isinstance(stored_commands, dict):
            commands.update(stored_commands)
        if isinstance(stored_receipts, dict):
            receipts.update(stored_receipts)
        if isinstance(stored_leases, dict):
            leases.update(
                {
                    str(key): float(value)
                    for key, value in stored_leases.items()
                    if isinstance(value, (int, float))
                }
            )
        _trim(commands)
        _trim(receipts)
        _trim(leases)
    except Exception as exc:
        print(
            f"STATE_LOAD_ERROR {type(exc).__name__}: {exc}",
            flush=True,
        )


_load_state()

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


def _decrypt_direct_envelope(envelope: dict[str, Any]) -> Command:
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

    direct = DirectCommand.model_validate(decoded)
    if direct.protocol != DIRECT_PROTOCOL:
        raise ValueError("invalid direct protocol")
    if direct.request_id != request_id:
        raise ValueError("request_id mismatch")
    if not CONTROLLER_TOKEN:
        raise RuntimeError("controller dispatch is not configured")
    if not hmac.compare_digest(
        direct.controller_token,
        CONTROLLER_TOKEN,
    ):
        raise PermissionError("invalid controller token")

    now = int(time.time())
    if direct.issued_at < now - 90 or direct.issued_at > now + 30:
        raise ValueError("direct command outside dispatch window")
    if direct.action not in ACTIONS:
        raise ValueError("invalid action")

    return Command(
        protocol=PROTOCOL,
        request_id=direct.request_id,
        device=direct.device,
        action=direct.action,
        args=direct.args,
    )


def _bridge_authorized(request: Request) -> bool:
    supplied = request.headers.get("x-bridge-token", "")
    return bool(BRIDGE_TOKEN) and hmac.compare_digest(supplied, BRIDGE_TOKEN)


def _device_credentials() -> dict[str, dict[str, Any]]:
    try:
        value = json.loads(DEVICE_CREDENTIALS_RAW)
    except Exception:
        return {}
    if not isinstance(value, dict):
        return {}
    return {
        str(key): dict(record)
        for key, record in value.items()
        if isinstance(record, dict)
    }


DEVICE_CREDENTIALS = _device_credentials()


def _device_authorized(
    request: Request,
    device_id: str,
) -> tuple[bool, dict[str, Any] | None]:
    device_id = str(device_id or "").strip()
    supplied_id = str(
        request.headers.get("x-bridge-device-id", "")
    ).strip()
    supplied_secret = str(
        request.headers.get("x-bridge-device-secret", "")
    )
    if not device_id or not supplied_id or supplied_id != device_id:
        return False, None
    record = DEVICE_CREDENTIALS.get(device_id)
    if not isinstance(record, dict) or not record.get("enabled", True):
        return False, None
    expected_hash = str(record.get("secret_sha256") or "").strip().lower()
    if not expected_hash or not supplied_secret:
        return False, None
    actual_hash = hashlib.sha256(
        supplied_secret.encode("utf-8")
    ).hexdigest()
    if not hmac.compare_digest(actual_hash, expected_hash):
        return False, None
    return True, record


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
    _save_state()
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
    for key, info in sorted(devices_seen.items()):
        age = max(0.0, now - float(info["seen_epoch"]))
        items.append(
            {
                "device": info.get("name") or key,
                "device_id": info.get("device_id"),
                "auth": info.get("auth") or "legacy",
                "last_seen": info["last_seen"],
                "seconds_ago": round(age, 1),
                "online": age <= 30.0,
            }
        )
    return {
        "devices": items,
        "registered_device_count": len(DEVICE_CREDENTIALS),
        "relay_version": SERVICE_VERSION,
    }


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


@mcp.tool()
async def bridge_action(
    device: str,
    action: str,
    args: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run any action from the relay's explicit allowlist."""
    if action not in ACTIONS:
        raise ValueError(f"unsupported action: {action}")
    return await _send_and_wait(device, action, dict(args or {}))


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



controller_tickets: dict[str, dict[str, Any]] = {}


def _issue_controller_ticket(request_id: str) -> str:
    token = secrets.token_urlsafe(24)
    controller_tickets[request_id] = {
        "token_hash": hashlib.sha256(token.encode("utf-8")).hexdigest(),
        "expires_at": time.time() + 300.0,
    }
    _trim(controller_tickets, 500)
    return token


def _controller_ticket_ok(request_id: str, token: str) -> bool:
    record = controller_tickets.get(request_id)
    if not isinstance(record, dict):
        return False
    if float(record.get("expires_at") or 0.0) < time.time():
        controller_tickets.pop(request_id, None)
        return False
    expected = str(record.get("token_hash") or "")
    actual = hashlib.sha256(str(token or "").encode("utf-8")).hexdigest()
    return bool(expected) and hmac.compare_digest(actual, expected)


@mcp.custom_route("/controller/dispatch", methods=["GET"])
async def controller_dispatch(request: Request) -> JSONResponse:
    if not DIRECT_DISPATCH_ENABLED:
        return JSONResponse(
            {"detail": "direct dispatch disabled"},
            status_code=404,
        )
    envelope = {
        "protocol": ENCRYPTED_PROTOCOL,
        "request_id": str(request.query_params.get("request_id") or ""),
        "ephemeral_public_key": str(
            request.query_params.get("ephemeral_public_key") or ""
        ),
        "nonce": str(request.query_params.get("nonce") or ""),
        "ciphertext": str(request.query_params.get("ciphertext") or ""),
    }
    try:
        command = _decrypt_direct_envelope(envelope)
        _, existing = _queue_payload(command)
    except PermissionError:
        return JSONResponse({"detail": "unauthorized"}, status_code=401)
    except ValidationError as exc:
        return JSONResponse({"detail": str(exc)}, status_code=422)
    except RuntimeError as exc:
        return JSONResponse({"detail": str(exc)}, status_code=503)
    except Exception as exc:
        return JSONResponse(
            {"detail": f"invalid direct command: {type(exc).__name__}"},
            status_code=400,
        )

    print(
        "CONTROLLER_COMMAND_QUEUED "
        + json.dumps(
            {
                "request_id": command.request_id,
                "device": command.device,
                "action": command.action,
            },
            sort_keys=True,
        ),
        flush=True,
    )

    try:
        wait_seconds = float(request.query_params.get("wait_seconds") or 12)
    except ValueError:
        wait_seconds = 12.0
    wait_seconds = max(0.0, min(wait_seconds, 20.0))
    deadline = time.monotonic() + wait_seconds

    while time.monotonic() < deadline:
        receipt = receipts.get(command.request_id)
        if receipt is not None:
            return JSONResponse(
                {
                    "queued": True,
                    "existing": existing,
                    "completed": True,
                    "request_id": command.request_id,
                    "receipt": receipt,
                }
            )
        await asyncio.sleep(0.1)

    ticket = _issue_controller_ticket(command.request_id)
    return JSONResponse(
        {
            "queued": True,
            "existing": existing,
            "completed": False,
            "request_id": command.request_id,
            "receipt_token": ticket,
        },
        status_code=202,
    )


@mcp.custom_route(
    "/controller/receipt/{request_id}",
    methods=["GET"],
)
async def controller_receipt(request: Request) -> JSONResponse:
    if not DIRECT_DISPATCH_ENABLED:
        return JSONResponse(
            {"detail": "direct dispatch disabled"},
            status_code=404,
        )
    request_id = str(request.path_params.get("request_id") or "")
    token = str(request.query_params.get("token") or "")
    if not REQUEST_RE.fullmatch(request_id):
        return JSONResponse({"detail": "invalid request_id"}, status_code=400)
    if not _controller_ticket_ok(request_id, token):
        return JSONResponse({"detail": "invalid receipt token"}, status_code=401)

    receipt = receipts.get(request_id)
    if receipt is None:
        return JSONResponse(
            {
                "completed": False,
                "request_id": request_id,
            },
            status_code=202,
        )

    controller_tickets.pop(request_id, None)
    return JSONResponse(
        {
            "completed": True,
            "request_id": request_id,
            "receipt": receipt,
        }
    )



def _verify_github_webhook(raw: bytes, supplied: str) -> bool:
    if not GITHUB_WEBHOOK_SECRET:
        return False
    supplied = str(supplied or "")
    if not supplied.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(
        GITHUB_WEBHOOK_SECRET.encode("utf-8"),
        raw,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(supplied, expected)


@mcp.custom_route("/github/webhook", methods=["POST"])
async def github_webhook(request: Request) -> JSONResponse:
    raw = await request.body()
    signature = request.headers.get("x-hub-signature-256", "")
    if not _verify_github_webhook(raw, signature):
        return JSONResponse({"detail": "invalid webhook signature"}, status_code=401)

    event = str(request.headers.get("x-github-event") or "").strip().casefold()
    try:
        payload = json.loads(raw.decode("utf-8"))
    except Exception:
        return JSONResponse({"detail": "invalid webhook json"}, status_code=400)

    if event == "ping":
        return JSONResponse({"ok": True, "event": "ping"})

    if event != "issues":
        return JSONResponse({"ignored": True, "event": event})

    if not isinstance(payload, dict) or str(payload.get("action") or "") != "opened":
        return JSONResponse({"ignored": True, "reason": "issue action"})

    repository = payload.get("repository") or {}
    issue = payload.get("issue") or {}
    if str(repository.get("full_name") or "") != GITHUB_COMMAND_REPO:
        return JSONResponse({"detail": "repository not allowed"}, status_code=403)
    if not isinstance(issue, dict) or "pull_request" in issue:
        return JSONResponse({"detail": "invalid issue"}, status_code=400)
    if str(issue.get("state") or "") != "open":
        return JSONResponse({"detail": "issue is not open"}, status_code=409)
    if str((issue.get("user") or {}).get("login") or "") != GITHUB_COMMAND_AUTHOR:
        return JSONResponse({"detail": "issue author not allowed"}, status_code=403)
    if not str(issue.get("title") or "").startswith(ISSUE_TITLE_PREFIX):
        return JSONResponse({"ignored": True, "reason": "title prefix"})

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
        _, existing = _queue_payload(command)
    except ValidationError as exc:
        return JSONResponse({"detail": str(exc)}, status_code=422)
    except RuntimeError as exc:
        return JSONResponse({"detail": str(exc)}, status_code=409)
    except Exception as exc:
        return JSONResponse(
            {"detail": f"invalid encrypted command: {type(exc).__name__}"},
            status_code=400,
        )

    issue_number = int(issue.get("number") or 0)
    print(
        "GITHUB_WEBHOOK_QUEUED "
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
            "issue": issue_number,
        },
        status_code=202,
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
    device_name = str(request.query_params.get("device") or "").strip()
    device_id = str(request.query_params.get("device_id") or "").strip()
    if not device_name or len(device_name) > 128:
        return JSONResponse({"detail": "invalid device"}, status_code=400)
    if len(device_id) > 128:
        return JSONResponse({"detail": "invalid device_id"}, status_code=400)

    device_ok, record = _device_authorized(request, device_id)
    legacy_ok = _bridge_authorized(request)
    if not device_ok and not legacy_ok:
        return JSONResponse({"detail": "invalid device credentials"}, status_code=401)

    if device_ok and isinstance(record, dict):
        expected_name = str(record.get("name") or "").strip()
        if expected_name and expected_name.casefold() != device_name.casefold():
            return JSONResponse({"detail": "device name mismatch"}, status_code=403)

    try:
        wait_seconds = float(request.query_params.get("wait_seconds") or 0)
    except ValueError:
        wait_seconds = 0.0
    wait_seconds = max(0.0, min(wait_seconds, 25.0))
    deadline = time.monotonic() + wait_seconds
    seen_key = device_id or device_name

    while True:
        now = time.time()
        devices_seen[seen_key] = {
            "device_id": device_id or None,
            "name": device_name,
            "auth": "device" if device_ok else "legacy",
            "last_seen": _utcnow(),
            "seen_epoch": now,
        }
        _trim(devices_seen, 100)

        accepted_targets = {"*", device_name}
        if device_id:
            accepted_targets.add(device_id)

        for request_id, payload in commands.items():
            target = str(payload.get("device") or "*")
            if target not in accepted_targets:
                continue
            lease_until = float(leases.get(request_id) or 0.0)
            if lease_until > now:
                continue
            leases[request_id] = now + 30.0
            _trim(leases, 500)
            _save_state()
            return JSONResponse({"command": payload})

        if time.monotonic() >= deadline:
            return JSONResponse({"command": None})
        await asyncio.sleep(0.2)


@mcp.custom_route("/devices", methods=["GET"])
async def devices_route(request: Request) -> JSONResponse:
    if not _bridge_authorized(request):
        return JSONResponse({"detail": "invalid bridge token"}, status_code=401)
    return JSONResponse(bridge_devices())


@mcp.custom_route("/receipt/{request_id}", methods=["GET", "POST"])
async def receipt_route(request: Request) -> JSONResponse:
    request_id = str(request.path_params.get("request_id") or "")
    if not REQUEST_RE.fullmatch(request_id):
        return JSONResponse({"detail": "invalid request_id"}, status_code=400)

    if request.method == "GET":
        if not _bridge_authorized(request):
            return JSONResponse({"detail": "invalid bridge token"}, status_code=401)
        payload = receipts.get(request_id)
        if payload is None:
            return JSONResponse({"detail": "receipt not found"}, status_code=404)
        return JSONResponse(payload)

    device_id = str(
        request.headers.get("x-bridge-device-id", "")
    ).strip()
    device_ok, record = _device_authorized(request, device_id)
    legacy_ok = _bridge_authorized(request)
    if not device_ok and not legacy_ok:
        return JSONResponse({"detail": "invalid device credentials"}, status_code=401)

    try:
        receipt = Receipt.model_validate(await request.json())
    except ValidationError as exc:
        return JSONResponse({"detail": str(exc)}, status_code=422)

    if device_ok and isinstance(record, dict):
        expected_name = str(record.get("name") or "").strip()
        if (
            expected_name
            and expected_name.casefold() != receipt.device.casefold()
        ):
            return JSONResponse({"detail": "device name mismatch"}, status_code=403)

    payload = receipt.model_dump()
    if device_id:
        payload["device_id"] = device_id
    payload["received_at"] = _utcnow()
    receipts[request_id] = payload
    commands.pop(request_id, None)
    leases.pop(request_id, None)
    _trim(receipts)
    _save_state()
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