#!/usr/bin/env python3
from pathlib import Path
import re, sys
root=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
required=['relationship-map/SKILL.md','relationship-map/references/card-list-ux.md','relationship-map/references/semantic-trigger-gate.md','relationship-map/references/data-safety.md','relationship-map/references/hermes-native-runtime.md','relationship-map/references/user-customization.md','relationship-map/references/adaptive-dimensions.md','relationship-map/references/feishu-output-policy.md','relationship-map/references/feishu-native-card-companion.md','relationship-map/scripts/feishu_card_renderer.py','relationship-map/scripts/test_feishu_card_renderer.py','relationship-map/templates/adaptive-dimensions.md','relationship-map/references/trigger-test-cases.md','relationship-map/templates/contact-list-item.md','relationship-map/templates/contact-detail-view.md','relationship-map/templates/relationship-metrics.md','relationship-map/templates/contact-timeline.md','relationship-map/templates/contact.schema.json','relationship-map/templates/timeline-event.schema.json','relationship-map/examples/open-map-demo.md','relationship-map/scripts/relationship_runtime.py','relationship-map/scripts/run_runtime_stress_tests.py','relationship-map/scripts/relationship_store.py','relationship-map/scripts/relationship_card_adapter.py','relationship-map/scripts/run_storage_card_e2e_tests.py','README.md','INSTALL.md','CHANGELOG.md']
for rel in required:
    if not (root/rel).exists():
        print('缺少', rel); sys.exit(1)
skill=(root/'relationship-map/SKILL.md').read_text(encoding='utf-8')
if not skill.startswith('---\n') or 'name: relationship-map' not in skill or 'version: 2.0' not in skill:
    print('SKILL.md frontmatter 不合格'); sys.exit(1)
forbidden = '人脉' + '资源'
if forbidden in skill:
    print('SKILL.md 仍含旧命名'); sys.exit(1)
for p in root.rglob('*'):
    if p.is_file() and '.git' not in p.parts and p.suffix in {'.md','.py','.json','.txt'}:
        txt=p.read_text(encoding='utf-8', errors='ignore')
        if forbidden in txt:
            print('发现旧命名', p); sys.exit(1)

for phrase in ['不能用“关键词命中”直接打开卡片', 'Intent gate before opening', 'Do not open examples', '如果是否打开存在歧义，不要擅自打开']:
    if phrase not in skill:
        print('缺少语义触发闸门:', phrase); sys.exit(1)

required_phrases = [
    '不能用“关键词命中”直接打开卡片',
    '如果是否打开存在歧义，不要擅自打开',
    '不得覆盖上述用户数据目录',
    '没有依据的指标不得显示空字段',
    '一级列表不得展示',
    '时间线只追加，不覆盖',
    '张三是我重庆的人脉，帮我写个话术',
]
all_text = ''.join(p.read_text(encoding='utf-8', errors='ignore') for p in root.rglob('*') if p.is_file() and '.git' not in p.parts and p.suffix in {'.md','.py','.json','.txt'})
for phrase in required_phrases:
    if phrase not in all_text:
        print('缺少发布级安全短语:', phrase); sys.exit(1)

for script_phrase in ['classify_intent', 'list_view', 'detail_view', 'return_to_list', 'propose_update', 'parse_open_request', 'metric_evidence', 'RelationshipStore', 'RelationshipCardAdapter', 'Hermes 原生', '不单独部署服务器', '$HERMES_HOME/data/relationship-map', 'extensions/', 'Adaptive Relationship Intelligence', 'infer_adaptive_dimensions', 'Feishu-friendly Output Policy', 'Feishu Native Card Companion', 'Link-only Install and Update Intent']:
    if script_phrase not in all_text:
        print('缺少运行层能力:', script_phrase); sys.exit(1)
print('校验通过：v2.0 人脉地图发布级安全与运行层校验通过，未发现旧命名。')
