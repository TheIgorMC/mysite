import json
import os
import re
import secrets
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from threading import Lock

from flask import Flask, jsonify, request, send_from_directory, session
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
LOCAL_DATA_DIR = BASE_DIR / "local_data"
TRACKED_CONTENT_FILE = BASE_DIR / "content.json"
TRACKED_REGISTRATIONS_FILE = BASE_DIR / "registrations.json"
TRACKED_LOCALES_DIR = BASE_DIR / "locales"
TRACKED_ASSETS_DIR = BASE_DIR / "assets"

CONTENT_FILE = LOCAL_DATA_DIR / "content.json"
REGISTRATIONS_FILE = LOCAL_DATA_DIR / "registrations.json"
LOCALES_DIR = LOCAL_DATA_DIR / "locales"
ASSETS_DIR = LOCAL_DATA_DIR / "assets"
AUTH_FILE = LOCAL_DATA_DIR / "auth.json"

SUPPORTED_LOCALES = ("en", "it", "fr", "es")
ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp"}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
VALID_INTENTS = {"stay_posted", "buy_if_price", "contribute"}
WRITE_LOCK = Lock()
CONTENT_FALLBACK = {"updates": [], "timeline": [], "milestones": [], "planned_work": [], "gallery": []}
AUTH_SESSION_KEY = "orion_admin_authenticated"
LIST_IDENTITY_KEYS = {
    "updates": ("date", "title"),
    "timeline": ("date", "label"),
    "milestones": ("target", "name"),
    "planned_work": ("window", "task"),
    "gallery": ("src",),
    "registrations": ("id",),
}

app = Flask(__name__)


def _atomic_write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.flush()
        os.fsync(handle.fileno())


def _load_json(path: Path, fallback):
    if not path.exists():
        return deepcopy(fallback)
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (json.JSONDecodeError, OSError):
        return deepcopy(fallback)


def _locale_identity(value):
    if isinstance(value, dict):
        for candidate in ("en", "it", "fr", "es"):
            text = value.get(candidate)
            if text:
                return str(text)
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    if isinstance(value, list):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return value


def _item_identity(item, path: str):
    if not isinstance(item, dict):
        return ("primitive", item)

    path_key = path.split(".")[-1]
    identity_fields = LIST_IDENTITY_KEYS.get(path_key)
    if not identity_fields:
        return ("dict", json.dumps(item, ensure_ascii=False, sort_keys=True))

    parts = []
    for field in identity_fields:
        parts.append(_locale_identity(item.get(field)))
    return (path_key, tuple(parts))


def _merge_json(existing, source, path: str = ""):
    if isinstance(existing, dict) and isinstance(source, dict):
        merged = deepcopy(existing)
        for key, value in source.items():
            if key not in merged:
                merged[key] = deepcopy(value)
            else:
                child_path = f"{path}.{key}" if path else key
                merged[key] = _merge_json(merged[key], value, child_path)
        return merged
    if isinstance(existing, list) and isinstance(source, list):
        if all(not isinstance(item, dict) for item in existing + source):
            merged = list(existing)
            for item in source:
                if item not in merged:
                    merged.append(deepcopy(item))
            return merged

        merged = list(existing)
        index_by_identity = {}
        for index, item in enumerate(merged):
            index_by_identity[_item_identity(item, path)] = index

        for source_item in source:
            identity = _item_identity(source_item, path)
            if identity in index_by_identity:
                target_index = index_by_identity[identity]
                merged[target_index] = _merge_json(merged[target_index], source_item, path)
            else:
                index_by_identity[identity] = len(merged)
                merged.append(deepcopy(source_item))

        return merged
    return deepcopy(existing if existing is not None else source)


def _seed_json_file(local_path: Path, source_path: Path, fallback, path: str):
    source = _load_json(source_path, fallback)
    local = _load_json(local_path, source)
    merged = _merge_json(local, source, path)
    _atomic_write_json(local_path, merged)
    return merged


def _ensure_auth_config() -> dict:
    default_config = {"password_hash": "", "session_secret_key": secrets.token_urlsafe(48)}
    config = _load_json(AUTH_FILE, default_config)
    if not isinstance(config, dict):
        config = deepcopy(default_config)

    changed = False
    if not config.get("session_secret_key"):
        config["session_secret_key"] = secrets.token_urlsafe(48)
        changed = True
    if "password_hash" not in config:
        config["password_hash"] = ""
        changed = True

    if changed or not AUTH_FILE.exists():
        _atomic_write_json(AUTH_FILE, config)

    return config


