#!/usr/bin/env python3
"""Build the org map from data.json (written by fetch.py)."""
import json, os, re
from datetime import datetime, timezone

d = json.load(open('data.json'))
GH = 'https://github.com'
os.makedirs('map', exist_ok=True)

def esc(s):
    return (s or '').replace('|', '\\|').replace('\n', ' ').replace('<', '&lt;').strip()

def url(u):
    u = (u or '').strip()
    if not u: return ''
    if not re.match(r'^https?://', u): u = 'https://' + u
    return u

def slug(name):
    return name.lower()

def page(kind, login, v):
    repos = sorted(v['repos'], key=lambda r: (r['archived'], r['fork'], -(r['stargazers_count'] or 0), r['name'].lower()))
    m = v['meta']
    L = [f"# [{login}]({GH}/{login})", '']
    L.append(f"[← all organizations](../README.md) · [profile]({GH}/{login}) · "
             f"[repositories]({GH}/{login}?tab=repositories)" if kind == 'user' else
             f"[← all organizations](../README.md) · [profile]({GH}/{login}) · "
             f"[repositories]({GH}/orgs/{login}/repositories) · [people]({GH}/orgs/{login}/people)")
    L.append('')
    if m.get('description'): L += [f"> {esc(m['description'])}", '']
    if m.get('blog'): L += [f"Website: <{url(m['blog'])}>", '']
    n = len(repos); p = sum(r['private'] for r in repos); f = sum(r['fork'] for r in repos); a = sum(r['archived'] for r in repos)
    L += [f"**{n}** repos · {n-p} public · {p} private 🔒 · {f} forks · {a} archived", '']
    if not repos:
        L += ['_No repositories._', '']
    else:
        L += ['| Repository | Description | Language | ★ | Links |', '|---|---|---|--:|---|']
        for r in repos:
            flags = (' 🔒' if r['private'] else '') + (' 🍴' if r['fork'] else '') + (' 📦' if r['archived'] else '')
            name = f"[{r['name']}]({r['html_url']}){flags}"
            lang = f"[{r['language']}]({GH}/{login}?language={r['language'].lower().replace(' ','+')})" if r['language'] and kind=='user' else \
                   (f"[{r['language']}]({GH}/orgs/{login}/repositories?language={r['language'].lower().replace(' ','+')})" if r['language'] else '')
            links = [f"[code]({r['html_url']}/tree/{r['default_branch']})" if r['default_branch'] else '']
            if not r['private']: links.append(f"[issues]({r['html_url']}/issues)")
            if url(r['homepage']): links.append(f"[site]({url(r['homepage'])})")
            L.append(f"| {name} | {esc(r['description'])} | {lang} | {r['stargazers_count'] or 0} | {' · '.join(x for x in links if x)} |")
        L.append('')
    L += ['🔒 private · 🍴 fork · 📦 archived', '']
    open(f"map/{slug(login)}.md", 'w').write('\n'.join(L))
    return n, p

rows = {'org': [], 'user': []}
for kind, grp in (('org', d['orgs']), ('user', d['users'])):
    for login, v in grp.items():
        n, p = page(kind, login, v)
        rows[kind].append((login, v['meta'], n, p))

total = sum(r[2] for k in rows.values() for r in k); priv = sum(r[3] for k in rows.values() for r in k)
now = datetime.now(timezone.utc).strftime('%Y-%m-%d')
R = ['# orgmap', '',
     f'The organizations and repositories of [Professor Codephreak]({GH}/Professor-Codephreak), '
     'the Software Engineer and Platform Architect behind them.', '',
     f'**{len(rows["org"])} organizations** · **{len(rows["user"])} accounts** · **{total} repositories** '
     f'({total-priv} public, {priv} private 🔒) · generated {now} from the GitHub API', '',
     '## Sites', '',
     '| Site | What |', '|---|---|',
     '| [pythai.net](https://pythai.net) | PYTHAI home |',
     '| [ai.pythai.net](https://ai.pythai.net) | Transparent Augmented Intelligence |',
     '| [rage.pythai.net](https://rage.pythai.net) | RAGE: Retrieval Augmented Generative Engine |',
     '| [gpt.pythai.net](https://gpt.pythai.net) | GPT4 augmentation agents |',
     '| [mindx.pythai.net](https://mindx.pythai.net) | mindX |',
     '| [mastermind.pythai.net](https://mastermind.pythai.net) | the Boardroom and war council |',
     '| [deltaverse.pythai.net](https://deltaverse.pythai.net) | DeltaVerse |',
     '| [agenticplace.pythai.net](https://agenticplace.pythai.net) | AgenticPlace |',
     '| [luv.pythai.net](https://luv.pythai.net) | SHAMBA LUV |', '',
     '## Accounts', '',
     '| Account | Repos | 🔒 | Map |', '|---|--:|--:|---|']
for login, m, n, p in rows['user']:
    R.append(f"| [{login}]({GH}/{login}) | [{n}]({GH}/{login}?tab=repositories) | {p} | [map](map/{slug(login)}.md) |")
R += ['', '## Organizations', '', '| Organization | Description | Website | Repos | 🔒 | Map |', '|---|---|---|--:|--:|---|']
for login, m, n, p in sorted(rows['org'], key=lambda r: r[0].lower()):
    site = f"[{re.sub(r'^https?://','',url(m.get('blog'))).rstrip('/')}]({url(m.get('blog'))})" if m.get('blog') else ''
    R.append(f"| [{login}]({GH}/{login}) | {esc(m.get('description'))} | {site} | [{n}]({GH}/orgs/{login}/repositories) | {p} | [map](map/{slug(login)}.md) |")
R += ['', '## Regenerate', '', '```sh', 'python3 fetch.py     # needs an authenticated gh', 'python3 generate.py', '```', '']
open('README.md', 'w').write('\n'.join(R))
print('orgs', len(rows['org']), 'users', len(rows['user']), 'repos', total, 'private', priv)
