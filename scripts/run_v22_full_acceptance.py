#!/usr/bin/env python3
"""v2.2 highest-strength acceptance test.

Creates an isolated Hermes home, installs/enables the companion plugin from the
local package, seeds relationship data, simulates Feishu gateway dispatch and
card button callbacks, and scans the whole package for stale or misleading
artifacts.
"""
from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import re
import shutil
import sqlite3
import tempfile
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_SRC = ROOT / "plugins" / "relationship-map-feishu-card"
PLUGIN_NAME = "relationship-map-feishu-card"


def assert_true(cond, msg):
    if not cond:
        raise AssertionError(msg)


class FakePlatform:
    value = "feishu"
    def __hash__(self): return hash("feishu")
    def __eq__(self, other): return getattr(other, "value", other) == "feishu"


PLATFORM = FakePlatform()


class FakeAdapter:
    def __init__(self): self.sent=[]
    async def _feishu_send_with_retry(self, chat_id, msg_type, payload, reply_to=None, metadata=None):
        self.sent.append({"chat_id":chat_id,"msg_type":msg_type,"payload":payload,"reply_to":reply_to,"metadata":metadata})
        return SimpleNamespace(success=lambda: True)


class FakeGateway:
    def __init__(self, adapter): self.adapters={PLATFORM: adapter}


def event(text):
    return SimpleNamespace(text=text, message_id="m_user", source=SimpleNamespace(platform=PLATFORM, chat_id="oc_test"))


def load_plugin(path: Path):
    spec=importlib.util.spec_from_file_location("relationship_map_feishu_card_runtime", path / "__init__.py")
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)  # type: ignore
    return mod


def seed_contact(home: Path):
    db_dir = home / "data" / "relationship-map"
    db_dir.mkdir(parents=True, exist_ok=True)
    db = db_dir / "relationship_map.db"
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE contacts (id TEXT PRIMARY KEY,name TEXT NOT NULL,city TEXT,organization TEXT,role TEXT,tags TEXT NOT NULL DEFAULT '[]',created_at TEXT NOT NULL,updated_at TEXT NOT NULL,last_interaction_at TEXT,next_touch_at TEXT,facts TEXT NOT NULL DEFAULT '[]',inferences TEXT NOT NULL DEFAULT '[]',private_json TEXT NOT NULL DEFAULT '{}',metrics TEXT NOT NULL DEFAULT '{}',metric_evidence TEXT NOT NULL DEFAULT '{}',deleted INTEGER NOT NULL DEFAULT 0)")
    conn.execute("CREATE TABLE timeline_events (id TEXT PRIMARY KEY,contact_id TEXT NOT NULL,timestamp TEXT NOT NULL,event_type TEXT NOT NULL,summary TEXT NOT NULL,metric_changes TEXT NOT NULL DEFAULT '[]',source TEXT,confidence TEXT)")
    conn.execute("INSERT INTO contacts VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0)", (
        "c_zhang", "张仁红", "四川", "科技产业", "产业资源", json.dumps(["科技产业"], ensure_ascii=False),
        "2026-07-15 10:00:00", "2026-07-15 10:00:00", "2026-07-15 今天聊过", "下次联系时了解具体公司和业务方向",
        json.dumps(["用户提到去四川时可考虑拜访"], ensure_ascii=False), "[]", "{}",
        json.dumps({"关系温度":"温"}, ensure_ascii=False), json.dumps({"关系温度":"用户明确记录"}, ensure_ascii=False)
    ))
    conn.execute("INSERT INTO timeline_events VALUES (?,?,?,?,?,?,?,?)", ("e1","c_zhang","2026-07-15 10:00:00","note","今天聊过，适合后续了解公司和业务方向","[]","test","high"))
    conn.commit(); conn.close()


