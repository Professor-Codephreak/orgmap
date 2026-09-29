#!/usr/bin/env python3
"""Fetch a one-paragraph README summary for public originals and undescribed public forks into readme.json."""
import json, re, subprocess, base64
from concurrent.futures import ThreadPoolExecutor

def clean(t):
    t = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', t)
    t = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', t)
    t = re.sub(r'<[^>]+>', ' ', t)
    t = re.sub(r'[*_`#]{1,3}', '', t)
    return ' '.join(t.split())

def cut(t, n=320):
    return t if len(t) <= n else t[:n].rsplit(' ', 1)[0] + '…'

def summary(md, name=''):
    md = re.sub(r'<!--.*?-->', ' ', md, flags=re.S)
    md = re.sub(r'```.*?```', ' ', md, flags=re.S)
    md = re.sub(r'</?(p|div|h[1-6]|br)[^>]*>', '\n\n', md, flags=re.I)
    paras = [p.strip() for p in re.split(r'\n\s*\n', md) if p.strip()]
    for minlen in (40, 15):
        for para in paras:
            if para.startswith(('#', '|', '[![', '![', '---', '===', '- [', '* [')): continue
            t = clean(para)
            if len(t) >= minlen and re.search(r'[^\W\d_]{3}', t) and not t.startswith(('Hi there', 'Here are some ideas')):
                return cut(t)
    # fall back to the README title when it says more than the repo name
    for para in paras:
        if para.startswith('#'):
            t = clean(para.split('\n')[0])
            if t and not t.startswith('Hi there') and t.lower().replace('-', ' ').replace('_', ' ') != name.lower().replace('-', ' ').replace('_', ' ') and len(t) > 3:
                return cut(t)
            break
    return ''

def one(full):
    p = subprocess.run(['gh', 'api', f'repos/{full}/readme', '--jq', '.content'], capture_output=True, text=True)
    if p.returncode: return full, ''
    try: return full, summary(base64.b64decode(p.stdout).decode('utf-8', 'replace'), full.split('/')[1])
    except Exception: return full, ''

detail = json.load(open('detail.json'))
want = [f"{o}/{n}" for o, rs in detail.items() for n, r in rs.items()
        if not r['isPrivate'] and (not r['isFork'] or not (r['description'] or (r['parent'] or {}).get('description')))]
import os
res = json.load(open('readme.json')) if os.path.exists('readme.json') else {}
want = [w for w in want if not res.get(w)]
print(len(want), 'readmes to fetch', flush=True)
with ThreadPoolExecutor(8) as ex:
    res.update(dict(ex.map(one, want)))
json.dump(res, open('readme.json', 'w'), indent=0)
print('with summary', sum(bool(v) for v in res.values()))
