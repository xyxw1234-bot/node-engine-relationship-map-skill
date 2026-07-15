#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,random
from relationship_runtime import RelationshipMapRuntime, generate_contacts

def assert_true(cond,msg):
    if not cond: raise AssertionError(msg)

def run(contacts:int=500, rounds:int=2000, extended:bool=False):
    rt=RelationshipMapRuntime(generate_contacts(contacts))
    should_open=["打开我的人脉地图。","看看我现在库里有哪些人。","联系人库打开一下。","打开重庆的人脉地图。"]
    should_not=["不要打开人脉地图。","刚才你错误进入了人脉地图。","比如用户说打开人脉地图时应该怎么设计？","张三是我重庆的人脉，帮我写个话术。","我想做人脉地图这个产品能力。","你的人脉地图触发机制不对。","我刚认识一个重庆客户，你帮我判断下怎么跟进。"]
    for s in should_open:
        assert_true(rt.classify_intent(s)=='open_map', f'应打开但未打开: {s}')
    for s in should_not:
        assert_true(rt.classify_intent(s)!='open_map', f'不应打开却打开: {s}')
    confirm="我是不是可以打开人脉地图？"
    assert_true(rt.classify_intent(confirm)=='confirm','疑问句应先确认')
    assert_true(rt.classify_intent('好，继续展现')=='continue_list','自然语言继续展现未识别')
    lv=rt.list_view(page=1,page_size=20)
    assert_true(lv['total']==contacts, '总数不对')
    assert_true(len(lv['items'])<=20, '一级列表未分组展现')
    assert_true(lv['has_next'] is (contacts>20), '继续展现状态错误')
    for item in lv['items']:
        assert_true(not item['leaked'], f"一级列表泄露敏感信息: {item}")
        assert_true(item['text'].count('\n')<=2, '一级摘要超过三行')
        assert_true('历史控件' not in item['text'], '一级摘要有不该出现的旧痕迹')
    state={"page":2,"page_size":15,"query":"","city":"重庆","sort":"updated_desc"}
    lv2=rt.list_view(page=state["page"], page_size=state["page_size"], query=state["query"], city=state["city"], sort=state["sort"])
    if lv2['items']:
        cid=lv2['items'][0]['id']
        detail=rt.detail_view(cid,state)
        assert_true('next_actions' in detail, '详情缺自然语言后续动作')
        back=rt.return_to_list(detail)
        assert_true(back['page']==state['page'] and back['city']==state['city'], '返回状态丢失')
    p=rt.propose_update(random.choice(list(rt.contacts.keys())), 'metrics', {'risk_level':'高'}, operation='risk_assessment')
    assert_true(p['requires_confirmation'], '风险评估必须确认')
    before=len([c for c in rt.contacts.values() if c.deleted])
    delete=rt.propose_update(random.choice(list(rt.contacts.keys())), 'deleted', True, operation='delete')
    assert_true(delete['requires_confirmation'], '删除必须确认')
    rt.apply_confirmed_update(delete)
    after=len([c for c in rt.contacts.values() if c.deleted])
    assert_true(after==before+1, '确认删除未生效')
    for i in range(rounds):
        city='重庆' if i%3==0 else ''
        page=(i%max(1,contacts//20))+1
        lv=rt.list_view(page=page,page_size=20,city=city)
        assert_true(len(lv['items'])<=20, '压力测试分组展现失效')
        for item in lv['items']:
            assert_true(not item['leaked'], '压力测试一级列表泄密')
        if lv['items']:
            detail=rt.detail_view(random.choice(lv['items'])['id'], {"page":page,"page_size":15,"query":"","city":city,"sort":"updated_desc"})
            back=rt.return_to_list(detail)
            assert_true(back['page']==page and back['city']==city, '压力测试返回状态丢失')
    if extended:
        for text in ['投资人介绍了一个项目','校长说预算流程复杂','会长可以引荐资源','对方没兑现承诺']:
            assert_true(rt.classify_intent(text)=='normal','普通叙述不应打开')
    return {'passed':True,'contacts':contacts,'rounds':rounds,'extended':extended,'open_cases':len(should_open),'blocked_cases':len(should_not)}
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--contacts',type=int,default=500); ap.add_argument('--rounds',type=int,default=2000); ap.add_argument('--extended',action='store_true')
    a=ap.parse_args(); print(json.dumps(run(a.contacts,a.rounds,a.extended),ensure_ascii=False,indent=2))


