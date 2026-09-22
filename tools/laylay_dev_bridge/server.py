from __future__ import annotations

import base64
import fnmatch
import hashlib
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any

from mcp.server import MCPServer

import bridge_runtime

APP_NAME = "Laylay Dev Bridge"
APP_VERSION = "0.9.0"
BASE_DIR = (
    Path(sys.executable).resolve().parent
    if getattr(sys, "frozen", False)
    else Path(__file__).resolve().parent
)
REMOTE_CONFIG_PATH = BASE_DIR / "bridge_remote.json"
REMOTE_STATE_PATH = BASE_DIR / "bridge_remote_state.json"
REMOTE_PENDING_PATH = BASE_DIR / "bridge_remote_pending.json"

try:
    _BOOT_CONFIG = json.loads(
        REMOTE_CONFIG_PATH.read_text(encoding="utf-8-sig")
    )
except Exception:
    _BOOT_CONFIG = {}
if not isinstance(_BOOT_CONFIG, dict):
    _BOOT_CONFIG = {}

_workspace_root = str(_BOOT_CONFIG.get("workspace_root") or "").strip()
_root_value = os.environ.get("LAYLAY_BRIDGE_ROOT") or _workspace_root
ROOT = Path(_root_value or (BASE_DIR / "sandbox")).resolve()

_MACHINE_CONFIG = _BOOT_CONFIG.get("machine_access") or {}
if not isinstance(_MACHINE_CONFIG, dict):
    _MACHINE_CONFIG = {}
MACHINE_ACCESS_ENABLED = bool(_MACHINE_CONFIG.get("enabled", False))


def _config_paths(name: str, fallback: list[str]) -> tuple[Path, ...]:
    values = _MACHINE_CONFIG.get(name)
    if not isinstance(values, list):
        values = fallback
    paths: list[Path] = []
    for value in values:
        text = str(value or "").strip()
        if not text:
            continue
        try:
            paths.append(Path(text).resolve(strict=False))
        except Exception:
            continue
    return tuple(paths)


USER_PROFILE = Path(os.environ.get("USERPROFILE") or Path.home()).resolve(strict=False)
READ_ROOTS = _config_paths("read_roots", [str(ROOT)])
WRITE_ROOTS = _config_paths("write_roots", [str(ROOT)])
DENIED_ROOTS = _config_paths(
    "denied_roots",
    [
        str(Path(os.environ.get("WINDIR") or r"C:\Windows")),
        r"C:\Program Files",
        r"C:\Program Files (x86)",
        r"C:\ProgramData",
        r"C:\Recovery",
        r"C:\System Volume Information",
        r"C:\$Recycle.Bin",
        r"C:\Boot",
        r"C:\EFI",
    ],
)
WRITE_DENIED_ROOTS = _config_paths(
    "write_denied_roots",
    [str(USER_PROFILE / "AppData")],
)
PROTECTED_FILES = _config_paths(
    "protected_files",
    [
        str(REMOTE_CONFIG_PATH),
        str(BASE_DIR / "mcp_client.json"),
        str(BASE_DIR / "dist" / "bridge_remote.json"),
    ],
)
ALLOW_PROCESS_EXECUTION = bool(
    _MACHINE_CONFIG.get("allow_process_execution", False)
)
_project_python_value = str(
    _MACHINE_CONFIG.get("project_python") or sys.executable
).strip()
PROJECT_PYTHON = Path(_project_python_value).resolve(strict=False)
PY_LAUNCHER = shutil.which("py")
PROJECT_PYTHON_COMMAND = (
    [str(PY_LAUNCHER), "-3.14"]
    if PY_LAUNCHER
    else [str(PROJECT_PYTHON)]
)

_UI_CONFIG = _MACHINE_CONFIG.get("ui_automation") or {}
if not isinstance(_UI_CONFIG, dict):
    _UI_CONFIG = {}
UI_AUTOMATION_ENABLED = bool(_UI_CONFIG.get("enabled", False))
_ui_profiles_value = _UI_CONFIG.get("profiles") or {}
UI_PROFILES = (
    _ui_profiles_value
    if isinstance(_ui_profiles_value, dict)
    else {}
)
_ui_risk_words = _UI_CONFIG.get("high_risk_keywords") or []
UI_HIGH_RISK_KEYWORDS = tuple(
    str(item).strip().casefold()
    for item in _ui_risk_words
    if str(item).strip()
)
_UI_CHALLENGE_LOCK = threading.RLock()
_UI_CHALLENGES: dict[str, dict[str, Any]] = {}

PORT = int(os.environ.get("LAYLAY_BRIDGE_PORT", "8766"))
MAX_TEXT_BYTES = 2 * 1024 * 1024
MAX_LIST_ENTRIES = 200
MAX_SEARCH_RESULTS = 200
MAX_SEARCH_FILES = 50000
MAX_BINARY_BYTES = 300 * 1024
MAX_COPY_FILES = 10000
REMOTE_PROTOCOL = "laylay-bridge-command-v1"
REMOTE_ACTIONS = {
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
REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9_-]{8,128}$")

ROOT.mkdir(parents=True, exist_ok=True)

mcp = MCPServer(
    APP_NAME,
    version=APP_VERSION,
    instructions=(
        "Bridge local de desenvolvimento da Laylay. "
        "Todas as operacoes de arquivo ficam presas ao sandbox configurado."
    ),
)


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _is_secret_path(path: Path) -> bool:
    name = path.name.casefold()
    if name == ".env" or (
        name.startswith(".env.")
        and name not in {".env.example", ".env.sample", ".env.template"}
    ):
        return True
    if name in {
        "id_rsa",
        "id_ed25519",
        "id_ecdsa",
        "known_hosts.old",
        "credentials.json",
    }:
        return True
    return False


def _blocked_reason(path: Path, operation: str) -> str | None:
    root_system_files = {
        "$winre_backup_partition.marker",
        "bootmgr",
        "bootnxt",
        "bootsect.bak",
        "dumpstack.log",
        "dumpstack.log.tmp",
        "hiberfil.sys",
        "pagefile.sys",
        "swapfile.sys",
    }
    if path.parent == Path(path.anchor) and path.name.casefold() in root_system_files:
        return "arquivo critico do sistema na raiz do volume"

    for protected in PROTECTED_FILES:
        if path == protected:
            return "arquivo protegido do proprio Bridge"
    for denied in DENIED_ROOTS:
        if _is_within(path, denied):
            return f"zona protegida: {denied}"
    if operation != "read":
        for denied in WRITE_DENIED_ROOTS:
            if _is_within(path, denied):
                return f"zona sem escrita: {denied}"
    if _is_secret_path(path):
        return "arquivo de credencial/segredo protegido"
    return None


def _allowed_roots(operation: str) -> tuple[Path, ...]:
    if not MACHINE_ACCESS_ENABLED:
        return (ROOT,)
    return READ_ROOTS if operation == "read" else WRITE_ROOTS


def _safe_path(user_path: str, operation: str = "read") -> Path:
    operation = str(operation or "read").casefold()
    if operation not in {"read", "write"}:
        raise ValueError(f"Operacao de caminho invalida: {operation}")

    raw = Path(str(user_path or "."))
    candidate = raw if raw.is_absolute() else ROOT / raw
    resolved = candidate.resolve(strict=False)

    roots = _allowed_roots(operation)
    if not any(_is_within(resolved, root) for root in roots):
        raise ValueError(
            f"Caminho fora das raizes autorizadas para {operation}: {user_path}"
        )

    reason = _blocked_reason(resolved, operation)
    if reason:
        raise PermissionError(f"Acesso bloqueado: {reason}")
    return resolved


def _path_allowed(path: Path, operation: str = "read") -> bool:
    try:
        _safe_path(str(path), operation)
        return True
    except Exception:
        return False


