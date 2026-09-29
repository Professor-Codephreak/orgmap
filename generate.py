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
    u = (u or '').strip().split()[0] if (u or '').strip() else ''
    if not u: return ''
    if not re.match(r'^https?://', u): u = 'https://' + u
    return u

def slug(name):
    return name.lower()

DET = json.load(open('detail.json')) if os.path.exists('detail.json') else {}
RDM = json.load(open('readme.json')) if os.path.exists('readme.json') else {}
DOM = json.load(open('domains.json'))['domains']
DOMAIN_OF = {o: x for x in DOM for o in x['orgs']}

def det(login, r):
    return DET.get(login, {}).get(r['name'], {})

def studies(login, r):
    """The upstream a public research fork studies, or None."""
    return (det(login, r).get('parent') or None) if r['fork'] and not r['private'] else None

def about(login, r):
    """Best description of a public repo: its own, the upstream's for forks, else a README summary."""
    up = studies(login, r) or {}
    own = (r['description'] or '').strip()
    if r['fork']:
        return (up.get('description') or '').strip() or own or RDM.get(r['full_name'], '')
    return own or RDM.get(r['full_name'], '')

def lang_link(kind, login, lang):
    if not lang: return '—'
    q = lang.lower().replace(' ', '+')
    return f"[{lang}]({GH}/{login}?tab=repositories&language={q})" if kind == 'user' else f"[{lang}]({GH}/orgs/{login}/repositories?language={q})"

def counter(items, n):
    c = {}
    for i in items:
        if i: c[i] = c.get(i, 0) + 1
    return sorted(c.items(), key=lambda x: (-x[1], x[0].lower()))[:n]

