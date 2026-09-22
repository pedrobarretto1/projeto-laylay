from __future__ import annotations

import os
import subprocess
import threading
import time
import uuid
from collections import deque
from pathlib import Path
from typing import Any

import psutil

try:
    import win32con
    import win32gui
    import win32process
except Exception:
    win32con = None
    win32gui = None
    win32process = None

try:
    from PIL import ImageGrab
except Exception:
    ImageGrab = None

try:
    from pywinauto import Desktop
except Exception:
    Desktop = None


_SESSION_LOCK = threading.RLock()
_SESSIONS: dict[str, dict[str, Any]] = {}
_MAX_SESSIONS = 32
_MAX_BUFFER_LINES = 5000


def _now() -> float:
    return time.time()


def _session_snapshot(session: dict[str, Any]) -> dict[str, Any]:
    process: subprocess.Popen[str] = session["process"]
    return {
        "session_id": session["session_id"],
        "label": session["label"],
        "pid": process.pid,
        "running": process.poll() is None,
        "returncode": process.poll(),
        "cwd": session["cwd"],
        "started_at": session["started_at"],
        "last_seq": session["seq"],
    }


def _reader(session_id: str) -> None:
    with _SESSION_LOCK:
        session = _SESSIONS.get(session_id)
    if not session:
        return
    process: subprocess.Popen[str] = session["process"]
    stream = process.stdout
    if stream is None:
        return
    try:
        for line in iter(stream.readline, ""):
            with _SESSION_LOCK:
                current = _SESSIONS.get(session_id)
                if not current:
                    return
                current["seq"] += 1
                current["lines"].append((current["seq"], line.rstrip("\r\n")))
    finally:
        try:
            stream.close()
        except Exception:
            pass


def start_session(
    command: list[str],
    *,
    cwd: Path,
    label: str,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    if not command:
        raise ValueError("command vazio")

    with _SESSION_LOCK:
        running = [
            s for s in _SESSIONS.values()
            if s["process"].poll() is None
        ]
        if len(running) >= _MAX_SESSIONS:
            raise RuntimeError("Limite de sessoes simultaneas atingido")

    creationflags = 0
    if os.name == "nt":
        creationflags |= getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)

    process = subprocess.Popen(
        command,
        cwd=str(cwd),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        shell=False,
        env=env,
        creationflags=creationflags,
    )

    session_id = "ps_" + uuid.uuid4().hex[:16]
    session = {
        "session_id": session_id,
        "label": str(label),
        "process": process,
        "cwd": str(cwd),
        "started_at": _now(),
        "lines": deque(maxlen=_MAX_BUFFER_LINES),
        "seq": 0,
    }
    with _SESSION_LOCK:
        _SESSIONS[session_id] = session

    thread = threading.Thread(
        target=_reader,
        args=(session_id,),
        name=f"laylay-process-{session_id}",
        daemon=True,
    )
    thread.start()
    return _session_snapshot(session)


def list_sessions(include_finished: bool = True) -> list[dict[str, Any]]:
    with _SESSION_LOCK:
        sessions = list(_SESSIONS.values())
    result: list[dict[str, Any]] = []
    for session in sessions:
        snap = _session_snapshot(session)
        if include_finished or snap["running"]:
            result.append(snap)
    result.sort(key=lambda item: item["started_at"], reverse=True)
    return result


def read_output(
    session_id: str,
    *,
    cursor: int = 0,
    max_lines: int = 200,
) -> dict[str, Any]:
    max_lines = max(1, min(int(max_lines), 1000))
    cursor = max(0, int(cursor))
    with _SESSION_LOCK:
        session = _SESSIONS.get(session_id)
        if not session:
            raise KeyError(f"Sessao inexistente: {session_id}")
        lines = list(session["lines"])
        snapshot = _session_snapshot(session)

    selected = [
        {"seq": seq, "text": text}
        for seq, text in lines
        if seq > cursor
    ][:max_lines]
    next_cursor = selected[-1]["seq"] if selected else cursor
    snapshot.update(
        {
            "cursor": cursor,
            "next_cursor": next_cursor,
            "lines": selected,
            "more_available": any(seq > next_cursor for seq, _ in lines),
        }
    )
    return snapshot


