#!/usr/bin/env python3
"""Build the org map from data.json (written by fetch.py)."""
import json, os, re
from datetime import datetime, timezone

d = json.load(open('data.json'))
GH = 'https://github.com'
os.makedirs('map', exist_ok=True)

def esc(s):
    return (s or '').replace('|', '\\|').replace('\n', ' ').replace('<', '&lt;').strip()

def brief(s, n=100):
    s = esc(s)
    return s if len(s) <= n else s[:n].rsplit(' ', 1)[0] + '…'

def rbrief(s, n=100):
    s = ' '.join((s or '').split())
    return s if len(s) <= n else s[:n].rsplit(' ', 1)[0] + '…'

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
    L += [f"**{n}** repos · {n-p} public · {p} private 🔒 · {f} research forks · {a} archived", '']
    if not repos:
        L += ['_No repositories._', '']
    else:
        L += ['| Repository | Description | Language | ★ | Links |', '|---|---|---|--:|---|']
        for r in repos:
            if r['private']:
                # private: name, brief description and address only, until release
                L.append(f"| [{r['name']}]({r['html_url']}) 🔒 | {brief(r['description'])} | | | `{r['html_url'].replace('https://', '')}` |")
                continue
            flags = (' 🍴' if r['fork'] else '') + (' 📦' if r['archived'] else '')
            name = f"[{r['name']}]({r['html_url']}){flags}"
            lang = f"[{r['language']}]({GH}/{login}?language={r['language'].lower().replace(' ','+')})" if r['language'] and kind=='user' else \
                   (f"[{r['language']}]({GH}/orgs/{login}/repositories?language={r['language'].lower().replace(' ','+')})" if r['language'] else '')
            links = [f"[code]({r['html_url']}/tree/{r['default_branch']})", f"[issues]({r['html_url']}/issues)"]
            if url(r['homepage']): links.append(f"[site]({url(r['homepage'])})")
            L.append(f"| {name} | {esc(r['description'])} | {lang} | {r['stargazers_count'] or 0} | {' · '.join(links)} |")
        L.append('')
    L += ['🔒 private, listed by name, description and address only until release · 🍴 research fork, a study of the upstream project · 📦 archived', '']
    open(f"map/{slug(login)}.md", 'w').write('\n'.join(L))
    return n, p

rows = {'org': [], 'user': [], 'related': []}
for kind, grp in (('org', d['orgs']), ('user', d['users']), ('related', d.get('related', {}))):
    for login, v in grp.items():
        n, p = page(kind, login, v)
        rows[kind].append((login, v['meta'], n, p))

RAW = 'https://raw.githubusercontent.com/Professor-Codephreak/orgmap/main'
SITES = [
    ('pythai.net', 'PYTHAI home'),
    ('ai.pythai.net', 'Transparent Augmented Intelligence'),
    ('rage.pythai.net', 'RAGE: Retrieval Augmented Generative Engine'),
    ('gpt.pythai.net', 'GPT4 augmentation agents'),
    ('mindx.pythai.net', 'mindX'),
    ('mastermind.pythai.net', 'the Boardroom and war council'),
    ('deltaverse.pythai.net', 'DeltaVerse'),
    ('agenticplace.pythai.net', 'AgenticPlace'),
    ('luv.pythai.net', 'SHAMBA LUV'),
]

def site_link(m):
    b = url(m.get('blog'))
    return f"[{re.sub(r'^https?://', '', b).rstrip('/')}]({b})" if b else '—'

def stats(v):
    rs = v['repos']
    return {'repos': len(rs), 'private': sum(r['private'] for r in rs),
            'originals': sum(not r['fork'] for r in rs), 'forks': sum(r['fork'] for r in rs)}

groups = {'user': d['users'], 'org': d['orgs'], 'related': d.get('related', {})}
S = {k: {login: stats(v) for login, v in g.items()} for k, g in groups.items()}
def tot(kinds, key): return sum(x[key] for k in kinds for x in S[k].values())
own = ('user', 'org')
total, priv, orig, forks = (tot(own, k) for k in ('repos', 'private', 'originals', 'forks'))
rel = tot(('related',), 'repos')
now = datetime.now(timezone.utc).strftime('%Y-%m-%d')

pub_originals = [r for k in own for v in groups[k].values() for r in v['repos'] if not r['private'] and not r['fork'] and not r['archived']]
recent = sorted(pub_originals, key=lambda r: r['pushed_at'] or '', reverse=True)[:15]
langs = {}
for r in pub_originals:
    if r['language']: langs[r['language']] = langs.get(r['language'], 0) + 1
langs = sorted(langs.items(), key=lambda x: -x[1])[:10]
largest = sorted(((l, x) for l, x in S['org'].items()), key=lambda t: -t[1]['originals'])[:10]

