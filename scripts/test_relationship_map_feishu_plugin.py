#!/usr/bin/env python3
from __future__ import annotations
import asyncio, importlib.util
from pathlib import Path
from types import SimpleNamespace

PLUGIN = Path(__file__).resolve().parents[1] / "plugins" / "relationship-map-feishu-card" / "__init__.py"
spec = importlib.util.spec_from_file_location("rm_plugin", PLUGIN)
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)  # type: ignore

class FakeAdapter:
    def __init__(self): self.sent=[]
    async def _feishu_send_with_retry(self, chat_id, msg_type, payload, reply_to=None, metadata=None):
        self.sent.append((chat_id,msg_type,payload,reply_to,metadata)); return SimpleNamespace(success=lambda: True)

class FakeGateway:
    def __init__(self, platform, adapter): self.adapters={platform: adapter}

class FakePlatform:
    value = "feishu"
    def __hash__(self): return hash("feishu")
    def __eq__(self, other): return getattr(other, "value", other) == "feishu"

PLATFORM = FakePlatform()

def event(text):
    return SimpleNamespace(text=text, message_id="m1", source=SimpleNamespace(platform=PLATFORM, chat_id="oc_test"))

async def main():
    adapter=FakeAdapter(); gw=FakeGateway(event("").source.platform, adapter)
    r=mod._pre_gateway_dispatch(event=event("打开人脉地图"), gateway=gw)
    assert r["action"] == "skip"
    await asyncio.sleep(0)
    assert adapter.sent and adapter.sent[0][1] == "interactive"
    assert '"tag": "button"' in adapter.sent[0][2] or '"tag":"button"' in adapter.sent[0][2]
    assert "[查看详情]" not in adapter.sent[0][2]
    r2=mod._pre_gateway_dispatch(event=event('比如打开人脉地图怎么设计'), gateway=gw)
    assert r2 is None
    detail='/card button {"relationship_map_action":"detail","contact_id":"missing","page":1}'
    r3=mod._pre_gateway_dispatch(event=event(detail), gateway=gw)
    assert r3["action"] == "skip"
    await asyncio.sleep(0)
    assert len(adapter.sent) == 2
    print('relationship map feishu plugin ok')

asyncio.run(main())
