/* SPDX-License-Identifier: MIT — Read-only playback of actual RTL samples. */
'use strict';
const $=s=>document.querySelector(s);
const meta={
 fibonacci:['01 / SEQUENCE','Fibonacci','Build a sequence, one addition at a time.','12 Fibonacci numbers'],
 arithmetic:['02 / COMPUTATION','Arithmetic & bits','Watch overflow, signed comparisons, shifts, and bit operations.','Wrap, shift, compare'],
 array_sum:['03 / ACCUMULATION','Array sum','Read six signed words and accumulate a sum of 37.','Six words → one result'],
 sort:['04 / ORDERING','Bubble sort','Compare adjacent signed values and swap them in memory.','Six values, in place'],
 memory_copy:['05 / TRANSFER','Memory copy','Move sixteen bytes, including values with their high bit set.','Byte by byte'],
 search:['06 / CONTROL FLOW','Linear search','Follow the branches until the target 19 is found at index four.','Find a value']
};
const stateNames=['FETCH','DECODE','EXECUTE','MEMORY','WRITEBACK','HALT'];
const hex=(n,width=8)=>'0x'+(n>>>0).toString(16).padStart(width,'0');
let manifest,trace,index=0,timer=null,loadToken=0,selectedProgram='fibonacci',selectedLatency=2;
function pause(){if(timer!==null)clearInterval(timer);timer=null;$('#play').textContent='▶ Play';}
function memoryAt(i){
 const mem=Uint8Array.from(trace.initial_memory);
 for(let j=0;j<=i;j++){
  const f=trace.frames[j];
  if(f.valid&&f.ready&&f.write&&!f.error){
   for(let k=0;k<4;k++)if(f.mask&(1<<k)){
    const pos=f.addr+k-1024;if(pos>=0&&pos<mem.length)mem[pos]=(f.wdata>>>(k*8))&255;
   }
  }
 }
 return mem;
}
function explanation(f){
 const rd=(f.insn>>>7)&31,rs1=(f.insn>>>15)&31,rs2=(f.insn>>>20)&31;
 if(f.halted)return ['Breakpoint reached','EBREAK ends this experiment with terminal trap cause 3. It does not retire. Reset or choose another program to explore again.'];
 switch(f.state){
 case 0:return ['Fetch the next instruction',`The program counter places ${hex(f.pc)} on the memory address bus. ${f.ready?'Memory responds on this edge; the instruction register captures the word.':'The request stays stable while the processor waits for a memory response.'}`];
 case 1:return ['Decode the instruction',`The instruction bits select the operation, register addresses, and immediate. The register file exposes x${rs1} and x${rs2}; the next state is execute.`];
 case 2:{
  const op=f.insn&127;
  if(op===3||op===35)return ['Calculate the data address','The base register plus the sign-extended offset gives the byte address. The core checks alignment, then saves the address and any store data for the memory state.'];
  if(op===99)return ['Choose the next address','The control logic compares the two register values using the instruction’s signed or unsigned rule. A taken branch selects PC plus offset; otherwise execution continues at PC + 4.'];
  if(op===111||op===103)return ['Prepare a jump','The core computes the target and saves PC + 4 as the return address. JALR clears target bit zero; a remaining alignment error would trap.'];
  if(op===15)return ['Complete the memory fence','All memory operations finish in order before the next instruction starts, so FENCE needs no additional transaction.'];
  if(op===55||op===23)return ['Form the upper-immediate result',`${op===55?'LUI places the instruction’s upper immediate into the result latch.':'AUIPC adds the upper immediate to this instruction’s PC.'} Register x${rd} will be updated during writeback.`];
  return ['Compute and latch the result',`The ALU sees A = ${hex(f.a)} and B = ${hex(f.b)}. Its sampled result is ${hex(f.alu)}. The execute edge saves this value for writeback.`];
 }
 case 3:return [f.write?'Store to data memory':'Load from data memory',`${f.write?'A store':'A load'} requests aligned word ${hex(f.addr)}. ${f.ready?(f.write?`Memory acknowledges once; byte enable ${f.mask.toString(2).padStart(4,'0')} selects the written lanes.`:'Memory responds; the core extracts the requested byte, halfword, or word and extends it if needed.'):'No response yet. The address, write data, and byte enables remain stable.'}`];
 case 4:return ['Retire the instruction',`${f.rd?`x${f.rd} receives ${hex(f.rd_data)}. `:'No general-purpose register changes. '}The architectural PC becomes ${hex(f.retire_next_pc)}. This is the point checked against the project’s reference model.`];
 default:return ['Processor halted','A terminal execution-environment trap stopped the core.'];
 }
}
function render(){
 const f=trace.frames[index],previous=index?trace.frames[index-1].regs:Array(32).fill(0);
 $('#cycle').textContent=String(f.cycle).padStart(3,'0');$('#total').textContent=trace.frames.length;
 $('#timeline').value=index;$('#progress').textContent=`Cycle ${f.cycle}`;
 $('#pc').textContent=hex(f.pc);
 const listed=trace.listing[f.pc];
 $('#asm').textContent=(listed?listed.text:'Unknown instruction')+(f.state===0?' · fetching':'');
 $('#word').textContent=hex(f.state===0?(listed?listed.word:f.rdata):f.insn);
 $('#state-label').textContent=f.halted?'HALT · EBREAK':stateNames[f.state];
 $('#stages').replaceChildren(...stateNames.slice(0,5).map((name,i)=>{
  const el=document.createElement('div');el.className='stage'+(f.state===i?' active':'')+(f.halted?' done':'');el.textContent=`0${i+1} ${name}`;return el;
 }));
 document.querySelectorAll('[data-states]').forEach(el=>el.classList.toggle('active',!f.halted&&el.dataset.states.split(' ').includes(String(f.state))));
 $('#svg-pc').textContent=hex(f.pc);$('#svg-ir').textContent=f.state===0?'await fetch':hex(f.insn);
 $('#svg-control').textContent=f.halted?'HALT':stateNames[f.state];
 $('#svg-alu').textContent=f.state===2?hex(f.alu,8).slice(2):'—';
 $('#svg-address').textContent=f.valid?hex(f.addr):'idle';$('#svg-response').textContent=f.valid?(f.ready?'acknowledged':'waiting…'):'idle';
 const [title,text]=explanation(f);$('#explain-title').textContent=title;$('#explain').textContent=text;
 $('#explain-number').textContent=String(f.state+1).padStart(2,'0');
 $('#edge-status').textContent=f.halted?'HALTED':f.retire?'RETIRED':f.valid?(f.ready?'RESPONSE':'WAITING'):'INTERNAL';
 $('#registers').replaceChildren(...f.regs.map((v,r)=>{
  const el=document.createElement('div');el.className='reg'+(v!==previous[r]?' changed':'');
  const name=document.createElement('span');name.textContent='x'+r;
  const value=document.createElement('code');value.textContent=(v>>>0).toString(16).padStart(8,'0');
  el.append(name,value);return el;
 }));
 const mem=memoryAt(index);$('#memory').replaceChildren(...Array.from({length:32},(_,n)=>{
  const address=1024+n*4;const word=(mem[n*4]|mem[n*4+1]<<8|mem[n*4+2]<<16|mem[n*4+3]<<24)>>>0;
  const changed=f.valid&&f.ready&&f.write&&!f.error&&f.addr===address;
  const el=document.createElement('div');el.className='memrow'+(changed?' changed':'');
  const label=document.createElement('span');label.textContent=hex(address,4);
  const value=document.createElement('code');value.textContent=hex(word);
  const signed=document.createElement('small');signed.textContent=word|0;
  el.append(label,value,signed);return el;
 }));
 const end=index===trace.frames.length-1;
 $('#step').disabled=end;$('#instruction').disabled=end;
 if(end)pause();
}
function advance(){if(!trace)return;if(index<trace.frames.length-1)index++;render();}
function play(){
 if(!trace || $('#play').disabled)return;
 if(timer!==null){pause();return;}
 if(index===trace.frames.length-1)index=0;
 $('#play').textContent='Ⅱ Pause';timer=setInterval(advance,Number($('#speed').value));render();
}
function loading(active){
 $('#workspace').setAttribute('aria-busy',String(active));
 for(const id of ['play','step','instruction','reset','timeline'])$('#'+id).disabled=active;
}
async function select(id,latency=selectedLatency){
 selectedProgram=id;selectedLatency=latency;
 const token=++loadToken;pause();loading(true);$('#loading').hidden=false;
 $('#loading').textContent=`Loading ${meta[id][1]} with ${latency}-cycle memory…`;
 try{
  const program=manifest.programs.find(p=>p.id===id);
  const entry=program.variants.find(v=>v.latency===latency);
  const response=await fetch('data/'+entry.file);if(!response.ok)throw new Error('Trace could not be loaded. Choose a program or memory latency to retry.');
  const next=await response.json();if(token!==loadToken)return;
  trace=next;index=0;
  const [kicker,title,desc]=meta[id];$('#program-kicker').textContent=kicker;$('#program-title').textContent=title;$('#program-desc').textContent=desc;
  $('#source').textContent=trace.assembly;$('#timeline').max=trace.frames.length-1;
  $('#latency').value=latency;$('#memory-tag').textContent=`${latency}-CYCLE MEMORY`;
  $('#metric-cycles').textContent=trace.stats.cycles;
  $('#metric-retired').textContent=trace.stats.retired;
  $('#metric-waits').textContent=trace.stats.wait_cycles;
  $('#metric-cpi').textContent=trace.stats.cpi.toFixed(3);
  const baseline=program.variants.find(v=>v.latency===1).stats;
  $('#latency-explanation').textContent=latency===1
   ? `Baseline: memory responds on the first request edge. There are no waiting cycles. ${baseline.retired} instructions retire.`
   : `${trace.stats.requests} memory requests × ${latency-1} extra ${latency===2?'cycle':'cycles'} = ${trace.stats.wait_cycles} waiting cycles. The program still retires ${baseline.retired} instructions; total cycles are ${(trace.stats.cycles/baseline.cycles).toFixed(2)}× the one-cycle baseline.`;
  document.querySelectorAll('.program').forEach(b=>{b.classList.toggle('active',b.dataset.program===id);b.setAttribute('aria-pressed',String(b.dataset.program===id));});
  $('#loading').hidden=true;loading(false);render();
 }catch(e){if(token===loadToken){$('#workspace').setAttribute('aria-busy','false');$('#loading').hidden=false;$('#loading').textContent=e.message;}}
}
loading(true);
$('#latency').addEventListener('change',e=>select(selectedProgram,Number(e.target.value)));
$('#play').addEventListener('click',play);$('#step').addEventListener('click',()=>{pause();advance();});
$('#reset').addEventListener('click',()=>{pause();if(trace){index=0;render();}});
$('#instruction').addEventListener('click',()=>{pause();if(!trace)return;do{index++;}while(index<trace.frames.length-1&&!trace.frames[index].retire);render();});
$('#timeline').addEventListener('input',e=>{pause();if(trace){index=Number(e.target.value);render();}});
$('#speed').addEventListener('change',()=>{if(timer!==null){pause();play();}});
document.addEventListener('keydown',e=>{if(e.code==='Space'&&e.target===document.body){e.preventDefault();play();}});
(async()=>{
 try{
  const response=await fetch('data/manifest.json');if(!response.ok)throw new Error('Missing trace manifest; run make benchmark and make demo.');
  manifest=await response.json();
  for(const [id,values] of Object.entries(meta)){
   const button=document.createElement('button');button.className='program';button.dataset.program=id;
   const number=document.createElement('span');number.className='index';number.textContent=values[0].slice(0,2);
   const name=document.createElement('span');name.textContent=values[1];const small=document.createElement('small');small.textContent=values[3];name.append(small);
   button.append(number,name);button.addEventListener('click',()=>select(id));$('#programs').append(button);
  }
  await select('fibonacci');
 }catch(e){$('#loading').textContent=e.message;}
})();
