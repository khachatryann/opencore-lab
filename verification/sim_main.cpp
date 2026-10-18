// SPDX-License-Identifier: MIT
#include "Vcore.h"
#include "verilated.h"
#include "verilated_vcd_c.h"
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <memory>
#include <random>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

int main(int argc,char** argv) try {
  if(argc<4) throw std::runtime_error("usage: sim image.bin trace.jsonl latency [jitter seed waveform.vcd]");
  int latency=std::stoi(argv[3]), jitter=argc>4?std::stoi(argv[4]):0;
  unsigned seed=argc>5?std::stoul(argv[5]):1;
  if(latency<1 || jitter<0) throw std::runtime_error("invalid latency");
  std::mt19937 rng(seed);
  std::array<uint8_t,65536> mem{};
  std::ifstream image(argv[1],std::ios::binary);
  if(!image) throw std::runtime_error("cannot open image");
  image.read(reinterpret_cast<char*>(mem.data()),mem.size());
  if(image.gcount()==0) throw std::runtime_error("empty image");
  std::ofstream out(argv[2]);
  if(!out) throw std::runtime_error("cannot open trace");
  auto context=std::make_unique<VerilatedContext>();
  context->traceEverOn(true);
  auto top=std::make_unique<Vcore>(context.get());
  std::unique_ptr<VerilatedVcdC> vcd;
  if(argc>6) { vcd=std::make_unique<VerilatedVcdC>(); top->trace(vcd.get(),99); vcd->open(argv[6]); }
  uint64_t time=0;
  auto eval=[&](int clk) { top->clk=clk; top->eval(); if(vcd) vcd->dump(time); time++; };
  top->reset=1; top->mem_ready=0; top->mem_error=0; top->mem_rdata=0;
  eval(0); eval(1); eval(0); top->reset=0;
  uint64_t retired=0,waits=0,requests=0,stores=0,cycles=0;
  int age=0,delay=0;
  uint32_t held_addr=0,held_data=0; unsigned held_mask=0,held_write=0;
  for(uint64_t c=1;c<=200000;c++) {
    eval(0);
    unsigned state=top->state; uint32_t pc=top->pc,insn=top->insn;
    uint32_t addr=top->mem_addr,data=top->mem_wdata;
    unsigned valid=top->mem_valid,write=top->mem_write,mask=top->mem_wstrb;
    uint32_t a=top->debug_a,b=top->debug_b,alu=top->debug_alu;
    bool ready=false,error=false;
    if(valid) {
      if(age==0) { delay=latency+(jitter?int(rng()%(unsigned(jitter)+1)):0); requests++;
        held_addr=addr; held_data=data; held_mask=mask; held_write=write;
      } else if(addr!=held_addr || data!=held_data || mask!=held_mask || write!=held_write)
        throw std::runtime_error("memory request changed while waiting");
      age++; ready=age>=delay; error=addr>mem.size()-4 || (addr&3);
      if(!ready) waits++;
    } else if(age) throw std::runtime_error("memory request withdrawn before response");
    uint32_t rdata=0;
    if(valid && !error) for(int i=0;i<4;i++) rdata|=uint32_t(mem[addr+i])<<(8*i);
    top->mem_ready=ready; top->mem_error=error; top->mem_rdata=rdata;
    eval(0);
    if(valid && ready && !error && write) {
      for(int i=0;i<4;i++) if(mask&(1<<i)) mem[addr+i]=uint8_t(data>>(8*i));
      stores++;
    }
    eval(1); cycles=c;
    if(top->retire) retired++;
    out << "{\"cycle\":"<<c<<",\"state\":"<<state<<",\"next_state\":"<<unsigned(top->state)
      <<",\"pc\":"<<pc<<",\"insn\":"<<insn<<",\"next_pc\":"<<top->pc
      <<",\"a\":"<<a<<",\"b\":"<<b<<",\"alu\":"<<alu
      <<",\"valid\":"<<valid<<",\"write\":"<<write<<",\"addr\":"<<addr
      <<",\"wdata\":"<<data<<",\"mask\":"<<mask<<",\"ready\":"<<ready
      <<",\"error\":"<<error<<",\"rdata\":"<<rdata<<",\"retire\":"<<unsigned(top->retire)
      <<",\"retire_pc\":"<<top->retire_pc<<",\"retire_insn\":"<<top->retire_insn
      <<",\"retire_next_pc\":"<<top->retire_next_pc<<",\"rd\":"<<unsigned(top->retire_rd)
      <<",\"rd_data\":"<<top->retire_data<<",\"regs\":[";
    for(int i=0;i<32;i++) out<<(i?",":"")<<top->debug_regs[i];
    out<<"],\"halted\":"<<unsigned(top->halted)<<",\"cause\":"<<unsigned(top->trap_cause)
       <<",\"trap_value\":"<<top->trap_value<<"}\n";
    if(ready) age=0;
    if(top->halted) break;
  }
  if(!top->halted) throw std::runtime_error("cycle limit reached");
  top->final(); if(vcd) vcd->close();
  std::cout<<"{\"cycles\":"<<cycles<<",\"retired\":"<<retired<<",\"wait_cycles\":"<<waits
    <<",\"requests\":"<<requests<<",\"stores\":"<<stores<<",\"latency\":"<<latency
    <<",\"jitter\":"<<jitter<<",\"seed\":"<<seed<<",\"cause\":"<<unsigned(top->trap_cause)<<"}\n";
  return 0;
} catch(const std::exception& e) { std::cerr<<e.what()<<'\n'; return 1; }
