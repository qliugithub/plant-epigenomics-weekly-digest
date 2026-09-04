const fs=require('fs'),vm=require('vm'),assert=require('assert');
class Node{constructor(tag){this.tag=tag;this.children=[];this.dataset={};this.textContent='';this.classList={toggle(){}};this.attributes={};}append(...xs){for(const x of xs){this.children.push(x);if(x&&typeof x==='object')x.parentNode=this;}}prepend(...xs){this.children.unshift(...xs);}appendChild(x){this.append(x);return x;}replaceChildren(...xs){this.children=[];this.append(...xs);}setAttribute(k,v){this.attributes[k]=v;}click(){this.onclick?.();}}
const nodes=new Map(),local=new Map(),document={body:{dataset:{}},documentElement:{},getElementById:id=>{if(!nodes.has(id))nodes.set(id,new Node('div'));return nodes.get(id)},createElement:t=>new Node(t),createTextNode:text=>({textContent:text}),querySelector:()=>new Node('div'),querySelectorAll:()=>[]};
const ctx={document,window:{addEventListener(){}},localStorage:{getItem:k=>local.get(k),setItem:(k,v)=>local.set(k,v)},fetch:()=>new Promise(()=>{}),history:{replaceState(){}},location:{pathname:'/',search:'',reload(){}},URLSearchParams,URL,Date,Set,Blob,setTimeout,console};vm.createContext(ctx);
for(const file of ['i18n','reader','app'])vm.runInContext(fs.readFileSync('dist/'+file+'.js','utf8'),ctx);
for(const[k,f]of [['data','digest'],['catalog','catalog'],['topics','topics'],['pool','candidates'],['revisions','revisions']])vm.runInContext(k+'='+fs.readFileSync('dist/'+f+'.json','utf8'),ctx);
const run=s=>vm.runInContext(s,ctx),walk=n=>[n,...(n.children||[]).flatMap(walk)],text=n=>walk(n).map(x=>x.textContent||'').join(' ');
assert.equal(run('filteredPapers().length'),run('catalog.papers.length'));
run("tags.add('species:拟南芥');tags.add('regulation:H3K27me3')");assert(run('filteredPapers().length')>=1);assert(run("filteredPapers().every(p=>p.classification.species.includes('拟南芥')&&p.classification.regulation.includes('H3K27me3'))"));
run("filters.methods='Fiber-seq'");assert(run("filteredPapers().every(p=>p.classification.methods.includes('Fiber-seq'))"));
run("tags.clear();filters.methods='';selected='2026-08-21'");assert.equal(run('filteredPapers().length'),5);
run("selected='';lang='en';render()");assert.equal(document.documentElement.lang,'en');
for(let i=0;i<run('catalog.papers.length');i++){const paper=run('renderPaper(catalog.papers['+i+'],0,true)');assert.equal(walk(paper).filter(n=>n.tag==='li').length,6);assert(!/[\u4e00-\u9fff]/.test(text(paper)),'Chinese content leaked into English paper '+i);}
for(const view of ['topics','personal','candidates','library'])run(`view='${view}';render()`);
run("view='topics';topicId='h3k27me3';render()");assert(run('filteredPapers().length')>0);
run("view='library';topicId='';query='tomato';render()");assert(run('filteredPapers().length')>0);
const id=run('catalog.papers[0].id');run(`R.set('${id}',{state:'read',star:true,note:'Private <script> text'});view='personal';query='';render()`);assert.equal(run('filteredPapers().length'),1);
const before=run('JSON.stringify(R.backup().records)');assert.throws(()=>run(`R.restore({format:'plant-epigenomics-reading',version:1,records:{bad:{}}})`));assert.equal(run('JSON.stringify(R.backup().records)'),before);
run(`R.restore({format:'plant-epigenomics-reading',version:1,records:{'${id}':{state:'todo',star:false,note:'Older',updated_at:'2020-01-01T00:00:00Z'}}})`);assert.equal(run(`R.get('${id}').state`),'read');
assert(run('R.ris(catalog.papers.slice(0,1))').includes('TY  - JOUR'));assert(run('R.bibtex([{...catalog.papers[0],metadata:null,title:"A & B_{x}"}])').includes('A \\& B\\_\\{x\\}'));
ctx.localStorage.setItem=()=>{throw Error('No quota')};assert.equal(run(`R.set('${id}',{note:'Keep in memory'})`),false);assert.equal(run(`R.backup().records['${id}'].note`),'Keep in memory');
console.log('PASS: bilingual 13×6, combined tags, filters, topic views, reading state, atomic backup validation, citation escaping and unavailable-storage recovery.');
