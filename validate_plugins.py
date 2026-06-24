from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse


REQUIRED_FIELDS = {
    "id",
    "name",
    "version",
    "type",
    "description",
    "author",
    "repo",
    "archive",
    "checksum",
    "targets",
    "permissions",
    "resources",
}

VALID_TYPES = {"tool", "channel", "device", "service", "data", "bridge", "profile"}
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SEMVER_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.-]+)?$")
CHECKSUM_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def load_index(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("index must be a JSON object")
    return data


def validate_url(value: str, *, field: str) -> str | None:
    parsed = urlparse(value)
    if parsed.scheme not in {"https", "http"}:
        return f"{field} must use http or https"
    if not parsed.netloc:
        return f"{field} must include a host"
    return None


def validate_plugin(plugin: dict, index: int) -> list[str]:
    prefix = f"plugins[{index}]"
    errors: list[str] = []

    missing = sorted(REQUIRED_FIELDS - set(plugin))
    if missing:
        errors.append(f"{prefix}: missing fields: {', '.join(missing)}")
        return errors

    plugin_id = plugin.get("id")
    if not isinstance(plugin_id, str) or not ID_RE.match(plugin_id):
        errors.append(f"{prefix}.id must be kebab-case lowercase")

    version = plugin.get("version")
    if not isinstance(version, str) or not SEMVER_RE.match(version):
        errors.append(f"{prefix}.version must be SemVer")

    plugin_type = plugin.get("type")
    if plugin_type not in VALID_TYPES:
        errors.append(f"{prefix}.type must be one of {', '.join(sorted(VALID_TYPES))}")

    for field in ("name", "description", "author"):
        if not isinstance(plugin.get(field), str) or not plugin[field].strip():
            errors.append(f"{prefix}.{field} must be a non-empty string")

    for field in ("repo", "archive"):
        if not isinstance(plugin.get(field), str):
            errors.append(f"{prefix}.{field} must be a string")
        else:
            error = validate_url(plugin[field], field=f"{prefix}.{field}")
            if error:
                errors.append(error)

    checksum = plugin.get("checksum")
    if not isinstance(checksum, str) or not CHECKSUM_RE.match(checksum):
        errors.append(f"{prefix}.checksum must be sha256 followed by 64 lowercase hex characters")

    targets = plugin.get("targets")
    if not isinstance(targets, list) or not targets or not all(isinstance(item, str) for item in targets):
        errors.append(f"{prefix}.targets must be a non-empty string list")

    permissions = plugin.get("permissions")
    if not isinstance(permissions, list) or not all(isinstance(item, str) for item in permissions):
        errors.append(f"{prefix}.permissions must be a string list")

    resources = plugin.get("resources")
    if not isinstance(resources, dict):
        errors.append(f"{prefix}.resources must be an object")
    else:
        gpio = resources.get("gpio", [])
        if not isinstance(gpio, list):
            errors.append(f"{prefix}.resources.gpio must be a list")

    return errors


def validate_index(data: dict) -> list[str]:
    errors: list[str] = []
    if data.get("schema") != 1:
        errors.append("schema must be 1")
    plugins = data.get("plugins")
    if not isinstance(plugins, list):
        errors.append("plugins must be a list")
        return errors

    seen: set[str] = set()
    for index, plugin in enumerate(plugins):
        if not isinstance(plugin, dict):
            errors.append(f"plugins[{index}] must be an object")
            continue
        plugin_id = plugin.get("id")
        if isinstance(plugin_id, str):
            if plugin_id in seen:
                errors.append(f"duplicate plugin id: {plugin_id}")
            seen.add(plugin_id)
        errors.extend(validate_plugin(plugin, index))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate BareBrain plugin index")
    parser.add_argument("plugins_json", nargs="?", default="plugins.json")
    args = parser.parse_args()

    try:
        data = load_index(Path(args.plugins_json))
        errors = validate_index(data)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("Plugin index OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
