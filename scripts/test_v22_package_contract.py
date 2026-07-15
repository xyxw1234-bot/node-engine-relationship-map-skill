#!/usr/bin/env python3
from pathlib import Path
root=Path(__file__).resolve().parents[1]
text=(root/'SKILL.md').read_text(encoding='utf-8')
installer=(root/'scripts/install_relationship_map_feishu_card.py').read_text(encoding='utf-8')
assert 'version: 2.2' in text
assert 'v2.2 Hard Requirement' in text
assert 'install_relationship_map_feishu_card.py' in text
assert 'relationship-map-feishu-card' in installer
assert '--enable' in installer
assert 'restart_required' in installer
assert (root/'scripts/run_v22_full_acceptance.py').exists()
assert '不得继续打开人脉地图' in text
print('v2.2 package contract ok')
