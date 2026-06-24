from __future__ import annotations

import json
from pathlib import Path


def main() -> int:
    index_path = Path("plugins.json")
    cache_path = Path("plugin_cache.json")
    index = json.loads(index_path.read_text(encoding="utf-8"))
    plugins = index.get("plugins", [])
    cache = {
        "schema": 1,
        "generated_at": index.get("generated_at"),
        "plugins": {plugin["id"]: plugin for plugin in plugins},
    }
    cache_path.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(cache_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
