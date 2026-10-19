// SPDX-License-Identifier: MIT
// Exercise the actual page script with controlled network responses and a minimal DOM.
// This isolates loading/error/race behavior; real-browser layout is checked separately.
'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const root=path.resolve(__dirname,'..');
class Element {
 constructor(){this.textContent='';this.disabled=false;this.hidden=false;this.value='';this.dataset={};this.attrs={};this.listeners={};this.children=[];this.classList={toggle(){}};}
 setAttribute(key,value){this.attrs[key]=value;}
 addEventListener(event,fn){this.listeners[event]=fn;}
 append(...nodes){this.children.push(...nodes);}
 replaceChildren(...nodes){this.children=nodes;}
}
const elements=new Map();
const node=id=>{if(!elements.has(id))elements.set(id,new Element());return elements.get(id);};
const body=new Element();
const pending=[];const timers=new Map();let nextTimer=0;
const manifest=JSON.parse(fs.readFileSync(path.join(root,'demo/data/manifest.json'),'utf8'));
const traceFor=(program,latency)=>{
 const entry=manifest.programs.find(p=>p.id===program).variants.find(v=>v.latency===latency);
 return JSON.parse(fs.readFileSync(path.join(root,'demo/data',entry.file),'utf8'));
};
const document={body,querySelector:s=>node(s),querySelectorAll:()=>[],createElement:()=>new Element(),
 addEventListener:(event,fn)=>{document[event]=fn;}};
const context=vm.createContext({document,console,Uint8Array,
 fetch:url=>url==='data/manifest.json'?Promise.resolve({ok:true,json:async()=>manifest}):new Promise(resolve=>pending.push({url,resolve})),
 setInterval:fn=>{const id=++nextTimer;timers.set(id,fn);return id;},clearInterval:id=>timers.delete(id)});
vm.runInContext(fs.readFileSync(path.join(root,'demo/app.js'),'utf8'),context);
const flush=()=>new Promise(resolve=>setImmediate(resolve));
const keySpace=()=>document.keydown({code:'Space',target:body,preventDefault(){}});
const choose=latency=>node('#latency').listeners.change({target:{value:String(latency)}});
const respond=(request,program,latency)=>request.resolve({ok:true,json:async()=>traceFor(program,latency)});
(async()=>{
 await flush();
 assert.equal(pending.length,1);assert.equal(node('#play').disabled,true);
 keySpace();assert.equal(timers.size,0,'startup loading cannot play');
 respond(pending.shift(),'fibonacci',2);await flush();
 assert.equal(node('#cycle').textContent,'001');assert.equal(node('#play').disabled,false);
 keySpace();assert.equal(timers.size,1,'Space starts a loaded trace');keySpace();assert.equal(timers.size,0);
 choose(4);assert.equal(node('#play').disabled,true);assert.equal(node('#workspace').attrs['aria-busy'],'true');
 keySpace();assert.equal(timers.size,0,'Space cannot play stale data while a new trace loads');
 pending.shift().resolve({ok:false});await flush();
 assert.equal(node('#workspace').attrs['aria-busy'],'false');assert.equal(node('#play').disabled,true);
 assert.match(node('#loading').textContent,/retry/);
 keySpace();assert.equal(timers.size,0,'Space cannot play stale data after a failed load');
 choose(1);respond(pending.shift(),'fibonacci',1);await flush();
 assert.equal(node('#metric-cycles').textContent,367);assert.equal(node('#play').disabled,false,'selector retries successfully');
 // Finish the newer response first; a late older response must not replace it.
 choose(4);const old=pending.shift();choose(2);const current=pending.shift();
 respond(current,'fibonacci',2);await flush();respond(old,'fibonacci',4);await flush();
 assert.equal(node('#metric-cycles').textContent,468);assert.equal(node('#latency').value,2);
 keySpace();assert.equal(timers.size,1);choose(4);assert.equal(timers.size,0,'switching cancels running playback');
 respond(pending.shift(),'fibonacci',4);await flush();
 assert.equal(node('#metric-cycles').textContent,670);assert.equal(node('#cycle').textContent,'001');
 assert.equal(node('#metric-waits').textContent,303);
 console.log('PASS: demo startup, loading keyboard guard, failed-load guard, retry, stale-response race, and playback cancellation');
})().catch(error=>{console.error(error);process.exitCode=1;});
