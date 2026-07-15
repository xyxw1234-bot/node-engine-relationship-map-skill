#!/usr/bin/env python3
"""Create or update the GitHub Release object for v2.2.

This fixes the case where git tag v2.2 exists but GitHub Releases still shows
v2.0 as Latest in the repository sidebar.

Requires GITHUB_TOKEN with repo permission.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

OWNER = "xyxw1234-bot"
REPO = "node-engine-relationship-map-skill"
TAG = "v2.2"
TARGET = "main"
API = f"https://api.github.com/repos/{OWNER}/{REPO}"
BODY = """## v2.2 严格发布版

本版本修复 v2.0/v2.1 的关键交付问题：

- 不再把 `[查看详情]` 等文本伪按钮冒充为飞书真按钮；
- 新增 `relationship-map-feishu-card` 飞书原生交互卡片 companion 插件；
- 新增插件安装器 `scripts/install_relationship_map_feishu_card.py`；
- 明确只更新 `SKILL.md` 不算完成，必须安装/启用/重启/验收；
- 新增 `scripts/run_v22_full_acceptance.py` 隔离环境端到端验收；
- 新增 `scripts/run_v22_strict_lop.py` 最高强度 LOP 门禁；
- 全局同步 README / INSTALL / CHANGELOG / references / scripts / plugin manifest / 版本号。

正式安装链接：
https://raw.githubusercontent.com/xyxw1234-bot/node-engine-relationship-map-skill/main/节点引擎-人脉地图/SKILL.md
"""


def token() -> str:
    t = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not t:
        raise SystemExit("missing GITHUB_TOKEN")
    return t


def request(method: str, path: str, payload: dict | None = None):
    data = json.dumps(payload, ensure_ascii=False).encode() if payload is not None else None
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer " + token(),
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(API + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")
        raise RuntimeError(f"GitHub API {method} {path} failed: {e.code} {body}") from e


def maybe_request(method: str, path: str, payload: dict | None = None):
    try:
        return request(method, path, payload)
    except RuntimeError as e:
        if " 404 " in str(e):
            return None
        raise


def main() -> int:
    latest_before = maybe_request("GET", "/releases/latest")
    existing = maybe_request("GET", f"/releases/tags/{TAG}")
    payload = {
        "tag_name": TAG,
        "target_commitish": TARGET,
        "name": TAG,
        "body": BODY,
        "draft": False,
        "prerelease": False,
        "make_latest": "true",
    }
    if existing:
        release = request("PATCH", f"/releases/{existing['id']}", payload)
    else:
        release = request("POST", "/releases", payload)
    latest_after = request("GET", "/releases/latest")
    ok = latest_after.get("tag_name") == TAG and release.get("tag_name") == TAG
    print(json.dumps({
        "ok": ok,
        "latest_before": latest_before.get("tag_name") if latest_before else None,
        "latest_after": latest_after.get("tag_name"),
        "release_url": release.get("html_url"),
    }, ensure_ascii=False, indent=2))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
