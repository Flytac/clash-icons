#!/usr/bin/env python3
"""Check the generated catalogue before publishing."""

import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

root = Path(__file__).resolve().parents[1]
items = json.loads((root / "scripts/icons.json").read_text(encoding="utf-8"))
ns = "{http://www.w3.org/2000/svg}"
required = {
    "docker", "steam", "playstation", "nintendo", "google", "youtube",
    "openai", "telegram", "github", "microsoft", "apple", "netflix",
    "discord", "cloudflare", "japan", "hongkong", "usa", "singapore",
    "direct", "proxy", "auto",
}
errors = []
active = [item for item in items if item["source"] != "missing"]
for item in active:
    path = root / "icons" / item["category"] / f"{item['name']}.svg"
    if not path.is_file():
        errors.append(f"missing: {path}")
        continue
    try:
        svg = ET.parse(path).getroot()
    except ET.ParseError as exc:
        errors.append(f"invalid XML: {path}: {exc}")
        continue
    if svg.tag != ns + "svg" or not svg.get("viewBox"):
        errors.append(f"namespace/viewBox missing: {path}")
    if svg.get("width") or svg.get("height"):
        errors.append(f"fixed root size: {path}")
    text = path.read_text(encoding="utf-8")
    if item["source"] in ("simple-icons", "tabler") and "currentColor" in text:
        errors.append(f"unresolved currentColor: {path}")
    if item["source"] == "simple-icons" and not re.fullmatch(r"#[0-9A-F]{6}", svg.get("fill", "")):
        errors.append(f"brand color missing: {path}")

available = {item["name"] for item in active}
errors.extend(f"required icon missing: {name}" for name in sorted(required - available))
docker = ET.parse(root / "icons/brands/docker.svg").getroot() if "docker" in available else None
if docker is not None and docker.get("fill") != "#2496ED":
    errors.append("Docker is not #2496ED")
for error in errors:
    print(error, file=sys.stderr)
print(f"Validated {len(active)} SVGs; errors: {len(errors)}")
raise SystemExit(1 if errors else 0)
