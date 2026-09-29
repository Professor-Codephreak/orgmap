#!/usr/bin/env python3
"""Fetch per-repo detail (upstream of each research fork, topics, licence) into detail.json. Needs data.json."""
import json, subprocess, time

Q = '''query($login:String!,$after:String){ %s(login:$login){ repositories(first:100, after:$after%s){
  pageInfo{hasNextPage endCursor}
  nodes{ name isFork isPrivate isArchived description url homepageUrl stargazerCount pushedAt
    primaryLanguage{name} licenseInfo{spdxId} repositoryTopics(first:8){nodes{topic{name}}}
    parent{ nameWithOwner url description stargazerCount isArchived primaryLanguage{name} owner{login} } } } } }'''

def run(kind, login):
    q = Q % (kind, ', ownerAffiliations:OWNER' if kind == 'user' else '')
    out, after = [], None
    while True:
        args = ['gh', 'api', 'graphql', '-f', f'query={q}', '-F', f'login={login}']
        if after: args += ['-f', f'after={after}']
        for attempt in range(4):
            p = subprocess.run(args, capture_output=True, text=True)
            if p.returncode == 0: break
            time.sleep(5 * (attempt + 1))
        else:
            raise SystemExit(f'{login}: {p.stderr[:200]}')
        r = json.loads(p.stdout)['data'][kind]['repositories']
        out += r['nodes']
        if not r['pageInfo']['hasNextPage']: return out
        after = r['pageInfo']['endCursor']

d = json.load(open('data.json'))
detail = {}
for grp, kind in (('users', 'user'), ('orgs', 'organization'), ('related', 'organization')):
    for login in d.get(grp, {}):
        nodes = run(kind, login)
        if grp == 'related': nodes = [n for n in nodes if not n['isPrivate']]
        detail[login] = {n['name']: n for n in nodes}
        print(login, len(nodes), flush=True)
json.dump(detail, open('detail.json', 'w'))