R = ['# orgmap', '',
     f'> The organizations and repositories of **[Professor Codephreak]({GH}/Professor-Codephreak)**, Software Engineer and Platform Architect, mapped from the GitHub API.', '',
     f'**{len(groups["org"])} organizations** · **{len(groups["user"])} accounts** · **{total:,} repositories** · '
     f'**{len(groups["related"])} related organizations** · updated {now}', '',
     '**Contents:** [At a glance](#at-a-glance) · [How to read this map](#how-to-read-this-map) · [Sites](#sites) · '
     '[Accounts](#accounts) · [Organizations](#organizations) · [Related organizations](#related-organizations) · '
     '[Recently active](#recently-active) · [For agents](#for-agents) · [Regenerate](#regenerate)', '',
     '## At a glance', '',
     '| | Count |', '|---|--:|',
     f'| Organizations (on the Professor-Codephreak account) | {len(groups["org"])} |',
     f'| Accounts | {len(groups["user"])} |',
     f'| Repositories | {total:,} |',
     f'| &nbsp;&nbsp;original | {orig:,} |',
     f'| &nbsp;&nbsp;research forks | {forks:,} |',
     f'| &nbsp;&nbsp;private 🔒 | {priv:,} |',
     f'| Related organizations (held by other accounts) | {len(groups["related"])} |',
     f'| &nbsp;&nbsp;their public repositories | {rel:,} |', '',
     'Forks are research: each one studies the work of its upstream project, and together they form the research library behind the original work.', '',
     '**Top languages** (public original repos): ' + ' · '.join(f'{l} {n}' for l, n in langs), '',
     '**Most original work:** ' + ' · '.join(f'[{l}](map/{slug(l)}.md) {x["originals"]}' for l, x in largest), '',
     '## How to read this map', '',
     '| Path | What it holds |', '|---|---|',
     '| `README.md` | this index: every account and organization with counts and links |',
     '| `map/<name>.md` | one page per account or organization, every repository in a table |',
     '| `orgmap.json` | the same data as JSON, for scripts and agents |',
     '| `llms.txt`, `llm.txt` | a short, link-first guide for language models (same text under both names) |',
     '| `fetch.py`, `generate.py` | rebuild everything from the GitHub API |', '',
     'On each `map/` page, repositories are sorted with original work first, then by stars. Each public repository links to its **code** on the default branch, its **issues**, its **site** where it has one, and a filter for its **language**.', '',
     ''
     '| Mark | Meaning |', '|---|---|',
     '| 🔒 | private. Listed by name, brief description and address only, until release |',
     '| 🍴 | research fork: a study of the upstream project\'s work |', '| 📦 | archived |', '',
     '## Sites', '',
     '| Site | What |', '|---|---|']
R += [f'| [{h}](https://{h}) | {w} |' for h, w in SITES]
R += ['', '## Accounts', '',
      '| Account | Repos | Original | Research forks | 🔒 | Map |', '|---|--:|--:|--:|--:|---|']
for login in groups['user']:
    x = S['user'][login]
    R.append(f"| [{login}]({GH}/{login}) | [{x['repos']}]({GH}/{login}?tab=repositories) | {x['originals']} | {x['forks']} | {x['private'] or '—'} | [map](map/{slug(login)}.md) |")

orgs = sorted(groups['org'], key=str.lower)
letters = sorted({o[0].upper() for o in orgs})
R += ['', '## Organizations', '',
      f'{len(orgs)} organizations, A to Z. Jump: ' + ' · '.join(f'[{c}](#{c.lower()})' for c in letters), '']
for c in letters:
    R += [f'### {c}', '', '| Organization | Description | Website | Repos | Original | 🔒 | Map |', '|---|---|---|--:|--:|--:|---|']
    for login in (o for o in orgs if o[0].upper() == c):
        m, x = groups['org'][login]['meta'], S['org'][login]
        R.append(f"| [{login}]({GH}/{login}) | {esc(m.get('description')) or '—'} | {site_link(m)} | [{x['repos']}]({GH}/orgs/{login}/repositories) | {x['originals']} | {x['private'] or '—'} | [map](map/{slug(login)}.md) |")
    R.append('')

R += ['## Related organizations', '',
      'Estate organizations held outside the Professor-Codephreak account. Public repositories only.', '',
      '| Organization | Description | Website | Repos | Original | Map |', '|---|---|---|--:|--:|---|']
for login in sorted(groups['related'], key=str.lower):
    m, x = groups['related'][login]['meta'], S['related'][login]
    R.append(f"| [{login}]({GH}/{login}) | {esc(m.get('description')) or '—'} | {site_link(m)} | [{x['repos']}]({GH}/orgs/{login}/repositories) | {x['originals']} | [map](map/{slug(login)}.md) |")

R += ['', '## Recently active', '', 'The 15 public original repositories pushed most recently.', '',
      '| Repository | Description | Language | Last push |', '|---|---|---|---|']