def send_input(session_id: str, data: str) -> dict[str, Any]:
    with _SESSION_LOCK:
        session = _SESSIONS.get(session_id)
        if not session:
            raise KeyError(f"Sessao inexistente: {session_id}")
        process: subprocess.Popen[str] = session["process"]
    if process.poll() is not None:
        raise RuntimeError("Processo ja finalizado")
    if process.stdin is None:
        raise RuntimeError("Sessao sem stdin")
    process.stdin.write(str(data))
    process.stdin.flush()
    return _session_snapshot(session)


def stop_session(
    session_id: str,
    *,
    force: bool = False,
) -> dict[str, Any]:
    with _SESSION_LOCK:
        session = _SESSIONS.get(session_id)
        if not session:
            raise KeyError(f"Sessao inexistente: {session_id}")
        process: subprocess.Popen[str] = session["process"]

    if process.poll() is None:
        try:
            parent = psutil.Process(process.pid)
            children = parent.children(recursive=True)
            for child in reversed(children):
                try:
                    child.terminate()
                except psutil.Error:
                    pass
            try:
                parent.terminate()
            except psutil.Error:
                pass

            _, alive = psutil.wait_procs(
                [*children, parent],
                timeout=2.0,
            )
            if force and alive:
                for proc in alive:
                    try:
                        proc.kill()
                    except psutil.Error:
                        pass
        except psutil.Error:
            if force:
                process.kill()
            else:
                process.terminate()

    return _session_snapshot(session)


def system_metrics(path: Path | None = None) -> dict[str, Any]:
    virtual = psutil.virtual_memory()
    swap = psutil.swap_memory()
    disk_target = str(path or Path.home().anchor or "C:\\")
    disk = psutil.disk_usage(disk_target)
    net = psutil.net_io_counters()
    battery = None
    try:
        raw_battery = psutil.sensors_battery()
        if raw_battery is not None:
            battery = {
                "percent": raw_battery.percent,
                "plugged": raw_battery.power_plugged,
                "seconds_left": raw_battery.secsleft,
            }
    except Exception:
        battery = None

    return {
        "cpu_percent": psutil.cpu_percent(interval=0.2),
        "cpu_count_logical": psutil.cpu_count(logical=True),
        "memory": {
            "total": virtual.total,
            "available": virtual.available,
            "used": virtual.used,
            "percent": virtual.percent,
        },
        "swap": {
            "total": swap.total,
            "used": swap.used,
            "percent": swap.percent,
        },
        "disk": {
            "path": disk_target,
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent,
        },
        "network": {
            "bytes_sent": net.bytes_sent,
            "bytes_recv": net.bytes_recv,
            "packets_sent": net.packets_sent,
            "packets_recv": net.packets_recv,
        },
        "battery": battery,
        "boot_time": psutil.boot_time(),
    }


def list_processes(
    *,
    name_filter: str = "",
    limit: int = 200,
) -> list[dict[str, Any]]:
    needle = str(name_filter or "").casefold()
    limit = max(1, min(int(limit), 500))
    items: list[dict[str, Any]] = []
    for proc in psutil.process_iter(
        ["pid", "name", "status", "username", "memory_info", "create_time"]
    ):
        try:
            info = proc.info
            name = str(info.get("name") or "")
            if needle and needle not in name.casefold():
                continue
            memory = info.get("memory_info")
            items.append(
                {
                    "pid": int(info["pid"]),
                    "name": name,
                    "status": info.get("status"),
                    "username": info.get("username"),
                    "memory_rss": getattr(memory, "rss", None),
                    "started_at": info.get("create_time"),
                }
            )
            if len(items) >= limit:
                break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return items


def list_windows(limit: int = 200) -> list[dict[str, Any]]:
    if win32gui is None or win32process is None:
        raise RuntimeError("pywin32 indisponivel")
    limit = max(1, min(int(limit), 500))
    windows: list[dict[str, Any]] = []

    def callback(hwnd: int, _extra: Any) -> bool:
        if len(windows) >= limit:
            return False
        try:
            if not win32gui.IsWindowVisible(hwnd):
                return True
            title = win32gui.GetWindowText(hwnd).strip()
            if not title:
                return True
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process_name = ""
            try:
                process_name = psutil.Process(pid).name()
            except psutil.Error:
                process_name = ""
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            windows.append(
                {
                    "hwnd": int(hwnd),
                    "pid": int(pid),
                    "process_name": process_name,
                    "title": title[:500],
                    "rect": {
                        "left": left,
                        "top": top,
                        "right": right,
                        "bottom": bottom,
                    },
                }
            )
        except Exception:
            pass
        return True

    win32gui.EnumWindows(callback, None)
    return windows


