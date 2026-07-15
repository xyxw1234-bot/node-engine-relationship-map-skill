"""节点引擎-人脉地图：飞书原生交互卡片 companion 插件。

目标：没有飞书流式卡片插件时，也要真正发送 msg_type=interactive 的飞书原生卡片，
不能把 [查看详情] 这类伪按钮当成交互能力。
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

PLUGIN_NAME = "relationship-map-feishu-card"
CARD_ACTION_KEY = "relationship_map_action"


def register(ctx):
    ctx.register_hook("pre_gateway_dispatch", _pre_gateway_dispatch)


def _platform_value(event: Any) -> str:
    source = getattr(event, "source", None)
    platform = getattr(source, "platform", "")
    return str(getattr(platform, "value", platform) or "")


def _chat_id(event: Any) -> str:
    return str(getattr(getattr(event, "source", None), "chat_id", "") or "")


def _message_id(event: Any) -> str:
    return str(getattr(event, "message_id", "") or "")


def _norm(text: str) -> str:
    return re.sub(r"\s+", "", (text or "").strip())


def _is_open_relationship_map(text: str) -> bool:
    t = _norm(text)
    yes = {"打开人脉地图", "打开我的人脉地图", "打开人脉库", "看看我的人脉地图", "看看我的人脉库", "联系人库打开一下"}
    no_markers = ("不要打开", "别打开", "不要弹", "别弹", "比如", "例如", "怎么设计", "触发机制", "开发一个")
    return t in yes and not any(m in t for m in no_markers)


def _parse_card_action(text: str) -> Optional[Dict[str, Any]]:
    text = (text or "").strip()
    if not text.startswith("/card"):
        return None
    m = re.search(r"\{.*\}\s*$", text, re.S)
    if not m:
        return None
    try:
        value = json.loads(m.group(0))
    except Exception:
        return None
    if not isinstance(value, dict) or CARD_ACTION_KEY not in value:
        return None
    return value


def _vault_path() -> Path:
    home = os.environ.get("HERMES_HOME")
    if home:
        return Path(home).expanduser().resolve() / "data" / "relationship-map"
    return Path.home() / ".hermes" / "data" / "relationship-map"


def _load_contacts() -> List[Dict[str, Any]]:
    vault = _vault_path()
    db = vault / "relationship_map.db"
    if not db.exists():
        return []
    try:
        conn = sqlite3.connect(str(db))
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id,name,city,organization,role,tags,updated_at,last_interaction_at,next_touch_at "
            "FROM contacts WHERE deleted=0 ORDER BY updated_at DESC LIMIT 50"
        ).fetchall()
        conn.close()
    except Exception:
        return []
    contacts=[]
    for r in rows:
        d=dict(r)
        try:
            d["tags"] = json.loads(d.get("tags") or "[]")
        except Exception:
            d["tags"] = []
        contacts.append(d)
    return contacts


def _load_detail(contact_id: str) -> Optional[Dict[str, Any]]:
    vault = _vault_path()
    db = vault / "relationship_map.db"
    if not db.exists() or not contact_id:
        return None
    try:
        conn = sqlite3.connect(str(db)); conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM contacts WHERE id=? AND deleted=0", (contact_id,)).fetchone()
        if not row:
            conn.close(); return None
        d=dict(row)
        for k in ("tags", "facts", "inferences"):
            try: d[k]=json.loads(d.get(k) or "[]")
            except Exception: d[k]=[]
        for k in ("metrics", "metric_evidence"):
            try: d[k]=json.loads(d.get(k) or "{}")
            except Exception: d[k]={}
        events=conn.execute("SELECT timestamp,summary,event_type FROM timeline_events WHERE contact_id=? ORDER BY timestamp DESC LIMIT 5", (contact_id,)).fetchall()
        d["timeline"]=[dict(e) for e in events]
        conn.close(); return d
    except Exception:
        return None


def _md(content: str) -> Dict[str, Any]:
    # 用 markdown 元素承载普通中文短句；不输出 Markdown 源码表格和伪按钮。
    return {"tag":"markdown", "content": content}


def _btn(label: str, action: str, **value: Any) -> Dict[str, Any]:
    return {"tag":"button", "text":{"tag":"plain_text","content":label}, "type":"default", "value":{CARD_ACTION_KEY: action, **value}}


def _card(title: str, elements: List[Dict[str, Any]], template: str="blue") -> Dict[str, Any]:
    return {"config":{"wide_screen_mode": True}, "header":{"template": template, "title":{"tag":"plain_text", "content": title}}, "elements": elements}


def _empty_card() -> Dict[str, Any]:
    return _card("节点引擎｜人脉地图", [
        _md("你的人脉地图还没有联系人。\n可以直接说：帮我记录张三，重庆人，做文旅资源。"),
        {"tag":"action", "actions":[_btn("查看示例", "example"), _btn("使用说明", "help")]}
    ])


def _list_card(page: int=1, page_size: int=10) -> Dict[str, Any]:
    contacts=_load_contacts()
    if not contacts:
        return _empty_card()
    page=max(1, int(page or 1)); page_size=max(1, min(20, int(page_size or 10)))
    start=(page-1)*page_size; chunk=contacts[start:start+page_size]
    elements=[_md(f"当前共 {len(contacts)} 人｜第 {page} 页\n一级列表只显示摘要，详情请点按钮进入。")]
    for c in chunk:
        tags="、".join((c.get("tags") or [])[:2])
        line1="｜".join(x for x in [c.get("name"), c.get("city"), c.get("role") or tags or c.get("organization")] if x) or "联系人"
        recent=c.get("last_interaction_at") or c.get("updated_at") or "暂无互动时间"
        nxt=c.get("next_touch_at") or "建议补充下一步动作"
        elements.append(_md(f"**{line1}**\n最近互动：{recent}\n下一步：{nxt}"))
        elements.append({"tag":"action", "actions":[_btn("查看详情", "detail", contact_id=c.get("id"), page=page)]})
    nav=[]
    if page > 1:
        nav.append(_btn("上一页", "list", page=page-1))
    if start + page_size < len(contacts):
        nav.append(_btn("下一页", "list", page=page+1))
    nav.extend([_btn("新增联系人", "add_hint"), _btn("搜索/筛选", "filter_hint")])
    elements.append({"tag":"action", "actions": nav})
    return _card("节点引擎｜人脉地图", elements)


def _detail_card(contact_id: str, page: int=1) -> Dict[str, Any]:
    d=_load_detail(contact_id)
    if not d:
        return _card("节点引擎｜人脉详情", [_md("没有找到这个联系人，可能已删除或数据未同步。"), {"tag":"action", "actions":[_btn("返回列表", "list", page=page)]}], "orange")
    lines=[f"**{d.get('name','联系人')}**"]
    for label,key in [("城市","city"),("单位","organization"),("角色","role")]:
        if d.get(key): lines.append(f"{label}：{d[key]}")
    facts=d.get("facts") or []
    if facts: lines.append("事实：" + "；".join(str(x) for x in facts[:3]))
    metrics=d.get("metrics") or {}; ev=d.get("metric_evidence") or {}
    shown=[f"{k}：{v}" for k,v in metrics.items() if k in ev and v]
    if shown: lines.append("关系判断：" + "；".join(shown[:4]))
    tl=d.get("timeline") or []
    if tl: lines.append("最近时间线：" + "；".join((e.get("summary") or "") for e in tl[:3] if e.get("summary")))
    return _card("节点引擎｜人脉详情", [
        _md("\n".join(lines)),
        {"tag":"action", "actions":[_btn("返回列表", "list", page=page), _btn("生成联系话术", "outreach", contact_id=contact_id), _btn("更新信息", "update_hint", contact_id=contact_id)]}
    ])


def _info_card(kind: str) -> Dict[str, Any]:
    mapping={
        "example": "示例：帮我记录张三，重庆人，做文旅资源。\n示例：我下周去重庆，看看适合联系谁。",
        "help": "人脉地图用于管理关系资产。你可以自然说话记录、更新、查看和生成联系方案。",
        "add_hint": "请直接发一句话新增联系人，例如：帮我记录张三，重庆人，做文旅资源。",
        "filter_hint": "筛选能力将继续扩展。当前可先用自然语言说：只看重庆的人脉。",
        "outreach": "请继续补充本次联系目标，我会结合联系人背景生成话术。",
        "update_hint": "请直接说要更新的事实，例如：补充张三现在负责重庆研学项目。",
    }
    return _card("节点引擎｜人脉地图", [_md(mapping.get(kind, "该功能正在准备中。")), {"tag":"action", "actions":[_btn("返回列表", "list", page=1)]}])


def _build_card(value: Optional[Dict[str, Any]]=None) -> Dict[str, Any]:
    if not value:
        return _list_card()
    action=str(value.get(CARD_ACTION_KEY) or "list")
    if action == "list":
        return _list_card(page=int(value.get("page") or 1))
    if action == "detail":
        return _detail_card(str(value.get("contact_id") or ""), page=int(value.get("page") or 1))
    return _info_card(action)


async def _send_interactive(adapter: Any, chat_id: str, card: Dict[str, Any], reply_to: str="") -> None:
    payload=json.dumps(card, ensure_ascii=False)
    if hasattr(adapter, "_feishu_send_with_retry"):
        await adapter._feishu_send_with_retry(chat_id=chat_id, msg_type="interactive", payload=payload, reply_to=reply_to or None, metadata={"source": PLUGIN_NAME})
        return
    # 测试/非飞书兜底：明确说明没有真实卡片能力，不伪装按钮。
    if hasattr(adapter, "send"):
        await adapter.send(chat_id, "人脉地图需要飞书原生交互卡片能力；当前环境未暴露 interactive 发送接口。", reply_to=reply_to or None)


def _schedule_send(gateway: Any, event: Any, card: Dict[str, Any]) -> bool:
    source=getattr(event, "source", None)
    adapter=getattr(gateway, "adapters", {}).get(getattr(source, "platform", None)) if gateway else None
    if adapter is None:
        return False
    coro=_send_interactive(adapter, _chat_id(event), card, _message_id(event))
    loop=getattr(adapter, "_loop", None)
    if loop is not None and hasattr(adapter, "_submit_on_loop"):
        return bool(adapter._submit_on_loop(loop, coro))
    try:
        running=asyncio.get_running_loop()
        running.create_task(coro)
        return True
    except RuntimeError:
        # No running loop; cannot safely send asynchronously.
        return False


def _pre_gateway_dispatch(**kwargs):
    event=kwargs.get("event")
    gateway=kwargs.get("gateway")
    if _platform_value(event) != "feishu":
        return None
    text=str(getattr(event, "text", "") or "")
    value=_parse_card_action(text)
    if value is not None:
        card=_build_card(value)
    elif _is_open_relationship_map(text):
        card=_build_card()
    else:
        return None
    if _schedule_send(gateway, event, card):
        return {"action":"skip", "reason":"relationship-map-feishu-card-handled"}
    return {"action":"allow"}