def _relative(path: Path) -> str:
    resolved = path.resolve(strict=False)
    try:
        return str(resolved.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(resolved)


def _receipt(action: str, **extra: Any) -> dict[str, Any]:
    return {
        "bridge": APP_NAME,
        "version": APP_VERSION,
        "action": action,
        "executed": True,
        "confirmed": True,
        **extra,
    }


@mcp.tool()
def ping() -> dict[str, Any]:
    """Confirma que o bridge esta online."""
    return _receipt(
        "ping",
        device=socket.gethostname(),
        root=str(ROOT),
        python=sys.version.split()[0],
    )


@mcp.tool()
def system_info() -> dict[str, Any]:
    """Retorna informacoes basicas do dispositivo e do sandbox."""
    return _receipt(
        "system_info",
        device=socket.gethostname(),
        platform=platform.platform(),
        architecture=platform.machine(),
        python=sys.version.split()[0],
        root=str(ROOT),
        machine_access=MACHINE_ACCESS_ENABLED,
    )


@mcp.tool()
def access_info() -> dict[str, Any]:
    """Mostra a politica de acesso de arquivos ativa, sem revelar segredos."""
    return _receipt(
        "access_info",
        machine_access=MACHINE_ACCESS_ENABLED,
        default_workspace=str(ROOT),
        read_roots=[str(path) for path in READ_ROOTS],
        write_roots=[str(path) for path in WRITE_ROOTS],
        denied_roots=[str(path) for path in DENIED_ROOTS],
        write_denied_roots=[str(path) for path in WRITE_DENIED_ROOTS],
        protected_file_count=len(PROTECTED_FILES),
        process_execution=ALLOW_PROCESS_EXECUTION,
        process_profiles=["laylay", "pytest", "vscode"],
        project_python=str(PROJECT_PYTHON),
        device_id=str(_BOOT_CONFIG.get("device_id") or ""),
        device_auth=bool(
            _BOOT_CONFIG.get("device_id")
            and _BOOT_CONFIG.get("device_secret")
        ),
        ui_automation=UI_AUTOMATION_ENABLED,
        ui_profiles=sorted(str(name) for name in UI_PROFILES),
    )


@mcp.tool()
def list_files(path: str = ".") -> dict[str, Any]:
    """Lista arquivos e pastas dentro do sandbox."""
    target = _safe_path(path)
    if not target.exists():
        raise FileNotFoundError(path)
    if not target.is_dir():
        raise NotADirectoryError(path)

    entries: list[dict[str, Any]] = []
    try:
        children = sorted(
            target.iterdir(),
            key=lambda p: (not p.is_dir(), p.name.casefold()),
        )
    except PermissionError as exc:
        raise PermissionError(f"Sem permissao para listar: {target}") from exc

    for item in children:
        if len(entries) >= MAX_LIST_ENTRIES:
            break
        if not _path_allowed(item, "read"):
            continue
        info = {
            "name": item.name,
            "path": _relative(item),
            "type": "directory" if item.is_dir() else "file",
        }
        if item.is_file():
            try:
                info["size"] = item.stat().st_size
            except OSError:
                info["size"] = None
        entries.append(info)
    return _receipt("list_files", path=_relative(target), entries=entries)


def _searchable_files(base: Path):
    skipped_names = {".git", ".venv", "venv", "__pycache__", "node_modules"}
    broad_root = base == Path(base.anchor) or base == USER_PROFILE
    scanned = 0

    def onerror(_error: OSError) -> None:
        return None

    for current, dirnames, filenames in os.walk(
        base,
        topdown=True,
        onerror=onerror,
        followlinks=False,
    ):
        current_path = Path(current)
        kept_dirs: list[str] = []
        for dirname in dirnames:
            if dirname.casefold() in skipped_names:
                continue
            if broad_root and current_path == USER_PROFILE and dirname.casefold() == "appdata":
                continue
            child = current_path / dirname
            if _path_allowed(child, "read"):
                kept_dirs.append(dirname)
        dirnames[:] = kept_dirs

        for filename in filenames:
            item = current_path / filename
            if not _path_allowed(item, "read"):
                continue
            scanned += 1
            if scanned > MAX_SEARCH_FILES:
                return
            yield item


@mcp.tool()
def find_files(
    pattern: str,
    path: str = ".",
    max_results: int = 100,
) -> dict[str, Any]:
    """Busca arquivos por nome ou caminho relativo dentro do sandbox."""
    base = _safe_path(path)
    if not base.exists() or not base.is_dir():
        raise NotADirectoryError(path)

    pattern = str(pattern or "").strip()
    if not pattern:
        raise ValueError("pattern nao pode ser vazio")
    if not any(ch in pattern for ch in "*?[]"):
        pattern = f"*{pattern}*"
    max_results = max(1, min(int(max_results), MAX_SEARCH_RESULTS))

    matches: list[dict[str, Any]] = []
    scanned = 0
    for item in _searchable_files(base):
        scanned += 1
        rel = _relative(item)
        if fnmatch.fnmatch(rel.casefold(), pattern.casefold()) or fnmatch.fnmatch(
            item.name.casefold(), pattern.casefold()
        ):
            matches.append(
                {
                    "path": rel,
                    "name": item.name,
                    "size": item.stat().st_size,
                }
            )
            if len(matches) >= max_results:
                break

    return _receipt(
        "find_files",
        path=_relative(base),
        pattern=pattern,
        matches=matches,
        scanned_files=scanned,
        truncated=len(matches) >= max_results,
    )


@mcp.tool()
def search_text(
    query: str,
    path: str = ".",
    file_glob: str = "*.py",
    max_results: int = 100,
    case_sensitive: bool = False,
) -> dict[str, Any]:
    """Busca texto recursivamente em arquivos do sandbox."""
    base = _safe_path(path)
    if not base.exists() or not base.is_dir():
        raise NotADirectoryError(path)

    query = str(query or "")
    if not query:
        raise ValueError("query nao pode ser vazio")
    file_glob = str(file_glob or "*").strip() or "*"
    max_results = max(1, min(int(max_results), MAX_SEARCH_RESULTS))
    needle = query if case_sensitive else query.casefold()

    matches: list[dict[str, Any]] = []
    scanned = 0
    skipped_large = 0
    for item in _searchable_files(base):
        rel = _relative(item)
        if not (
            fnmatch.fnmatch(item.name.casefold(), file_glob.casefold())
            or fnmatch.fnmatch(rel.casefold(), file_glob.casefold())
        ):
            continue
        scanned += 1
        if item.stat().st_size > MAX_TEXT_BYTES:
            skipped_large += 1
            continue
        try:
            content = item.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for line_number, line in enumerate(content.splitlines(), start=1):
            haystack = line if case_sensitive else line.casefold()
            if needle in haystack:
                matches.append(
                    {
                        "path": rel,
                        "line": line_number,
                        "text": line[:500],
                    }
                )
                if len(matches) >= max_results:
                    return _receipt(
                        "search_text",
                        path=_relative(base),
                        query=query,
                        file_glob=file_glob,
                        matches=matches,
                        scanned_files=scanned,
                        skipped_large=skipped_large,
                        truncated=True,
                    )

    return _receipt(
        "search_text",
        path=_relative(base),
        query=query,
        file_glob=file_glob,
        matches=matches,
        scanned_files=scanned,
        skipped_large=skipped_large,
        truncated=False,
    )


@mcp.tool()
def read_text(path: str, max_chars: int = 20000) -> dict[str, Any]:
    """Le um arquivo de texto dentro do sandbox."""
    target = _safe_path(path)
    if not target.exists():
        raise FileNotFoundError(path)
    if not target.is_file():
        raise IsADirectoryError(path)

    max_chars = max(1, min(int(max_chars), MAX_TEXT_BYTES))
    raw = target.read_bytes()
    if len(raw) > MAX_TEXT_BYTES:
        raw = raw[:MAX_TEXT_BYTES]
    content = raw.decode("utf-8", errors="replace")
    truncated = len(content) > max_chars
    content = content[:max_chars]
    return _receipt(
        "read_text",
        path=_relative(target),
        content=content,
        truncated=truncated,
        sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
    )


@mcp.tool()
def read_text_range(
    path: str,
    start_line: int = 1,
    max_lines: int = 200,
) -> dict[str, Any]:
    """Le uma faixa de linhas de um arquivo UTF-8 dentro do sandbox."""
    target = _safe_path(path)
    if not target.exists():
        raise FileNotFoundError(path)
    if not target.is_file():
        raise IsADirectoryError(path)

    raw = target.read_bytes()
    if len(raw) > MAX_TEXT_BYTES:
        raise ValueError(f"Arquivo excede {MAX_TEXT_BYTES} bytes")
    content = raw.decode("utf-8", errors="replace")
    lines = content.splitlines()
    total_lines = len(lines)
    start_line = max(1, int(start_line))
    max_lines = max(1, min(int(max_lines), 1000))
    start_index = min(start_line - 1, total_lines)
    selected = lines[start_index:start_index + max_lines]

    return _receipt(
        "read_text_range",
        path=_relative(target),
        start_line=start_index + 1 if total_lines else 1,
        end_line=start_index + len(selected),
        total_lines=total_lines,
        content="\n".join(selected),
        sha256=hashlib.sha256(raw).hexdigest(),
        truncated=(start_index + len(selected)) < total_lines,
    )


@mcp.tool()
def write_text(
    path: str,
    content: str,
    overwrite: bool = False,
    expected_sha256: str = "",
) -> dict[str, Any]:
    """Cria ou substitui um arquivo UTF-8 dentro das areas de escrita."""
    target = _safe_path(path, "write")
    payload = str(content).encode("utf-8")
    if len(payload) > MAX_TEXT_BYTES:
        raise ValueError(f"Conteudo excede {MAX_TEXT_BYTES} bytes")

    if target.exists():
        if not overwrite:
            raise FileExistsError(f"Arquivo ja existe: {_relative(target)}")
        current_sha = hashlib.sha256(target.read_bytes()).hexdigest()
        expected_sha256 = str(expected_sha256 or "").strip().lower()
        if not _is_within(target, ROOT) and not expected_sha256:
            raise PermissionError(
                "Sobrescrita fora do workspace padrao exige expected_sha256"
            )
        if expected_sha256 and current_sha != expected_sha256:
            raise RuntimeError(
                f"SHA256 mudou: esperado={expected_sha256} atual={current_sha}"
            )

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)
    return _receipt(
        "write_text",
        path=_relative(target),
        bytes=len(payload),
        sha256=hashlib.sha256(payload).hexdigest(),
    )


