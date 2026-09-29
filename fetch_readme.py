#!/usr/bin/env python3
"""Fetch a one-paragraph README summary for public originals and undescribed public forks into readme.json."""
import json, re, subprocess, base64
from concurrent.futures import ThreadPoolExecutor

def summary(md):
    md = re.sub(r'<!--.*?-->', ' ', md, flags=re.S)
    md = re.sub(r'```.*?```', ' ', md, flags=re.S)
    for para in re.split(r'\n\s*\n', md):
        t = para.strip()
        if not t or t.startswith(('#', '|', '<', '[![', '![', '---', '===', '>', '- [', '* [', '```')):
            continue
        t = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', t)
        t = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', t)
        t = re.sub(r'<[^>]+>', '', t)
        t = re.sub(r'[*_`]{1,3}', '', t)
        t = ' '.join(t.split())
        if len(t) >= 40 and re.search(r'[a-zA-Z]{3}', t):
            return t if len(t) <= 320 else t[:320].rsplit(' ', 1)[0] + '…'
    return ''

def one(full):
    p = subprocess.run(['gh', 'api', f'repos/{full}/readme', '--jq', '.content'], capture_output=True, text=True)
    if p.returncode: return full, ''
    try: return full, summary(base64.b64decode(p.stdout).decode('utf-8', 'replace'))
    except Exception: return full, ''

detail = json.load(open('detail.json'))
want = [f"{o}/{n}" for o, rs in detail.items() for n, r in rs.items()
        if not r['isPrivate'] and (not r['isFork'] or not (r['description'] or (r['parent'] or {}).get('description')))]
print(len(want), 'readmes', flush=True)
with ThreadPoolExecutor(8) as ex:
    res = dict(ex.map(one, want))
json.dump(res, open('readme.json', 'w'), indent=0)
print('with summary', sum(bool(v) for v in res.values()))
