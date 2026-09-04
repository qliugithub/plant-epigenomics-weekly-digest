"""Offline regression coverage for identity and administrator imports."""
import sys,copy,tempfile,os,json
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'scripts'))
import identity as ident, import_paper as importer, store, update_digest as u
from catalog import TAXONOMY
assert ident.duplicate({'doi':'HTTPS://DOI.ORG/10.1234/ABC','title':'A'},[{'doi':'10.1234/abc','title':'A'}])
assert not ident.duplicate({'doi':'10.1234/a','title':'Same title'},[{'doi':'10.1234/b','title':'Same title'}])
assert ident.identifier({'url':'https://www.biorxiv.org/content/10.1234/abc123v2.full-text'})=='10.1234/abc123'
p={'id':'a','doi':'10.1234/a','title':'Preprint','metadata':{'status':'matched','relations':[{'type':'is-preprint-of','id':'10.1234/b'}]}}
q={'id':'b','doi':'10.1234/b','title':'Published'}
assert ident.relations(p,[p,q])[0]['paper_id']=='b'
assert ident.relations(q,[p,q])[0]['paper_id']=='a'
importer.request=lambda _: {'resultList':{'result':[{'doi':'10.1234/a','title':'Old pepper paper','abstractText':'An abstract','firstPublicationDate':'2000-01-01','source':'MED'}]}}
record,existing=importer.resolve('https://doi.org/10.1234/a',[])
assert record['date']=='2000-01-01' and not existing
assert importer.resolve('10.1234/a',[p])[1]==p
try:importer.resolve('10.1234/wrong',[]);raise AssertionError('Mismatched DOI accepted')
except ValueError:pass
with tempfile.TemporaryDirectory() as folder:
 store.ROOT=u.ROOT=Path(folder);(store.ROOT/'dist').mkdir()
 prior=[{'date':'2026-09-04','entries':[]}];store.write('issues.json',prior)
 section_labels=['真正的新发现','机制或方法上的关键点','与你的辣椒研究关系','对22组织图谱的具体启示','需要注意','建议优先看']
 en_labels=['What is new','Mechanistic or methodological key point','Relevance to pepper research','Implications for the 22-tissue atlas','Limitations','What to read first']
 result={'summary':'历史补录','summary_en':'Historical backfill','papers':[{'id':0,'journal_club':None,'heading':'解读','priority':'全文精读','tags':[],'classification':{k:[] for k in TAXONOMY},'sections':[{'label':v,'text':'完整解读'} for v in section_labels],'translations':{'en':{'heading':'Commentary','sections':[{'label':v,'text':'Full commentary'} for v in en_labels]}}}]}
 os.environ['OPENAI_API_KEY']='offline-test'
 u.request=lambda *a,**k:{'status':'completed','output':[{'content':[{'type':'output_text','text':json.dumps(result)}]}]}
 u.main('10.1234/a')
 assert store.read('issues.json',[])[0]==prior[0]
 assert len(store.read('issues.json',[]))==2
 assert store.read('papers.json',[])[0]['entry_type']=='backfill'
 before=store.read('revisions.json',{})
 u.main('10.1234/a')
 assert store.read('revisions.json',{})==before
 assert len(store.read('papers.json',[]))==1
print('PASS: DOI identity, distinct publication versions, reverse relations, exact-source resolution, isolated backfill, duplicate import.')