def _ensure_data_files() -> None:
    LOCAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOCALES_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    _seed_json_file(CONTENT_FILE, TRACKED_CONTENT_FILE, CONTENT_FALLBACK, "content")
    _seed_json_file(REGISTRATIONS_FILE, TRACKED_REGISTRATIONS_FILE, [], "registrations")
    for lang in SUPPORTED_LOCALES:
        _seed_json_file(LOCALES_DIR / f"{lang}.json", TRACKED_LOCALES_DIR / f"{lang}.json", {}, f"locales.{lang}")


_ensure_data_files()
AUTH_CONFIG = _ensure_auth_config()
app.secret_key = AUTH_CONFIG["session_secret_key"]
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")


def _json_response(error: str, status: int):
    return jsonify({"error": error}), status


def _is_admin_authenticated() -> bool:
    return bool(session.get(AUTH_SESSION_KEY))


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not _is_admin_authenticated():
            return _json_response("Unauthorized", 401)
        return view_func(*args, **kwargs)

    return wrapper


def _read_content_file():
    content = _load_json(CONTENT_FILE, CONTENT_FALLBACK)
    if not isinstance(content, dict):
        return deepcopy(CONTENT_FALLBACK)
    normalized = deepcopy(CONTENT_FALLBACK)
    normalized.update({k: content.get(k, []) for k in normalized.keys()})
    return normalized


def _read_locales_file():
    locales = {}
    for lang in SUPPORTED_LOCALES:
        data = _load_json(LOCALES_DIR / f"{lang}.json", {})
        locales[lang] = data if isinstance(data, dict) else {}
    return locales


def _collect_assets():
    assets = {}
    for source, directory in (("tracked", TRACKED_ASSETS_DIR), ("local", ASSETS_DIR)):
        if not directory.exists():
            continue
        for file_path in sorted(directory.iterdir()):
            if not file_path.is_file() or file_path.suffix.lower() not in ALLOWED_IMAGE_EXTS:
                continue
            assets[file_path.name] = {
                "name": file_path.name,
                "url": f"assets/{file_path.name}",
                "size": file_path.stat().st_size,
                "source": source,
                "deletable": source == "local",
            }
    return [assets[name] for name in sorted(assets)]


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/api/auth/status")
def auth_status():
    return jsonify({"configured": bool(AUTH_CONFIG.get("password_hash")), "authenticated": _is_admin_authenticated()})


@app.post("/api/auth/login")
def auth_login():
    payload = request.get_json(silent=True) or {}
    password = str(payload.get("password", ""))

    if not AUTH_CONFIG.get("password_hash"):
        return _json_response("Admin password is not configured", 503)
    if not password or not check_password_hash(AUTH_CONFIG["password_hash"], password):
        return _json_response("Invalid password", 401)

    session[AUTH_SESSION_KEY] = True
    session.permanent = True
    return jsonify({"ok": True})


@app.post("/api/auth/logout")
def auth_logout():
    session.pop(AUTH_SESSION_KEY, None)
    return jsonify({"ok": True})


@app.get("/api/content")
def get_content():
    return jsonify(_read_content_file())


@app.get("/api/locales")
def get_locales():
    return jsonify(_read_locales_file())


