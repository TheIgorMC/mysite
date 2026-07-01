#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import secrets
from copy import deepcopy
from getpass import getpass
from pathlib import Path

from werkzeug.security import generate_password_hash

BASE_DIR = Path(__file__).resolve().parents[1]
LOCAL_DATA_DIR = BASE_DIR / "local_data"
TRACKED_CONTENT_FILE = BASE_DIR / "content.json"
TRACKED_REGISTRATIONS_FILE = BASE_DIR / "registrations.json"
TRACKED_LOCALES_DIR = BASE_DIR / "locales"
CONTENT_FILE = LOCAL_DATA_DIR / "content.json"
REGISTRATIONS_FILE = LOCAL_DATA_DIR / "registrations.json"
LOCALES_DIR = LOCAL_DATA_DIR / "locales"
ASSETS_DIR = LOCAL_DATA_DIR / "assets"
AUTH_FILE = LOCAL_DATA_DIR / "auth.json"
SUPPORTED_LOCALES = ("en", "it", "fr", "es")
LIST_IDENTITY_KEYS = {
    "updates": ("date", "title"),
    "timeline": ("date", "label"),
    "milestones": ("target", "name"),
    "planned_work": ("window", "task"),
    "gallery": ("src",),
    "registrations": ("id",),
}
CONTENT_FALLBACK = {"updates": [], "timeline": [], "milestones": [], "planned_work": [], "gallery": []}


def load_json(path: Path, fallback):
    if not path.exists():
        return deepcopy(fallback)
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (json.JSONDecodeError, OSError):
        return deepcopy(fallback)
    return data if data is not None else deepcopy(fallback)


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def locale_identity(value):
    if isinstance(value, dict):
        for candidate in ("en", "it", "fr", "es"):
            text = value.get(candidate)
            if text:
                return str(text)
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    if isinstance(value, list):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return value


def item_identity(item, path: str):
    if not isinstance(item, dict):
        return ("primitive", item)

    path_key = path.split(".")[-1]
    identity_fields = LIST_IDENTITY_KEYS.get(path_key)
    if not identity_fields:
        return ("dict", json.dumps(item, ensure_ascii=False, sort_keys=True))

    parts = []
    for field in identity_fields:
        parts.append(locale_identity(item.get(field)))
    return (path_key, tuple(parts))


def merge_json(existing, source, path: str = ""):
    if isinstance(existing, dict) and isinstance(source, dict):
        merged = deepcopy(existing)
        for key, value in source.items():
            if key not in merged:
                merged[key] = deepcopy(value)
            else:
                child_path = f"{path}.{key}" if path else key
                merged[key] = merge_json(merged[key], value, child_path)
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
            index_by_identity[item_identity(item, path)] = index

        for source_item in source:
            identity = item_identity(source_item, path)
            if identity in index_by_identity:
                target_index = index_by_identity[identity]
                merged[target_index] = merge_json(merged[target_index], source_item, path)
            else:
                index_by_identity[identity] = len(merged)
                merged.append(deepcopy(source_item))
        return merged
    return deepcopy(existing if existing is not None else source)


def merge_file(local_path: Path, source_path: Path, fallback, path: str):
    source = load_json(source_path, fallback)
    local = load_json(local_path, source)
    merged = merge_json(local, source, path)
    write_json(local_path, merged)


def ensure_auth_file(password: str | None, reset: bool) -> None:
    auth = load_json(AUTH_FILE, {})
    if not isinstance(auth, dict):
        auth = {}

    if not auth.get("session_secret_key"):
        auth["session_secret_key"] = secrets.token_urlsafe(48)

    if reset or not auth.get("password_hash"):
        if not password:
            password = getpass("Admin password: ")
            confirm = getpass("Confirm admin password: ")
            if password != confirm:
                raise SystemExit("Passwords do not match.")
        if not password:
            raise SystemExit("A password is required.")
        auth["password_hash"] = generate_password_hash(password)

    write_json(AUTH_FILE, auth)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create or refresh OrionPnP local data files.")
    parser.add_argument("--password", help="Set or replace the admin password without prompting.")
    parser.add_argument("--reset-password", action="store_true", help="Force password update in auth.json.")
    args = parser.parse_args()

    LOCAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOCALES_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    merge_file(CONTENT_FILE, TRACKED_CONTENT_FILE, CONTENT_FALLBACK, "content")
    merge_file(REGISTRATIONS_FILE, TRACKED_REGISTRATIONS_FILE, [], "registrations")
    for lang in SUPPORTED_LOCALES:
        merge_file(LOCALES_DIR / f"{lang}.json", TRACKED_LOCALES_DIR / f"{lang}.json", {}, f"locales.{lang}")

    ensure_auth_file(args.password, args.reset_password)
    print(f"Local data prepared in {LOCAL_DATA_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
