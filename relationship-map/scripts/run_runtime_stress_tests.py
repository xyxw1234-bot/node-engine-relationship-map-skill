#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, random, sys
from relationship_runtime import RelationshipMapRuntime, generate_contacts, infer_adaptive_dimensions

def assert_true(cond, msg):
    if not cond:
        raise AssertionError(msg)

def run(contacts:int, rounds:int, seed:int=42, extended:bool=False):
    rt=RelationshipMapRuntime(generate_contacts(contacts, seed))
    should_open=["打开我的人脉地图。","看看我现在库里有哪些人。","联系人库打开一下。","打开重庆的人脉地图。"]
    should_not=["不要打开人脉地图。","别弹卡片。","刚才你错误打开了人脉地图。","比如用户说打开人脉地图时应该怎么设计？","张三是我重庆的人脉，帮我写个话术。","我想做人脉地图这个产品能力。","你的人脉地图触发机制不对。","我刚认识一个重庆客户，你帮我判断下怎么跟进。"]
    for s in should_open:
        assert_true(rt.classify_intent(s)=="open_map", f"应打开但未打开: {s}")
    assert_true(rt.classify_intent("能不能打开人脉地图？")=="confirm", "疑问句应确认而不是打开")
    parsed=rt.parse_open_request("打开重庆的人脉地图。")
    assert_true(parsed["intent"]=="open_map" and parsed["state"]["city"]=="重庆", "城市打开请求未带筛选")
    for s in should_not:
        assert_true(rt.classify_intent(s)!="open_map", f"不应打开却打开: {s}")
    # 大列表分页、不泄露敏感字段
    lv=rt.list_view(page=1,page_size=15)
    assert_true(lv['total']==contacts, '总数不对')
    assert_true(len(lv['cards'])<=15, '一级列表未分页')
    assert_true(lv['has_next'] is (contacts>15), '下一页状态错误')
    for card in lv['cards']:
        assert_true(not card['leaked'], f"一级列表泄露敏感信息: {card}")
        assert_true(card['text'].count('\n')<=3, '一级摘要超过姓名+两行+按钮')
    # 详情/返回状态
    state={"page":2,"page_size":15,"query":"","city":"重庆","sort":"updated_desc"}
    lv2=rt.list_view(**state)
    if lv2['cards']:
        cid=lv2['cards'][0]['id']
        detail=rt.detail_view(cid,state)
        assert_true('返回人脉地图' in detail['buttons'], '详情缺返回按钮')
        assert_true('加入机会地图' in detail['buttons'], '详情缺加入机会地图')
        back=rt.return_to_list(detail)
        assert_true(back['page']==state['page'] and back['city']==state['city'], '返回未恢复状态')
    # 指标按需：构造低信息联系人不应有指标
    low=[c for c in rt.contacts.values() if not c.last_interaction_at and not c.metrics]
    assert_true(len(low)>0, '测试数据缺少低信息联系人')
    # 写入必须确认，确认后追加时间线
    cid=next(iter(rt.contacts))
    before=len(rt.contacts[cid].timeline)
    prop=rt.propose_update(cid,'role','新角色',sensitive=True)
    assert_true(prop['requires_confirmation'], '敏感更新未要求确认')
    assert_true(len(rt.contacts[cid].timeline)==before, '未确认就写入了时间线')
    rt.apply_confirmed_update(prop)
    assert_true(len(rt.contacts[cid].timeline)==before+1, '确认更新未追加时间线')
    # 随机压力：分页、详情、返回
    for _ in range(rounds):
        city=random.choice(["重庆","上海","北京","深圳","成都","杭州","郑州","广州","西安","武汉",""])
        page=random.randint(1, max(1, contacts//15))
        lv=rt.list_view(page=page,page_size=15,city=city)
        assert_true(len(lv['cards'])<=15, '压力测试分页失效')
        for card in lv['cards']:
            assert_true(not card['leaked'], '压力测试一级列表泄密')
        if lv['cards']:
            detail=rt.detail_view(random.choice(lv['cards'])['id'], {"page":page,"page_size":15,"query":"","city":city,"sort":"updated_desc"})
            back=rt.return_to_list(detail)
            assert_true(back['city']==city and back['page']==page, '压力测试返回状态丢失')
    if extended:
        # 所有显示指标必须有依据；无依据指标不得出现在列表/详情
        for c in rt.contacts.values():
            for k in c.metrics:
                assert_true(k in c.metric_evidence, f"指标缺依据: {c.id}:{k}")
        # 所有敏感字段类型都应进入生成集，且一级列表不能泄露
        sensitive_seen=set()
        for c in rt.contacts.values():
            sensitive_seen.update(c.private.keys())
        for key in ["phone","wechat","address","id_number","finance_note","private_judgment"]:
            assert_true(key in sensitive_seen, f"敏感字段未覆盖: {key}")
        for page in range(1, min(20, max(2, contacts//15))):
            lv=rt.list_view(page=page,page_size=15)
            for card in lv['cards']:
                assert_true(not card['leaked'], '扩展敏感测试一级列表泄密')
        # 高风险操作全部必须 proposal + confirm
        cid=next(iter(rt.contacts))
        ops=[("delete","deleted",True),("merge","merge_target","x"),("bulk_import","batch","x"),("sensitive_label","sensitive","x"),("risk_assessment","risk_level","高"),("trust_assessment","trust_level","高")]
        for op,field,val in ops:
            before=len(rt.contacts[cid].timeline)
            prop=rt.propose_update(cid, field, val, sensitive=True, operation=op)
            assert_true(prop['requires_confirmation'], f"{op} 未要求确认")
            assert_true(len(rt.contacts[cid].timeline)==before, f"{op} 未确认就写入")
            rt.apply_confirmed_update(prop)
            assert_true(len(rt.contacts[cid].timeline)==before+1, f"{op} 确认后未追加时间线")
        try:
            rt.propose_update(cid,'__dict__','bad',operation='update')
            raise AssertionError('非法字段未被拒绝')
        except ValueError:
            pass
    assert_true(any(d["role"]=="投资人" and "投资偏好" in d["dimensions"] for d in infer_adaptive_dimensions("张三是投资人")), "投资人自适应维度缺失")
    assert_true(any(d["role"]=="校长" and "决策关注点" in d["dimensions"] for d in infer_adaptive_dimensions("李四是校长")), "校长自适应维度缺失")
    assert_true(any(d["role"]=="资源连接者" for d in infer_adaptive_dimensions("他帮我介绍过人")), "引荐维度缺失")
    return {"passed": True, "contacts": contacts, "rounds": rounds, "extended": extended, "open_cases": len(should_open), "blocked_cases": len(should_not)}

if __name__ == '__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--contacts',type=int,default=500)
    ap.add_argument('--rounds',type=int,default=2000)
    ap.add_argument('--seed',type=int,default=42)
    ap.add_argument('--extended', action='store_true')
    args=ap.parse_args()
    print(json.dumps(run(args.contacts,args.rounds,args.seed,args.extended), ensure_ascii=False, indent=2))