@mcp.tool()
def stat_path(path: str = ".") -> dict[str, Any]:
    """Retorna metadados de um arquivo ou pasta dentro do sandbox."""
    target = _safe_path(path)
    if not target.exists():
        raise FileNotFoundError(path)

    stat = target.stat()
    info: dict[str, Any] = {
        "path": _relative(target),
        "type": "directory" if target.is_dir() else "file",
        "size": stat.st_size,
        "mtime": stat.st_mtime,
    }
    if target.is_file():
        info["sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
    return _receipt("stat_path", **info)


@mcp.tool()
def create_directory(path: str) -> dict[str, Any]:
    """Cria uma pasta dentro do sandbox."""
    target = _safe_path(path, "write")
    if target.exists() and not target.is_dir():
        raise FileExistsError(f"Ja existe um arquivo em: {_relative(target)}")
    target.mkdir(parents=True, exist_ok=True)
    return _receipt("create_directory", path=_relative(target))


@mcp.tool()
def copy_file(
    source: str,
    destination: str,
    overwrite: bool = False,
    expected_destination_sha256: str = "",
) -> dict[str, Any]:
    """Copia um arquivo de uma area legivel para uma area gravavel."""
    src = _safe_path(source, "read")
    dst = _safe_path(destination, "write")
    if not src.exists() or not src.is_file():
        raise FileNotFoundError(source)

    if dst.exists():
        if not overwrite:
            raise FileExistsError(destination)
        if not dst.is_file():
            raise IsADirectoryError(destination)
        current_sha = hashlib.sha256(dst.read_bytes()).hexdigest()
        expected = str(expected_destination_sha256 or "").strip().lower()
        if not _is_within(dst, ROOT) and not expected:
            raise PermissionError(
                "Sobrescrita fora do workspace padrao exige "
                "expected_destination_sha256"
            )
        if expected and current_sha != expected:
            raise RuntimeError(
                f"SHA256 mudou: esperado={expected} atual={current_sha}"
            )

    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    payload = dst.read_bytes()
    return _receipt(
        "copy_file",
        source=_relative(src),
        destination=_relative(dst),
        bytes=len(payload),
        sha256=hashlib.sha256(payload).hexdigest(),
    )


@mcp.tool()
def backup_file(path: str) -> dict[str, Any]:
    """Cria snapshot imutavel de um arquivo dentro do workspace."""
    src = _safe_path(path, "read")
    if not src.exists() or not src.is_file():
        raise FileNotFoundError(path)
    raw = src.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", src.name)[:120]
    destination = _safe_path(
        str(
            ROOT
            / ".bridge_backups"
            / f"{int(time.time() * 1000)}_{digest[:12]}_{safe_name}.bak"
        ),
        "write",
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, destination)
    return _receipt(
        "backup_file",
        source=_relative(src),
        backup_path=_relative(destination),
        bytes=len(raw),
        sha256=digest,
    )


@mcp.tool()
def restore_backup(
    backup_path: str,
    destination: str,
    expected_destination_sha256: str = "",
) -> dict[str, Any]:
    """Restaura snapshot criado pelo Bridge com protecao de destino."""
    backup = _safe_path(backup_path, "read")
    backup_root = (ROOT / ".bridge_backups").resolve(strict=False)
    if not _is_within(backup, backup_root):
        raise PermissionError("backup_path nao pertence a .bridge_backups")
    if not backup.exists() or not backup.is_file():
        raise FileNotFoundError(backup_path)

    dst = _safe_path(destination, "write")
    if dst.exists():
        if not dst.is_file():
            raise IsADirectoryError(destination)
        current_sha = hashlib.sha256(dst.read_bytes()).hexdigest()
        expected = str(expected_destination_sha256 or "").strip().lower()
        if not expected:
            raise PermissionError(
                "Restauracao sobre arquivo existente exige "
                "expected_destination_sha256"
            )
        if current_sha != expected:
            raise RuntimeError(
                f"SHA256 mudou: esperado={expected} atual={current_sha}"
            )

    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(backup, dst)
    raw = dst.read_bytes()
    return _receipt(
        "restore_backup",
        backup_path=_relative(backup),
        destination=_relative(dst),
        bytes=len(raw),
        sha256=hashlib.sha256(raw).hexdigest(),
    )


@mcp.tool()
def copy_directory(source: str, destination: str) -> dict[str, Any]:
    """Copia uma arvore de diretorios sem seguir links simbolicos."""
    src = _safe_path(source, "read")
    dst = _safe_path(destination, "write")
    if not src.exists() or not src.is_dir():
        raise NotADirectoryError(source)
    if dst.exists():
        raise FileExistsError(destination)

    copied = 0
    for current, dirnames, filenames in os.walk(
        src,
        topdown=True,
        followlinks=False,
    ):
        current_path = Path(current)
        if current_path.is_symlink():
            raise PermissionError("Links simbolicos nao sao copiados")
        relative = current_path.relative_to(src)
        target_dir = _safe_path(str(dst / relative), "write")
        target_dir.mkdir(parents=True, exist_ok=True)

        kept_dirs: list[str] = []
        for dirname in dirnames:
            child = current_path / dirname
            if child.is_symlink():
                continue
            if _path_allowed(child, "read"):
                kept_dirs.append(dirname)
        dirnames[:] = kept_dirs

        for filename in filenames:
            item = current_path / filename
            if item.is_symlink() or not _path_allowed(item, "read"):
                continue
            copied += 1
            if copied > MAX_COPY_FILES:
                raise RuntimeError(
                    f"Limite de {MAX_COPY_FILES} arquivos excedido"
                )
            target_file = _safe_path(
                str(target_dir / filename),
                "write",
            )
            shutil.copy2(item, target_file)

    return _receipt(
        "copy_directory",
        source=_relative(src),
        destination=_relative(dst),
        files=copied,
    )


@mcp.tool()
def delete_directory(
    path: str,
    recursive: bool = False,
    confirm_name: str = "",
) -> dict[str, Any]:
    """Remove pasta; exclusao recursiva fica restrita ao workspace padrao."""
    target = _safe_path(path, "write")
    if not target.exists() or not target.is_dir():
        raise NotADirectoryError(path)
    if target == ROOT:
        raise PermissionError("Nao e permitido remover o workspace raiz")

    if recursive:
        if not _is_within(target, ROOT):
            raise PermissionError(
                "Exclusao recursiva fora do workspace padrao nao e permitida"
            )
        if str(confirm_name) != target.name:
            raise PermissionError(
                "Exclusao recursiva exige confirm_name igual ao nome da pasta"
            )
        shutil.rmtree(target)
    else:
        target.rmdir()

    return _receipt(
        "delete_directory",
        path=_relative(target),
        recursive=bool(recursive),
    )


@mcp.tool()
def tail_file(path: str, lines: int = 100) -> dict[str, Any]:
    """Retorna as ultimas linhas de um arquivo de texto."""
    target = _safe_path(path, "read")
    if not target.exists() or not target.is_file():
        raise FileNotFoundError(path)
    raw = target.read_bytes()
    if len(raw) > MAX_TEXT_BYTES:
        raw = raw[-MAX_TEXT_BYTES:]
    text = raw.decode("utf-8", errors="replace")
    count = max(1, min(int(lines), 1000))
    selected = text.splitlines()[-count:]
    return _receipt(
        "tail_file",
        path=_relative(target),
        lines=len(selected),
        content="\n".join(selected),
        sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
    )


@mcp.tool()
def read_binary(path: str, max_bytes: int = MAX_BINARY_BYTES) -> dict[str, Any]:
    """Le arquivo binario pequeno como base64 para diagnosticos/artefatos."""
    target = _safe_path(path, "read")
    if not target.exists() or not target.is_file():
        raise FileNotFoundError(path)
    limit = max(1, min(int(max_bytes), MAX_BINARY_BYTES))
    size = target.stat().st_size
    if size > limit:
        raise ValueError(
            f"Arquivo possui {size} bytes; limite desta acao e {limit}"
        )
    raw = target.read_bytes()
    return _receipt(
        "read_binary",
        path=_relative(target),
        bytes=len(raw),
        sha256=hashlib.sha256(raw).hexdigest(),
        base64=base64.b64encode(raw).decode("ascii"),
    )


@mcp.tool()
def patch_text(
    path: str,
    old_string: str,
    new_string: str,
    expected_replacements: int = 1,
    expected_sha256: str = "",
) -> dict[str, Any]:
    """Aplica uma substituicao textual protegida por contagem e SHA opcional."""
    target = _safe_path(path, "write")
    if not target.exists():
        raise FileNotFoundError(path)
    if not target.is_file():
        raise IsADirectoryError(path)

    raw = target.read_bytes()
    if len(raw) > MAX_TEXT_BYTES:
        raise ValueError(f"Arquivo excede {MAX_TEXT_BYTES} bytes")
    current_sha = hashlib.sha256(raw).hexdigest()
    expected_sha256 = str(expected_sha256 or "").strip().lower()
    if not _is_within(target, ROOT) and not expected_sha256:
        raise PermissionError(
            "Edicao fora do workspace padrao exige expected_sha256"
        )
    if expected_sha256 and current_sha != expected_sha256:
        raise RuntimeError(
            f"SHA256 mudou: esperado={expected_sha256} atual={current_sha}"
        )

    old_string = str(old_string)
    new_string = str(new_string)
    if not old_string:
        raise ValueError("old_string nao pode ser vazio")
    expected_replacements = int(expected_replacements)
    if expected_replacements < 1 or expected_replacements > 100:
        raise ValueError("expected_replacements deve estar entre 1 e 100")

    text = raw.decode("utf-8")
    matches = text.count(old_string)
    if matches != expected_replacements:
        raise RuntimeError(
            f"Quantidade de ocorrencias inesperada: "
            f"esperado={expected_replacements} atual={matches}"
        )

    updated = text.replace(old_string, new_string)
    payload = updated.encode("utf-8")
    if len(payload) > MAX_TEXT_BYTES:
        raise ValueError(f"Conteudo final excede {MAX_TEXT_BYTES} bytes")

    temp = target.with_name(target.name + ".laylaytmp")
    temp.write_bytes(payload)
    temp.replace(target)
    return _receipt(
        "patch_text",
        path=_relative(target),
        replacements=matches,
        previous_sha256=current_sha,
        sha256=hashlib.sha256(payload).hexdigest(),
        bytes=len(payload),
    )


@mcp.tool()
def move_path(
    source: str,
    destination: str,
    expected_source_sha256: str = "",
) -> dict[str, Any]:
    """Move ou renomeia um caminho sem sobrescrever o destino."""
    src = _safe_path(source, "write")
    dst = _safe_path(destination, "write")
    if not src.exists():
        raise FileNotFoundError(source)
    if dst.exists():
        raise FileExistsError(destination)

    if not _is_within(src, ROOT):
        if not src.is_file():
            raise PermissionError(
                "Mover diretorios fora do workspace padrao nao e permitido"
            )
        current_sha = hashlib.sha256(src.read_bytes()).hexdigest()
        expected_source_sha256 = str(
            expected_source_sha256 or ""
        ).strip().lower()
        if not expected_source_sha256:
            raise PermissionError(
                "Mover arquivo fora do workspace padrao exige "
                "expected_source_sha256"
            )
        if current_sha != expected_source_sha256:
            raise RuntimeError(
                f"SHA256 mudou: esperado={expected_source_sha256} "
                f"atual={current_sha}"
            )

    dst.parent.mkdir(parents=True, exist_ok=True)
    src.rename(dst)
    return _receipt(
        "move_path",
        source=str(source).replace("\\", "/"),
        destination=_relative(dst),
    )


@mcp.tool()
def delete_file(path: str, expected_sha256: str = "") -> dict[str, Any]:
    """Apaga um arquivo em area de escrita, com protecao por SHA."""
    target = _safe_path(path, "write")
    if not target.exists():
        raise FileNotFoundError(path)
    if not target.is_file():
        raise IsADirectoryError(path)

    raw = target.read_bytes()
    current_sha = hashlib.sha256(raw).hexdigest()
    expected_sha256 = str(expected_sha256 or "").strip().lower()
    if not _is_within(target, ROOT) and not expected_sha256:
        raise PermissionError(
            "Exclusao fora do workspace padrao exige expected_sha256"
        )
    if expected_sha256 and current_sha != expected_sha256:
        raise RuntimeError(
            f"SHA256 mudou: esperado={expected_sha256} atual={current_sha}"
        )
    size = len(raw)
    relative = _relative(target)
    target.unlink()
    return _receipt(
        "delete_file",
        path=relative,
        bytes=size,
        previous_sha256=current_sha,
    )


@mcp.tool()
def check_python_syntax(path: str) -> dict[str, Any]:
    """Valida a sintaxe de um arquivo Python sem executa-lo."""
    target = _safe_path(path)
    if not target.exists():
        raise FileNotFoundError(path)
    if not target.is_file():
        raise IsADirectoryError(path)
    if target.suffix.casefold() != ".py":
        raise ValueError("Somente arquivos .py sao aceitos")

    raw = target.read_bytes()
    if len(raw) > MAX_TEXT_BYTES:
        raise ValueError(f"Arquivo excede {MAX_TEXT_BYTES} bytes")
    source = raw.decode("utf-8", errors="replace")
    try:
        compile(source, str(target), "exec")
    except SyntaxError as exc:
        return _receipt(
            "check_python_syntax",
            path=_relative(target),
            ok=False,
            line=exc.lineno,
            offset=exc.offset,
            error=exc.msg,
            text=(exc.text or "").strip(),
            sha256=hashlib.sha256(raw).hexdigest(),
        )

    return _receipt(
        "check_python_syntax",
        path=_relative(target),
        ok=True,
        sha256=hashlib.sha256(raw).hexdigest(),
    )


READONLY_COMMANDS: dict[str, list[str]] = {
    "python_version": [sys.executable, "--version"],
    "git_status": ["git", "status", "--short", "--branch"],
    "git_head": ["git", "rev-parse", "HEAD"],
    "git_diff_stat": ["git", "diff", "--stat"],
    "git_diff_check": ["git", "diff", "--check"],
}


@mcp.tool()
def run_readonly(command: str, cwd: str = ".") -> dict[str, Any]:
    """Executa um comando predefinido sem shell dentro do sandbox."""
    if command not in READONLY_COMMANDS:
        raise ValueError(
            "Comando nao permitido. Opcoes: "
            + ", ".join(sorted(READONLY_COMMANDS))
        )

    workdir = _safe_path(cwd)
    if not workdir.exists() or not workdir.is_dir():
        raise NotADirectoryError(cwd)

    if command == "python_version":
        return _receipt(
            "run_readonly",
            command=command,
            cwd=_relative(workdir),
            returncode=0,
            ok=True,
            stdout=f"Python {sys.version.split()[0]}\n",
            stderr="",
        )

    completed = subprocess.run(
        READONLY_COMMANDS[command],
        cwd=workdir,
        capture_output=True,
        text=True,
        timeout=30,
        shell=False,
    )
    return _receipt(
        "run_readonly",
        command=command,
        cwd=_relative(workdir),
        returncode=completed.returncode,
        ok=completed.returncode == 0,
        stdout=completed.stdout[-20000:],
        stderr=completed.stderr[-20000:],
    )


def _project_process_env() -> dict[str, str]:
    env = dict(os.environ)
    for key in (
        "PYTHONUSERBASE",
        "PYTHONHOME",
        "VIRTUAL_ENV",
        "__PYVENV_LAUNCHER__",
    ):
        env.pop(key, None)
    return env


def _run_sync(
    command: list[str],
    *,
    cwd: Path,
    timeout: int = 60,
    max_chars: int = 50000,
) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=max(1, min(int(timeout), 300)),
        shell=False,
        env=_project_process_env(),
    )
    return {
        "returncode": completed.returncode,
        "ok": completed.returncode == 0,
        "stdout": completed.stdout[-max_chars:],
        "stderr": completed.stderr[-max_chars:],
    }