def install_plugin(home: Path):
    target = home / "plugins" / PLUGIN_NAME
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists(): shutil.rmtree(target)
    shutil.copytree(PLUGIN_SRC, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    cfg = home / "config.yaml"
    cfg.write_text("plugins:\n  enabled:\n    - relationship-map-feishu-card\n", encoding="utf-8")
    return target


def extract_buttons(payload: str):
    card=json.loads(payload)
    buttons=[]
    def walk(x):
        if isinstance(x, dict):
            if x.get("tag") == "button": buttons.append(x)
            for v in x.values(): walk(v)
        elif isinstance(x, list):
            for v in x: walk(v)
    walk(card)
    return card, buttons


async def runtime_acceptance():
    with tempfile.TemporaryDirectory(prefix="rm_v22_accept_") as td:
        home=Path(td)
        os.environ["HERMES_HOME"] = str(home)
        plugin_path=install_plugin(home)
        seed_contact(home)
        assert_true((plugin_path/"plugin.yaml").exists(), "plugin.yaml not installed")
        assert_true(PLUGIN_NAME in (home/"config.yaml").read_text(encoding="utf-8"), "plugin not enabled in config")
        mod=load_plugin(plugin_path)
        adapter=FakeAdapter(); gw=FakeGateway(adapter)
        res=mod._pre_gateway_dispatch(event=event("打开人脉地图"), gateway=gw)
        assert_true(res and res.get("action") == "skip", "open map was not intercepted before LLM")
        await asyncio.sleep(0)
        assert_true(adapter.sent, "no Feishu send happened")
        first=adapter.sent[-1]
        assert_true(first["msg_type"] == "interactive", "open map did not send interactive card")
        assert_true("[查看详情]" not in first["payload"], "payload leaked fake [查看详情] button")
        card, buttons = extract_buttons(first["payload"])
        assert_true(buttons, "interactive card has no real buttons")
        detail_buttons=[b for b in buttons if (b.get("text") or {}).get("content") == "查看详情"]
        assert_true(detail_buttons, "no real 查看详情 button")
        val=detail_buttons[0].get("value") or {}
        assert_true(val.get("relationship_map_action") == "detail", "detail button missing relationship_map_action")
        # Simulate Feishu /card callback from button click
        cb='/card button ' + json.dumps(val, ensure_ascii=False)
        res2=mod._pre_gateway_dispatch(event=event(cb), gateway=gw)
        assert_true(res2 and res2.get("action") == "skip", "card callback not intercepted")
        await asyncio.sleep(0)
        second=adapter.sent[-1]
        assert_true(second["msg_type"] == "interactive", "detail callback did not send interactive card")
        assert_true("返回列表" in second["payload"], "detail card missing return button")
        assert_true("[查看详情]" not in second["payload"], "detail payload leaked fake button")
        # Negative trigger must not intercept
        res3=mod._pre_gateway_dispatch(event=event("比如打开人脉地图这个功能怎么设计"), gateway=gw)
        assert_true(res3 is None, "example/design sentence wrongly opened map")
        return {"interactive_sends": len(adapter.sent), "home": str(home), "buttons": len(buttons)}


def package_scan():
    problems=[]
    required_paths=[
        "SKILL.md", "节点引擎-人脉地图/SKILL.md", "README.md", "INSTALL.md", "CHANGELOG.md",
        "plugins/relationship-map-feishu-card/__init__.py", "scripts/install_relationship_map_feishu_card.py",
        "scripts/test_v22_package_contract.py", "scripts/run_v22_full_acceptance.py",
    ]
    for rel in required_paths:
        if not (ROOT/rel).exists(): problems.append(f"missing:{rel}")
    for rel in ["SKILL.md", "节点引擎-人脉地图/SKILL.md", "relationship-map/SKILL.md"]:
        txt=(ROOT/rel).read_text(encoding="utf-8")
        if "version: 2.2" not in txt: problems.append(f"bad-version:{rel}")
        for phrase in ["v2.2 Hard Requirement", "install_relationship_map_feishu_card.py", "不得继续打开人脉地图", "relationship-map-feishu-card"]:
            if phrase not in txt: problems.append(f"missing-phrase:{rel}:{phrase}")
    all_text="\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts and p.suffix in {".md",".py",".yaml",".json",".txt"})
    for rel in ["SKILL.md", "节点引擎-人脉地图/SKILL.md", "relationship-map/SKILL.md", "plugins/relationship-map-feishu-card/plugin.yaml"]:
        head=(ROOT/rel).read_text(encoding="utf-8", errors="ignore")[:500]
        if "version: 2.0" in head or "version: 2.1" in head:
            problems.append(f"stale-frontmatter:{rel}")
    # Positive fake button use forbidden; allowed only in explicit negative/failure/test contexts.
    for p in ROOT.rglob("*"):
        if not p.is_file() or ".git" in p.parts or p.suffix not in {".md",".py"}: continue
        txt=p.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(r"\[查看详情\]|新增联系人｜搜索", txt):
            w=txt[max(0,m.start()-80):m.end()+80]
            if not any(k in w for k in ["不得", "禁止", "不是", "没有", "失败", "伪按钮", "不能", "严禁", "not in", "re.finditer", "fake"]):
                problems.append(f"positive-fake-button:{p.relative_to(ROOT)}:{w}")
    return problems


async def main():
    runtime=await runtime_acceptance()
    problems=package_scan()
    assert_true(not problems, "package scan failed: " + json.dumps(problems, ensure_ascii=False, indent=2))
    print(json.dumps({"passed": True, "runtime": runtime, "scan_problems": problems}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
