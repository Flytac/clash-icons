#!/usr/bin/env python3
"""Fetch vetted upstream SVGs and build the Clash icon catalogue.

Standard-library only. Run from any directory with Python 3.10+.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Path(__file__).with_name("icons.json")
SIMPLE_VERSION = "16.32.0"
SIMPLE_BASE = f"https://cdn.jsdelivr.net/npm/simple-icons@{SIMPLE_VERSION}"
TABLER_BASE = "https://cdn.jsdelivr.net/npm/@tabler/icons@latest/icons/outline"
FLAGS_BASE = "https://raw.githubusercontent.com/HatScripts/circle-flags/gh-pages/flags"
SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "clash-color-icons/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def upstream_url(item: dict) -> str:
    source = item["source"]
    slug = item["slug"]
    if source == "simple-icons":
        return f"{SIMPLE_BASE}/icons/{slug}.svg"
    if source == "tabler":
        return f"{TABLER_BASE}/{slug}.svg"
    if source == "circle-flags":
        return f"{FLAGS_BASE}/{slug}.svg"
    if source == "iconify":
        return f"https://api.iconify.design/{item['set']}/{slug}.svg"
    raise ValueError(f"Unknown source: {source}")


def paint(svg: bytes, item: dict, metadata: dict) -> tuple[bytes, str | None]:
    root = ET.fromstring(svg)
    if root.tag != f"{{{SVG_NS}}}svg" or "viewBox" not in root.attrib:
        raise ValueError("SVG root or viewBox missing")
    root.attrib.pop("width", None)
    root.attrib.pop("height", None)
    source = item["source"]
    color = item.get("color")
    if source == "simple-icons":
        brand = metadata.get(item["slug"])
        if not brand:
            raise ValueError("Brand slug missing from pinned Simple Icons metadata")
        color = color or brand["hex"]
        if not re.fullmatch(r"[0-9A-Fa-f]{6}", color):
            raise ValueError("Invalid brand color")
        color = color.upper()
        root.set("fill", f"#{color}")
        for element in root.iter():
            for attr in ("fill", "stroke"):
                if element is root and attr == "fill":
                    continue
                if element.get(attr, "").lower() in ("currentcolor", "#000", "#000000", "black"):
                    element.set(attr, f"#{color}")
    elif source == "tabler":
        color = (color or "3B82F6").upper()
        root.set("stroke", f"#{color}")
        for element in root.iter():
            if element is not root and element.get("stroke", "").lower() == "currentcolor":
                element.set("stroke", f"#{color}")
    elif source == "iconify" and color:
        color = color.upper()
        root.set("fill", f"#{color}")
        for element in root.iter():
            for attr in ("fill", "stroke"):
                if element is root and attr == "fill":
                    continue
                if element.get(attr, "").lower() == "currentcolor":
                    element.set(attr, f"#{color}")
    # Multicolour Iconify and flag SVGs keep every original path colour.
    for element in root.iter():
        element.attrib.pop("width", None) if element is root else None
        element.attrib.pop("height", None) if element is root else None
    result = ET.tostring(root, encoding="unicode", short_empty_elements=True)
    if "currentColor" in result and source in ("simple-icons", "tabler"):
        raise ValueError("Unresolved currentColor")
    return (result + "\n").encode("utf-8"), f"#{color}" if color else None


def source_name(item: dict) -> tuple[str, str]:
    source = item["source"]
    if source == "simple-icons":
        return "Simple Icons", "CC0 collection; individual brand rights may differ"
    if source == "tabler":
        return "Tabler Icons", "MIT"
    if source == "circle-flags":
        return "HatScripts/circle-flags", "MIT"
    if item["set"] == "cib":
        return "Iconify / CoreUI Brands", "CC0-1.0 collection; brand rights may differ"
    return "Iconify / SVG Logos", "CC0-1.0 collection; brand rights may differ"


def generate_one(item: dict, metadata: dict) -> dict:
    url = upstream_url(item)
    svg, color = paint(fetch(url), item, metadata)
    path = ROOT / "icons" / item["category"] / f"{item['name']}.svg"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(svg)
    return {**item, "url": url, "path": path.relative_to(ROOT).as_posix(), "resolved_color": color}


def make_docs(success: list[dict], missing: list[dict], owner: str, repo: str) -> None:
    base = f"https://fastly.jsdelivr.net/gh/{owner}/{repo}@main"
    groups = {"brands": "品牌与服务", "regions": "国家与地区", "general": "通用策略组"}
    lines = ["# 图标 URL 清单", "", f"仓库：`{owner}/{repo}`。若为占位符，请先替换用户名和仓库名。", ""]
    yaml = ["# 复制所需条目到自己的 Clash/Mihomo 配置；此文件不是完整配置", "# 如用户名仍为 USERNAME，请先替换 URL", ""]
    sources = ["# 图标来源", "", f"Simple Icons 固定版本：`{SIMPLE_VERSION}`。通用图标由 Tabler 提供，旗帜由 HatScripts 提供。", ""]
    for category, title in groups.items():
        lines += [f"## {title}", "", "| 图标 | 文件 | CDN |", "| --- | --- | --- |"]
        sources += [f"## {title}", "", "| 名称 | 来源 | 上游图标 | 颜色 | 许可 / 备注 |", "| --- | --- | --- | --- | --- |"]
        for item in sorted((x for x in success if x["category"] == category), key=lambda x: x["name"]):
            name = item["name"]
            cdn = f"{base}/{item['path']}"
            lines.append(f"| {name} | [`{item['path']}`]({item['path']}) | `{cdn}` |")
            yaml += [f"{name}:", f"  icon: {cdn}", ""]
            display, license_text = source_name(item)
            note = item.get("note", "")
            brand_meta = item.get("brand_meta", {})
            if brand_meta.get("license"):
                license_text += f"; 单图标: {brand_meta['license'].get('type', 'unknown')}"
            if note:
                license_text += f"; {note}"
            sources.append(f"| {name} | {display} | [`{item['slug']}`]({item['url']}) | {item['resolved_color'] or '保留原 SVG 多色'} | {license_text} |")
        lines.append("")
        sources.append("")
    (ROOT / "icons.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    examples = ROOT / "examples"
    examples.mkdir(exist_ok=True)
    (examples / "clash-icons.yaml").write_text("\n".join(yaml), encoding="utf-8")
    (ROOT / "SOURCES.md").write_text("\n".join(sources), encoding="utf-8")
    missing_lines = ["# 暂缺图标", "", "这些名称仍保留在 `scripts/icons.json` 中，不会用假 Logo 代替。", "", "| 名称 | 原因 |", "| --- | --- |"]
    for item in missing:
        missing_lines.append(f"| {item['name']} | {item['reason']} |")
    if not missing:
        missing_lines.append("| 无 | 当前清单全部生成成功 |")
    (ROOT / "missing-icons.md").write_text("\n".join(missing_lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner", default="USERNAME", help="GitHub username or organization")
    parser.add_argument("--repo", default="REPOSITORY", help="GitHub repository name")
    args = parser.parse_args()
    items = json.loads(MANIFEST.read_text(encoding="utf-8"))
    names = [(x["category"], x["name"]) for x in items]
    if len(names) != len(set(names)):
        parser.error("Duplicate category/name in icons.json")
    try:
        data = json.loads(fetch(f"{SIMPLE_BASE}/data/simple-icons.json"))
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        print(f"无法获取 Simple Icons 元数据；相关品牌将逐项报告失败：{exc}", file=sys.stderr)
        data = []
    metadata = {x.get("slug") or re.sub(r"[^a-z0-9]", "", x["title"].lower()): x for x in data}
    missing = [{**x} for x in items if x["source"] == "missing"]
    active = [x for x in items if x["source"] != "missing"]
    success: list[dict] = []
    failed: list[tuple[str, str]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        jobs = {pool.submit(generate_one, x, metadata): x for x in active}
        for job in concurrent.futures.as_completed(jobs):
            item = jobs[job]
            try:
                result = job.result()
                if item["source"] == "simple-icons":
                    result["brand_meta"] = metadata[item["slug"]]
                success.append(result)
            except Exception as exc:  # Continue through individual 404 and network errors.
                failed.append((item["name"], str(exc)))
                missing.append({**item, "reason": f"本次生成失败：{exc}"})
    make_docs(success, missing, args.owner, args.repo)
    print(f"成功：{len(success)}  失败：{len(failed)}  跳过：{len(items) - len(active)}")
    for name, reason in sorted(failed):
        print(f"失败：{name} — {reason}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
