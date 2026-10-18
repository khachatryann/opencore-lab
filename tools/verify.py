#!/usr/bin/env python3
"""Directed + reproducible random differential regression, including bus stalls."""
from pathlib import Path
import json
import random
import re
import subprocess
import sys
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'verification'))
from runner import run_case
from assembler import assemble,R_OPS,I_OPS,BRANCHES,LOADS,STORES


def li(r,n):
    n &= 0xffffffff
    lo=(n&4095)-(4096 if n&2048 else 0)
    hi=((n-lo)>>12)&0xfffff
    return f'lui x{r}, {hi}\naddi x{r}, x{r}, {lo}\n'

def directed():
    src=li(1,0x80000000)+li(2,0xffffffff)+li(3,1)+li(4,0x7fffffff)
    for op in R_OPS:
        for a,b in [(1,2),(2,3),(3,4),(4,3),(1,1)]: src+=f'{op} x5, x{a}, x{b}\n'
        src+=f'{op} x0, x1, x2\n'
    for op in I_OPS:
        for v in ([0,1,31] if op in ('slli','srli','srai') else [-2048,-1,0,2047]):
            src+=f'{op} x6, x1, {v}\n'
    src+='auipc x7, 0x80000\n'
    for op in BRANCHES:
        for i,(a,b) in enumerate([(1,2),(2,1),(1,1),(3,4)]):
            label=f'{op}_{i}'
            src+=f'{op} x{a}, x{b}, {label}\naddi x8, x8, 1\n{label}:\naddi x9, x9, 1\n'
    src+='jal x11, jump\naddi x8, x0, 666\njump:\n'
    # JALR clears bit zero and reads old rs1 even when rd == rs1.
    src+='auipc x12, 0\naddi x12, x12, 17\njalr x12, 0(x12)\naddi x8, x0, 666\nfence\n'
    src+='addi x20, x0, 1024\n'+li(1,0x80ff7f01)
    src+='sw x1, 0(x20)\n'
    for op in LOADS:
        for off in (range(4) if op in ('lb','lbu') else [0,2] if op in ('lh','lhu') else [0]):
            src+=f'{op} x2, {off}(x20)\n'
    src+='lw x0, 0(x20)\n'
    for off in range(4): src+=f'sb x1, {4+off}(x20)\n'
    for off in (0,2): src+=f'sh x1, {8+off}(x20)\n'
    # Negative address offset and register shift masking by low 5 bits.
    src+='addi x21, x20, 4\nlw x3, -4(x21)\naddi x4, x0, 32\nsll x5, x1, x4\nsra x5, x1, x4\nebreak\n'
    return src

