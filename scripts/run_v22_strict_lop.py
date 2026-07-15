#!/usr/bin/env python3
"""Strict v2.2 LOP gate.

This script is intentionally stricter than a normal package validator. It fails
on stale runtime artifacts, misleading install claims, unsynchronised core docs,
missing plugin install requirements, fake-button regressions, and failure of the
full isolated Feishu interactive-card acceptance test.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fail(msg: str):
    raise AssertionError(msg)


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8", errors="ignore")


def sha(rel: str) -> str:
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def run(cmd: list[str]) -> str:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    p = subprocess.run(cmd, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=300, env=env)
    if p.returncode != 0:
        raise AssertionError("command failed: " + " ".join(cmd) + "\n" + p.stdout[-4000:])
    return p.stdout


def cleanup_runtime_artifacts():
    import shutil
    for p in list(ROOT.rglob("__pycache__")):
        shutil.rmtree(p, ignore_errors=True)
    for p in list(ROOT.rglob("*.pyc")):
        try:
            p.unlink()
        except FileNotFoundError:
            pass


def all_text_files():
    for p in ROOT.rglob("*"):
        if not p.is_file() or ".git" in p.parts:
            continue
        if p.suffix in {".md", ".py", ".yaml", ".json", ".txt"}:
            yield p


def gate_structure_and_sync():
    required = [
        "SKILL.md", "节点引擎-人脉地图/SKILL.md", "relationship-map/SKILL.md",
        "README.md", "INSTALL.md", "CHANGELOG.md",
        "references/v2.2-strict-lop.md", "relationship-map/references/v2.2-strict-lop.md",
        "plugins/relationship-map-feishu-card/plugin.yaml", "plugins/relationship-map-feishu-card/__init__.py",
        "scripts/install_relationship_map_feishu_card.py", "scripts/run_v22_full_acceptance.py",
        "scripts/test_v22_package_contract.py", "scripts/validate_skill_package.py",
    ]
    missing = [rel for rel in required if not (ROOT / rel).exists()]
    if missing: fail("missing required files: " + json.dumps(missing, ensure_ascii=False))
    if sha("SKILL.md") != sha("节点引擎-人脉地图/SKILL.md"):
        fail("root SKILL.md and Chinese-path SKILL.md are not identical")
    if "version: 2.2" not in read("SKILL.md"):
        fail("root SKILL.md not v2.2")
    if "version: 2.2" not in read("relationship-map/SKILL.md"):
        fail("relationship-map/SKILL.md not v2.2")
    if "version: 2.2.0" not in read("plugins/relationship-map-feishu-card/plugin.yaml"):
        fail("plugin manifest not 2.2.0")


def gate_no_stale_pollution():
    bad_paths=[]
    for p in ROOT.rglob("*"):
        rel=p.relative_to(ROOT).as_posix()
        if ".git" in p.parts:
            continue
        if "__pycache__" in p.parts or p.suffix == ".pyc" or p.name.endswith((".tmp", ".bak", ".orig")):
            bad_paths.append(rel)
        if p.is_file() and p.name in {"relationship_map.db", "test.db"}:
            bad_paths.append(rel)
    if bad_paths:
        fail("stale runtime/cache artifacts present: " + json.dumps(bad_paths, ensure_ascii=False))

    for rel in ["SKILL.md", "节点引擎-人脉地图/SKILL.md", "relationship-map/SKILL.md", "plugins/relationship-map-feishu-card/plugin.yaml"]:
        head = read(rel)[:800]
        if "version: 2.0" in head or "version: 2.1" in head or "version: 2.1.0" in head:
            fail("stale version in active header: " + rel)

    forbidden_name = "人脉" + "资源"
    hits=[]
    for p in all_text_files():
        txt=p.read_text(encoding="utf-8", errors="ignore")
        if forbidden_name in txt:
            hits.append(p.relative_to(ROOT).as_posix())
    if hits:
        fail("old naming pollution found: " + json.dumps(hits, ensure_ascii=False))


def gate_fake_button_policy():
    problems=[]
    for p in all_text_files():
        rel=p.relative_to(ROOT).as_posix()
        txt=p.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(r"\[查看详情\]|新增联系人｜搜索", txt):
            window = txt[max(0, m.start()-90):m.end()+90]
            ok = any(k in window for k in ["不得", "禁止", "不是", "没有", "失败", "伪按钮", "不能", "严禁", "not in", "fake", "re.finditer"])
            if not ok:
                problems.append({"file": rel, "context": window})
    if problems:
        fail("positive fake-button examples found: " + json.dumps(problems, ensure_ascii=False, indent=2))


def gate_install_claims():
    combined = "\n".join(read(rel) for rel in ["SKILL.md", "README.md", "INSTALL.md", "CHANGELOG.md"])
    must = [
        "hermes plugins install xyxw1234-bot/node-engine-relationship-map-skill/plugins/relationship-map-feishu-card --force --enable",
        "scripts/install_relationship_map_feishu_card.py",
        "重启",
        "restart_required",
        "不得继续打开人脉地图",
        "relationship_map_action",
        "msg_type=interactive",
    ]
    missing=[x for x in must if x not in combined and x not in read("scripts/install_relationship_map_feishu_card.py") and x not in read("plugins/relationship-map-feishu-card/__init__.py")]
    if missing:
        fail("missing install/runtime claims: " + json.dumps(missing, ensure_ascii=False))

    misleading=[]
    for p in all_text_files():
        rel=p.relative_to(ROOT).as_posix()
        txt=p.read_text(encoding="utf-8", errors="ignore")
        if "只发链接" in txt and not any(x in txt for x in ["不够", "不能", "不等于", "不得"]):
            misleading.append(rel)
    if misleading:
        fail("misleading link-only install claims: " + json.dumps(misleading, ensure_ascii=False))


def gate_commands():
    outputs = {}
    commands = [
        ["python3", "scripts/run_v22_full_acceptance.py"],
        ["python3", "scripts/validate_skill_package.py", "."],
        ["python3", "scripts/test_v22_package_contract.py"],
        ["python3", "scripts/test_relationship_map_feishu_plugin.py"],
        ["python3", "scripts/test_feishu_card_renderer.py"],
        ["python3", "scripts/run_runtime_stress_tests.py"],
        ["python3", "scripts/run_storage_card_e2e_tests.py"],
    ]
    for cmd in commands:
        outputs[" ".join(cmd)] = run(cmd).strip()[-1200:]
    run(["python3", "-m", "py_compile", "scripts/run_v22_full_acceptance.py", "scripts/install_relationship_map_feishu_card.py", "scripts/test_v22_package_contract.py", "plugins/relationship-map-feishu-card/__init__.py"])
    return outputs


def main():
    cleanup_runtime_artifacts()
    gate_structure_and_sync()
    gate_no_stale_pollution()
    gate_fake_button_policy()
    gate_install_claims()
    outputs = gate_commands()
    cleanup_runtime_artifacts()
    gate_no_stale_pollution()
    print(json.dumps({"passed": True, "strict_lop": "v2.2", "commands": outputs}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
