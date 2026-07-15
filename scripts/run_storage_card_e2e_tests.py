#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,shutil,tempfile
from pathlib import Path
from relationship_runtime import generate_contacts
from relationship_store import RelationshipStore
from relationship_card_adapter import RelationshipCardAdapter

def assert_true(cond,msg):
    if not cond: raise AssertionError(msg)

def run(contacts:int, rounds:int):
    tmp=Path(tempfile.mkdtemp(prefix='relationship_map_e2e_'))
    try:
        store=RelationshipStore(tmp)
        for c in generate_contacts(contacts):
            store.upsert_contact({'id':c.id,'name':c.name,'city':c.city,'organization':c.organization,'role':c.role,'tags':c.tags,'created_at':c.created_at,'last_interaction_at':c.last_interaction_at,'next_touch_at':c.next_touch_at,'private':c.private,'metrics':c.metrics,'metric_evidence':c.metric_evidence,'facts':c.facts,'inferences':c.inferences}, confirmed=True)
        adapter=RelationshipCardAdapter(store)
        state={'page':1,'page_size':15,'query':'','city':'','sort':'updated_desc'}
        card=adapter.list_card(state)
        assert_true(card['total']==contacts,'写入总数错误')
        assert_true(len(card['elements'])<=15,'卡片列表未分页')
        assert_true(all(not e['leaked'] for e in card['elements']),'一级卡片泄露敏感字段')
        cid=card['elements'][0]['contact_id']; detail=adapter.detail_card(cid,state)
        assert_true(any(b['text']=='返回人脉地图' for b in detail['buttons']),'详情缺返回')
        back=adapter.list_card(detail['return_state']); assert_true(back['state']==state,'返回状态丢失')
        state2={'page':1,'page_size':15,'query':'','city':'重庆','sort':'updated_desc'}; c2=adapter.list_card(state2)
        assert_true(all('重庆' in e['summary'] for e in c2['elements']),'城市筛选错误')
        before=len(list((tmp/'backups').glob('*.db'))); prop=store.propose_operation('delete',cid)
        try:
            store.apply_confirmed(prop,confirmed=False); raise AssertionError('未确认删除未被拦截')
        except PermissionError: pass
        store.apply_confirmed(prop,confirmed=True); after=len(list((tmp/'backups').glob('*.db'))); assert_true(after==before+1,'确认操作未备份')
        for i in range(rounds):
            page=(i%max(1,contacts//15))+1; city='重庆' if i%3==0 else ''
            card=adapter.list_card({'page':page,'page_size':15,'query':'','city':city,'sort':'updated_desc'})
            assert_true(len(card['elements'])<=15,'压力分页失败')
            assert_true(all(not e['leaked'] for e in card['elements']),'压力敏感泄露')
        store.close(); return {'passed':True,'contacts':contacts,'rounds':rounds,'vault_files':len(list(tmp.rglob('*')))}
    finally:
        shutil.rmtree(tmp,ignore_errors=True)
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--contacts',type=int,default=5000); ap.add_argument('--rounds',type=int,default=10000)
    args=ap.parse_args(); print(json.dumps(run(args.contacts,args.rounds),ensure_ascii=False,indent=2))