def focus_window(hwnd: int) -> dict[str, Any]:
    if win32gui is None or win32con is None:
        raise RuntimeError("pywin32 indisponivel")
    hwnd = int(hwnd)
    if not win32gui.IsWindow(hwnd):
        raise ValueError("Janela invalida")
    if not win32gui.IsWindowVisible(hwnd):
        raise ValueError("Janela nao esta visivel")

    try:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    except Exception:
        pass
    try:
        win32gui.SetForegroundWindow(hwnd)
    except Exception as exc:
        raise RuntimeError(f"Nao foi possivel focar a janela: {exc}") from exc

    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    return {
        "hwnd": hwnd,
        "pid": int(pid),
        "title": win32gui.GetWindowText(hwnd),
    }


def window_identity(hwnd: int) -> dict[str, Any]:
    if win32gui is None or win32process is None:
        raise RuntimeError("pywin32 indisponivel")
    hwnd = int(hwnd)
    if not win32gui.IsWindow(hwnd):
        raise ValueError("Janela invalida")
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    try:
        process_name = psutil.Process(pid).name()
    except psutil.Error:
        process_name = ""
    return {
        "hwnd": hwnd,
        "pid": int(pid),
        "process_name": process_name,
        "title": win32gui.GetWindowText(hwnd).strip(),
        "visible": bool(win32gui.IsWindowVisible(hwnd)),
    }


def window_action(hwnd: int, action: str) -> dict[str, Any]:
    if win32gui is None or win32con is None:
        raise RuntimeError("pywin32 indisponivel")
    hwnd = int(hwnd)
    action = str(action or "").strip().casefold()
    commands = {
        "focus": win32con.SW_RESTORE,
        "restore": win32con.SW_RESTORE,
        "minimize": win32con.SW_MINIMIZE,
        "maximize": win32con.SW_MAXIMIZE,
    }
    if action not in commands:
        raise ValueError(
            "Acao de janela nao permitida. Opcoes: "
            + ", ".join(sorted(commands))
        )
    if not win32gui.IsWindow(hwnd):
        raise ValueError("Janela invalida")
    win32gui.ShowWindow(hwnd, commands[action])
    if action in {"focus", "restore", "maximize"}:
        try:
            win32gui.SetForegroundWindow(hwnd)
        except Exception:
            pass
    result = window_identity(hwnd)
    result["window_action"] = action
    return result


def _uia_root(hwnd: int):
    if Desktop is None:
        raise RuntimeError("pywinauto/UI Automation indisponivel")
    hwnd = int(hwnd)
    return Desktop(backend="uia").window(handle=hwnd).wrapper_object()


def _uia_control_record(control: Any) -> dict[str, Any]:
    info = control.element_info
    rect = control.rectangle()
    return {
        "control_type": str(getattr(info, "control_type", "") or ""),
        "name": str(getattr(info, "name", "") or "")[:300],
        "automation_id": str(getattr(info, "automation_id", "") or "")[:300],
        "class_name": str(getattr(info, "class_name", "") or "")[:200],
        "enabled": bool(control.is_enabled()),
        "visible": bool(control.is_visible()),
        "rect": {
            "left": int(rect.left),
            "top": int(rect.top),
            "right": int(rect.right),
            "bottom": int(rect.bottom),
        },
    }


def uia_controls(
    hwnd: int,
    *,
    allowed_types: set[str] | None = None,
    max_depth: int = 5,
    max_items: int = 300,
) -> list[dict[str, Any]]:
    root = _uia_root(hwnd)
    allowed = {str(x) for x in (allowed_types or set())}
    max_depth = max(1, min(int(max_depth), 8))
    max_items = max(1, min(int(max_items), 800))
    result: list[dict[str, Any]] = []

    def walk(control: Any, depth: int) -> None:
        if len(result) >= max_items or depth > max_depth:
            return
        try:
            children = control.children()
        except Exception:
            return
        for child in children:
            if len(result) >= max_items:
                return
            try:
                record = _uia_control_record(child)
            except Exception:
                continue
            control_type = record["control_type"]
            if not allowed or control_type in allowed:
                if record["name"] or record["automation_id"]:
                    record["depth"] = depth
                    result.append(record)
            walk(child, depth + 1)

    walk(root, 1)
    return result


