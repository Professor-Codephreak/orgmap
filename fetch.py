import json, subprocess
def gh(*a):
    return json.loads(subprocess.run(['gh','api','--paginate',*a],capture_output=True,text=True,check=True).stdout.replace('][',','))
orgs=[o['login'] for o in gh('user/orgs?per_page=100')]
out={'orgs':{},'users':{}}
for o in orgs:
    meta=json.loads(subprocess.run(['gh','api',f'orgs/{o}'],capture_output=True,text=True).stdout)
    repos=gh(f'orgs/{o}/repos?per_page=100&type=all')
    out['orgs'][o]={'meta':{k:meta.get(k) for k in ('name','description','blog','html_url','login')},'repos':repos}
    print(o,len(repos))
me=gh('user/repos?per_page=100&affiliation=owner')
out['users']['Professor-Codephreak']={'meta':{},'repos':me}; print('Professor-Codephreak',len(me))
for u in ['simplemind','simplecode','sAGI']:
    try:
        r=gh(f'users/{u}/repos?per_page=100&type=owner'); out['users'][u]={'meta':{},'repos':r}; print(u,len(r))
    except subprocess.CalledProcessError as e: print(u,'ERR',e.stderr[:100])
KEEP=('name','full_name','html_url','description','private','fork','archived','homepage','language','stargazers_count','pushed_at','default_branch','parent')
for grp in out.values():
    for v in grp.values():
        v['repos']=[{k:r.get(k) for k in KEEP} for r in v['repos']]
json.dump(out,open('data.json','w'),indent=1)
