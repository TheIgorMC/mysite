import json
import os
import re
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

from flask import Flask, jsonify, request, send_from_directory

BASE_DIR = Path(__file__).resolve().parent
CONTENT_FILE = BASE_DIR / "content.json"
REGISTRATIONS_FILE = BASE_DIR / "registrations.json"
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
VALID_INTENTS = {"stay_posted", "buy_if_price", "contribute"}
WRITE_LOCK = Lock()

app = Flask(__name__)


def _atomic_write_json(path: Path, data) -> None:
    with tempfile.NamedTemporaryFile("w", delete=False, dir=path.parent, encoding="utf-8") as tmp:
        json.dump(data, tmp, ensure_ascii=False, indent=2)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)


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


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/api/content")
def get_content():
    content = _load_json(CONTENT_FILE, {"updates": [], "milestones": [], "planned_work": []})
    return jsonify(content)


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

    KNOWN_KEYS = {"updates", "timeline", "milestones", "planned_work"}
    for key in KNOWN_KEYS:
        if key in payload and not isinstance(payload[key], list):
            return jsonify({"error": f"'{key}' must be a list"}), 400

    # Preserve any extra keys already in the file, then overwrite known ones
    with WRITE_LOCK:
        existing = _load_json(CONTENT_FILE, {})
        existing.update({k: payload[k] for k in KNOWN_KEYS if k in payload})
        _atomic_write_json(CONTENT_FILE, existing)

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
    _ensure_data_files()
    port = int(os.getenv("PORT", "1080"))
    host = os.getenv("HOST", "127.0.0.1")
    app.run(host=host, port=port)