@mcp.tool()
def run_named_command(name: str, cwd: str = ".") -> dict[str, Any]:
    """Executa comandos de desenvolvimento explicitamente permitidos."""
    workdir = _safe_path(cwd, "read")
    if not workdir.exists() or not workdir.is_dir():
        raise NotADirectoryError(cwd)

    commands: dict[str, list[str]] = {
        "git_status": ["git", "status", "--short", "--branch"],
        "git_diff_check": ["git", "diff", "--check"],
        "git_diff_stat": ["git", "diff", "--stat"],
        "git_head": ["git", "rev-parse", "HEAD"],
        "python_version": [*PROJECT_PYTHON_COMMAND, "--version"],
        "ruff_check": [*PROJECT_PYTHON_COMMAND, "-m", "ruff", "check", "."],
        "mypy": [*PROJECT_PYTHON_COMMAND, "-m", "mypy", "mente_laylay"],
    }
    name = str(name or "").strip()
    if name not in commands:
        raise ValueError(
            "Comando nomeado nao permitido. Opcoes: "
            + ", ".join(sorted(commands))
        )

    result = _run_sync(
        commands[name],
        cwd=workdir,
        timeout=180 if name in {"ruff_check", "mypy"} else 60,
    )
    return _receipt(
        "run_named_command",
        name=name,
        cwd=_relative(workdir),
        **result,
    )