def randomized(seed):
    rng=random.Random(seed)
    lines=['addi x20, x0, 409', 'slli x20, x20, 4'] # data base 0x1990, beyond code
    for r in range(1,16): lines+=li(r,rng.getrandbits(32)).splitlines()
    for i in range(180):
        d=rng.randrange(16);a=rng.randrange(16);b=rng.randrange(16)
        choice=rng.randrange(5)
        if choice==0:
            op=rng.choice(list(R_OPS));lines.append(f'{op} x{d}, x{a}, x{b}')
        elif choice==1:
            op=rng.choice(list(I_OPS));im=rng.randrange(32) if op in ('slli','srli','srai') else rng.randrange(-2048,2048)
            lines.append(f'{op} x{d}, x{a}, {im}')
        elif choice==2:
            op=rng.choice(list(LOADS)+list(STORES));alignment=4 if op in ('lw','sw') else 2 if op in ('lh','lhu','sh') else 1
            offset=rng.randrange(64//alignment)*alignment
            lines.append(f'{op} x{d}, {offset}(x20)')
        elif choice==3:
            op=rng.choice(list(BRANCHES));lines.extend([f'{op} x{a}, x{b}, skip{i}',f'addi x{d}, x{a}, 1',f'skip{i}:'])
        else: lines.extend([f'jal x{d}, jump{i}','addi x0, x0, 0',f'jump{i}:'])
    lines.append('ebreak');return '\n'.join(lines)

def main():
    unit=subprocess.run([str(ROOT/'build/unit/Vunit_tb')],check=True,capture_output=True,text=True).stdout
    unit_count=int(re.search(r'UNIT_CHECKS=(\d+)',unit)[1])
    summaries=[];coverage=Counter(); seeds=[7,42,2026,0xc0ffee,0xdeadbeef]
    def run(name,source,latency=1,jitter=0,seed=1,wave=False):
        stats,frames,ref,_,_=run_case(name,source,latency,jitter,seed,wave)
        summaries.append(stats);coverage.update(ref.coverage)
        return stats,frames,ref
    for latency in [1,2,4]: run(f'directed-l{latency}',directed(),latency,wave=latency==2)
    for seed in seeds:
        run(f'random-{seed}',randomized(seed),2,5,seed)
    traps={
      'illegal':' .word 0xffffffff', 'mul':' .word 0x02000033',
      'badshift':' .word 0x02001013','badjalr':'.word 0x00001067',
      'badbranch':'.word 0x00002063','badload':'.word 0x00003003',
      'badstore':'.word 0x00003023','csr':'.word 0xc0001073',
      'fencei':'.word 0x0000100f','ecall':'ecall','ebreak':'ebreak',
      'load-half':'addi x1, x0, 1025\nlh x2, 0(x1)',
      'load-word':'addi x1, x0, 1026\nlw x0, 0(x1)',
      'store-half':'addi x1, x0, 1025\nsh x2, 0(x1)',
      'store-word':'addi x1, x0, 1026\nsw x2, 0(x1)',
      'jal-align':'jal x5, 2','branch-align':'beq x0, x0, 2',
      'jalr-align':'addi x1, x0, 3\njalr x1, 0(x1)',
      'fetch-fault':'lui x1, 0x10\njalr x0, 0(x1)',
      'load-fault':'addi x1, x0, -4\nlw x0, 0(x1)',
      'store-fault':'addi x1, x0, -4\nsw x1, 0(x1)',
      'system-reserved':'.word 0x00200073',
    }
    for name,source in traps.items():
        for latency in (1,4): run('trap-'+name+f'-l{latency}',source,latency)
    run('untaken-misaligned','bne x0, x0, 2\nebreak',4)
    # Reserved FENCE fields ignored; memory operations already serialized.
    run('fence-fields','.word 0xfffF8f8f\nebreak',3)
    # Expected values from pinned upstream TEST_RR_OP macros, not this oracle.
    upstream=(ROOT/'third_party/riscv-tests-add.S').read_text()
    matches=re.findall(r'TEST_RR_OP\(\s*(\d+),\s*add,\s*(0x[0-9a-f]+),\s*(0x[0-9a-f]+),\s*(0x[0-9a-f]+)\s*\)',upstream)
    assert len(matches)==15
    for ident,expected,a,b in matches:
        _,_,ref=run('upstream-add-'+ident,li(1,int(a,16))+li(2,int(b,16))+'add x3, x1, x2\nebreak',4)
        assert ref.regs[3]==int(expected,16)&0xffffffff
    for path in sorted((ROOT/'examples').glob('*.S')):
        _,_,ref=run('example-'+path.stem,path.read_text(),2,3,42)
        if path.stem=='fibonacci':
            assert [int.from_bytes(ref.memory[1024+i*4:1028+i*4],'little') for i in range(12)]==[0,1,1,2,3,5,8,13,21,34,55,89]
        elif path.stem=='sort':
            assert [int.from_bytes(ref.memory[1024+i*4:1028+i*4],'little',signed=True) for i in range(6)]==[-3,0,2,7,12,19]
        elif path.stem=='array_sum': assert ref.regs[10]==37
        elif path.stem=='search': assert ref.regs[10]==4
        elif path.stem=='memory_copy': assert ref.memory[1024:1040]==ref.memory[1088:1104]
        elif path.stem=='arithmetic': assert ref.regs[10]==127
    required=set(R_OPS)|set(I_OPS)|set(BRANCHES)|set(LOADS)|set(STORES)|{'jal','jalr','lui','auipc','fence'}
    assert required<=set(coverage),(required-set(coverage))
    for op in BRANCHES:
        assert coverage[op+'_taken'] and coverage[op+'_not_taken'],op
    # Known encoding anchors also exercise assembler independently of its round trip.
    for text,word in [('addi x1, x0, -1',0xfff00093),('sw x1, -4(x2)',0xfe112e23),('jal x0, -4',0xffdff06f),('beq x0, x0, -4',0xfe000ee3)]:
        assert int.from_bytes(assemble(text)[0],'little')==word
    for text in ['slli x1, x2, 32','addi x1, x2, 2048','jal x0, 3','lui x1, 1048576']:
        try: assemble(text)
        except ValueError: pass
        else: raise AssertionError('assembler accepted '+text)
    report={'passed':True,'unit_checks':unit_count,'processor_runs':len(summaries),
            'differential_retirements':sum(s['retired'] for s in summaries),
            'random_seeds':seeds,'upstream_add_vectors':len(matches),'coverage':dict(sorted(coverage.items())),
            'runs':summaries,'verilator':subprocess.check_output(['verilator','--version'],text=True).strip(),
            'python':sys.version.split()[0]}
    (ROOT/'results/verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f"PASS: {unit_count} unit checks, {len(summaries)} processor runs, {report['differential_retirements']} differential retirements; {len(matches)} upstream ADD vectors")

if __name__=='__main__': main()
