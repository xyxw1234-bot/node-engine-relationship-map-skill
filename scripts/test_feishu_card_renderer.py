#!/usr/bin/env python3
from feishu_card_renderer import empty_card, list_card, detail_card, confirm_card, secondary_card, example_card

def assert_true(cond,msg):
    if not cond: raise AssertionError(msg)

def walk_text(obj):
    if isinstance(obj, dict):
        for v in obj.values(): yield from walk_text(v)
    elif isinstance(obj, list):
        for v in obj: yield from walk_text(v)
    elif isinstance(obj, str):
        yield obj

def check_card(c):
    assert_true(c.get('header'), '缺 header')
    assert_true(c.get('elements'), '缺 elements')
    txt='\n'.join(walk_text(c))
    assert_true('---' not in txt, '不应出现 Markdown 分割线')
    assert_true('```' not in txt, '不应出现代码块')

if __name__=='__main__':
    state={'page':1,'page_size':15,'query':'','city':'','sort':'updated_desc'}
    lc={'total':1,'state':state,'has_next':False,'elements':[{'contact_id':'c1','summary':'张三｜重庆｜投资人\n最近互动：2026-01-01\n下一步：待跟进'}]}
    detail={'contact_id':'c1','return_state':state,'name':'张三','city':'重庆','organization':'测试机构','role':'投资人','metrics':{'relationship_temperature':'温'},'timestamps':{'created_at':'2026-01-01','updated_at':'2026-01-02'},'timeline':[{'timestamp':'2026-01-02','summary':'饭局见面'}]}
    for c in [empty_card(), list_card(lc), detail_card(detail), confirm_card({'id':'p1','preview':'新增张三'}), secondary_card('adaptive', {'return_state':state}), example_card()]:
        check_card(c)
    assert_true(any(a.get('value',{}).get('action')=='relationship_detail' for e in list_card(lc)['elements'] for a in (e.get('actions') or [])), '列表缺详情按钮')
    assert_true(any(a.get('text',{}).get('content')=='返回人脉地图' for e in detail_card(detail)['elements'] for a in (e.get('actions') or [])), '详情缺返回按钮')
    print('feishu card renderer ok')