def _find_uia_control(
    hwnd: int,
    *,
    control_type: str,
    name: str = "",
    automation_id: str = "",
) -> Any:
    root = _uia_root(hwnd)
    wanted_type = str(control_type or "").strip()
    wanted_name = str(name or "").strip()
    wanted_id = str(automation_id or "").strip()
    if not wanted_type:
        raise ValueError("control_type e obrigatorio")
    if not wanted_name and not wanted_id:
        raise ValueError("Informe name ou automation_id")

    matches: list[Any] = []
    for control in root.descendants(control_type=wanted_type):
        try:
            info = control.element_info
            current_name = str(getattr(info, "name", "") or "")
            current_id = str(getattr(info, "automation_id", "") or "")
            if wanted_name and current_name != wanted_name:
                continue
            if wanted_id and current_id != wanted_id:
                continue
            if not control.is_visible() or not control.is_enabled():
                continue
            matches.append(control)
            if len(matches) > 1:
                break
        except Exception:
            continue

    if not matches:
        raise LookupError("Controle UIA nao encontrado")
    if len(matches) > 1:
        raise LookupError(
            "Seletor UIA ambiguo; informe automation_id ou nome mais especifico"
        )
    return matches[0]


def uia_control_info(
    hwnd: int,
    *,
    control_type: str,
    name: str = "",
    automation_id: str = "",
) -> dict[str, Any]:
    control = _find_uia_control(
        hwnd,
        control_type=control_type,
        name=name,
        automation_id=automation_id,
    )
    return _uia_control_record(control)


def invoke_uia_control(
    hwnd: int,
    *,
    control_type: str,
    name: str = "",
    automation_id: str = "",
) -> dict[str, Any]:
    control = _find_uia_control(
        hwnd,
        control_type=control_type,
        name=name,
        automation_id=automation_id,
    )
    info = _uia_control_record(control)

    invoked = False
    for method_name in ("invoke", "select", "toggle"):
        method = getattr(control, method_name, None)
        if not callable(method):
            continue
        try:
            method()
            invoked = True
            break
        except Exception:
            continue
    if not invoked:
        raise RuntimeError(
            "Controle nao oferece uma acao UIA segura suportada"
        )
    return info


def capture_window(
    hwnd: int,
    destination: Path,
    *,
    quality: int = 70,
    max_width: int = 1280,
) -> dict[str, Any]:
    if ImageGrab is None or win32gui is None:
        raise RuntimeError("Captura de janela indisponivel")
    hwnd = int(hwnd)
    if not win32gui.IsWindow(hwnd):
        raise ValueError("Janela invalida")
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    if right <= left or bottom <= top:
        raise ValueError("Janela sem area capturavel")
    quality = max(30, min(int(quality), 95))
    max_width = max(320, min(int(max_width), 3840))
    destination.parent.mkdir(parents=True, exist_ok=True)
    image = ImageGrab.grab(
        bbox=(left, top, right, bottom),
        all_screens=True,
    ).convert("RGB")
    original_width, original_height = image.size
    if image.width > max_width:
        height = max(1, int(image.height * (max_width / image.width)))
        image = image.resize((max_width, height))
    image.save(destination, format="JPEG", quality=quality, optimize=True)
    return {
        "path": str(destination),
        "width": image.width,
        "height": image.height,
        "original_width": original_width,
        "original_height": original_height,
        "bytes": destination.stat().st_size,
    }


def capture_screen(
    destination: Path,
    *,
    quality: int = 70,
    max_width: int = 1280,
) -> dict[str, Any]:
    if ImageGrab is None:
        raise RuntimeError("Pillow/ImageGrab indisponivel")
    quality = max(30, min(int(quality), 95))
    max_width = max(320, min(int(max_width), 3840))
    destination.parent.mkdir(parents=True, exist_ok=True)
    image = ImageGrab.grab(all_screens=True).convert("RGB")
    original_width, original_height = image.size
    if image.width > max_width:
        height = max(1, int(image.height * (max_width / image.width)))
        image = image.resize((max_width, height))
    image.save(destination, format="JPEG", quality=quality, optimize=True)
    return {
        "path": str(destination),
        "width": image.width,
        "height": image.height,
        "original_width": original_width,
        "original_height": original_height,
        "bytes": destination.stat().st_size,
    }