def page(kind, login, v):
    repos = v['repos']
    m = v['meta']
    dom = DOMAIN_OF.get(login)
    originals = sorted((r for r in repos if not r['fork']), key=lambda r: (r['private'], r['archived'], -(r['stargazers_count'] or 0), r['name'].lower()))
    forks = [r for r in repos if r['fork']]
    pub_forks = [r for r in forks if not r['private']]
    ups = [(studies(login, r) or {}).get('owner', {}).get('login') for r in pub_forks]
    topics = [t['topic']['name'] for r in repos if not r['private'] for t in det(login, r).get('repositoryTopics', {}).get('nodes', [])]
    langs = [r['language'] for r in originals if not r['private']]

    L = [f"# [{login}]({GH}/{login})", '']
    nav = [f"[← master index](../README.md)", f"[concept archive](../ARCHIVE.md#{dom['key']})" if dom else '',
           f"[profile]({GH}/{login})",
           f"[repositories]({GH}/{login}?tab=repositories)" if kind == 'user' else f"[repositories]({GH}/orgs/{login}/repositories)"]
    L += [' · '.join(x for x in nav if x), '']
    if m.get('description'): L += [f"> {esc(m['description'])}", '']
    facts = []
    if dom: facts.append(f"**Domain:** [{dom['title']}](../ARCHIVE.md#{dom['key']})")
    if m.get('blog'): facts.append(f"**Website:** <{url(m['blog'])}>")
    if kind == 'related': facts.append('**Held outside the Professor-Codephreak account.** Public repositories only.')
    if facts: L += [' · '.join(facts), '']
    n = len(repos); p = sum(r['private'] for r in repos)
    L += [f"**{n}** repos · **{len(originals)}** original works · **{len(forks)}** research forks · {p} private 🔒", '']

    # the concept, read from the structure of the archive
    if repos:
        L += ['## Concept', '']
        if langs: L.append('- **Original work is written in:** ' + ', '.join(f'{l} ({c})' for l, c in counter(langs, 6)))
        if topics: L.append('- **Topics:** ' + ', '.join(f'`{t}`' for t, _ in counter(topics, 12)))
        if any(ups): L.append('- **Research studies the work of:** ' + ', '.join(f'[{o}]({GH}/{o}) ({c})' for o, c in counter(ups, 10)))
        L.append('')

    L += [f'## Original works ({len(originals)})', '']
    if not originals: L += ['_None._', '']
    for r in originals:
        if r['private']:
            L.append(f"- **[{r['name']}]({r['html_url']})** 🔒 {brief(r['description']) or ''} · `{r['html_url'].replace('https://', '')}`".rstrip())
            continue
        dd = det(login, r)
        meta = [lang_link(kind, login, r['language']) if r['language'] else '', f"★ {r['stargazers_count']}" if r['stargazers_count'] else '',
                (dd.get('licenseInfo') or {}).get('spdxId') or '', '📦 archived' if r['archived'] else '',
                f"[site]({url(r['homepage'])})" if url(r['homepage']) else '', f"[code]({r['html_url']}/tree/{r['default_branch']})"]
        L.append(f"- **[{r['name']}]({r['html_url']})** · " + ' · '.join(x for x in meta if x and x != 'NOASSERTION'))
        txt = about(login, r)
        if txt: L.append(f"  {esc(txt)}")
        tps = [t['topic']['name'] for t in dd.get('repositoryTopics', {}).get('nodes', [])]
        if tps: L.append('  ' + ' '.join(f'`{t}`' for t in tps))
    L.append('')

    L += [f'## Research forks ({len(forks)})', '']
    if not forks: L += ['_None._', '']
    else:
        L += ['Each fork is research into the work of its upstream project. Sorted by the upstream studied.', '',
              '| Research fork | Studies | What the work is | Upstream ★ | Language |', '|---|---|---|--:|---|']
        def fkey(r):
            u = studies(login, r) or {}
            return (r['private'], (u.get('nameWithOwner') or '~').lower(), r['name'].lower())
        for r in sorted(forks, key=fkey):
            if r['private']:
                L.append(f"| [{r['name']}]({r['html_url']}) 🔒 | | {brief(r['description'])} · `{r['html_url'].replace('https://', '')}` | | |")
                continue
            u = studies(login, r)
            st = f"[{u['nameWithOwner']}]({u['url']})" + (' 📦' if u.get('isArchived') else '') if u else '_upstream no longer available_'
            ustars = f"{u['stargazerCount']:,}" if u else ''
            lang = r['language'] or ((u or {}).get('primaryLanguage') or {}).get('name') or '—'
            L.append(f"| [{r['name']}]({r['html_url']}){' 📦' if r['archived'] else ''} | {st} | {brief(about(login, r), 220) or '—'} | {ustars} | {lang} |")
        L.append('')
    L += ['---', '', '🔒 private: name, brief description and address only, until release · 📦 archived', '']
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
DSTAT = {l: x for k in S for l, x in S[k].items()}
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
     "**The master archivist's file mapping.**", '',
     f'> The organizations and repositories of **[Professor Codephreak]({GH}/Professor-Codephreak)**, Software Engineer and Platform Architect, mapped from the GitHub API. '
     'Each organization is an archive of one concept, holding original works and research forks of the upstream projects it studies.', '',
     f'**{len(groups["org"])} organizations** · **{len(groups["user"])} accounts** · **{total:,} repositories** · '
     f'**{len(groups["related"])} related organizations** · updated {now}', '',
     '**Contents:** [At a glance](#at-a-glance) · [Concept domains](#concept-domains) · [How to read this map](#how-to-read-this-map) · [Sites](#sites) · '
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
     '## Concept domains', '',
     f'The organizations fall into {len(DOM)} concept domains. The full [concept archive](ARCHIVE.md) describes each one and every organization in it.', '',
     '| Domain | Concept | Organizations | Original works | Research forks |', '|---|---|--:|--:|--:|',
     *[f"| [{x['title']}](ARCHIVE.md#{x['key']}) | {x['concept']} | {len(x['orgs'])} | {sum(DSTAT[o]['originals'] for o in x['orgs'])} | {sum(DSTAT[o]['forks'] for o in x['orgs'])} |" for x in DOM], '',
     '## How to read this map', '',
     '| Path | What it holds |', '|---|---|',
     '| `README.md` | this index: every account and organization with counts and links |',
     '| `ARCHIVE.md` | the concept archive: the domains, and what each organization holds and studies |',
     '| `map/<name>.md` | one page per account or organization: its concept, every original work described, every research fork with the upstream it studies |',
     '| `orgmap.json` | the same data as JSON, for scripts and agents |',
     '| `llms.txt`, `llm.txt` | a short, link-first guide for language models (same text under both names) |',
     '| `domains.json` | the concept domains; edit it to refile an organization |',
     '| `fetch*.py`, `generate.py` | rebuild everything from the GitHub API |', '',
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
      '## Regenerate', '', '```sh', 'python3 fetch.py          # data.json: orgs and repos; needs an authenticated gh',
      'python3 fetch_detail.py   # detail.json: upstream of each research fork, topics, licences',
      'python3 fetch_readme.py   # readme.json: README summaries where a description is missing', 'python3 generate.py   # writes README.md, map/, orgmap.json, llms.txt, llm.txt', '```', '']