@mcp.tool()
def git_diff(
    cwd: str = ".",
    path: str = "",
    staged: bool = False,
    max_chars: int = 50000,
) -> dict[str, Any]:
    """Retorna o diff Git sem alterar o repositorio."""
    workdir = _safe_path(cwd, "read")
    if not workdir.exists() or not workdir.is_dir():
        raise NotADirectoryError(cwd)

    command = ["git", "diff"]
    if staged:
        command.append("--cached")
    command.extend(["--no-ext-diff", "--"])
    if str(path or "").strip():
        target = _safe_path(str(path), "read")
        if not _is_within(target, workdir):
            raise ValueError("path deve ficar dentro do cwd")
        command.append(
            str(target.relative_to(workdir)).replace("\\", "/")
        )

    result = _run_sync(
        command,
        cwd=workdir,
        timeout=60,
        max_chars=max(1000, min(int(max_chars), 200000)),
    )
    return _receipt(
        "git_diff",
        cwd=_relative(workdir),
        staged=bool(staged),
        **result,
    )


@mcp.tool()
def git_log(
    cwd: str = ".",
    limit: int = 20,
    path: str = "",
) -> dict[str, Any]:
    """Retorna historico Git resumido sem alterar o repositorio."""
    workdir = _safe_path(cwd, "read")
    limit = max(1, min(int(limit), 100))
    command = [
        "git",
        "log",
        f"-{limit}",
        "--date=iso",
        "--pretty=format:%h%x09%ad%x09%an%x09%s",
    ]
    if str(path or "").strip():
        target = _safe_path(str(path), "read")
        if not _is_within(target, workdir):
            raise ValueError("path deve ficar dentro do cwd")
        command.extend(
            ["--", str(target.relative_to(workdir)).replace("\\", "/")]
        )

    result = _run_sync(command, cwd=workdir, timeout=60)
    return _receipt(
        "git_log",
        cwd=_relative(workdir),
        limit=limit,
        **result,
    )


def _ensure_process_execution() -> None:
    if not ALLOW_PROCESS_EXECUTION:
        raise PermissionError(
            "Execucao de processos esta desabilitada na configuracao"
        )


def _start_named_process(
    profile: str,
    *,
    cwd: str = ".",
    target: str = "",
    keyword: str = "",
    maxfail: int = 1,
) -> dict[str, Any]:
    _ensure_process_execution()
    workdir = _safe_path(cwd, "write")
    if not workdir.exists() or not workdir.is_dir():
        raise NotADirectoryError(cwd)

    profile = str(profile or "").strip().casefold()
    label = profile
    command: list[str]

    if profile == "laylay":
        entry = _safe_path("laylay.py", "read")
        if not _is_within(entry, ROOT):
            raise PermissionError("Entrada da Laylay fora do workspace")
        command = [*PROJECT_PYTHON_COMMAND, str(entry)]
        label = "Laylay"

    elif profile == "pytest":
        command = [
            *PROJECT_PYTHON_COMMAND,
            "-m",
            "pytest",
            "-q",
            f"--maxfail={max(1, min(int(maxfail), 20))}",
        ]
        if str(target or "").strip():
            test_target = _safe_path(str(target), "read")
            if not _is_within(test_target, ROOT):
                raise PermissionError(
                    "Testes so podem apontar para o workspace da Laylay"
                )
            command.append(
                str(test_target.relative_to(workdir)).replace("\\", "/")
                if _is_within(test_target, workdir)
                else str(test_target)
            )
        if str(keyword or "").strip():
            command.extend(["-k", str(keyword)[:200]])
        label = "pytest"

    elif profile == "vscode":
        executable = (
            shutil.which("code")
            or shutil.which("code.cmd")
            or str(
                USER_PROFILE
                / "AppData"
                / "Local"
                / "Programs"
                / "Microsoft VS Code"
                / "Code.exe"
            )
        )
        command = [str(executable), str(workdir)]
        label = "VS Code"

    else:
        raise ValueError(
            "Perfil de processo nao permitido. Opcoes: laylay, pytest, vscode"
        )

    return bridge_runtime.start_session(
        command,
        cwd=workdir,
        label=label,
        env=_project_process_env(),
    )


@mcp.tool()
def run_tests(
    target: str = "",
    keyword: str = "",
    maxfail: int = 1,
) -> dict[str, Any]:
    """Inicia pytest em uma sessao persistente e devolve session_id."""
    session = _start_named_process(
        "pytest",
        cwd=".",
        target=target,
        keyword=keyword,
        maxfail=maxfail,
    )
    return _receipt("run_tests", **session)


@mcp.tool()
def process_start(
    profile: str,
    cwd: str = ".",
    target: str = "",
    keyword: str = "",
    maxfail: int = 1,
) -> dict[str, Any]:
    """Inicia processo permitido em sessao gerenciada pelo Bridge."""
    session = _start_named_process(
        profile,
        cwd=cwd,
        target=target,
        keyword=keyword,
        maxfail=maxfail,
    )
    return _receipt("process_start", **session)


@mcp.tool()
def process_sessions(include_finished: bool = True) -> dict[str, Any]:
    """Lista somente sessoes iniciadas pelo proprio Bridge."""
    return _receipt(
        "process_sessions",
        sessions=bridge_runtime.list_sessions(
            include_finished=bool(include_finished)
        ),
    )


@mcp.tool()
def process_output(
    session_id: str,
    cursor: int = 0,
    max_lines: int = 200,
) -> dict[str, Any]:
    """Le apenas a saida nova de uma sessao desde um cursor."""
    data = bridge_runtime.read_output(
        str(session_id),
        cursor=int(cursor),
        max_lines=int(max_lines),
    )
    return _receipt("process_output", **data)


@mcp.tool()
def process_input(session_id: str, data: str) -> dict[str, Any]:
    """Envia stdin apenas para sessoes gerenciadas pelo Bridge."""
    text = str(data)
    if len(text) > 4096:
        raise ValueError("Entrada excede 4096 caracteres")
    result = bridge_runtime.send_input(str(session_id), text)
    return _receipt("process_input", **result)


@mcp.tool()
def process_stop(session_id: str, force: bool = False) -> dict[str, Any]:
    """Encerra uma sessao iniciada pelo proprio Bridge."""
    result = bridge_runtime.stop_session(
        str(session_id),
        force=bool(force),
    )
    return _receipt("process_stop", **result)


@mcp.tool()
def system_status() -> dict[str, Any]:
    """Retorna CPU, memoria, disco, rede e bateria do dispositivo."""
    return _receipt(
        "system_status",
        **bridge_runtime.system_metrics(Path(ROOT.anchor)),
    )


@mcp.tool()
def list_processes(
    name_filter: str = "",
    limit: int = 200,
) -> dict[str, Any]:
    """Lista processos do Windows sem expor linha de comando."""
    return _receipt(
        "list_processes",
        processes=bridge_runtime.list_processes(
            name_filter=str(name_filter or ""),
            limit=int(limit),
        ),
    )


@mcp.tool()
def list_windows(limit: int = 200) -> dict[str, Any]:
    """Lista janelas visiveis com HWND, PID, titulo e retangulo."""
    return _receipt(
        "list_windows",
        windows=bridge_runtime.list_windows(limit=int(limit)),
    )


@mcp.tool()
def focus_window(hwnd: int) -> dict[str, Any]:
    """Traz uma janela visivel para frente pelo HWND."""
    result = bridge_runtime.focus_window(int(hwnd))
    return _receipt("focus_window", **result)


@mcp.tool()
def capture_screen(
    quality: int = 60,
    max_width: int = 1280,
) -> dict[str, Any]:
    """Captura a tela em JPEG dentro da pasta de artefatos do workspace."""
    destination = _safe_path(
        str(
            ROOT
            / ".bridge_artifacts"
            / "screenshots"
            / f"screen_{uuid.uuid4().hex[:16]}.jpg"
        ),
        "write",
    )
    result = bridge_runtime.capture_screen(
        destination,
        quality=int(quality),
        max_width=int(max_width),
    )
    result["path"] = _relative(destination)
    result["sha256"] = hashlib.sha256(
        destination.read_bytes()
    ).hexdigest()
    return _receipt("capture_screen", **result)


