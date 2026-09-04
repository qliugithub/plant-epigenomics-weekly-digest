'use strict';
const $=id=>document.getElementById(id);
const base=document.body.dataset.base||'./';
const detailId=document.body.dataset.paper||null;
const filters={};
let data,catalog,selected='all',query='',priority='';
const el=(tag,cls,text)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n;};
function link(text,url,cls=''){const a=el('a',cls,text);a.href=url;return a;}
function external(text,url){const a=link(text,url);a.target='_blank';a.rel='noopener noreferrer';return a;}
function paperHref(id){return base+'papers/'+encodeURIComponent(id)+'/';}
function filteredPapers(){
 const issue=data.issues.find(i=>i.date===selected);
 const ids=issue?new Set(issue.papers.map(p=>p.id)):null;
 return catalog.papers.filter(p=>(!ids||ids.has(p.id))&&(!priority||p.priority===priority)&&
 Object.entries(filters).every(([k,v])=>!v||(p.classification[k]||[]).includes(v))&&
 (!query||[p.title,p.heading,p.journal,...p.tags,...p.sections.map(s=>s.text)].join(' ').toLowerCase().includes(query)));
}
function renderPaper(p,index,detail=false){
 const article=el('article','paper');article.append(el('span','paper-number',String(index+1).padStart(2,'0')));
 const body=el('div');
 const title=el(detail?'h1':'h3','paper-heading');
 if(detail)title.textContent=p.priority+'｜'+p.heading;
 else title.append(link(p.priority+'｜'+p.heading,paperHref(p.id)));
 body.append(title,el('h4','',p.title));
 const meta=el('div','meta');meta.append(el('span','badge',p.priority),el('span','',p.kind),el('span','',p.journal),el('time','',p.date));body.append(meta);
 const evidence=p.evidence||{};
 const note=el('div','evidence-box');
 note.append(el('strong','',evidence.source_type==='abstract'?'解读依据：摘要':'解读依据：历史周报'),el('span','',evidence.reading_depth||'阅读深度未记录'),el('span','verification','内容核验：'+(evidence.verification||'待核验')));
 note.append(el('p','',evidence.note||'尚未核验全文；研究启示属于建议。'));
 if(evidence.retrieved_at)note.append(el('p','','摘要获取时间：'+formatDate(evidence.retrieved_at)));
 if(/^https:\/\//.test(evidence.source_url||''))note.append(external('查看依据来源 ↗',evidence.source_url));
 body.append(note);
 const tags=el('div','tags');
 Object.entries(catalog.taxonomy).forEach(([key,config])=>(p.classification[key]||[]).forEach(value=>{
  if(detail)tags.append(el('span','tag',config.label+'：'+value));
  else {const b=el('button','tag',config.label+'：'+value);b.type='button';b.onclick=()=>{selected='all';filters[key]=value;$('filter-'+key).value=value;updateURL();render();};tags.append(b);}
 }));body.append(tags,el('p','classification-note',evidence.classification_status||'分类待核验'));
 const list=el('ul','analysis-sections');
 p.sections.forEach((s,i)=>{const item=el('li','insight');
  const label=el('strong','',s.label+'：');item.append(label);
  if(i===2||i===3)item.append(el('span','section-kind','研究建议'));
  else if(i<2)item.append(el('span','section-kind reported',evidence.source_type==='abstract'?'摘要报告 · 待核验':'原周报报告 · 待核验'));
  item.append(document.createTextNode(s.text));list.append(item);
 });body.append(list);
 const actions=el('div','paper-actions');
 if(/^https:\/\//.test(p.url))actions.append(external('阅读原文 ↗',p.url));
 if(!detail)actions.append(link('独立论文页面',paperHref(p.id)));
 body.append(actions);
 if(detail){const issues=el('p','issue-links','收录周报：');p.issues.forEach(date=>issues.append(link(date,base+'?issue='+encodeURIComponent(date))));body.append(issues);}
 article.append(body);return article;
}
function render(){
 if(!data)return;
 if(detailId){
  const p=catalog.papers.find(p=>p.id===detailId);
  document.querySelector('.toolbar').hidden=true;$('filters').hidden=true;document.querySelector('.filter-footer').hidden=true;document.querySelector('.heading').hidden=true;
  $('detail-nav').hidden=false;$('detail-nav').replaceChildren(link('← 返回文献库',base));
  $('edition-label').textContent='PAPER RECORD';$('edition-title').textContent='论文解读';$('summary').textContent='';$('result-count').textContent='';
  $('papers').replaceChildren(p?renderPaper(p,0,true):el('p','empty','找不到这篇论文，请返回文献库。'));
  $('provenance').textContent='研究建议与原文证据分开标注；“待核验”不表示已确认全文结论。';return;
 }
 const papers=filteredPapers(),issue=data.issues.find(i=>i.date===selected);
 $('edition-label').textContent=issue?'WEEKLY EDITION':'LITERATURE CATALOG';
 $('edition-title').textContent=issue?issue.date:'全部文献';
 $('summary').textContent=issue?issue.summary:'按物种、过程、表观调控、技术、证据和文章类型组合查找。每篇论文保留完整六段解读。';
 $('result-count').textContent=papers.length+' / '+catalog.papers.length+' 篇';
 $('papers').replaceChildren(...papers.map((p,i)=>renderPaper(p,i)));
 if(!papers.length)$('papers').append(el('p','empty','没有同时满足这些条件的文献。请减少筛选条件或清除筛选。'));
 $('provenance').textContent=issue?issue.provenance:'历史解读来自原周报，新增应用建议已单独标记。当前分类与内容均不代表已完成原文核验。';
 document.querySelectorAll('nav button').forEach(b=>{const active=b.dataset.date===selected;b.classList.toggle('active',active);b.setAttribute('aria-pressed',String(active));});
}
function updateURL(){const params=new URLSearchParams();if(selected!=='all')params.set('issue',selected);if(query)params.set('q',query);if(priority)params.set('priority',priority);for(const [k,v]of Object.entries(filters))if(v)params.set(k,v);history.replaceState(null,'',location.pathname+(params.size?'?'+params:''));}
function readURL(){const params=new URLSearchParams(location.search);selected=params.get('issue')||'all';if(!data.issues.some(i=>i.date===selected))selected='all';query=(params.get('q')||'').toLowerCase();priority=params.get('priority')||'';if(!['','全文精读','快速浏览','背景参考'].includes(priority))priority='';$('search').value=query;$('priority').value=priority;for(const[k,c]of Object.entries(catalog.taxonomy)){const v=params.get(k)||'';filters[k]=c.values.includes(v)?v:'';$('filter-'+k).value=filters[k];}}
async function json(url){const r=await fetch(url,{cache:'no-store'});if(!r.ok)throw Error('HTTP '+r.status);return r.json();}
function formatDate(value){if(!value)return '尚无记录';const d=new Date(value);return Number.isNaN(d.getTime())?'时间未记录':d.toLocaleString('zh-CN',{timeZone:'Asia/Singapore',hour12:false})+'（新加坡）';}
function runLabel(run){if(!run)return '尚无运行记录';if(run.status!=='completed')return '运行中 / 排队中';return ({success:'成功',failure:'失败',cancelled:'已取消',timed_out:'超时',skipped:'已跳过',action_required:'等待操作'})[run.conclusion]||'结果待确认';}
function displayRuns(weekly,publishes,cached=false){
 const latest=weekly[0];const successful=[...weekly,...publishes].filter(r=>r.conclusion==='success').sort((a,b)=>b.updated_at.localeCompare(a.updated_at))[0];
 const latestPublish=[...weekly,...publishes].sort((a,b)=>b.created_at.localeCompare(a.created_at))[0];
 const box=$('run-status');box.replaceChildren();
 const row=el('div','status-grid');
 for(const [label,value,run]of [['最近周报任务',runLabel(latest),latest],['最近发布相关任务',runLabel(latestPublish),latestPublish],['最近成功发布',successful?formatDate(successful.updated_at):'尚无成功记录',successful]]){
  const cell=el('div');cell.append(el('span','',label),el('strong','',value));if(run)cell.append(external('查看记录 ↗',run.html_url));row.append(cell);
 }box.append(row);$('status-note').textContent=(cached?'显示构建时缓存，当前状态无法实时确认。':'状态来自 GitHub Actions。')+' 周报任务成功不等于执行过新文献检索；实际检索时间与数量见下方。';
}
async function loadStatus(){
 let snapshot={};try{snapshot=await json(base+'status.json');}catch{}
 const search=snapshot.last_search;
 $('search-stats').textContent=search?`最近实际检索：${formatDate(search.at)} · 检索 ${search.retrieved} 条 · 候选 ${search.candidates} 篇 · 推荐 ${search.recommended} 篇`:'最近实际检索：尚无记录。历史四期为导入内容，密钥检查和重复日期跳过不计作文献检索。';
 if(search?.recommended===0)$('search-stats').textContent+=' 本次检索完成，但没有推荐新论文。';
 try{
  const root='https://api.github.com/repos/qliugithub/plant-epigenomics-weekly-digest/actions/workflows/';
  const [a,b]=await Promise.all([json(root+'weekly.yml/runs?per_page=10'),json(root+'publish.yml/runs?per_page=10')]);
  displayRuns(a.workflow_runs,b.workflow_runs);
 }catch{if(snapshot.runs)displayRuns(snapshot.runs.weekly||[],snapshot.runs.publish||[],true);else{$('run-status').textContent='暂时无法读取运行状态（可能为网络或 API 限流）。';$('status-note').textContent='请打开运行记录确认；此提示不表示周报任务已失败。';}}
}
Promise.all([json(base+'digest.json'),json(base+'catalog.json')]).then(([d,c])=>{
 data=d;catalog=c;data.issues.sort((a,b)=>b.date.localeCompare(a.date));$('count').textContent=catalog.papers.length;
 for(const [key,config]of Object.entries(catalog.taxonomy)){const label=el('label','filter-label',config.label);const select=el('select');select.id='filter-'+key;select.append(el('option','','全部'+config.label));select.firstChild.value='';config.values.forEach(v=>{const o=el('option','',v);o.value=v;select.append(o);});select.onchange=()=>{filters[key]=select.value;updateURL();render();};label.append(select);$('filters').append(label);}
 for(const issue of [{date:'all',label:'全部文献'},...data.issues]){if(detailId){$('issues').append(link(issue.label||issue.date,base+(issue.date==='all'?'':'?issue='+issue.date),'nav-link'));continue;}const b=el('button','',issue.label||issue.date);b.type='button';b.dataset.date=issue.date;if(issue.papers)b.append(el('span','',issue.papers.length));b.onclick=()=>{selected=issue.date;updateURL();render();};$('issues').append(b);}
 readURL();render();
}).catch(()=>{$('edition-title').textContent='文献暂时无法载入';$('summary').textContent='请刷新页面重试。';});
$('search').oninput=e=>{query=e.target.value.trim().toLowerCase();updateURL();render();};
$('priority').onchange=e=>{priority=e.target.value;updateURL();render();};
$('clear-filters').onclick=()=>{query='';priority='';selected='all';$('search').value='';$('priority').value='';for(const key of Object.keys(filters)){filters[key]='';$('filter-'+key).value='';}updateURL();render();};
window.addEventListener('popstate',()=>{if(data&&!detailId){readURL();render();}});
loadStatus();
