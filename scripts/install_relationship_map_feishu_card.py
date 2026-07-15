#!/usr/bin/env python3
"""Install and enable the Relationship Map Feishu native-card companion plugin.

This script fixes the v2.0/v2.1 failure mode where only SKILL.md was updated,
but the Hermes runtime plugin was not installed/enabled, so Feishu still showed
fake text buttons like [查看详情].
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

PLUGIN_NAME = "relationship-map-feishu-card"
PLUGIN_SOURCE = "xyxw1234-bot/node-engine-relationship-map-skill/plugins/relationship-map-feishu-card"


def hermes_home() -> Path:
    return Path(os.environ.get("HERMES_HOME") or Path.home()/".hermes").expanduser().resolve()


def hermes_bin() -> str:
    for cand in [os.environ.get("HERMES_BIN"), shutil.which("hermes"), "/opt/hermes/.venv/bin/hermes"]:
        if cand and Path(cand).exists():
            return str(cand)
    return "hermes"


def run(cmd: list[str]) -> tuple[int, str]:
    p = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.strip()


def install_with_cli() -> bool:
    hb = hermes_bin()
    cmd = [hb, "plugins", "install", PLUGIN_SOURCE, "--force", "--enable"]
    code, out = run(cmd)
    return code == 0


def ensure_config_enabled() -> bool:
    # Fallback config writer if older Hermes CLI lacks --enable or install failed after copy.
    try:
        import yaml  # type: ignore
    except Exception:
        yaml = None
    cfg = hermes_home() / "config.yaml"
    data = {}
    if cfg.exists() and yaml:
        data = yaml.safe_load(cfg.read_text(encoding="utf-8")) or {}
    elif cfg.exists():
        txt = cfg.read_text(encoding="utf-8")
        if PLUGIN_NAME in txt:
            return True
        data = {}
    data.setdefault("plugins", {})
    enabled = data["plugins"].get("enabled") or []
    if PLUGIN_NAME not in enabled:
        enabled.append(PLUGIN_NAME)
    data["plugins"]["enabled"] = sorted(set(enabled))
    if yaml:
        cfg.parent.mkdir(parents=True, exist_ok=True)
        cfg.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
        return True
    return False


def verify() -> dict:
    home = hermes_home()
    plugin_dir = home / "plugins" / PLUGIN_NAME
    init = plugin_dir / "__init__.py"
    config = home / "config.yaml"
    config_text = config.read_text(encoding="utf-8", errors="ignore") if config.exists() else ""
    ok = init.exists() and PLUGIN_NAME in config_text
    return {"ok": ok, "plugin_dir": str(plugin_dir), "enabled_in_config": PLUGIN_NAME in config_text}


def main() -> int:
    cli_ok = install_with_cli()
    cfg_ok = ensure_config_enabled()
    result = verify()
    result["cli_install_ok"] = cli_ok
    result["config_write_ok"] = cfg_ok
    result["restart_required"] = True
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
