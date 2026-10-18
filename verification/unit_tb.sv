// SPDX-License-Identifier: MIT
module unit_tb;
  logic clk=0,reset=1,we=0;
  logic [31:0] a,b,y,insn,imm,wd,ra,rb;
  logic [3:0] op,kind,alu_op;
  logic [4:0] rs1,rs2,rd,r1=0,r2=0,wr=0;
  logic legal,write_rd;
  logic [31:0] regs [0:31];
  int checks=0;
  logic [31:0] expected, random_word;
  alu u_alu(a,b,op,y);
  decoder u_dec(insn,legal,write_rd,kind,alu_op,rs1,rs2,rd,imm);
  regfile u_rf(clk,reset,we,r1,r2,wr,wd,ra,rb,regs);
  task automatic check(input bit pass,input string message);
    checks++; if(!pass) $fatal(1,"%s (check %0d)",message,checks);
  endtask
  task automatic tick; #1; clk=1; #1; clk=0; #1; endtask
  initial begin
    a=0;b=0;op=0;insn=0;wd=0; tick(); reset=0;
    for(int j=0;j<32;j++) begin r1=5'(j); #1; check(ra==0,"reset register"); end
    for(int j=0;j<32;j++) begin
      we=1;wr=5'(j);wd=32'h98760000+32'(j);tick();r1=5'(j);r2=5'(j);#1;
      check(ra==(j==0?0:wd) && rb==ra,"write/read including x0");
    end
    we=0;wr=5'd3;wd=32'hdeadbeef;tick();r1=3;#1;check(ra==32'h98760003,"write enable");
    reset=1;tick();reset=0; for(int j=0;j<32;j++) check(regs[j]==0,"reset after writes");
    for(int n=0;n<1000;n++) begin
      a=$random; b=$random;
      if(n<5) begin
        case(n)
          0: begin a=32'h80000000;b=32'hffffffff;end
          1: begin a=32'h7fffffff;b=1;end
          2: begin a=32'hffffffff;b=32;end
          3: begin a=1;b=31;end
          4: begin a=0;b=0;end
        endcase
      end
      for(int o=0;o<10;o++) begin
        op=4'(o);
        case(o)
          0: expected=a+b; 1:expected=a-b; 2:expected=a<<b[4:0];
          3:expected=32'($signed(a)<$signed(b));4:expected=32'(a<b);
          5:expected=a^b;6:expected=a>>b[4:0];7:expected=$unsigned($signed(a)>>>b[4:0]);
          8:expected=a|b;9:expected=a&b;
          default:expected=0;
        endcase
        #1;check(y==expected,"ALU random/edge");
      end
    end
    for(int f=0;f<128;f++) for(int g=0;g<8;g++) begin
      insn=(32'(f)<<25)|(32'(g)<<12)|32'h33;#1;
      check(legal==(f==0 || (f==32 && (g==0 || g==5))),"R reserved funct7");
      insn=(32'(f)<<25)|(32'(g)<<12)|32'h13;#1;
      check(legal==((g==1)?f==0:(g==5)?(f==0 || f==32):1),"I shift reserved bits");
    end
    insn=32'hfff10093;#1;check(imm==32'hffffffff && rd==1 && rs1==2 && write_rd,"I negative");
    insn=32'hfe112e23;#1;check(imm==32'hfffffffc && kind==8,"S negative");
    insn=32'hfe000ee3;#1;check(imm==32'hfffffffc && kind==4,"B negative");
    insn=32'hffdff06f;#1;check(imm==32'hfffffffc && kind==5,"J negative");
    insn=32'h800000b7;#1;check(imm==32'h80000000 && kind==2,"U immediate");
    insn=32'h02000033;#1;check(!legal,"M extension rejected");
    insn=32'h0000100f;#1;check(!legal,"FENCE.I rejected");
    insn=32'h00100073;#1;check(legal && kind==10,"EBREAK decode");
    insn=32'h00000073;#1;check(legal && kind==10,"ECALL decode");
    insn=32'hc0001073;#1;check(!legal,"CSR rejected");
    $display("UNIT_CHECKS=%0d",checks); $finish;
  end
endmodule
