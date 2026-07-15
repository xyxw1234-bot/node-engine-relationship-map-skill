#!/usr/bin/env python3
from __future__ import annotations
import json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
FORBIDDEN_PATTERNS=[r'节点'+'引擎', r'Node '+'Engine', r'node-'+'engine', r'relationship-map-feishu-'+'card', r'pre_'+'gateway_dispatch', r'relationship_map_'+'action', r'msg_type=inter'+'active', r'inter'+'active ca'+'rd', r'飞书原生历史'+'复杂路线', r'\['+'看某个人详情'+r'\]', r'找某某智能体'+'帮你安装', r'帮我安装这个 '+'skill', r'装到某个'+'平台', r'```']
ALLOW_FILES={'CHANGELOG.md','scripts/run_v25_acceptance.py','scripts/validate_skill_package.py','relationship-map/scripts/validate_skill_package.py','scripts/run_storage_view_e2e_tests.py','relationship-map/scripts/run_storage_view_e2e_tests.py','relationship-map/scripts/run_v25_acceptance.py'}
TEXT_EXT={'.md','.py','.json','.yaml','.txt'}

def fail(msg):
    raise SystemExit(msg)

def cleanup_cache():
    for p in ROOT.rglob('__pycache__'):
        import shutil
        shutil.rmtree(p, ignore_errors=True)
    for p in ROOT.rglob('*.pyc'):
        p.unlink(missing_ok=True)

def scan():
    cleanup_cache()
    problems=[]
    for p in ROOT.rglob('*'):
        if not p.is_file() or '.git' in p.parts or '__pycache__' in p.parts: continue
        if p.suffix not in TEXT_EXT: continue
        rel=p.relative_to(ROOT).as_posix()
        txt=p.read_text(encoding='utf-8', errors='ignore')
        if rel in ALLOW_FILES:
            continue
        for pat in FORBIDDEN_PATTERNS:
            if re.search(pat, txt, flags=re.I):
                problems.append({'file':rel,'pattern':pat})
                break
    if problems:
        fail('发现固定名称依赖、历史复杂路线或格式源码污染：'+json.dumps(problems[:80],ensure_ascii=False,indent=2))

def run(cmd):
    p=subprocess.run(cmd, cwd=ROOT, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=300)
    if p.returncode:
        print(p.stdout); fail('命令失败：'+cmd)
    return p.stdout.strip()

def main():
    scan()
    outputs={
        'validate': run('python3 scripts/validate_skill_package.py .'),
        'view_e2e': run('python3 scripts/run_storage_view_e2e_tests.py --contacts 5000 --rounds 10000'),
        'runtime_stress': run('python3 scripts/run_runtime_stress_tests.py'),
        'py_compile': run('python3 -m py_compile scripts/relationship_view_adapter.py scripts/run_storage_view_e2e_tests.py scripts/validate_skill_package.py scripts/relationship_runtime.py'),
    }
    cleanup_cache()
    print(json.dumps({'passed':True,'version':'v2.5','mode':'brand_neutral_auto_install_relationship_view','outputs':outputs},ensure_ascii=False,indent=2))
if __name__=='__main__': main()
