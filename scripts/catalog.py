"""Shared controlled vocabulary and stable identifiers; no network access."""
import hashlib

TAXONOMY = {
    'species': {'label':'物种','values':['辣椒','番茄','其他茄科','其他果实','拟南芥','其他植物','多物种植物']},
    'process': {'label':'生物学过程','values':['果实发育','果实成熟','采后','色素代谢','激素响应','胁迫响应','胚胎与种子发育','营养生长','通用方法']},
    'regulation': {'label':'表观调控','values':['DNA甲基化','H3K27me3','组蛋白乙酰化','染色质可及性','染色质重塑','三维基因组','转录后调控','其他或未涉及']},
    'methods': {'label':'技术','values':['WGBS','ATAC-seq','CUT&Tag','Hi-C','单细胞或单核','多组学','TF footprint','Fiber-seq','表观基因组编辑','计算建模','数据库']},
    'evidence_type': {'label':'证据类型','values':['组学关联','遗传验证','直接结合或互作','位点编辑','方法评估','资源整合','待确认']},
    'article_type': {'label':'文章类型','values':['机制研究','关联研究','方法研究','数据库','综述或实质分析','待确认']},
}
SECTION_KINDS = ['reported','reported','application','application','limitation','reading']

def paper_id(p):
    identity = p.get('doi') or p['url']
    identity = identity.lower().replace('https://doi.org/','').strip().rstrip('/')
    return 'paper-' + hashlib.sha256(identity.encode()).hexdigest()[:16]

def validate_classification(c):
    if not isinstance(c, dict) or set(c) != set(TAXONOMY):
        raise ValueError('All six classification groups are required.')
    for key, config in TAXONOMY.items():
        if not isinstance(c[key],list) or any(v not in config['values'] for v in c[key]):
            raise ValueError('Unknown classification value: ' + key)

def enrich_paper(p):
    p.setdefault('id', paper_id(p))
    validate_classification(p['classification'])
    if len(p.get('sections',[])) != 6:
        raise ValueError('Six commentary sections are required.')
    for section, kind in zip(p['sections'],SECTION_KINDS):
        section['kind'] = kind
    return p
