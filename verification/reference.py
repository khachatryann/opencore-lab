"""Instruction-at-a-time interpreter; no RTL decoder/control-state reuse.

Uses byte-addressed memory and Python integers. Unsupported execution-environment
operations raise a terminal Trap. This is an in-house oracle, not Spike/Sail.
"""
from collections import Counter

MASK=(1<<32)-1

def sext(v,n): return (v&((1<<(n-1))-1))-(v&(1<<(n-1)))
def u(v): return v&MASK

def s(v): return sext(v,32)

class Trap(Exception):
    def __init__(self,cause,value=0): self.cause=cause;self.value=u(value)

class Reference:
    def __init__(self,image):
        self.regs=[0]*32;self.pc=0;self.memory=bytearray(65536)
        self.memory[:len(image)]=image;self.coverage=Counter()

    def read(self,address,size,cause):
        if address<0 or address+size>len(self.memory): raise Trap(cause,address)
        return int.from_bytes(self.memory[address:address+size],'little')

    def step(self):
        pc=self.pc
        if pc%4: raise Trap(0,pc)
        w=self.read(pc,4,1)
        opcode=w&127;d=(w>>7)&31;f=(w>>12)&7
        r1=(w>>15)&31;r2=(w>>20)&31;high=w>>25
        a,b=self.regs[r1],self.regs[r2]
        im=sext(w>>20,12);value=None;next_pc=u(pc+4)
        name=''
        if opcode in (0x33,0x13):
            immediate=opcode==0x13;v=u(im) if immediate else b
            if not immediate and high not in (0,32): raise Trap(2,w)
            if not immediate and high==32 and f not in (0,5): raise Trap(2,w)
            if immediate and f==1 and high!=0: raise Trap(2,w)
            if immediate and f==5 and high not in (0,32): raise Trap(2,w)
            if f==0:
                sub=not immediate and high==32
                value=a-v if sub else a+v;name='sub' if sub else 'addi' if immediate else 'add'
            elif f==1: value=a<<(v%32);name='slli' if immediate else 'sll'
            elif f==2: value=int(s(a)<s(v));name='slti' if immediate else 'slt'
            elif f==3: value=int(a<v);name='sltiu' if immediate else 'sltu'
            elif f==4: value=a^v;name='xori' if immediate else 'xor'
            elif f==5:
                arithmetic=bool(w&(1<<30));value=(s(a) if arithmetic else a)>>(v%32)
                name=('sra' if arithmetic else 'srl')+('i' if immediate else '')
            elif f==6: value=a|v;name='ori' if immediate else 'or'
            else: value=a&v;name='andi' if immediate else 'and'
        elif opcode in (0x37,0x17):
            value=(w&0xfffff000)+(pc if opcode==0x17 else 0);name='auipc' if opcode==0x17 else 'lui'
        elif opcode==0x6f:
            offset=sext(((w>>31)<<20)|(((w>>12)&255)<<12)|(((w>>20)&1)<<11)|(((w>>21)&1023)<<1),21)
            next_pc=u(pc+offset);value=pc+4;name='jal'
        elif opcode==0x67 and f==0:
            next_pc=u(a+im)&~1;value=pc+4;name='jalr'
        elif opcode==0x63 and f in (0,1,4,5,6,7):
            offset=sext(((w>>31)<<12)|(((w>>7)&1)<<11)|(((w>>25)&63)<<5)|(((w>>8)&15)<<1),13)
            conditions={0:a==b,1:a!=b,4:s(a)<s(b),5:s(a)>=s(b),6:a<b,7:a>=b}
            taken=conditions[f]
            if taken: next_pc=u(pc+offset)
            name={0:'beq',1:'bne',4:'blt',5:'bge',6:'bltu',7:'bgeu'}[f]
            self.coverage[name+('_taken' if taken else '_not_taken')]+=1
        elif opcode in (3,0x23):
            load=opcode==3
            if load and f not in (0,1,2,4,5): raise Trap(2,w)
            if not load and f not in (0,1,2): raise Trap(2,w)
            offset=im if load else sext(((w>>25)<<5)|((w>>7)&31),12)
            address=u(a+offset);size=1<<(f&3)
            if address%size: raise Trap(4 if load else 6,address)
            if load:
                value=self.read(address,size,5)
                if f<4: value=sext(value,size*8)
                name={0:'lb',1:'lh',2:'lw',4:'lbu',5:'lhu'}[f]
            else:
                self.read(address,size,7)
                self.memory[address:address+size]=(b&((1<<(size*8))-1)).to_bytes(size,'little')
                name={0:'sb',1:'sh',2:'sw'}[f]
        elif opcode==0x0f and f==0: name='fence'
        elif w in (0x73,0x100073): raise Trap(11 if w==0x73 else 3)
        else: raise Trap(2,w)
        if next_pc%4: raise Trap(0,next_pc)
        if value is not None and d!=0: self.regs[d]=u(value)
        self.regs[0]=0;self.pc=next_pc;self.coverage[name]+=1
        return {'pc':pc,'insn':w,'next_pc':next_pc,'rd':d if value is not None else 0,
                'rd_data':u(value) if value is not None and d else 0,'name':name}
