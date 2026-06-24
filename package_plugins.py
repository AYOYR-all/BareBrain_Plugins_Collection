from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


ROOT_FILES = ("barebrain.mod.json", "CMakeLists.txt", "README.md", "CHANGELOG.md", "LICENSE")


def package_plugin(plugin_dir: Path, output_dir: Path) -> tuple[str, str, Path]:
    manifest = json.loads((plugin_dir / "barebrain.mod.json").read_text(encoding="utf-8"))
    plugin_id = manifest["id"]
    files = [plugin_dir / name for name in ROOT_FILES]
    files.extend(sorted(path for path in (plugin_dir / "src").rglob("*") if path.is_file()))
    tests = plugin_dir / "tests"
    if tests.exists():
        files.extend(sorted(path for path in tests.rglob("*") if path.is_file()))
    missing = [str(path) for path in files[: len(ROOT_FILES)] if not path.is_file()]
    if missing:
        raise ValueError(f"{plugin_id}: missing release files: {', '.join(missing)}")

    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"{plugin_id}.zip"
    with ZipFile(output, "w", ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            info = ZipInfo(path.relative_to(plugin_dir).as_posix(), date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes(), compresslevel=9)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    return plugin_id, digest, output


def main() -> int:
    parser = argparse.ArgumentParser(description="Create deterministic BareBrain plugin archives")
    parser.add_argument("plugin_dirs", nargs="+", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("releases"))
    args = parser.parse_args()
    for plugin_dir in args.plugin_dirs:
        plugin_id, digest, output = package_plugin(plugin_dir.resolve(), args.output_dir.resolve())
        print(f"{plugin_id} {output} sha256:{digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