def _ui_profile(name: str) -> dict[str, Any]:
    if not UI_AUTOMATION_ENABLED:
        raise PermissionError("UI Automation esta desabilitada")
    key = str(name or "").strip().casefold()
    if not key:
        raise ValueError("profile e obrigatorio")
    for profile_name, value in UI_PROFILES.items():
        if str(profile_name).casefold() != key:
            continue
        if not isinstance(value, dict):
            break
        return value
    raise ValueError(
        "Perfil UI nao permitido. Opcoes: "
        + ", ".join(sorted(str(x) for x in UI_PROFILES))
    )


def _ui_authorize_window(
    profile: str,
    hwnd: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    config = _ui_profile(profile)
    identity = bridge_runtime.window_identity(int(hwnd))
    process_name = str(identity.get("process_name") or "").casefold()
    title = str(identity.get("title") or "")
    allowed_processes = {
        str(item).casefold()
        for item in (config.get("process_names") or [])
        if str(item).strip()
    }
    title_needles = [
        str(item)
        for item in (config.get("title_contains") or [])
        if str(item).strip()
    ]
    if allowed_processes and process_name not in allowed_processes:
        raise PermissionError(
            f"Processo {identity.get('process_name')} nao autorizado "
            f"para profile={profile}"
        )
    if title_needles and not any(
        needle.casefold() in title.casefold()
        for needle in title_needles
    ):
        raise PermissionError(
            f"Titulo da janela nao autorizado para profile={profile}"
        )
    if not identity.get("visible"):
        raise PermissionError("Janela nao esta visivel")
    return config, identity


def _ui_allowed_types(config: dict[str, Any]) -> set[str]:
    return {
        str(item)
        for item in (config.get("invoke_control_types") or [])
        if str(item).strip()
    }


def _ui_fingerprint(
    profile: str,
    identity: dict[str, Any],
    info: dict[str, Any],
) -> str:
    payload = json.dumps(
        {
            "profile": str(profile).casefold(),
            "hwnd": int(identity["hwnd"]),
            "pid": int(identity["pid"]),
            "process_name": identity.get("process_name"),
            "title": identity.get("title"),
            "control_type": info.get("control_type"),
            "name": info.get("name"),
            "automation_id": info.get("automation_id"),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _ui_risk(
    identity: dict[str, Any],
    info: dict[str, Any],
) -> dict[str, Any]:
    haystack = " ".join(
        [
            str(identity.get("title") or ""),
            str(info.get("name") or ""),
            str(info.get("automation_id") or ""),
        ]
    ).casefold()
    matched = [
        word
        for word in UI_HIGH_RISK_KEYWORDS
        if word and word in haystack
    ]
    return {
        "level": "high" if matched else "low",
        "requires_confirmation": bool(matched),
        "matched_keywords": sorted(set(matched))[:20],
    }


@mcp.tool()
def ui_profiles() -> dict[str, Any]:
    """Lista perfis permitidos para UI Automation."""
    profiles: list[dict[str, Any]] = []
    for name, value in sorted(UI_PROFILES.items()):
        if not isinstance(value, dict):
            continue
        profiles.append(
            {
                "name": str(name),
                "process_names": [
                    str(x) for x in (value.get("process_names") or [])
                ],
                "title_contains": [
                    str(x) for x in (value.get("title_contains") or [])
                ],
                "invoke_control_types": [
                    str(x)
                    for x in (value.get("invoke_control_types") or [])
                ],
            }
        )
    return _receipt(
        "ui_profiles",
        enabled=UI_AUTOMATION_ENABLED,
        profiles=profiles,
        free_text_input=False,
        coordinate_clicks=False,
        generic_shell=False,
    )


@mcp.tool()
def ui_windows(profile: str = "") -> dict[str, Any]:
    """Lista somente janelas autorizadas pelos perfis UI."""
    requested = str(profile or "").strip()
    candidates = bridge_runtime.list_windows(limit=300)
    result: list[dict[str, Any]] = []
    profile_names = (
        [requested]
        if requested
        else [str(name) for name in UI_PROFILES]
    )
    for item in candidates:
        for name in profile_names:
            try:
                _, identity = _ui_authorize_window(
                    name,
                    int(item["hwnd"]),
                )
            except Exception:
                continue
            record = dict(identity)
            record["profile"] = name
            result.append(record)
            break
    return _receipt("ui_windows", windows=result)


@mcp.tool()
def ui_controls(
    profile: str,
    hwnd: int,
    max_depth: int = 5,
    max_items: int = 300,
) -> dict[str, Any]:
    """Lista controles UIA acionaveis, sem Document/Edit/texto livre."""
    config, identity = _ui_authorize_window(profile, int(hwnd))
    allowed = _ui_allowed_types(config)
    controls = bridge_runtime.uia_controls(
        int(hwnd),
        allowed_types=allowed,
        max_depth=int(max_depth),
        max_items=int(max_items),
    )
    return _receipt(
        "ui_controls",
        profile=profile,
        window=identity,
        controls=controls,
    )


@mcp.tool()
def ui_window_action(
    profile: str,
    hwnd: int,
    window_action: str,
) -> dict[str, Any]:
    """Foca, restaura, minimiza ou maximiza janela autorizada."""
    _ui_authorize_window(profile, int(hwnd))
    result = bridge_runtime.window_action(
        int(hwnd),
        str(window_action),
    )
    return _receipt(
        "ui_window_action",
        profile=profile,
        **result,
    )


@mcp.tool()
def ui_prepare_invoke(
    profile: str,
    hwnd: int,
    control_type: str,
    name: str = "",
    automation_id: str = "",
) -> dict[str, Any]:
    """Analisa um controle e cria challenge se a acao for de alto risco."""
    config, identity = _ui_authorize_window(profile, int(hwnd))
    allowed = _ui_allowed_types(config)
    if str(control_type) not in allowed:
        raise PermissionError(
            f"control_type nao permitido: {control_type}"
        )
    info = bridge_runtime.uia_control_info(
        int(hwnd),
        control_type=str(control_type),
        name=str(name or ""),
        automation_id=str(automation_id or ""),
    )
    risk = _ui_risk(identity, info)
    token = ""
    expires_at = None
    if risk["requires_confirmation"]:
        token = "uic_" + uuid.uuid4().hex
        expires_at = time.time() + 120.0
        fingerprint = _ui_fingerprint(profile, identity, info)
        with _UI_CHALLENGE_LOCK:
            _UI_CHALLENGES[token] = {
                "fingerprint": fingerprint,
                "expires_at": expires_at,
            }
            for old_token, value in list(_UI_CHALLENGES.items()):
                if float(value.get("expires_at") or 0) < time.time():
                    _UI_CHALLENGES.pop(old_token, None)
    return _receipt(
        "ui_prepare_invoke",
        profile=profile,
        window=identity,
        control=info,
        risk=risk,
        confirmation_token=token,
        confirmation_expires_at=expires_at,
    )


@mcp.tool()
def ui_invoke(
    profile: str,
    hwnd: int,
    control_type: str,
    name: str = "",
    automation_id: str = "",
    confirmation_token: str = "",
) -> dict[str, Any]:
    """Invoca controle UIA permitido; alto risco exige challenge valido."""
    config, identity = _ui_authorize_window(profile, int(hwnd))
    allowed = _ui_allowed_types(config)
    if str(control_type) not in allowed:
        raise PermissionError(
            f"control_type nao permitido: {control_type}"
        )
    info = bridge_runtime.uia_control_info(
        int(hwnd),
        control_type=str(control_type),
        name=str(name or ""),
        automation_id=str(automation_id or ""),
    )
    risk = _ui_risk(identity, info)
    if risk["requires_confirmation"]:
        token = str(confirmation_token or "").strip()
        if not token:
            raise PermissionError(
                "Acao UI de alto risco exige confirmation_token "
                "gerado por ui_prepare_invoke"
            )
        fingerprint = _ui_fingerprint(profile, identity, info)
        with _UI_CHALLENGE_LOCK:
            challenge = _UI_CHALLENGES.pop(token, None)
        if not challenge:
            raise PermissionError("confirmation_token invalido ou usado")
        if float(challenge.get("expires_at") or 0) < time.time():
            raise PermissionError("confirmation_token expirado")
        if challenge.get("fingerprint") != fingerprint:
            raise PermissionError(
                "confirmation_token nao corresponde a este controle"
            )

    invoked = bridge_runtime.invoke_uia_control(
        int(hwnd),
        control_type=str(control_type),
        name=str(name or ""),
        automation_id=str(automation_id or ""),
    )
    return _receipt(
        "ui_invoke",
        profile=profile,
        window=identity,
        control=invoked,
        risk=risk,
    )


@mcp.tool()
def ui_capture_window(
    profile: str,
    hwnd: int,
    quality: int = 60,
    max_width: int = 1280,
) -> dict[str, Any]:
    """Captura apenas uma janela autorizada."""
    _, identity = _ui_authorize_window(profile, int(hwnd))
    destination = _safe_path(
        str(
            ROOT
            / ".bridge_artifacts"
            / "windows"
            / f"{profile}_{uuid.uuid4().hex[:16]}.jpg"
        ),
        "write",
    )
    result = bridge_runtime.capture_window(
        int(hwnd),
        destination,
        quality=int(quality),
        max_width=int(max_width),
    )
    result["path"] = _relative(destination)
    result["sha256"] = hashlib.sha256(
        destination.read_bytes()
    ).hexdigest()
    return _receipt(
        "ui_capture_window",
        profile=profile,
        window=identity,
        **result,
    )


def _load_json_file(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return default


def _save_json_file(path: Path, value: Any) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(
        json.dumps(value, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temp.replace(path)


def _http_json(
    url: str,
    *,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 15.0,
) -> Any:
    body = None
    request_headers = {
        "Accept": "application/json",
        "User-Agent": f"LaylayDevBridge/{APP_VERSION}",
    }
    if headers:
        request_headers.update(headers)
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        request_headers["Content-Type"] = "application/json"
    request = urllib.request.Request(
        url,
        data=body,
        headers=request_headers,
        method=method,
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read()
    return json.loads(raw.decode("utf-8")) if raw else {}


def _execute_remote_action(
    action: str,
    args: dict[str, Any],
) -> dict[str, Any]:
    if action == "ping":
        return ping()
    if action == "system_info":
        return system_info()
    if action == "access_info":
        return access_info()
    if action == "list_files":
        return list_files(path=str(args.get("path") or "."))
    if action == "find_files":
        return find_files(
            pattern=str(args.get("pattern") or ""),
            path=str(args.get("path") or "."),
            max_results=int(args.get("max_results") or 100),
        )
    if action == "search_text":
        return search_text(
            query=str(args.get("query") or ""),
            path=str(args.get("path") or "."),
            file_glob=str(args.get("file_glob") or "*.py"),
            max_results=int(args.get("max_results") or 100),
            case_sensitive=bool(args.get("case_sensitive", False)),
        )
    if action == "stat_path":
        return stat_path(path=str(args.get("path") or "."))
    if action == "read_text":
        return read_text(
            path=str(args.get("path") or ""),
            max_chars=int(args.get("max_chars") or 20000),
        )
    if action == "read_text_range":
        return read_text_range(
            path=str(args.get("path") or ""),
            start_line=int(args.get("start_line") or 1),
            max_lines=int(args.get("max_lines") or 200),
        )
    if action == "write_text":
        return write_text(
            path=str(args.get("path") or ""),
            content=str(args.get("content") or ""),
            overwrite=bool(args.get("overwrite", False)),
            expected_sha256=str(args.get("expected_sha256") or ""),
        )
    if action == "patch_text":
        return patch_text(
            path=str(args.get("path") or ""),
            old_string=str(args.get("old_string") or ""),
            new_string=str(args.get("new_string") or ""),
            expected_replacements=int(args.get("expected_replacements") or 1),
            expected_sha256=str(args.get("expected_sha256") or ""),
        )
    if action == "create_directory":
        return create_directory(path=str(args.get("path") or ""))
    if action == "copy_file":
        return copy_file(
            source=str(args.get("source") or ""),
            destination=str(args.get("destination") or ""),
            overwrite=bool(args.get("overwrite", False)),
            expected_destination_sha256=str(
                args.get("expected_destination_sha256") or ""
            ),
        )
    if action == "backup_file":
        return backup_file(path=str(args.get("path") or ""))
    if action == "restore_backup":
        return restore_backup(
            backup_path=str(args.get("backup_path") or ""),
            destination=str(args.get("destination") or ""),
            expected_destination_sha256=str(
                args.get("expected_destination_sha256") or ""
            ),
        )
    if action == "copy_directory":
        return copy_directory(
            source=str(args.get("source") or ""),
            destination=str(args.get("destination") or ""),
        )
    if action == "move_path":
        return move_path(
            source=str(args.get("source") or ""),
            destination=str(args.get("destination") or ""),
            expected_source_sha256=str(args.get("expected_source_sha256") or ""),
        )
    if action == "delete_file":
        return delete_file(
            path=str(args.get("path") or ""),
            expected_sha256=str(args.get("expected_sha256") or ""),
        )
    if action == "delete_directory":
        return delete_directory(
            path=str(args.get("path") or ""),
            recursive=bool(args.get("recursive", False)),
            confirm_name=str(args.get("confirm_name") or ""),
        )
    if action == "tail_file":
        return tail_file(
            path=str(args.get("path") or ""),
            lines=int(args.get("lines") or 100),
        )
    if action == "read_binary":
        return read_binary(
            path=str(args.get("path") or ""),
            max_bytes=int(args.get("max_bytes") or MAX_BINARY_BYTES),
        )
    if action == "check_python_syntax":
        return check_python_syntax(
            path=str(args.get("path") or ""),
        )
    if action == "run_readonly":
        return run_readonly(
            command=str(args.get("command") or ""),
            cwd=str(args.get("cwd") or "."),
        )
    if action == "run_named_command":
        return run_named_command(
            name=str(args.get("name") or ""),
            cwd=str(args.get("cwd") or "."),
        )
    if action == "git_diff":
        return git_diff(
            cwd=str(args.get("cwd") or "."),
            path=str(args.get("path") or ""),
            staged=bool(args.get("staged", False)),
            max_chars=int(args.get("max_chars") or 50000),
        )
    if action == "git_log":
        return git_log(
            cwd=str(args.get("cwd") or "."),
            limit=int(args.get("limit") or 20),
            path=str(args.get("path") or ""),
        )
    if action == "run_tests":
        return run_tests(
            target=str(args.get("target") or ""),
            keyword=str(args.get("keyword") or ""),
            maxfail=int(args.get("maxfail") or 1),
        )
    if action == "process_start":
        return process_start(
            profile=str(args.get("profile") or ""),
            cwd=str(args.get("cwd") or "."),
            target=str(args.get("target") or ""),
            keyword=str(args.get("keyword") or ""),
            maxfail=int(args.get("maxfail") or 1),
        )
    if action == "process_sessions":
        return process_sessions(
            include_finished=bool(args.get("include_finished", True)),
        )
    if action == "process_output":
        return process_output(
            session_id=str(args.get("session_id") or ""),
            cursor=int(args.get("cursor") or 0),
            max_lines=int(args.get("max_lines") or 200),
        )
    if action == "process_input":
        return process_input(
            session_id=str(args.get("session_id") or ""),
            data=str(args.get("data") or ""),
        )
    if action == "process_stop":
        return process_stop(
            session_id=str(args.get("session_id") or ""),
            force=bool(args.get("force", False)),
        )
    if action == "system_status":
        return system_status()
    if action == "list_processes":
        return list_processes(
            name_filter=str(args.get("name_filter") or ""),
            limit=int(args.get("limit") or 200),
        )
    if action == "list_windows":
        return list_windows(limit=int(args.get("limit") or 200))
    if action == "focus_window":
        return focus_window(hwnd=int(args.get("hwnd") or 0))
    if action == "capture_screen":
        return capture_screen(
            quality=int(args.get("quality") or 60),
            max_width=int(args.get("max_width") or 1280),
        )
    if action == "ui_profiles":
        return ui_profiles()
    if action == "ui_windows":
        return ui_windows(profile=str(args.get("profile") or ""))
    if action == "ui_controls":
        return ui_controls(
            profile=str(args.get("profile") or ""),
            hwnd=int(args.get("hwnd") or 0),
            max_depth=int(args.get("max_depth") or 5),
            max_items=int(args.get("max_items") or 300),
        )
    if action == "ui_window_action":
        return ui_window_action(
            profile=str(args.get("profile") or ""),
            hwnd=int(args.get("hwnd") or 0),
            window_action=str(args.get("window_action") or ""),
        )
    if action == "ui_prepare_invoke":
        return ui_prepare_invoke(
            profile=str(args.get("profile") or ""),
            hwnd=int(args.get("hwnd") or 0),
            control_type=str(args.get("control_type") or ""),
            name=str(args.get("name") or ""),
            automation_id=str(args.get("automation_id") or ""),
        )
    if action == "ui_invoke":
        return ui_invoke(
            profile=str(args.get("profile") or ""),
            hwnd=int(args.get("hwnd") or 0),
            control_type=str(args.get("control_type") or ""),
            name=str(args.get("name") or ""),
            automation_id=str(args.get("automation_id") or ""),
            confirmation_token=str(
                args.get("confirmation_token") or ""
            ),
        )
    if action == "ui_capture_window":
        return ui_capture_window(
            profile=str(args.get("profile") or ""),
            hwnd=int(args.get("hwnd") or 0),
            quality=int(args.get("quality") or 60),
            max_width=int(args.get("max_width") or 1280),
        )
    raise ValueError(f"Acao remota nao permitida: {action}")


def _remote_receipt(
    action: str,
    args: dict[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        data = _execute_remote_action(action, dict(args or {}))
        return {
            "device": socket.gethostname(),
            "action": action,
            "executed": bool(data.get("executed", True)),
            "confirmed": data.get("confirmed", True),
            "data": data,
        }
    except Exception as exc:
        return {
            "device": socket.gethostname(),
            "action": action,
            "executed": False,
            "confirmed": False,
            "data": {
                "error_type": type(exc).__name__,
                "error": str(exc)[:1000],
            },
        }


def _relay_auth_headers(config: dict[str, Any]) -> dict[str, str]:
    device_id = str(config.get("device_id") or "").strip()
    device_secret = str(config.get("device_secret") or "")
    if device_id and device_secret:
        return {
            "X-Bridge-Device-Id": device_id,
            "X-Bridge-Device-Secret": device_secret,
        }
    token = str(config.get("token") or "").strip()
    if token:
        return {"X-Bridge-Token": token}
    return {}


def _post_remote_receipt_payload(
    relay_url: str,
    auth_headers: dict[str, str],
    request_id: str,
    payload: dict[str, Any],
) -> None:
    endpoint = relay_url.rstrip("/") + "/receipt/" + urllib.parse.quote(
        request_id,
        safe="",
    )
    _http_json(
        endpoint,
        method="POST",
        payload=payload,
        headers=auth_headers,
    )


def _post_remote_receipt(
    relay_url: str,
    auth_headers: dict[str, str],
    request_id: str,
    action: str,
    args: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = _remote_receipt(action, args)
    _post_remote_receipt_payload(
        relay_url,
        auth_headers,
        request_id,
        payload,
    )
    return payload


def _poll_remote_once(config: dict[str, Any], processed: set[str]) -> bool:
    repo = str(config.get("repo") or "").strip()
    allowed_author = str(config.get("allowed_author") or "").strip()
    relay_url = str(config.get("relay_url") or "").strip()
    device = str(config.get("device") or socket.gethostname()).strip()
    device_id = str(config.get("device_id") or "").strip()
    auth_headers = _relay_auth_headers(config)
    if not all((repo, allowed_author, relay_url, device)) or not auth_headers:
        return False

    issues_url = (
        f"https://api.github.com/repos/{repo}/issues"
        "?state=open&per_page=30&sort=created&direction=desc"
    )
    issues = _http_json(issues_url)
    if not isinstance(issues, list):
        return False

    changed = False
    for issue in reversed(issues):
        if not isinstance(issue, dict) or "pull_request" in issue:
            continue
        if not str(issue.get("title") or "").startswith("[LAYLAY-BRIDGE]"):
            continue
        author = str((issue.get("user") or {}).get("login") or "")
        if author.casefold() != allowed_author.casefold():
            continue
        try:
            command = json.loads(str(issue.get("body") or ""))
        except Exception:
            continue
        if not isinstance(command, dict):
            continue
        if command.get("protocol") != REMOTE_PROTOCOL:
            continue

        request_id = str(command.get("request_id") or "")
        action = str(command.get("action") or "")
        target = str(command.get("device") or "*")
        args = command.get("args")
        if not isinstance(args, dict):
            args = {}
        if (
            not REQUEST_ID_RE.fullmatch(request_id)
            or request_id in processed
            or action not in REMOTE_ACTIONS
            or target not in {
                "*",
                device,
                socket.gethostname(),
                device_id,
            }
        ):
            continue

        _post_remote_receipt(
            relay_url,
            auth_headers,
            request_id,
            action,
            args,
        )
        processed.add(request_id)
        changed = True
        print(
            f"[REMOTE] receipt request={request_id} "
            f"action={action} issue={issue.get('number')}"
        )
    return changed



def _save_remote_tracking(
    processed: set[str],
    pending: dict[str, dict[str, Any]],
) -> None:
    _save_json_file(REMOTE_STATE_PATH, sorted(processed)[-500:])
    _save_json_file(REMOTE_PENDING_PATH, pending)


def _flush_pending_receipts(
    config: dict[str, Any],
    processed: set[str],
    pending: dict[str, dict[str, Any]],
) -> bool:
    relay_url = str(config.get("relay_url") or "").strip()
    auth_headers = _relay_auth_headers(config)
    if not auth_headers:
        return False
    changed = False
    for request_id, payload in list(pending.items()):
        _post_remote_receipt_payload(
            relay_url,
            auth_headers,
            request_id,
            payload,
        )
        processed.add(request_id)
        pending.pop(request_id, None)
        _save_remote_tracking(processed, pending)
        changed = True
    return changed


def _poll_relay_once(
    config: dict[str, Any],
    processed: set[str],
    pending: dict[str, dict[str, Any]],
) -> bool:
    relay_url = str(config.get("relay_url") or "").strip()
    device = str(config.get("device") or socket.gethostname()).strip()
    device_id = str(config.get("device_id") or "").strip()
    auth_headers = _relay_auth_headers(config)
    if not all((relay_url, device)) or not auth_headers:
        return False

    changed = _flush_pending_receipts(config, processed, pending)
    endpoint = relay_url.rstrip("/") + "/command/next?" + urllib.parse.urlencode(
        {
            "device": device,
            "device_id": device_id,
            "wait_seconds": 20,
        }
    )
    response = _http_json(
        endpoint,
        headers=auth_headers,
        timeout=25.0,
    )
    command = response.get("command") if isinstance(response, dict) else None
    if not isinstance(command, dict):
        return changed

    request_id = str(command.get("request_id") or "")
    action = str(command.get("action") or "")
    args = command.get("args")
    if not isinstance(args, dict):
        args = {}
    if (
        command.get("protocol") != REMOTE_PROTOCOL
        or not REQUEST_ID_RE.fullmatch(request_id)
        or action not in REMOTE_ACTIONS
    ):
        return changed
    if request_id in processed or request_id in pending:
        return changed

    print(
        f"[REMOTE] comando recebido request={request_id} action={action}",
        flush=True,
    )
    payload = _remote_receipt(action, args)
    data = payload.get("data") if isinstance(payload, dict) else {}
    if isinstance(data, dict):
        safe_parts: list[str] = []
        for key in (
            "path",
            "source",
            "destination",
            "backup_path",
            "session_id",
            "pid",
            "returncode",
            "ok",
        ):
            value = data.get(key)
            if value not in (None, ""):
                safe_parts.append(f"{key}={value}")
        status = "OK" if payload.get("executed") else "ERRO"
        suffix = (" " + " ".join(safe_parts)) if safe_parts else ""
        print(
            f"[REMOTE] resultado {status} action={action}{suffix}",
            flush=True,
        )
    pending[request_id] = payload
    _save_remote_tracking(processed, pending)
    _post_remote_receipt_payload(
        relay_url,
        auth_headers,
        request_id,
        payload,
    )
    processed.add(request_id)
    pending.pop(request_id, None)
    _save_remote_tracking(processed, pending)
    print(f"[REMOTE] relay receipt request={request_id} action={action}")
    return True


def _remote_loop(config: dict[str, Any]) -> None:
    processed = set(
        str(item)
        for item in _load_json_file(REMOTE_STATE_PATH, [])
        if isinstance(item, str)
    )
    loaded_pending = _load_json_file(REMOTE_PENDING_PATH, {})
    pending = loaded_pending if isinstance(loaded_pending, dict) else {}
    transport = str(
        config.get("command_transport") or "github"
    ).strip().casefold()
    if transport == "relay":
        interval = max(0.1, float(config.get("poll_seconds") or 0.2))
    else:
        transport = "github"
        interval = max(60, int(config.get("poll_seconds") or 65))
    print(
        f"[REMOTE] habilitado transport={transport} "
        f"device={config.get('device') or socket.gethostname()} "
        f"interval={interval}s"
    )
    while True:
        try:
            if transport == "relay":
                _poll_relay_once(config, processed, pending)
            elif _poll_remote_once(config, processed):
                _save_json_file(
                    REMOTE_STATE_PATH,
                    sorted(processed)[-500:],
                )
        except Exception as exc:
            print(f"[REMOTE] erro: {type(exc).__name__}: {exc}")
        time.sleep(interval)


def _start_remote_agent() -> None:
    config = _load_json_file(REMOTE_CONFIG_PATH, {})
    if not isinstance(config, dict) or not config.get("enabled"):
        print("[REMOTE] desabilitado")
        return
    threading.Thread(
        target=_remote_loop,
        args=(config,),
        name="laylay-remote-agent",
        daemon=True,
    ).start()


if __name__ == "__main__":
    print(f"{APP_NAME} v{APP_VERSION}")
    print(f"Sandbox: {ROOT}")
    print(f"MCP: http://127.0.0.1:{PORT}/mcp")
    _start_remote_agent()
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=PORT,
        stateless_http=True,
        json_response=True,
    )