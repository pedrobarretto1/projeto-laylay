from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Laylay Bridge Relay", version="0.1.0")
TOKEN = os.environ.get("BRIDGE_RECEIPT_TOKEN", "")
REQUEST_RE = re.compile(r"^[A-Za-z0-9_-]{8,128}$")
receipts: dict[str, dict[str, Any]] = {}


class Receipt(BaseModel):
    device: str
    action: str
    executed: bool
    confirmed: bool | None = None
    data: dict[str, Any] = {}


@app.get("/")
def root() -> dict[str, Any]:
    return {"service": "laylay-bridge-relay", "version": "0.1.0"}


@app.get("/health")
def health() -> dict[str, Any]:
    return {"ok": True, "stored_receipts": len(receipts)}


@app.post("/receipt/{request_id}")
def post_receipt(
    request_id: str,
    receipt: Receipt,
    x_bridge_token: str | None = Header(default=None),
) -> dict[str, Any]:
    if not TOKEN or x_bridge_token != TOKEN:
        raise HTTPException(status_code=401, detail="invalid bridge token")
    if not REQUEST_RE.fullmatch(request_id):
        raise HTTPException(status_code=400, detail="invalid request_id")

    payload = receipt.model_dump()
    payload["request_id"] = request_id
    payload["received_at"] = datetime.now(timezone.utc).isoformat()
    receipts[request_id] = payload
    return {"stored": True, "request_id": request_id}


@app.get("/receipt/{request_id}")
def get_receipt(request_id: str) -> dict[str, Any]:
    if not REQUEST_RE.fullmatch(request_id):
        raise HTTPException(status_code=400, detail="invalid request_id")
    payload = receipts.get(request_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="receipt not found")
    return payload
