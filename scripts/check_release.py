#!/usr/bin/env python3
"""Fail closed when private/runtime files accidentally enter the Git index or release tree."""
from pathlib import Path
import subprocess
import sys

root=Path(__file__).resolve().parents[1]
required=['README.en.md','docs/USAGE.en.md','docs/FEISHU.en.md','tests/test_integration.py','docs/ACCEPTANCE.md','README.md','SKILL.md','LICENSE','SECURITY.md','CONTRIBUTING.md','CHANGELOG.md','.env.example','docs/USAGE.md','docs/FEISHU.md','tests/test_core.py','.github/workflows/check.yml']
missing=[f for f in required if not (root/f).is_file()]
if missing: print('Missing release files:',', '.join(missing));sys.exit(1)
private={'.env','data/','config.json','config.demo.json','.venv/'}
try:
    tracked=subprocess.check_output(['git','ls-files','-z'],cwd=root,stderr=subprocess.DEVNULL).decode().split('\0')
except (subprocess.CalledProcessError,FileNotFoundError): tracked=[]
bad=[p for p in tracked if p in private or any(p.startswith(x) for x in private if x.endswith('/')) or p.endswith(('.sqlite','.sqlite-wal','.sqlite-shm','.lock'))]
if bad: print('Private/runtime files tracked:',', '.join(bad));sys.exit(1)
if '.env' in tracked: print('Credential file tracked');sys.exit(1)
print('Release source files present; no private runtime files tracked.')
