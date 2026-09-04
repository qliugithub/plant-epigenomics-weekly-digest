'use strict';
let data, selected, query='', priority='';
const $=id=>document.getElementById(id);
const el=(tag,cls,text)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(text)n.textContent=text;return n;};
function render(){
 const all=selected==='all';const issues=all?data.issues:data.issues.filter(i=>i.date===selected);
 $('edition-label').textContent=all?'THE ARCHIVE':'WEEKLY EDITION';$('edition-title').textContent=all?'全部周报':selected;
 $('summary').textContent=all?'按关键词与阅读建议，查找历史推荐。':issues[0].summary;
 $('provenance').textContent=all?'历史内容来自已提供的周报；未在此次建站中重新核验全部论文。':issues[0].provenance;
 const papers=issues.flatMap(i=>i.papers.map(p=>({...p,issueDate:i.date}))).filter(p=>(!priority||p.priority===priority)&&JSON.stringify(p).toLowerCase().includes(query));
 $('result-count').textContent=`${papers.length} 篇文献`;$('papers').replaceChildren();
 if(!papers.length)$('papers').append(el('div','empty','没有符合条件的文献。试试其他关键词或阅读建议。'));
 papers.forEach((p,k)=>{const article=el('article','paper');article.append(el('span','paper-number',String(k+1).padStart(2,'0')));const body=el('div');const meta=el('div','meta');meta.append(el('span','badge'+(p.priority==='全文精读'?'':' skim'),p.priority),el('span','',p.journal),el('span','',p.kind),el('span','',p.date));body.append(meta,el('h3','',p.title));const tags=el('div','tags');p.tags.forEach(t=>tags.append(el('span','tag',t)));body.append(tags);if(p.heading)body.append(el('h4','',p.heading));const sections=p.sections||[{label:'新在哪里',text:p.novelty},{label:'研究关联',text:p.relevance},{label:'阅读重点',text:p.reading},{label:'研究边界',text:p.limit}];for(const section of sections){const line=el('p','insight');line.append(el('strong','',section.label+' · '),document.createTextNode(section.text));body.append(line)}const a=el('a','','阅读原文 ↗');if(/^https:\/\//.test(p.url)){a.href=p.url;a.target='_blank';a.rel='noopener noreferrer';body.append(a)}article.append(body);$('papers').append(article)});
 document.querySelectorAll('nav button').forEach(b=>{const active=b.dataset.date===selected;b.classList.toggle('active',active);b.setAttribute('aria-pressed',String(active))});
}
fetch('digest.json').then(r=>{if(!r.ok)throw Error('load');return r.json()}).then(d=>{data=d;d.issues.sort((a,b)=>b.date.localeCompare(a.date));selected=d.issues[0].date;$('count').textContent=d.issues.reduce((s,i)=>s+i.papers.length,0);if(d.automation?.enabled)$('schedule-status').textContent='已配置 GitHub 定时更新';for(const i of [{date:'all',papers:[],label:'全部归档'},...d.issues]){const b=el('button','',i.label||i.date);b.dataset.date=i.date;if(!i.label)b.append(el('span','',String(i.papers.length)));b.onclick=()=>{selected=i.date;render()};$('issues').append(b)}render()}).catch(()=>{$('edition-title').textContent='周报暂时无法载入';$('summary').textContent='请刷新页面重试。';});
$('search').addEventListener('input',e=>{query=e.target.value.toLowerCase().trim();if(query)selected='all';render()});$('priority').addEventListener('change',e=>{priority=e.target.value;render()});
