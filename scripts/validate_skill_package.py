#!/usr/bin/env python3
from pathlib import Path
import sys
root=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
required=[
 'SKILL.md','人脉地图/SKILL.md','README.md','INSTALL.md',
 'references/list-ux.md','references/feishu-output-policy.md','references/v2.6-strict-lop.md',
 'relationship-map/SKILL.md','relationship-map/references/list-ux.md','relationship-map/references/feishu-output-policy.md','relationship-map/references/v2.6-strict-lop.md',
 'scripts/relationship_runtime.py','scripts/relationship_store.py','scripts/relationship_view_adapter.py','scripts/run_storage_view_e2e_tests.py','scripts/run_v26_acceptance.py',
 'relationship-map/scripts/relationship_runtime.py','relationship-map/scripts/relationship_store.py','relationship-map/scripts/relationship_view_adapter.py','relationship-map/scripts/run_storage_view_e2e_tests.py','relationship-map/scripts/run_v26_acceptance.py',
]
for rel in required:
    if not (root/rel).exists():
        print('缺少', rel); sys.exit(1)
for rel in ['SKILL.md','人脉地图/SKILL.md','relationship-map/SKILL.md']:
    txt=(root/rel).read_text(encoding='utf-8')
    if 'version: 2.6' not in txt:
        print('版本号不合格', rel); sys.exit(1)
    if '人脉管理 Skill' not in txt:
        print('定位不合格', rel); sys.exit(1)
    if '收到链接时的安装规则' not in txt:
        print('安装规则缺失', rel); sys.exit(1)
removed_files=['plugins','节点'+'引擎-人脉地图','scripts/feishu_'+'card_renderer.py','scripts/relationship_'+'card_adapter.py','scripts/test_relationship_map_feishu_plugin.py','scripts/install_relationship_map_feishu_'+'card.py','scripts/run_v'+'22_full_acceptance.py','scripts/run_v'+'22_strict_lop.py','scripts/create_github_release_v'+'22.py','scripts/run_v'+'23_plain_'+'text_acceptance.py','scripts/run_v'+'24_acceptance.py','scripts/relationship_'+'text_adapter.py','scripts/run_storage_'+'text_e2e_tests.py','references/v'+'22-strict-lop.md','references/v'+'23-strict-lop.md','references/v'+'24-strict-lop.md','references/v'+'25-strict-lop.md','scripts/run_v'+'25_acceptance.py','references/plain-'+'text-list-ux.md']
for rel in removed_files:
    if (root/rel).exists():
        print('残留历史文件', rel); sys.exit(1)
forbidden=['节点'+'引擎','Node '+'Engine','node-'+'engine','relationship-map-feishu-'+'card','pre_'+'gateway_dispatch','relationship_map_'+'action','msg_type=inter'+'active','inter'+'active ca'+'rd','but'+'ton','ca'+'rd','['+'看某个人详情'+']','纯'+'文本稳定版','纯'+'文字版','纯'+'文本版','plain_'+'text','text_'+'adapter','run_v'+'23_plain_'+'text','run_v'+'24_acceptance','v2.'+'3 是','v2.'+'4','2.'+'4','v2.'+'5','2.'+'5','v2.'+'0 到 v2.'+'2','找某某智能体'+'帮你安装','帮我安装这个 '+'skill','装到某个'+'平台','上一'+'页','下一'+'页','分页展示','每页建议 10 到 15 人']
allow={'scripts/validate_skill_package.py','relationship-map/scripts/validate_skill_package.py','scripts/run_v26_acceptance.py','scripts/run_storage_view_e2e_tests.py','relationship-map/scripts/run_storage_view_e2e_tests.py','relationship-map/scripts/run_v26_acceptance.py'}
for p in root.rglob('*'):
    if not p.is_file() or '.git' in p.parts or '__pycache__' in p.parts or p.suffix not in {'.md','.py','.json','.yaml','.txt'}:
        continue
    rel=p.relative_to(root).as_posix()
    if rel in allow:
        continue
    txt=p.read_text(encoding='utf-8', errors='ignore')
    for x in forbidden:
        if x in txt:
            print('发现发布污染', rel, x); sys.exit(1)
for p in root.rglob('*'):
    if '.git' not in p.parts and ('__pycache__' in p.parts or p.suffix=='.pyc'):
        print('发现缓存污染', p); sys.exit(1)

required_semantic_terms=['按联系频次排序','关系最密切','变生疏','长沙认识的朋友','打标签','安装完成后，不要只说安装成功','资料解析','会前准备','会后沉淀','资源路径','关键人维护','可调动度']
for rel in ['SKILL.md','人脉地图/SKILL.md','relationship-map/SKILL.md']:
    txt=(root/rel).read_text(encoding='utf-8')
    for term in required_semantic_terms[:11]:
        if term not in txt:
            print('缺少语义能力示例', rel, term); sys.exit(1)
for rel in ['README.md','INSTALL.md']:
    txt=(root/rel).read_text(encoding='utf-8')
    if required_semantic_terms[-1] not in txt:
        print('缺少安装后能力展示要求', rel); sys.exit(1)

print('校验通过：v2.6 人脉管理 Skill，安装体验和历史污染扫描通过。')




