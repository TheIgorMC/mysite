import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
CONTENT_FILE = BASE_DIR / "content.json"
REGISTRATIONS_FILE = BASE_DIR / "registrations.json"
LOCALES_DIR = BASE_DIR / "locales"
ASSETS_DIR = BASE_DIR / "assets"
SUPPORTED_LOCALES = ("en", "it", "fr", "es")
ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp"}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
VALID_INTENTS = {"stay_posted", "buy_if_price", "contribute"}
WRITE_LOCK = Lock()

app = Flask(__name__)


def _atomic_write_json(path: Path, data) -> None:
    # Write directly with an explicit flush+fsync. The caller holds WRITE_LOCK
    # so concurrent writes are already serialised. A temp-file rename is not
    # used because Docker bind-mount volumes return EBUSY on os.replace().
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())


def _load_json(path: Path, fallback):
    if not path.exists():
        _atomic_write_json(path, fallback)
        return fallback
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        _atomic_write_json(path, fallback)
        return fallback


def _ensure_data_files() -> None:
    _load_json(CONTENT_FILE, {"updates": [], "milestones": [], "planned_work": []})
    _load_json(REGISTRATIONS_FILE, [])
    LOCALES_DIR.mkdir(parents=True, exist_ok=True)
    for lang in SUPPORTED_LOCALES:
        _load_json(LOCALES_DIR / f"{lang}.json", {})


# Ensure data files exist whether the app is started via `python app.py` or imported by Gunicorn.
_ensure_data_files()


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/api/content")
def get_content():
    content = _load_json(CONTENT_FILE, {"updates": [], "milestones": [], "planned_work": []})
    return jsonify(content)


@app.get("/api/locales")
def get_locales():
    locales = {}
    for lang in SUPPORTED_LOCALES:
        data = _load_json(LOCALES_DIR / f"{lang}.json", {})
        locales[lang] = data if isinstance(data, dict) else {}
    return jsonify(locales)


@app.post("/api/register")
def register_interest():
    payload = request.get_json(silent=True) or {}

    name     = str(payload.get("name",     "")).strip()
    email    = str(payload.get("email",    "")).strip().lower()
    interest = str(payload.get("interest", "")).strip()
    message  = str(payload.get("message",  "")).strip()
    language = str(payload.get("language", "en")).strip().lower() or "en"
    intent   = str(payload.get("intent",   "stay_posted")).strip().lower()
    max_price_raw = payload.get("max_price", None)

    if not name or len(name) > 120:
        return jsonify({"error": "Invalid name"}), 400
    if not EMAIL_RE.match(email):
        return jsonify({"error": "Invalid email"}), 400
    if not interest or len(interest) > 200:
        return jsonify({"error": "Invalid interest"}), 400
    if len(message) > 1000:
        return jsonify({"error": "Message too long"}), 400
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
        "id":         str(uuid.uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "name":       name,
        "email":      email,
        "interest":   interest,
        "message":    message,
        "intent":     intent,
        "max_price":  max_price,
        "language":   language,
        "ip":         request.headers.get("X-Forwarded-For", request.remote_addr),
        "user_agent": request.headers.get("User-Agent", "unknown"),
    }

    with WRITE_LOCK:
        registrations = _load_json(REGISTRATIONS_FILE, [])
        registrations.append(record)
        _atomic_write_json(REGISTRATIONS_FILE, registrations)

    return jsonify({"ok": True, "id": record["id"]})


@app.get("/api/registrations/export")
def export_registrations():
    admin_token = os.getenv("ORION_ADMIN_TOKEN", "").strip()
    provided    = request.args.get("token", "").strip()

    if admin_token and provided != admin_token:
        return jsonify({"error": "Unauthorized"}), 401

    registrations = _load_json(REGISTRATIONS_FILE, [])
    return jsonify(registrations)


@app.put("/api/content")
def put_content():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Expected JSON object"}), 400

    KNOWN_KEYS = {"updates", "timeline", "milestones", "planned_work", "gallery"}
    for key in KNOWN_KEYS:
        if key in payload and not isinstance(payload[key], list):
            return jsonify({"error": f"'{key}' must be a list"}), 400

    # Preserve any extra keys already in the file, then overwrite known ones
    with WRITE_LOCK:
        existing = _load_json(CONTENT_FILE, {})
        existing.update({k: payload[k] for k in KNOWN_KEYS if k in payload})
        _atomic_write_json(CONTENT_FILE, existing)

    return jsonify({"ok": True})


@app.put("/api/locales")
def put_locales():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Expected JSON object"}), 400

    normalized = {}
    for lang in SUPPORTED_LOCALES:
        value = payload.get(lang, {})
        if not isinstance(value, dict):
            return jsonify({"error": f"'{lang}' must be an object"}), 400
        normalized[lang] = {str(k): str(v) for k, v in value.items()}

    with WRITE_LOCK:
        for lang in SUPPORTED_LOCALES:
            _atomic_write_json(LOCALES_DIR / f"{lang}.json", normalized[lang])

    return jsonify({"ok": True})


@app.get("/api/assets")
def list_assets():
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    files = []
    for f in sorted(ASSETS_DIR.iterdir()):
        if f.is_file() and f.suffix.lower() in ALLOWED_IMAGE_EXTS:
            files.append({"name": f.name, "url": f"assets/{f.name}", "size": f.stat().st_size})
    return jsonify(files)


@app.post("/api/assets/upload")
def upload_asset():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "Empty filename"}), 400
    filename = secure_filename(f.filename)
    if not filename:
        return jsonify({"error": "Invalid filename"}), 400
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTS:
        return jsonify({"error": "File type not allowed"}), 400
    data = f.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        return jsonify({"error": "File too large (max 10 MB)"}), 400
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    (ASSETS_DIR / filename).write_bytes(data)
    return jsonify({"ok": True, "url": f"assets/{filename}", "name": filename})


@app.delete("/api/assets/<path:filename>")
def delete_asset(filename):
    filename = secure_filename(filename)
    if not filename:
        return jsonify({"error": "Invalid filename"}), 400
    target = ASSETS_DIR / filename
    if not target.exists() or not target.is_file():
        return jsonify({"error": "Not found"}), 404
    target.unlink()
    return jsonify({"ok": True})


@app.get("/edit")
def edit_ui():
    return send_from_directory(BASE_DIR, "edit.html")


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_files(path: str):
    if path.startswith("api/"):
        return jsonify({"error": "Not found"}), 404
    if path:
        target = BASE_DIR / path
        if target.exists() and target.is_file():
            return send_from_directory(BASE_DIR, path)
    return send_from_directory(BASE_DIR, "index.html")


if __name__ == "__main__":
    port = int(os.getenv("PORT", "1080"))
    host = os.getenv("HOST", "127.0.0.1")
    app.run(host=host, port=port)
