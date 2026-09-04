"""Build bilingual catalog and immutable issue snapshots from canonical records."""
import json
from html import escape
from pathlib import Path
try:
    from .catalog import TAXONOMY, enrich_paper
    from .store import read, write, record_revision
except ImportError:
    from catalog import TAXONOMY, enrich_paper
    from store import read, write, record_revision
ROOT=Path(__file__).resolve().parents[1]
def build():
    papers=read('papers.json',[]);issues=read('issues.json',[])
    ids=set()
    for p in papers:
        enrich_paper(p)
        if p['id'] in ids:raise ValueError('Duplicate stable paper ID: '+p['id'])
        ids.add(p['id'])
        if any(not isinstance(s.get('text'),str) or not s['text'].strip() for s in p['sections']):raise ValueError('Complete Chinese commentary required: '+p['id'])
        en=p.get('translations',{}).get('en',{})
        if not en.get('heading') or len(en.get('sections',[]))!=6 or any(not s.get('text','').strip() for s in en['sections']):raise ValueError('Complete English commentary required: '+p['id'])
        record_revision(p,'Bilingual commentary update')
        p['issues']=[i['date'] for i in issues if any(e['paper_id']==p['id'] for e in i['entries'])]
    try:
        from .identity import relations
    except ImportError:
        from identity import relations
    for p in papers:p['related_papers']=relations(p,papers)
    write('papers.json',papers)
    revisions=read('revisions.json',{});by_id={p['id']:p for p in papers}
    rendered=[]
    for issue in issues:
        rows=[]
        for entry in issue['entries']:
            p=by_id[entry['paper_id']]
            revision=next(r for r in revisions[p['id']] if r['version']==entry['revision'])
            rows.append({**p,**revision['content'],'revision':entry['revision'],'priority':entry['priority']})
        rendered.append({**issue,'papers':rows})
    outputs={'catalog.json':{'taxonomy':TAXONOMY,'papers':papers},'digest.json':{'issues':rendered},'topics.json':read('topics.json',[]),'candidates.json':read('candidates.json',{}),'revisions.json':revisions}
    for name,value in outputs.items():(ROOT/'dist'/name).write_text(json.dumps(value,ensure_ascii=False,indent=2))
    template=(ROOT/'dist/index.html').read_text()
    for p in papers:
        sections=''.join('<li><strong>'+escape(s['label'])+'：</strong>'+escape(s['text'])+'</li>' for s in p['sections'])
        page=template.replace('<title>Plant Epigenomics Weekly Digest</title>','<title>'+escape(p['title'])+' | Plant Epigenomics Weekly Digest</title>')
        for asset in ['style.css','app.js','reader.js','i18n.js']:page=page.replace('"'+asset+'"','"../../'+asset+'"')
        page=page.replace('<body>','<body data-base="../../" data-paper="'+p['id']+'">').replace('href="./"','href="../../"')
        page=page.replace('<div id="papers"></div>','<div id="papers"><h2>'+escape(p['title'])+'</h2><ul>'+sections+'</ul></div>')
        dest=ROOT/'dist/papers'/p['id']/'index.html';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(page)
    print(f'Built {len(papers)} bilingual papers, {len(issues)} version-pinned issues.')
if __name__=='__main__':build()
