#!/usr/bin/env python3
from pathlib import Path
import sys
root=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
required=[
 'SKILL.md','节点引擎-人脉地图/SKILL.md','README.md','INSTALL.md','CHANGELOG.md',
 'references/list-ux.md','references/feishu-output-policy.md','references/v2.4-strict-lop.md',
 'relationship-map/SKILL.md','relationship-map/references/list-ux.md','relationship-map/references/feishu-output-policy.md','relationship-map/references/v2.4-strict-lop.md',
 'scripts/relationship_runtime.py','scripts/relationship_store.py','scripts/relationship_view_adapter.py','scripts/run_storage_view_e2e_tests.py','scripts/run_v24_acceptance.py',
 'relationship-map/scripts/relationship_runtime.py','relationship-map/scripts/relationship_store.py','relationship-map/scripts/relationship_view_adapter.py','relationship-map/scripts/run_storage_view_e2e_tests.py',
]
for rel in required:
    if not (root/rel).exists():
        print('缺少', rel); sys.exit(1)
for rel in ['SKILL.md','节点引擎-人脉地图/SKILL.md','relationship-map/SKILL.md']:
    txt=(root/rel).read_text(encoding='utf-8')
    if 'version: 2.4' not in txt:
        print('版本号不合格', rel); sys.exit(1)
    if '人脉管理 Skill' not in txt:
        print('定位不合格', rel); sys.exit(1)
removed_files=['plugins','scripts/feishu_'+'card_renderer.py','scripts/relationship_'+'card_adapter.py','scripts/test_relationship_map_feishu_plugin.py','scripts/install_relationship_map_feishu_'+'card.py','scripts/run_v22_full_acceptance.py','scripts/run_v22_strict_lop.py','scripts/create_github_release_v22.py','scripts/run_v23_plain_'+'text_acceptance.py','scripts/relationship_'+'text_adapter.py','scripts/run_storage_'+'text_e2e_tests.py','references/v2.2-strict-lop.md','references/v2.3-strict-lop.md','references/plain-'+'text-list-ux.md']
for rel in removed_files:
    if (root/rel).exists():
        print('残留历史文件', rel); sys.exit(1)
forbidden=['relationship-map-feishu-'+'card','pre_gateway_dispatch','relationship_map_action','msg_type=inter'+'active','inter'+'active ca'+'rd','but'+'ton','ca'+'rd','['+'看某个人详情'+']','纯'+'文本稳定版','纯'+'文字版','纯'+'文本版','plain_'+'text','text_'+'adapter','run_v23_plain_'+'text','v2.'+'3 是','v2.'+'0 到 v2.'+'2']
allow={'scripts/validate_skill_package.py','relationship-map/scripts/validate_skill_package.py','scripts/run_v24_acceptance.py','scripts/run_storage_view_e2e_tests.py','relationship-map/scripts/run_storage_view_e2e_tests.py'}
for p in root.rglob('*'):
    if not p.is_file() or '.git' in p.parts or '__pycache__' in p.parts or p.suffix not in {'.md','.py','.json','.yaml','.txt'}:
        continue
    rel=p.relative_to(root).as_posix()
    if rel in allow:
        continue
    txt=p.read_text(encoding='utf-8', errors='ignore')
    for x in forbidden:
        if x in txt:
            print('发现历史污染', rel, x); sys.exit(1)
for p in root.rglob('*'):
    if '.git' not in p.parts and ('__pycache__' in p.parts or p.suffix=='.pyc'):
        print('发现缓存污染', p); sys.exit(1)
print('校验通过：v2.4 人脉管理 Skill，历史污染扫描通过。')
