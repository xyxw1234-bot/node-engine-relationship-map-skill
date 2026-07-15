#!/usr/bin/env python3
"""飞书原生交互卡片渲染器。

平台中立输入 -> 飞书 interactive card JSON。
不依赖流式卡片插件；作为没有流式卡片时的兜底展示层。
"""
from __future__ import annotations
from typing import Any, Dict, List
import json

BRAND_COLOR="blue"

def md(text:str)->Dict[str,Any]:
    return {"tag":"div","text":{"tag":"lark_md","content":text}}

def button(text:str, action:str, **value)->Dict[str,Any]:
    return {"tag":"button","text":{"tag":"plain_text","content":text},"type":"default","value":{"action":action,**value}}

def actions(*buttons):
    return {"tag":"action","actions":list(buttons)}

def card(title:str, elements:List[Dict[str,Any]], color:str=BRAND_COLOR)->Dict[str,Any]:
    return {"config":{"wide_screen_mode":True},"header":{"template":color,"title":{"tag":"plain_text","content":title}},"elements":elements}

def empty_card()->Dict[str,Any]:
    return card("人脉地图",[
        md("当前还没有联系人。\n你可以直接说一句话，我会帮你建立第一张人脉卡。\n例如：帮我记录张三，重庆人，做文旅资源。"),
        actions(button("添加联系人示例","relationship_example", kind="add_contact"), button("查看使用说明","relationship_secondary", page="help"))
    ])

def list_card(list_state:Dict[str,Any])->Dict[str,Any]:
    total=list_state.get('total',0); state=list_state.get('state',{})
    elements=[md(f"共 {total} 人｜第 {state.get('page',1)} 页\n每张卡只显示摘要，点击查看详情。")]
    for item in list_state.get('elements',[]):
        summary=item['summary']
        elements.append(md(summary))
        elements.append(actions(button("查看详情","relationship_detail", contact_id=item['contact_id'], return_state=state)))
    nav=[]
    if state.get('page',1)>1: nav.append(button("上一页","relationship_list", **{**state,'page':state.get('page',1)-1}))
    if list_state.get('has_next'): nav.append(button("下一页","relationship_list", **{**state,'page':state.get('page',1)+1}))
    nav.append(button("筛选/搜索","relationship_secondary", page="filters", return_state=state))
    elements.append(actions(*nav))
    return card("人脉地图｜列表",elements)

def detail_card(detail:Dict[str,Any])->Dict[str,Any]:
    lines=[f"**{detail.get('name','联系人')}**"]
    for k in ['city','organization','role']:
        if detail.get(k): lines.append(f"{k}：{detail[k]}")
    metrics=detail.get('metrics') or {}
    if metrics:
        lines.append("\n**关系判断**")
        for k,v in metrics.items(): lines.append(f"- {k}：{v}")
    ts=detail.get('timestamps') or {}
    if ts:
        lines.append("\n**时间**")
        for k,v in ts.items():
            if v: lines.append(f"- {k}：{v}")
    timeline=detail.get('timeline') or []
    if timeline:
        lines.append("\n**最近时间线**")
        for e in timeline[:5]: lines.append(f"- {e.get('timestamp','')}｜{e.get('summary','')}")
    return_state=detail.get('return_state') or {}
    return card("人脉地图｜详情",[
        md("\n".join(lines)),
        actions(button("返回人脉地图","relationship_list", **return_state), button("更新此人信息","relationship_update", contact_id=detail['contact_id']), button("生成联系话术","relationship_outreach", contact_id=detail['contact_id']), button("加入机会地图","relationship_opportunity", contact_id=detail['contact_id']))
    ])

def confirm_card(proposal:Dict[str,Any])->Dict[str,Any]:
    return card("人脉地图｜确认保存",[
        md(f"请确认是否保存这次变更：\n{proposal.get('preview','待确认变更')}"),
        actions(button("确认保存","relationship_confirm", proposal_id=proposal.get('id')), button("修改","relationship_modify", proposal_id=proposal.get('id')), button("放弃","relationship_cancel", proposal_id=proposal.get('id')))
    ], color="orange")

def secondary_card(page:str, context:Dict[str,Any]|None=None)->Dict[str,Any]:
    context=context or {}
    pages={
        "help":"你可以直接用自然语言记录人脉：\n- 帮我记录张三，重庆人，做文旅资源。\n- 张三是投资人，帮我整理下适合怎么联系。\n- 我下周去重庆，看看适合联系谁。",
        "filters":"常用筛选：城市、行业、项目、待跟进、久未联系、关系温度。\n复杂筛选放在二级页，一级列表保持干净。",
        "adaptive":"复杂能力模块会进入二级页面：投资人分析、政府/协会关系、校长客户、供应链伙伴、风险关系等。"
    }
    return_state=context.get('return_state') or {"page":1,"page_size":15,"query":"","city":"","sort":"updated_desc"}
    return card("人脉地图｜二级页面",[
        md(pages.get(page,"该模块正在准备中。")),
        actions(button("返回人脉地图","relationship_list", **return_state))
    ])

def example_card()->Dict[str,Any]:
    return card("人脉地图｜示例",[
        md("**三个高频用法**\n1. 帮我记录张三，重庆人，做文旅资源。\n2. 张三是投资人，帮我分析适合怎么沟通。\n3. 我下周去重庆，看看适合联系谁。"),
        actions(button("开始记录","relationship_example", kind="add_contact"), button("返回人脉地图","relationship_list", page=1,page_size=15,query="",city="",sort="updated_desc"))
    ])

if __name__=='__main__':
    print(json.dumps(empty_card(), ensure_ascii=False, indent=2))