@app.post("/api/register")
def register_interest():
    payload = request.get_json(silent=True) or {}

    name = str(payload.get("name", "")).strip()
    email = str(payload.get("email", "")).strip().lower()
    interest = str(payload.get("interest", "")).strip()
    message = str(payload.get("message", "")).strip()
    language = str(payload.get("language", "en")).strip().lower() or "en"
    intent = str(payload.get("intent", "stay_posted")).strip().lower()
    max_price_raw = payload.get("max_price", None)

    if not name or len(name) > 120:
        return _json_response("Invalid name", 400)
    if not EMAIL_RE.match(email):
        return _json_response("Invalid email", 400)
    if not interest or len(interest) > 200:
        return _json_response("Invalid interest", 400)
    if len(message) > 1000:
        return _json_response("Message too long", 400)
    if intent not in VALID_INTENTS:
        intent = "stay_posted"

    max_price = None
    if max_price_raw is not None:
        try:
            max_price = float(max_price_raw)
            if max_price < 0 or max_price > 99999:
                max_price = None
        except (TypeError, ValueError):
            max_price = None

    record = {
        "id": str(uuid.uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "name": name,
        "email": email,
        "interest": interest,
        "message": message,
        "intent": intent,
        "max_price": max_price,
        "language": language,
        "ip": request.headers.get("X-Forwarded-For", request.remote_addr),
        "user_agent": request.headers.get("User-Agent", "unknown"),
    }

    with WRITE_LOCK:
        registrations = _load_json(REGISTRATIONS_FILE, [])
        if not isinstance(registrations, list):
            registrations = []
        registrations.append(record)
        _atomic_write_json(REGISTRATIONS_FILE, registrations)

    return jsonify({"ok": True, "id": record["id"]})


@app.get("/api/registrations/export")
def export_registrations():
    admin_token = os.getenv("ORION_ADMIN_TOKEN", "").strip()
    provided = request.args.get("token", "").strip()

    if admin_token and provided != admin_token:
        return _json_response("Unauthorized", 401)

    registrations = _load_json(REGISTRATIONS_FILE, [])
    return jsonify(registrations if isinstance(registrations, list) else [])


@app.put("/api/content")
@admin_required
def put_content():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _json_response("Expected JSON object", 400)

    allowed_keys = {"updates", "timeline", "milestones", "planned_work", "gallery"}
    for key in allowed_keys:
        if key in payload and not isinstance(payload[key], list):
            return _json_response(f"'{key}' must be a list", 400)

    with WRITE_LOCK:
        existing = _read_content_file()
        for key in allowed_keys:
            if key in payload:
                existing[key] = payload[key]
        _atomic_write_json(CONTENT_FILE, existing)

    return jsonify({"ok": True})


@app.put("/api/locales")
@admin_required
def put_locales():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _json_response("Expected JSON object", 400)

    normalized = {}
    for lang in SUPPORTED_LOCALES:
        value = payload.get(lang, {})
        if not isinstance(value, dict):
            return _json_response(f"'{lang}' must be an object", 400)
        normalized[lang] = {str(k): str(v) for k, v in value.items()}

    with WRITE_LOCK:
        for lang in SUPPORTED_LOCALES:
            _atomic_write_json(LOCALES_DIR / f"{lang}.json", normalized[lang])

    return jsonify({"ok": True})


@app.get("/api/assets")
def list_assets():
    return jsonify(_collect_assets())


@app.post("/api/assets/upload")
@admin_required
def upload_asset():
    if "file" not in request.files:
        return _json_response("No file provided", 400)
    file_obj = request.files["file"]
    if not file_obj.filename:
        return _json_response("Empty filename", 400)

    filename = secure_filename(file_obj.filename)
    if not filename:
        return _json_response("Invalid filename", 400)
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTS:
        return _json_response("File type not allowed", 400)

    data = file_obj.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        return _json_response("File too large (max 10 MB)", 400)

    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    (ASSETS_DIR / filename).write_bytes(data)
    return jsonify({"ok": True, "url": f"assets/{filename}", "name": filename})


@app.delete("/api/assets/<path:filename>")
@admin_required
def delete_asset(filename):
    filename = secure_filename(Path(filename).name)
    if not filename:
        return _json_response("Invalid filename", 400)

    local_target = ASSETS_DIR / filename
    tracked_target = TRACKED_ASSETS_DIR / filename

    if local_target.exists() and local_target.is_file():
        local_target.unlink()
        return jsonify({"ok": True})

    if tracked_target.exists() and tracked_target.is_file():
        return _json_response("Tracked assets cannot be deleted from the CMS", 403)

    return _json_response("Not found", 404)


@app.get("/edit")
def edit_ui():
    return send_from_directory(BASE_DIR, "edit.html")


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_files(path: str):
    if path.startswith("api/") or path.startswith("local_data/"):
        return _json_response("Not found", 404)

    if path.startswith("assets/"):
        asset_name = secure_filename(Path(path).name)
        if not asset_name:
            return _json_response("Not found", 404)

        local_asset = ASSETS_DIR / asset_name
        if local_asset.exists() and local_asset.is_file():
            return send_from_directory(ASSETS_DIR, asset_name)

        tracked_asset = TRACKED_ASSETS_DIR / asset_name
        if tracked_asset.exists() and tracked_asset.is_file():
            return send_from_directory(TRACKED_ASSETS_DIR, asset_name)

        return _json_response("Not found", 404)

    if path:
        target = BASE_DIR / path
        if target.exists() and target.is_file() and LOCAL_DATA_DIR not in target.parents:
            return send_from_directory(BASE_DIR, path)

    return send_from_directory(BASE_DIR, "index.html")


if __name__ == "__main__":
    port = int(os.getenv("PORT", "1080"))
    host = os.getenv("HOST", "127.0.0.1")
    app.run(host=host, port=port)
