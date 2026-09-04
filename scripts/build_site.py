"""Generate directly addressable article pages from the preserved issue archive."""
import json
from html import escape
from pathlib import Path
try:
    from .catalog import TAXONOMY, enrich_paper
except ImportError:
    from catalog import TAXONOMY, enrich_paper
ROOT = Path(__file__).resolve().parents[1]

def build():
    data=json.loads((ROOT/'dist/digest.json').read_text())
    catalog={}
    for issue in data['issues']:
        for paper in issue['papers']:
            enrich_paper(paper)
            if paper['id'] in catalog and catalog[paper['id']]['title'] != paper['title']:
                raise ValueError('Conflicting paper identity')
            catalog.setdefault(paper['id'],{**paper,'issues':[]})['issues'].append(issue['date'])
    (ROOT/'dist/catalog.json').write_text(json.dumps({'taxonomy':TAXONOMY,'papers':list(catalog.values())},ensure_ascii=False,indent=2))
    (ROOT/'dist/digest.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
    for p in catalog.values():
        esc=escape
        sections=''.join('<li><strong>'+esc(s['label'])+'：</strong>'+esc(s['text'])+'</li>' for s in p['sections'])
        # Text is escaped both in server-rendered fallback and the enhanced UI.
        fallback=f'<h1>{esc(p["heading"])}</h1><h2>{esc(p["title"])}</h2><p>{esc(p["journal"])} · {esc(p["date"])} · {esc(p["kind"])}</p><p>内容待核验；研究启示不等同于论文结论。</p><ul>{sections}</ul><a href="{esc(p["url"],quote=True)}">论文原文</a>'
        template=(ROOT/'dist/index.html').read_text()
        template=template.replace('<title>Plant Epigenomics Weekly Digest</title>',f'<title>{esc(p["title"])} | Plant Epigenomics Weekly Digest</title>')
        template=template.replace('href="style.css"','href="../../style.css"').replace('src="app.js"','src="../../app.js"')
        template=template.replace('<body>','<body data-base="../../" data-paper="'+p['id']+'">')
        template=template.replace('<a class="brand" href="./">','<a class="brand" href="../../">')
        template=template.replace('<div id="papers" aria-live="polite"></div>','<div id="papers" aria-live="polite">'+fallback+'</div>')
        dest=ROOT/'dist/papers'/p['id']/'index.html';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(template)
    print(f'Built {len(catalog)} article pages; all six sections retained.')
if __name__=='__main__':build()
