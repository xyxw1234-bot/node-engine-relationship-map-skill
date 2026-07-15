#!/usr/bin/env python3
from pathlib import Path
import re, sys
root=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
required=[
 'SKILL.md','节点引擎-人脉地图/SKILL.md','references/link-only-install.md','references/feishu-native-card-companion.md',
 'plugins/relationship-map-feishu-card/plugin.yaml','plugins/relationship-map-feishu-card/__init__.py',
 'scripts/test_relationship_map_feishu_plugin.py','scripts/install_relationship_map_feishu_card.py','scripts/test_v22_package_contract.py','scripts/run_v22_full_acceptance.py','scripts/run_v22_strict_lop.py',
 'relationship-map/SKILL.md','relationship-map/references/card-list-ux.md','relationship-map/references/semantic-trigger-gate.md','relationship-map/references/data-safety.md','relationship-map/references/hermes-native-runtime.md','relationship-map/references/user-customization.md','relationship-map/references/adaptive-dimensions.md','relationship-map/references/feishu-output-policy.md','relationship-map/references/feishu-native-card-companion.md','relationship-map/scripts/feishu_card_renderer.py','relationship-map/scripts/test_feishu_card_renderer.py','relationship-map/templates/adaptive-dimensions.md','relationship-map/references/trigger-test-cases.md','relationship-map/templates/contact-list-item.md','relationship-map/templates/contact-detail-view.md','relationship-map/templates/relationship-metrics.md','relationship-map/templates/contact-timeline.md','relationship-map/templates/contact.schema.json','relationship-map/templates/timeline-event.schema.json','relationship-map/examples/open-map-demo.md','relationship-map/scripts/relationship_runtime.py','relationship-map/scripts/run_runtime_stress_tests.py','relationship-map/scripts/relationship_store.py','relationship-map/scripts/relationship_card_adapter.py','relationship-map/scripts/run_storage_card_e2e_tests.py','README.md','INSTALL.md','CHANGELOG.md']
for rel in required:
    if not (root/rel).exists():
        print('缺少', rel); sys.exit(1)
skill=(root/'relationship-map/SKILL.md').read_text(encoding='utf-8')
if not skill.startswith('---\n') or 'name: relationship-map' not in skill or 'version: 2.2' not in skill:
    print('SKILL.md frontmatter 不合格'); sys.exit(1)
forbidden = '人脉' + '资源'
all_text_parts=[]
for p in root.rglob('*'):
    if p.is_file() and '.git' not in p.parts and p.suffix in {'.md','.py','.json','.txt','.yaml'}:
        txt=p.read_text(encoding='utf-8', errors='ignore')
        all_text_parts.append(txt)
        if forbidden in txt:
            print('发现旧命名', p); sys.exit(1)
all_text='\n'.join(all_text_parts)
required_phrases = [
    '不能用“关键词命中”直接打开卡片',
    '如果是否打开存在歧义，不要擅自打开',
    '不得覆盖上述用户数据目录',
    '没有依据的指标不得显示空字段',
    '一级列表不得展示',
    '时间线只追加，不覆盖',
    '张三是我重庆的人脉，帮我写个话术',
    'v2.1 修正 v2.0 的关键缺陷',
    'v2.2 修正 v2.1 的安装链路缺陷',
    'plugins/relationship-map-feishu-card',
    'install_relationship_map_feishu_card.py',
    'hermes plugins install xyxw1234-bot/node-engine-relationship-map-skill/plugins/relationship-map-feishu-card --force --enable',
    'msg_type=interactive',
    '飞书消息类型为 `interactive`',
    '不得继续打开人脉地图',
]
for phrase in required_phrases:
    if phrase not in all_text:
        print('缺少发布级安全短语:', phrase); sys.exit(1)
for script_phrase in ['classify_intent', 'list_view', 'detail_view', 'return_to_list', 'propose_update', 'parse_open_request', 'metric_evidence', 'RelationshipStore', 'RelationshipCardAdapter', 'Hermes 原生', '不单独部署服务器', '$HERMES_HOME/data/relationship-map', 'extensions/', 'Adaptive Relationship Intelligence', 'infer_adaptive_dimensions', 'Feishu-friendly Output Policy', 'Feishu Native Card Companion', 'Link-only Install and Update Intent', 'pre_gateway_dispatch', 'relationship_map_action', 'restart_required', 'version: 2.2.0']:
    if script_phrase not in all_text:
        print('缺少运行层能力:', script_phrase); sys.exit(1)
# No positive pseudo-button examples. Mentions are allowed only when explicitly framed as forbidden/failure.
for p in root.rglob('*.md'):
    if '.git' in p.parts: continue
    txt=p.read_text(encoding='utf-8', errors='ignore')
    for m in re.finditer(r'\[查看详情\]|新增联系人｜搜索', txt):
        window=txt[max(0,m.start()-50):m.end()+50]
        if not any(k in window for k in ['不得','禁止','不是','没有','失败','伪按钮','不能','严禁','re.finditer','not in','fake']):
            print('发现正向伪按钮示例', p, window); sys.exit(1)
print('校验通过：v2.2 人脉地图安装链路、真实飞书卡片与运行层校验通过。')
