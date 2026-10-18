"""Small two-pass RV32I assembler. No compiler, packages, relaxation, or ELF needed."""
from pathlib import Path
import argparse
import re
import struct

R_OPS = {'add':(0,0),'sub':(0,32),'sll':(1,0),'slt':(2,0),'sltu':(3,0),
         'xor':(4,0),'srl':(5,0),'sra':(5,32),'or':(6,0),'and':(7,0)}
I_OPS = {'addi':0,'slti':2,'sltiu':3,'xori':4,'ori':6,'andi':7,'slli':1,'srli':5,'srai':5}
BRANCHES = {'beq':0,'bne':1,'blt':4,'bge':5,'bltu':6,'bgeu':7}
LOADS = {'lb':0,'lh':1,'lw':2,'lbu':4,'lhu':5}
STORES = {'sb':0,'sh':1,'sw':2}

def reg(s):
    if not re.fullmatch(r'x(?:[0-9]|[12][0-9]|3[01])',s):
        raise ValueError(f'expected x0..x31, got {s}')
    return int(s[1:])

def signed(n,bits):
    if not -(1<<(bits-1)) <= n < (1<<(bits-1)):
        raise ValueError(f'{n} does not fit signed {bits} bits')
    return n & ((1<<bits)-1)

def assemble(source):
    labels,rows={},[]
    pc=0
    for line_no,line in enumerate(source.splitlines(),1):
        line=line.split('#',1)[0].strip()
        if not line: continue
        if ':' in line:
            name,line=line.split(':',1)
            if name.strip() in labels: raise ValueError('duplicate label '+name)
            labels[name.strip()]=pc;line=line.strip()
            if not line: continue
        tokens=line.replace(',',' ').split()
        op=tokens[0].lower(); args=tokens[1:]
        if op=='.org':
            if len(args)!=1: raise ValueError('.org takes one operand')
            dest=int(args[0],0)
            if dest<pc: raise ValueError('backward .org')
            pc=dest; continue
        size=4*len(args) if op=='.word' else len(args) if op=='.byte' else 4
        if op not in ('.word','.byte') and pc%4: raise ValueError('unaligned instruction')
        rows.append((pc,op,args,line,line_no));pc+=size
    if pc>65536: raise ValueError('image exceeds test memory')
    image=bytearray(pc);listing={}
    def val(s): return labels[s] if s in labels else int(s,0)
    for pc,op,t,line,line_no in rows:
        try:
            arity=3 if op in R_OPS or op in I_OPS or op in BRANCHES else 2 if op in LOADS or op in STORES or op in ('jalr','jal','lui','auipc') else 0
            if op not in ('.word','.byte') and len(t)!=arity: raise ValueError(f'{op} requires {arity} operands')
            if op in ('.word','.byte'):
                width=4 if op=='.word' else 1
                for i,arg in enumerate(t):
                    n=val(arg)
                    if not -(1<<(8*width-1))<=n<(1<<(8*width)): raise ValueError('data overflow')
                    image[pc+i*width:pc+(i+1)*width]=(n&((1<<(width*8))-1)).to_bytes(width,'little')
                continue
            if op in R_OPS:
                f3,f7=R_OPS[op];d,s1,s2=map(reg,t)
                word=f7<<25|s2<<20|s1<<15|f3<<12|d<<7|0x33
            elif op in I_OPS:
                d,s1=map(reg,t[:2]);n=val(t[2])
                if op in ('slli','srli','srai'):
                    if not 0<=n<32: raise ValueError('shift must be 0..31')
                    n |= 0x400 if op=='srai' else 0
                else: n=signed(n,12)
                word=n<<20|s1<<15|I_OPS[op]<<12|d<<7|0x13
            elif op in LOADS or op in STORES or op=='jalr':
                d=reg(t[0]);m=re.fullmatch(r'([^()]+)\((x\d+)\)',t[1])
                if not m: raise ValueError('expected offset(xN)')
                n=signed(val(m[1]),12);s1=reg(m[2])
                if op in STORES:
                    word=(n>>5)<<25|d<<20|s1<<15|STORES[op]<<12|(n&31)<<7|0x23
                else: word=n<<20|s1<<15|(LOADS[op] if op in LOADS else 0)<<12|d<<7|(3 if op in LOADS else 0x67)
            elif op in BRANCHES or op=='jal':
                n=val(t[-1])-(pc if t[-1] in labels else 0)
                if n%2: raise ValueError('branch/jump offset must be even')
                if op=='jal':
                    n=signed(n,21);word=(n>>20)<<31|((n>>1)&1023)<<21|((n>>11)&1)<<20|((n>>12)&255)<<12|reg(t[0])<<7|0x6f
                else:
                    n=signed(n,13);word=(n>>12)<<31|((n>>5)&63)<<25|reg(t[1])<<20|reg(t[0])<<15|BRANCHES[op]<<12|((n>>1)&15)<<8|((n>>11)&1)<<7|0x63
            elif op in ('lui','auipc'):
                n=val(t[1])
                if not 0<=n<1<<20: raise ValueError('upper immediate must be unsigned 20-bit field')
                word=n<<12|reg(t[0])<<7|(0x37 if op=='lui' else 0x17)
            elif op in ('ecall','ebreak','fence','nop'):
                if t: raise ValueError('no operands supported for '+op)
                word={'ecall':0x73,'ebreak':0x100073,'fence':0x0ff0000f,'nop':0x13}[op]
            else: raise ValueError('unsupported mnemonic '+op)
            image[pc:pc+4]=struct.pack('<I',word)
            listing[pc]={'text':line,'word':word}
        except (ValueError,IndexError,TypeError) as exc:
            raise ValueError(f'line {line_no}: {line}: {exc}') from exc
    return bytes(image),listing

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_bytes(assemble(a.source.read_text())[0])