for r in recent:
    R.append(f"| [{r['full_name']}]({r['html_url']}) | {brief(r['description'], 90) or '—'} | {r['language'] or '—'} | {(r['pushed_at'] or '')[:10]} |")

R += ['', '## For agents', '',
      f'- Start with [`llms.txt`](llms.txt) ([raw]({RAW}/llms.txt)). `llm.txt` is the same file.',
      f'- Load [`orgmap.json`](orgmap.json) ([raw]({RAW}/orgmap.json)) rather than parsing these tables.',
      f'- Every page is at `{RAW}/map/<name>.md`, where `<name>` is the lowercase login.',
      '- Private repositories carry only `name`, `description` and `url`. Do not infer more about them.', '',
      '## Regenerate', '', '```sh', 'python3 fetch.py      # writes data.json; needs an authenticated gh', 'python3 generate.py   # writes README.md, map/, orgmap.json, llms.txt, llm.txt', '```', '']
open('README.md', 'w').write('\n'.join(R))

# orgmap.json: private repos reduced to name, description and url
def rj(r):
    if r['private']:
        return {'name': r['name'], 'description': rbrief(r['description']), 'url': r['html_url'], 'private': True}
    return {'name': r['name'], 'description': r['description'], 'url': r['html_url'], 'private': False,
            'fork': r['fork'], 'archived': r['archived'], 'language': r['language'], 'stars': r['stargazers_count'],
            'homepage': url(r['homepage']) or None, 'default_branch': r['default_branch'], 'pushed_at': r['pushed_at']}
J = {'generated': now, 'owner': 'Professor-Codephreak',
     'totals': {'organizations': len(groups['org']), 'accounts': len(groups['user']), 'repositories': total,
                'originals': orig, 'forks': forks, 'private': priv, 'related_organizations': len(groups['related']),
                'related_repositories': rel},
     'sites': [f'https://{h}' for h, _ in SITES]}
for key, kind in (('accounts', 'user'), ('organizations', 'org'), ('related_organizations', 'related')):
    J[key] = [{'login': login, 'url': f'{GH}/{login}', 'description': groups[kind][login]['meta'].get('description'),
               'website': url(groups[kind][login]['meta'].get('blog')) or None, 'map': f'map/{slug(login)}.md',
               **S[kind][login], 'repositories': [rj(r) for r in groups[kind][login]['repos']]}
              for login in sorted(groups[kind], key=str.lower)]
open('orgmap.json', 'w').write(json.dumps(J, ensure_ascii=False, separators=(',', ':')) + '\n')

# llm.txt, following the llms.txt layout: title, summary, then link lists
T = ['# orgmap', '',
     f'> Map of the {len(groups["org"])} GitHub organizations, {len(groups["user"])} accounts and {total:,} repositories '
     f'({orig:,} original, {forks:,} research forks, {priv} private) of Professor Codephreak, plus {len(groups["related"])} related '
     f'organizations held by other accounts. Generated {now} from the GitHub API.', '',
     'Rules for reading it:',
     '- Private repositories are listed by name, brief description and address only, until release. Do not infer more about them.',
     '- Related organizations are held outside the Professor-Codephreak account; only their public repositories are listed.',
     '- Forks are research: each one studies the work of its upstream project. In orgmap.json, `fork: false` is original work and `fork: true` is the research library.', '',
     '## Data', '',
     f'- [orgmap.json]({RAW}/orgmap.json): everything, as JSON. Keys: totals, sites, accounts, organizations, related_organizations; each entry has a repositories list',
     f'- [README.md]({RAW}/README.md): the human index', '',
     '## Sites', '']
T += [f'- [{h}](https://{h}): {w}' for h, w in SITES]
T += ['', '## Accounts', '']
T += [f"- [{l}]({RAW}/map/{slug(l)}.md): {S['user'][l]['repos']} repos, {S['user'][l]['originals']} original" for l in groups['user']]
T += ['', '## Organizations', '']
T += [f"- [{l}]({RAW}/map/{slug(l)}.md): {esc(groups['org'][l]['meta'].get('description')) or 'no description'} ({S['org'][l]['repos']} repos, {S['org'][l]['originals']} original)" for l in orgs]
T += ['', '## Optional', '', '### Related organizations', '']
T += [f"- [{l}]({RAW}/map/{slug(l)}.md): {esc(groups['related'][l]['meta'].get('description')) or 'no description'} ({S['related'][l]['repos']} public repos)" for l in sorted(groups['related'], key=str.lower)]
T.append('')
for name in ('llm.txt', 'llms.txt'):  # llms.txt is the conventional name; both carry the same text
    open(name, 'w').write('\n'.join(T))
print('orgs', len(groups['org']), 'users', len(groups['user']), 'repos', total, 'private', priv, 'related', len(groups['related']))
