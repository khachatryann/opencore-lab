// SPDX-License-Identifier: MIT
// Reset aborts the responder's outstanding request; committed RAM is retained.
module reset_tb;
  logic clk=0, reset=1;
  logic valid,write,ready,error,retire,halted;
  logic [31:0] addr,wdata,rdata,pc,insn,regs[0:31],a,b,y;
  logic [31:0] retire_pc,retire_insn,retire_next_pc,retire_data,trap_value;
  logic [4:0] retire_rd;
  logic [3:0] mask,cause;
  logic [2:0] state;
  logic [31:0] ram[0:31];
  int age,stores;
  int latency=4,checks=0,scenarios=0;
  core dut(clk,reset,valid,write,addr,wdata,mask,ready,error,rdata,state,
    pc,insn,regs,a,b,y,retire,retire_pc,retire_insn,retire_next_pc,
    retire_rd,retire_data,halted,cause,trap_value);
  assign ready=valid && age==latency-1 && !reset;
  assign error=addr>=128;
  assign rdata=error ? 0 : ram[addr[6:2]];
  always @(posedge clk) begin
    if(reset) age<=0;
    else if(valid) begin
      if(ready) begin
        age<=0;
        if(write && !error) begin
          for(int k=0;k<4;k++) if(mask[k]) ram[addr[6:2]][8*k+:8]<=wdata[8*k+:8];
          stores<=stores+1;
        end
      end else age<=age+1;
    end else age<=0;
  end
  task automatic check(input bit pass,input string message);
    checks++; if(!pass) $fatal(1,"%s (scenario %0d, check %0d)",message,scenarios,checks);
  endtask
  task automatic tick; #1;clk=1;#1;clk=0;#1;endtask
  task automatic reset_core;
    reset=1;tick();tick();
    check(state==0 && pc==0 && !retire && !halted && cause==0,"reset control state");
    for(int r=0;r<32;r++) check(regs[r]==0,"reset register file");
    reset=0;#1;
  endtask
  initial begin
    for(int l=0;l<3;l++) begin
      latency=l==0?2:l==1?4:8;
      for(int scenario=0;scenario<4;scenario++) begin
        scenarios++;reset=1;tick();stores=0;
        for(int n=0;n<32;n++) ram[n]=0;
        // x1=64; x2=RAM[64]; RAM[68]=x2; EBREAK.
        ram[0]=32'h04000093;ram[1]=32'h0000a103;
        ram[2]=32'h0020a223;ram[3]=32'h00100073;ram[16]=32'h12345678;
        reset_core();
        begin : find_reset_point
          for(int timeout=0;timeout<200;timeout++) begin
            if((scenario==0 && state==0 && age==1) ||
               (scenario==1 && state==3 && !write && age==1) ||
               (scenario==2 && state==3 && write && age==1) ||
               (scenario==3 && state==4 && pc==8)) disable find_reset_point;
            tick();
          end
          $fatal(1,"did not reach reset point");
        end
        // An acknowledged store is retained; a stalled store is cancelled.
        check(stores==(scenario==3?1:0),"store count before reset");
        check(ram[17]==(scenario==3?32'h12345678:0),"pre-reset RAM effects");
        reset_core();
        check(stores==(scenario==3?1:0),"no store while reset is held");
        begin : finish_program
          int retired_count;
          retired_count=0;
          for(int timeout=0;timeout<200;timeout++) begin
            tick();
            if(retire) retired_count++;
            check(regs[0]==0,"x0 after reset");
            if(halted) begin
              check(cause==3 && pc==12,"restart ends at EBREAK");
              check(retired_count==3,"no ghost or missing retirement");
              check(regs[1]==64 && regs[2]==32'h12345678,"restart register results");
              check(ram[17]==32'h12345678,"restart store result");
              check(stores==(scenario==3?2:1),"exact committed store count");
              disable finish_program;
            end
          end
          $fatal(1,"restart timed out");
        end
      end
    end
    $display("RESET_SCENARIOS=%0d RESET_CHECKS=%0d",scenarios,checks);$finish;
  end
endmodule
