from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field

app = FastAPI(title="Laylay Bridge Relay", version="0.2.0")
TOKEN = os.environ.get("BRIDGE_RECEIPT_TOKEN", "")
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
receipts: dict[str, dict[str, Any]] = {}
commands: dict[str, dict[str, Any]] = {}


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


def _require_token(x_bridge_token: str | None) -> None:
    if not TOKEN or x_bridge_token != TOKEN:
        raise HTTPException(status_code=401, detail="invalid bridge token")


@app.get("/")
def root() -> dict[str, Any]:
    return {"service": "laylay-bridge-relay", "version": "0.2.0"}


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "stored_receipts": len(receipts),
        "pending_commands": len(commands),
    }


@app.post("/command")
def post_command(
    command: Command,
    x_bridge_token: str | None = Header(default=None),
) -> dict[str, Any]:
    _require_token(x_bridge_token)
    if command.protocol != PROTOCOL:
        raise HTTPException(status_code=400, detail="invalid protocol")
    if not REQUEST_RE.fullmatch(command.request_id):
        raise HTTPException(status_code=400, detail="invalid request_id")
    if command.action not in ACTIONS:
        raise HTTPException(status_code=400, detail="invalid action")

    payload = command.model_dump()
    existing = commands.get(command.request_id)
    if existing is not None:
        if existing != payload:
            raise HTTPException(status_code=409, detail="request_id already queued")
        return {"queued": True, "existing": True, "request_id": command.request_id}
    if command.request_id in receipts:
        return {"queued": False, "completed": True, "request_id": command.request_id}

    payload["queued_at"] = datetime.now(timezone.utc).isoformat()
    commands[command.request_id] = payload
    return {"queued": True, "existing": False, "request_id": command.request_id}


@app.get("/command/next")
def next_command(
    device: str = Query(min_length=1, max_length=128),
    x_bridge_token: str | None = Header(default=None),
) -> dict[str, Any]:
    _require_token(x_bridge_token)
    for payload in commands.values():
        target = str(payload.get("device") or "*")
        if target in {"*", device}:
            return {"command": payload}
    return {"command": None}


@app.post("/receipt/{request_id}")
def post_receipt(
    request_id: str,
    receipt: Receipt,
    x_bridge_token: str | None = Header(default=None),
) -> dict[str, Any]:
    _require_token(x_bridge_token)
    if not REQUEST_RE.fullmatch(request_id):
        raise HTTPException(status_code=400, detail="invalid request_id")

    payload = receipt.model_dump()
    payload["request_id"] = request_id
    payload["received_at"] = datetime.now(timezone.utc).isoformat()
    receipts[request_id] = payload
    commands.pop(request_id, None)
    print(
        "BRIDGE_RECEIPT "
        + json.dumps(payload, ensure_ascii=False, sort_keys=True),
        flush=True,
    )
    return {"stored": True, "request_id": request_id}


@app.get("/receipt/{request_id}")
def get_receipt(
    request_id: str,
    x_bridge_token: str | None = Header(default=None),
) -> dict[str, Any]:
    _require_token(x_bridge_token)
    if not REQUEST_RE.fullmatch(request_id):
        raise HTTPException(status_code=400, detail="invalid request_id")
    payload = receipts.get(request_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="receipt not found")
    return payload
