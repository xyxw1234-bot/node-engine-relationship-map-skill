#!/usr/bin/env python3
"""人脉地图可执行模拟运行层：用于压力测试 Skill 设计，不连接真实用户数据。"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import random, re, uuid
from typing import Dict, List, Optional, Tuple, Any

SENSITIVE_KEYS = {"phone", "wechat", "address", "id_number", "finance_note", "private_judgment"}

ROLE_DIMENSIONS={
    "投资人":["投资偏好","关注赛道","阶段偏好","决策周期","资源网络","融资风险"],
    "会长":["可触达圈层","引荐意愿","引荐成本","合规边界","适合请教话题"],
    "校长":["学校类型","决策关注点","教师阻力","预算路径","样板场景","隐私风险"],
    "专家":["专业领域","可咨询问题","背书价值","观点可靠性"],
    "供应链":["供给能力","交付稳定性","账期风险","可替代性","履约记录"]
}
def infer_adaptive_dimensions(text: str):
    dims=[]
    for role, items in ROLE_DIMENSIONS.items():
        if role in text:
            dims.append({"role":role,"trigger":role,"dimensions":items,"confidence":"medium","requires_confirmation":True})
    if "介绍" in text or "引荐" in text:
        dims.append({"role":"资源连接者","trigger":"介绍/引荐","dimensions":["引荐价值","关系消耗","适合转介绍类型"],"confidence":"medium","requires_confirmation":True})
    if "没兑现" in text or "没回复" in text:
        dims.append({"role":"风险关系","trigger":"没兑现/没回复","dimensions":["承诺风险","关系降温依据","下次触达边界"],"confidence":"medium","requires_confirmation":True})
    return dims


@dataclass
class TimelineEvent:
    id: str
    contact_id: str
    timestamp: str
    event_type: str
    summary: str
    metric_changes: List[str] = field(default_factory=list)

@dataclass
class Contact:
    id: str
    name: str
    city: str = ""
    organization: str = ""
    role: str = ""
    tags: List[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    last_interaction_at: str = ""
    next_touch_at: str = ""
    facts: List[str] = field(default_factory=list)
    inferences: List[str] = field(default_factory=list)
    private: Dict[str, str] = field(default_factory=dict)
    metrics: Dict[str, str] = field(default_factory=dict)
    metric_evidence: Dict[str, str] = field(default_factory=dict)
    deleted: bool = False
    timeline: List[TimelineEvent] = field(default_factory=list)

class RelationshipMapRuntime:
    def __init__(self, contacts: List[Contact]):
        self.contacts = {c.id: c for c in contacts}

    def classify_intent(self, text: str) -> str:
        """返回 open_map / normal / confirm。先语义闸门，禁止关键词直开。
        疑问、请求许可、上下文不完整时默认 confirm，不直接打开。
        """
        s = text.strip()
        negative = ["不要打开", "别打开", "别弹", "不要弹", "错误打开", "误打开", "触发机制", "不对", "bug", "比如", "假设", "设计", "开发", "产品能力"]
        if any(x in s for x in negative):
            return "normal"
        objects = ["人脉地图", "人脉库", "联系人库"]
        if any(o in s for o in objects) and any(q in s for q in ["能不能", "可以不", "要不要", "是不是", "打开吗", "能打开", "能否"]):
            return "confirm"
        open_verbs = ["打开", "看看", "查看", "浏览", "进入", "列出", "展示"]
        if any(v in s for v in open_verbs) and any(o in s for o in objects):
            task_words = ["话术", "判断", "怎么跟进", "记录一下", "帮我分析", "今晚见", "刚认识"]
            if any(w in s for w in task_words):
                return "normal"
            return "open_map"
        if "有哪些人" in s and ("库" in s or "人脉" in s or "联系人" in s):
            return "open_map"
        return "normal"

    def parse_open_request(self, text: str) -> Dict[str, Any]:
        """把打开请求转成列表状态。"""
        cities=["重庆","上海","北京","深圳","成都","杭州","郑州","广州","西安","武汉"]
        city=next((c for c in cities if c in text), "")
        return {"intent": self.classify_intent(text), "state": {"page":1,"page_size":15,"query":"","city":city,"sort":"updated_desc"}}

    def list_view(self, page:int=1, page_size:int=15, query:str="", city:str="", sort:str="updated_desc") -> Dict:
        items=[c for c in self.contacts.values() if not c.deleted]
        if query:
            items=[c for c in items if query in c.name or query in c.organization or query in ''.join(c.tags)]
        if city:
            items=[c for c in items if c.city==city]
        if sort=="updated_desc":
            items.sort(key=lambda c: c.updated_at or "", reverse=True)
        total=len(items)
        start=(page-1)*page_size
        subset=items[start:start+page_size]
        cards=[]
        for c in subset:
            line1=f"{c.name}｜{c.city or c.organization or '信息待补充'}｜{'/'.join(c.tags[:2]) or c.role or '待补充'}"
            shown_metrics=[]
            for k in ["relationship_temperature", "action_priority"]:
                if k in c.metrics and k in c.metric_evidence: shown_metrics.append(c.metrics[k])
            if shown_metrics:
                line1 += "｜" + "｜".join(shown_metrics[:2])
            recent = f"最近互动：{c.last_interaction_at[:10]} {c.timeline[-1].summary[:22]}" if c.last_interaction_at and c.timeline else "最近互动：资料待补充"
            nxt = f"下一步：{c.next_touch_at[:10]} 可轻触达" if c.next_touch_at else "下一步：待补充"
            text="\n".join([line1, recent, nxt, "按钮：查看详情（需由飞书 interactive card 渲染为真按钮）"])
            # 一级列表敏感信息检测
            leaked=[]
            for key,val in c.private.items():
                if val and val in text:
                    leaked.append(key)
            cards.append({"id":c.id,"text":text,"leaked":leaked})
        return {"view":"list","page":page,"page_size":page_size,"query":query,"city":city,"sort":sort,"total":total,"cards":cards,"has_next":start+page_size<total}

    def detail_view(self, contact_id:str, return_state:Dict) -> Dict:
        c=self.contacts[contact_id]
        # 详情可以展示敏感分类名，但不应该无控制外发；测试只保证一级不泄露
        metrics={k:v for k,v in c.metrics.items() if v and k in c.metric_evidence}
        detail={
            "view":"detail",
            "contact_id":contact_id,
            "return_state":return_state,
            "name":c.name,
            "city":c.city,
            "organization":c.organization,
            "role":c.role,
            "metrics":metrics,
            "metric_evidence": {k:c.metric_evidence[k] for k in metrics},
            "created_at":c.created_at,
            "updated_at":c.updated_at,
            "last_interaction_at":c.last_interaction_at,
            "next_touch_at":c.next_touch_at,
            "timeline":[e.__dict__ for e in c.timeline],
            "buttons":["返回人脉地图","更新此人信息","生成联系话术","加入机会地图"]
        }
        return detail

    def return_to_list(self, detail:Dict) -> Dict:
        return self.list_view(**detail["return_state"])

    def propose_update(self, contact_id:str, field:str, value:Any, sensitive:bool=False, operation:str="update") -> Dict:
        """所有写操作先 proposal，不直接写入。"""
        allowed_ops={"update","delete","merge","bulk_import","sensitive_label","risk_assessment","trust_assessment"}
        if operation not in allowed_ops:
            raise ValueError(f"unsupported operation: {operation}")
        allowed_fields={"role","organization","city","next_touch_at","metrics","private","tags","facts","inferences"}
        if operation=="update" and field not in allowed_fields:
            raise ValueError(f"field not allowed: {field}")
        return {"requires_confirmation": True, "operation": operation, "contact_id": contact_id, "field": field, "value": value, "sensitive": sensitive, "preview": f"{operation}:{field}"}

    def apply_confirmed_update(self, proposal:Dict) -> None:
        if not proposal.get("requires_confirmation"):
            raise ValueError("proposal missing confirmation gate")
        c=self.contacts[proposal["contact_id"]]
        now=datetime.utcnow().strftime('%Y-%m-%d %H:%M')
        op=proposal.get("operation","update")
        if op=="delete":
            c.deleted=True
        elif op in {"merge","bulk_import"}:
            # 模拟层只记录确认，不自动执行复杂合并/导入
            pass
        elif op in {"sensitive_label","risk_assessment","trust_assessment"}:
            c.metrics[proposal["field"]]=proposal["value"]
            c.metric_evidence[proposal["field"]]=proposal.get("evidence", "用户确认")
        else:
            setattr(c, proposal["field"], proposal["value"])
        c.updated_at=now
        c.timeline.append(TimelineEvent(str(uuid.uuid4()), c.id, now, f"confirmed_{op}", f"确认执行 {op}:{proposal['field']}", []))

def generate_contacts(n:int=500, seed:int=42) -> List[Contact]:
    random.seed(seed)
    cities=["重庆","上海","北京","深圳","成都","杭州","郑州","广州","西安","武汉"]
    tags=["文旅资源","学校客户","企业服务","协会","资本","专家","渠道","供应链","HR","政府平台"]
    now=datetime(2026,7,15,12,0)
    contacts=[]
    for i in range(n):
        cid=f"contact_{i:04d}"
        created=now-timedelta(days=random.randint(1,900))
        updated=created+timedelta(days=random.randint(0,300))
        c=Contact(id=cid,name=f"测试联系人{i:04d}",city=random.choice(cities),organization=f"测试机构{i%37}",role=random.choice(["老板","校长","会长","总监","专家","投资人","负责人"]),tags=random.sample(tags,k=random.randint(1,3)),created_at=created.strftime('%Y-%m-%d %H:%M'),updated_at=updated.strftime('%Y-%m-%d %H:%M'))
        # 部分人才有互动和指标，按需生成
        if random.random()<0.72:
            last=updated+timedelta(days=random.randint(0,60))
            c.last_interaction_at=last.strftime('%Y-%m-%d %H:%M')
            c.timeline.append(TimelineEvent(str(uuid.uuid4()), cid, c.last_interaction_at, "interaction", random.choice(["饭局聊过合作", "电话沟通过需求", "微信轻触达", "会议见面", "朋友引荐认识"])))
            c.metrics["relationship_temperature"]=random.choice(["冷","温","热","关键期"])
            c.metric_evidence["relationship_temperature"]="存在最近互动"
        if random.random()<0.35:
            c.next_touch_at=(now+timedelta(days=random.randint(1,45))).strftime('%Y-%m-%d %H:%M')
            c.metrics["action_priority"]=random.choice(["A","B","C"])
            c.metric_evidence["action_priority"]="存在下一次建议触达时间"
        if random.random()<0.12:
            c.metrics["risk_level"]=random.choice(["中","高"])
            c.metric_evidence["risk_level"]="模拟风险信号"
        if random.random()<0.4:
            c.private={"phone":f"1380000{i%10000:04d}", "wechat":f"wx_secret_{i}", "address":f"测试地址{i}", "id_number":f"ID{i:018d}", "finance_note":f"财务备注{i}", "private_judgment":f"私密评价{i}"}
        contacts.append(c)
    return contacts
