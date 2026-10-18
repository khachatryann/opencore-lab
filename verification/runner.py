"""Run actual Verilated hardware; compare full architecture at each retirement."""
import json
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from assembler import assemble
from reference import Reference,Trap

ROOT=Path(__file__).resolve().parents[1]

def run_case(name,source,latency=1,jitter=0,seed=1,wave=False):
    image,listing=assemble(source)
    folder=ROOT/'build'/'runs';folder.mkdir(parents=True,exist_ok=True)
    base=folder/name
    base.with_suffix('.bin').write_bytes(image)
    command=[str(ROOT/'build/sim'),str(base.with_suffix('.bin')),str(base.with_suffix('.jsonl')),str(latency),str(jitter),str(seed)]
    if wave: command.append(str(base.with_suffix('.vcd')))
    proc=subprocess.run(command,check=True,capture_output=True,text=True)
    stats=json.loads(proc.stdout)
    frames=[json.loads(line) for line in base.with_suffix('.jsonl').read_text().splitlines()]
    ref=Reference(image);observed=bytearray(ref.memory);store_events=[];retired=0
    for f in frames:
        assert f['regs'][0]==0,(name,'x0')
        if f['valid'] and f['ready'] and not f['error'] and f['write']:
            address=f['addr'];data=f['wdata'];mask=f['mask']
            for i in range(4):
                if mask&(1<<i): observed[address+i]=(data>>(i*8))&255
            store_events.append((address,mask,data))
        if f['retire']:
            expected=ref.step();retired+=1
            for key,trace_key in [('pc','retire_pc'),('insn','retire_insn'),('next_pc','retire_next_pc'),('rd','rd'),('rd_data','rd_data')]:
                assert expected[key]==f[trace_key],(name,f['cycle'],key,expected[key],f[trace_key])
            assert ref.regs==f['regs'],(name,f['cycle'],'register state',ref.regs,f['regs'])
            assert observed==ref.memory,(name,f['cycle'],'memory state')
    try: ref.step()
    except Trap as t:
        last=frames[-1]
        assert last['halted'] and t.cause==last['cause'] and t.value==last['trap_value'],(name,'trap',t.cause,t.value,last)
        assert ref.pc==last['next_pc'],(name,'trap PC')
        assert ref.regs==last['regs'] and observed==ref.memory,(name,'trap side effects')
    else: raise AssertionError((name,'RTL halted without reference trap'))
    assert stats['retired']==retired and stats['cycles']==len(frames)
    assert stats['wait_cycles']==sum(bool(f['valid'] and not f['ready']) for f in frames)
    assert stats['stores']==len(store_events)==sum(ref.coverage[op] for op in ('sb','sh','sw'))
    stats['name']=name;stats['cpi']=stats['cycles']/retired if retired else None
    return stats,frames,ref,listing,image
