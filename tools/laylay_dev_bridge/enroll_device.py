from __future__ import annotations

import argparse
import base64
import hashlib
import json
import secrets
import socket
import uuid
from pathlib import Path

import win32crypt


def protect(secret: str) -> str:
    blob = win32crypt.CryptProtectData(
        secret.encode("utf-8"),
        "Laylay Dev Bridge device identity",
        None,
        None,
        None,
        0,
    )
    return base64.b64encode(blob).decode("ascii")


def unprotect(value: str) -> str:
    blob = base64.b64decode(value.encode("ascii"))
    return win32crypt.CryptUnprotectData(
        blob,
        None,
        None,
        None,
        0,
    )[1].decode("utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--path",
        default=str(Path(__file__).resolve().parent / "device_identity.json"),
    )
    parser.add_argument("--name", default=socket.gethostname())
    parser.add_argument("--rotate", action="store_true")
    args = parser.parse_args()

    path = Path(args.path).resolve()
    current: dict[str, object] = {}
    if path.exists():
        try:
            current = json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception:
            current = {}
    if not isinstance(current, dict):
        current = {}

    device_id = str(current.get("device_id") or "").strip()
    secret = str(current.get("device_secret") or "")
    protected = str(current.get("device_secret_dpapi") or "").strip()

    if protected and not secret:
        secret = unprotect(protected)

    if args.rotate or not device_id or not secret:
        device_id = "dev_" + uuid.uuid4().hex
        secret = secrets.token_urlsafe(48)

    output = {
        "device_id": device_id,
        "device_secret_dpapi": protect(secret),
    }
    path.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    registration = {
        "device_id": device_id,
        "name": str(args.name),
        "secret_sha256": hashlib.sha256(
            secret.encode("utf-8")
        ).hexdigest(),
        "enabled": True,
    }
    print(json.dumps(registration, ensure_ascii=False))


if __name__ == "__main__":
    main()