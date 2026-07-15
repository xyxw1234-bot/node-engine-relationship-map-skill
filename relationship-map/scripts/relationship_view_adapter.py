#!/usr/bin/env python3
from __future__ import annotations
import json
from typing import Any, Dict, List
from relationship_store import RelationshipStore

SENSITIVE_KEYS=['phone','wechat','address','id_number','finance_note','private_judgment']

class RelationshipViewAdapter:
    def __init__(self, store: RelationshipStore):
        self.store = store

    def list_text(self, state: Dict[str, Any]) -> Dict[str, Any]:
        data = self.store.list_contacts(page=state.get("page",1), page_size=state.get("page_size",15), query=state.get("query",""), city=state.get("city",""), sort=state.get("sort","updated_desc"))
        rows=[]
        for idx, r in enumerate(data['rows'], start=1+(data['page']-1)*data['page_size']):
            tags=json.loads(r['tags'] or '[]')
            metrics=json.loads(r['metrics'] or '{}')
            evidence=json.loads(r['metric_evidence'] or '{}')
            private=json.loads(r['private_json'] or '{}')
            role_or_tag='、'.join(tags[:2]) if tags else (r.get('role') or '信息待补充')
            position='｜'.join(x for x in [r.get('city') or '', r.get('organization') or '', role_or_tag] if x) or '信息待补充'
            shown=[]
            for k in ['relationship_temperature','action_priority']:
                if k in metrics and k in evidence and metrics[k]: shown.append(str(metrics[k]))
            status='｜'.join(shown) if shown else '待判断'
            recent=(r.get('last_interaction_at') or '')[:10] or '暂无记录'
            next_touch=(r.get('next_touch_at') or '')[:10] or '待补充'
            line=f"{idx}. {r['name']}｜{position}｜状态：{status}｜最近：{recent}｜下一步：{next_touch}"
            leaked=[k for k in SENSITIVE_KEYS if private.get(k) and str(private[k]) in line]
            rows.append({'contact_id':r['id'],'name':r['name'],'line':line,'leaked':leaked})
        summary=f"人脉地图共有 {data['total']} 人。当前显示第 {data['page']} 页，每页 {data['page_size']} 人。"
        if data['has_next']:
            summary += ' 还可以继续说：下一页。'
        if not rows:
            body='你的人脉库目前没有可显示的联系人。可以直接说：帮我记录某某，他是哪里人，主要做什么。'
        else:
            body='\n'.join([summary, *[r['line'] for r in rows], '想看某个人的详情，可以直接说他的姓名，或说：看第几个人。'])
        return {'type':'relationship_map_list_view','state':state,'total':data['total'],'has_next':data['has_next'],'rows':rows,'text':body}

    def detail_text(self, contact_id: str, return_state: Dict[str, Any]) -> Dict[str, Any]:
        c = self.store.get_contact(contact_id)
        lines=[f"{c['name']} 的人脉详情"]
        for label,key in [('城市','city'),('单位','organization'),('角色','role')]:
            if c.get(key): lines.append(f"{label}：{c[key]}")
        tags=c.get('tags') or []
        if tags: lines.append('标签：'+'、'.join(tags))
        metrics={k:v for k,v in c['metrics'].items() if v and k in c['metric_evidence']}
        if metrics:
            lines.append('关系判断：')
            for k,v in metrics.items():
                evidence=c['metric_evidence'].get(k,'')
                suffix=f"，依据：{evidence}" if evidence else ''
                lines.append(f"{k}：{v}{suffix}")
        facts=c.get('facts') or []
        if facts:
            lines.append('已确认事实：')
            lines.extend(str(x) for x in facts[:8])
        if c.get('last_interaction_at'): lines.append('最近互动：'+c['last_interaction_at'])
        if c.get('next_touch_at'): lines.append('下一步建议时间：'+c['next_touch_at'])
        timeline=c.get('timeline') or []
        if timeline:
            lines.append('最近记录：')
            for e in timeline[:8]:
                lines.append(f"{e.get('timestamp','')}｜{e.get('summary','')}")
        lines.append('如果要继续，可以说：更新这个人、生成联系话术、回到人脉列表。')
        return {'type':'relationship_map_detail_view','contact_id':contact_id,'return_state':return_state,'text':'\n'.join(lines)}
