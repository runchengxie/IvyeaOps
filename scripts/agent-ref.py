#!/usr/bin/env python3
"""Resolve the validated IvyeaAgent ref or an explicit override."""
import os
from pathlib import Path
import re
import sys

config = Path(__file__).resolve().parents[1] / 'configs' / 'ivyea-agent.ref'
ref = os.environ.get('IVYEA_AGENT_REF') or config.read_text(encoding='utf-8').strip()
if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._/-]*', ref) or '..' in ref:
    sys.exit('Invalid IvyeaAgent ref')
print(ref)