open('README.md', 'w').write('\n'.join(R))

# ARCHIVE.md: the concept archive, read from the organization of the archives
ALL = {**groups['user'], **groups['org'], **groups['related']}
KIND = {**{l: 'user' for l in groups['user']}, **{l: 'org' for l in groups['org']}, **{l: 'related' for l in groups['related']}}
def upstream_owners(logins):
    return counter([(studies(l, r) or {}).get('owner', {}).get('login') for l in logins for r in ALL[l]['repos'] if r['fork'] and not r['private']], 12)
def notable(logins, n):
    rs = [(l, r) for l in logins for r in ALL[l]['repos'] if not r['fork'] and not r['private'] and not r['archived']]
    return sorted(rs, key=lambda t: (-(t[1]['stargazers_count'] or 0), -(int((t[1]['pushed_at'] or '0')[:10].replace('-', '') or 0))))[:n]

A = ['# Concept archive', '',
     "Part of the master archivist's file mapping. [← master index](README.md)", '',
     f'The {len(ALL) - len(groups["user"])} organizations are filed in {len(DOM)} concept domains. Each organization holds one concept: '
     'its **original works** express it, and its **research forks** study the upstream projects it learns from. '
     'The domains below are read from that structure: the organization descriptions, the work, and what the research studies.', '',
     'Domains: ' + ' · '.join(f"[{x['title']}](#{x['key']})" for x in DOM), '']
for x in DOM:
    o = x['orgs']
    A += [f'<a id="{x["key"]}"></a>', '', f"## {x['title']}", '', f"> {x['concept']}", '',
          f"**{len(o)}** organizations · **{sum(DSTAT[l]['originals'] for l in o)}** original works · **{sum(DSTAT[l]['forks'] for l in o)}** research forks", '',
          '| Organization | Its concept | Original | Research | Studies most |', '|---|---|--:|--:|---|']
    for l in sorted(o, key=lambda l: (-DSTAT[l]['originals'], l.lower())):
        top = upstream_owners([l])[:3]
        rel = ' _(related)_' if KIND[l] == 'related' else ''
        A.append(f"| [{l}](map/{slug(l)}.md){rel} | {esc(ALL[l]['meta'].get('description')) or '—'} | {DSTAT[l]['originals']} | {DSTAT[l]['forks']} | "
                 + (', '.join(f'[{u}]({GH}/{u})' for u, _ in top) or '—') + ' |')
    A.append('')
    nb = notable(o, 8)
    if nb:
        A += ['**Notable original works**', '']
        A += [f"- [{l}/{r['name']}]({r['html_url']}){' · ★ ' + str(r['stargazers_count']) if r['stargazers_count'] else ''}: {brief(about(l, r), 160) or '—'}" for l, r in nb]
        A.append('')
    uo = upstream_owners(o)
    if uo:
        A += ['**The research studies:** ' + ', '.join(f'[{u}]({GH}/{u}) ({c})' for u, c in uo), '']

A += ['## Personal accounts', '',
      '| Account | Original | Research | Studies most |', '|---|--:|--:|---|']
for l in groups['user']:
    A.append(f"| [{l}](map/{slug(l)}.md) | {DSTAT[l]['originals']} | {DSTAT[l]['forks']} | " + (', '.join(f'[{u}]({GH}/{u})' for u, _ in upstream_owners([l])[:3]) or '—') + ' |')
A.append('')
glob = counter([(studies(l, r) or {}).get('owner', {}).get('login') for l in ALL for r in ALL[l]['repos'] if r['fork'] and not r['private']], 30)
A += ['## Most-studied upstreams', '', 'The upstream owners whose work the archive researches most, across every organization.', '',
      '| Upstream | Research forks |', '|---|--:|'] + [f'| [{u}]({GH}/{u}) | {c} |' for u, c in glob] + ['']
open('ARCHIVE.md', 'w').write('\n'.join(A))

