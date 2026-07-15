#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,shutil,tempfile
from pathlib import Path
from relationship_runtime import generate_contacts
from relationship_store import RelationshipStore
from relationship_view_adapter import RelationshipViewAdapter

def assert_true(cond,msg):
    if not cond: raise AssertionError(msg)

def run(contacts:int, rounds:int):
    tmp=Path(tempfile.mkdtemp(prefix='relationship_map_text_e2e_'))
    try:
        store=RelationshipStore(tmp)
        for c in generate_contacts(contacts):
            store.upsert_contact({'id':c.id,'name':c.name,'city':c.city,'organization':c.organization,'role':c.role,'tags':c.tags,'created_at':c.created_at,'last_interaction_at':c.last_interaction_at,'next_touch_at':c.next_touch_at,'private':c.private,'metrics':c.metrics,'metric_evidence':c.metric_evidence,'facts':c.facts,'inferences':c.inferences}, confirmed=True)
        adapter=RelationshipViewAdapter(store)
        state={'page':1,'page_size':20,'query':'','city':'','sort':'updated_desc'}
        view=adapter.list_text(state)
        assert_true(view['total']==contacts,'写入总数错误')
        assert_true(len(view['rows'])<=20,'文本列表未分页')
        assert_true(all(not e['leaked'] for e in view['rows']),'一级文本列表泄露敏感字段')
        assert_true('想具体了解哪个人' in view['text'],'列表缺少自然语言下一步')
        forbidden=['['+'看某个人详情'+']','上一'+'页','下一'+'页','历史控件','inter'+'active','ca'+'rd','*'+'*','#'+'#','`'+'``']
        assert_true(not any(x in view['text'] for x in forbidden),'列表出现历史路线或格式源码痕迹')
        cid=view['rows'][0]['contact_id']; detail=adapter.detail_text(cid,state)
        assert_true('人脉详情' in detail['text'],'详情标题缺失')
        assert_true('如果要继续' in detail['text'],'详情缺少自然语言后续引导')
        assert_true(not any(x in detail['text'] for x in forbidden),'详情出现历史路线或格式源码痕迹')
        state2={'page':1,'page_size':20,'query':'','city':'重庆','sort':'updated_desc'}; c2=adapter.list_text(state2)
        assert_true(all('重庆' in e['line'] for e in c2['rows']),'城市筛选错误')
        before=len(list((tmp/'backups').glob('*.db'))); prop=store.propose_operation('delete',cid)
        try:
            store.apply_confirmed(prop,confirmed=False); raise AssertionError('未确认删除未被拦截')
        except PermissionError: pass
        store.apply_confirmed(prop,confirmed=True); after=len(list((tmp/'backups').glob('*.db'))); assert_true(after==before+1,'确认操作未备份')
        for i in range(rounds):
            page=(i%max(1,contacts//20))+1; city='重庆' if i%3==0 else ''
            view=adapter.list_text({'page':page,'page_size':20,'query':'','city':city,'sort':'updated_desc'})
            assert_true(len(view['rows'])<=20,'压力分页失败')
            assert_true(all(not e['leaked'] for e in view['rows']),'压力敏感泄露')
        store.close(); return {'passed':True,'mode':'relationship_view','contacts':contacts,'rounds':rounds,'vault_files':len(list(tmp.rglob('*')))}
    finally:
        shutil.rmtree(tmp,ignore_errors=True)
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--contacts',type=int,default=5000); ap.add_argument('--rounds',type=int,default=10000)
    args=ap.parse_args(); print(json.dumps(run(args.contacts,args.rounds),ensure_ascii=False,indent=2))




