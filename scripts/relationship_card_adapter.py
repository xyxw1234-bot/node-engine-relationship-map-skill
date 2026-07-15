#!/usr/bin/env python3
from __future__ import annotations
import json
from typing import Any, Dict
from relationship_store import RelationshipStore
SENSITIVE_KEYS=['phone','wechat','address','id_number','finance_note','private_judgment']
class RelationshipCardAdapter:
    def __init__(self, store:RelationshipStore): self.store=store
    def list_card(self,state:Dict[str,Any]):
        data=self.store.list_contacts(**state); elements=[]
        for r in data['rows']:
            tags=json.loads(r['tags'] or '[]'); metrics=json.loads(r['metrics'] or '{}'); evidence=json.loads(r['metric_evidence'] or '{}')
            shown=[]
            for k in ['relationship_temperature','action_priority']:
                if k in metrics and k in evidence: shown.append(metrics[k])
            title=f"{r['name']}｜{r.get('city') or r.get('organization') or '信息待补充'}｜{'/'.join(tags[:2]) if tags else (r.get('role') or '待补充')}"
            if shown: title+='｜'+'｜'.join(shown[:2])
            recent='最近互动：'+((r.get('last_interaction_at') or '')[:10] or '资料待补充')
            nxt='下一步：'+((r.get('next_touch_at') or '')[:10] or '待补充')
            private=json.loads(r['private_json'] or '{}'); text='\n'.join([title,recent,nxt])
            leaked=[k for k in SENSITIVE_KEYS if private.get(k) and str(private[k]) in text]
            elements.append({'contact_id':r['id'],'summary':text,'buttons':[{'text':'查看详情','action':'detail','contact_id':r['id']}],'leaked':leaked})
        return {'type':'relationship_map_list','state':state,'total':data['total'],'has_next':data['has_next'],'elements':elements,'nav':{'prev':max(1,state.get('page',1)-1),'next':state.get('page',1)+1 if data['has_next'] else None}}
    def detail_card(self,contact_id:str,return_state:Dict[str,Any]):
        c=self.store.get_contact(contact_id); metrics={k:v for k,v in c['metrics'].items() if k in c['metric_evidence']}
        return {'type':'relationship_map_detail','contact_id':contact_id,'return_state':return_state,'name':c['name'],'city':c.get('city',''),'organization':c.get('organization',''),'role':c.get('role',''),'metrics':metrics,'metric_evidence':{k:c['metric_evidence'][k] for k in metrics},'timestamps':{'created_at':c['created_at'],'updated_at':c['updated_at'],'last_interaction_at':c.get('last_interaction_at',''),'next_touch_at':c.get('next_touch_at','')},'timeline':c['timeline'][:20],'buttons':[{'text':'返回人脉地图','action':'list','state':return_state},{'text':'更新此人信息','action':'propose_update','contact_id':contact_id},{'text':'生成联系话术','action':'draft_outreach','contact_id':contact_id},{'text':'加入机会地图','action':'add_to_opportunity','contact_id':contact_id}]}