# orgmap.json: private repos reduced to name, description and url
LOGIN_OF = {r['full_name']: l for g in groups.values() for l, v in g.items() for r in v['repos']}
def rj(r):
    if r['private']:
        return {'name': r['name'], 'description': rbrief(r['description']), 'url': r['html_url'], 'private': True}
    return {'name': r['name'], 'description': r['description'], 'url': r['html_url'], 'private': False,
            'fork': r['fork'], 'archived': r['archived'], 'language': r['language'], 'stars': r['stargazers_count'],
            'homepage': url(r['homepage']) or None, 'default_branch': r['default_branch'], 'pushed_at': r['pushed_at'],
            'about': about(LOGIN_OF[r['full_name']], r) or None,
            'studies': ({'repo': u['nameWithOwner'], 'url': u['url'], 'description': u.get('description')} if (u := studies(LOGIN_OF[r['full_name']], r)) else None)}
J = {'generated': now, 'owner': 'Professor-Codephreak',
     'totals': {'organizations': len(groups['org']), 'accounts': len(groups['user']), 'repositories': total,
                'originals': orig, 'forks': forks, 'private': priv, 'related_organizations': len(groups['related']),
                'related_repositories': rel},
     'sites': [f'https://{h}' for h, _ in SITES],
     'domains': [{'key': x['key'], 'title': x['title'], 'concept': x['concept'], 'organizations': x['orgs']} for x in DOM]}
for key, kind in (('accounts', 'user'), ('organizations', 'org'), ('related_organizations', 'related')):
    J[key] = [{'login': login, 'url': f'{GH}/{login}', 'description': groups[kind][login]['meta'].get('description'),
               'domain': DOMAIN_OF[login]['key'] if login in DOMAIN_OF else None,
               'website': url(groups[kind][login]['meta'].get('blog')) or None, 'map': f'map/{slug(login)}.md',
               **S[kind][login], 'repositories': [rj(r) for r in groups[kind][login]['repos']]}
              for login in sorted(groups[kind], key=str.lower)]
open('orgmap.json', 'w').write(json.dumps(J, ensure_ascii=False, separators=(',', ':')) + '\n')

# llm.txt, following the llms.txt layout: title, summary, then link lists
T = ['# orgmap', '',
     f'> Map of the {len(groups["org"])} GitHub organizations, {len(groups["user"])} accounts and {total:,} repositories '
     f'({orig:,} original, {forks:,} research forks, {priv} private) of Professor Codephreak, plus {len(groups["related"])} related '
     f'organizations held by other accounts. Generated {now} from the GitHub API. '
     "This is the master archivist's file mapping: each organization is an archive of one concept, "
     'holding original works and research forks of the upstream projects it studies.', '',
     'Rules for reading it:',
     '- Private repositories are listed by name, brief description and address only, until release. Do not infer more about them.',
     '- Related organizations are held outside the Professor-Codephreak account; only their public repositories are listed.',
     '- Forks are research: each one studies the work of its upstream project. In orgmap.json, `fork: false` is original work and `fork: true` is the research library.', '',
     '## Data', '',
     f'- [orgmap.json]({RAW}/orgmap.json): everything, as JSON. Keys: totals, sites, domains, accounts, organizations, related_organizations. Each organization has a domain and a repositories list; public repos carry about (a description) and, for research forks, studies (the upstream)',
     f'- [README.md]({RAW}/README.md): the human index',
     f'- [ARCHIVE.md]({RAW}/ARCHIVE.md): the concept archive, domain by domain',
     f'- [domains.json]({RAW}/domains.json): which domain each organization is filed under',
     '- Each map page lists its original works with descriptions, and every research fork with the upstream it studies', '',
     '## Sites', '']
T += [f'- [{h}](https://{h}): {w}' for h, w in SITES]
T += ['', '## Accounts', '']
T += [f"- [{l}]({RAW}/map/{slug(l)}.md): {S['user'][l]['repos']} repos, {S['user'][l]['originals']} original" for l in groups['user']]
for x in DOM:
    T += ['', f"## {x['title']}", '', x['concept'], '']
    T += [f"- [{l}]({RAW}/map/{slug(l)}.md): {esc(ALL[l]['meta'].get('description')) or 'no description'} ({DSTAT[l]['originals']} original, {DSTAT[l]['forks']} research){' · related, held outside the account' if KIND[l] == 'related' else ''}" for l in x['orgs']]
T += ['', '## Optional', '', '- [README.md]({RAW}/README.md): also lists the related organizations with their websites'.replace('{RAW}', RAW)]
T.append('')
for name in ('llm.txt', 'llms.txt'):  # llms.txt is the conventional name; both carry the same text
    open(name, 'w').write('\n'.join(T))

print('orgs', len(groups['org']), 'users', len(groups['user']), 'repos', total, 'private', priv, 'related', len(groups['related']))
