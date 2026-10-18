// SPDX-License-Identifier: MIT
module core(
  input logic clk, reset,
  output logic mem_valid, mem_write,
  output logic [31:0] mem_addr, mem_wdata,
  output logic [3:0] mem_wstrb,
  input logic mem_ready, mem_error, input logic [31:0] mem_rdata,
  output logic [2:0] state,
  output logic [31:0] pc, insn,
  output logic [31:0] debug_regs [0:31],
  output logic [31:0] debug_a, debug_b, debug_alu,
  output logic retire, output logic [31:0] retire_pc, retire_insn, retire_next_pc,
  output logic [4:0] retire_rd, output logic [31:0] retire_data,
  output logic halted, output logic [3:0] trap_cause,
  output logic [31:0] trap_value
);
  localparam logic [2:0] FETCH=0, DECODE=1, EXECUTE=2, MEMORY=3, WRITEBACK=4, HALT=5;
  logic legal, write_rd, rf_we;
  logic [3:0] kind, alu_op;
  logic [4:0] rs1,rs2,rd;
  logic [31:0] imm, a,b,alu_b,alu_y,result,next_pc,ea,store_value;
  logic [31:0] target,effective,shifted_load;
  logic take_branch, bad_align;
  logic [2:0] f3;
  assign f3=insn[14:12];
  decoder dec(insn,legal,write_rd,kind,alu_op,rs1,rs2,rd,imm);
  assign rf_we=state==WRITEBACK && write_rd;
  regfile rf(clk,reset,rf_we,rs1,rs2,rd,result,a,b,debug_regs);
  assign alu_b=(kind==1 || kind==7 || kind==8) ? imm : b;
  alu arithmetic(a,alu_b,alu_op,alu_y);
  assign debug_a=a; assign debug_b=alu_b; assign debug_alu=alu_y;
  assign halted=state==HALT;
  assign effective=(kind==7 || kind==8) ? alu_y : a+imm;
  always_comb begin
    case(f3)
      0: take_branch=a==b;
      1: take_branch=a!=b;
      4: take_branch=$signed(a)<$signed(b);
      5: take_branch=$signed(a)>=$signed(b);
      6: take_branch=a<b;
      7: take_branch=a>=b;
      default: take_branch=0;
    endcase
    target=pc+4;
    if(kind==5 || (kind==4 && take_branch)) target=pc+imm;
    if(kind==6) target=effective & 32'hfffffffe;
    bad_align=((f3[1:0]==1) && effective[0]) ||
              ((f3[1:0]==2) && |effective[1:0]);
    mem_valid=state==FETCH || state==MEMORY;
    mem_write=state==MEMORY && kind==8;
    mem_addr=state==FETCH ? pc : {ea[31:2],2'b0};
    mem_wdata=store_value << {ea[1:0],3'b0};
    mem_wstrb=0;
    if(mem_write) begin
      case(f3)
        0: mem_wstrb=4'b0001 << ea[1:0];
        1: mem_wstrb=4'b0011 << ea[1:0];
        2: mem_wstrb=4'b1111;
        default: mem_wstrb=0;
      endcase
    end
    shifted_load=mem_rdata >> {ea[1:0],3'b0};
  end
  task automatic trap(input logic [3:0] cause, input logic [31:0] value);
    state<=HALT; trap_cause<=cause; trap_value<=value;
  endtask
  always_ff @(posedge clk) begin
    if(reset) begin
      state<=FETCH; pc<=0; insn<=0; result<=0; next_pc<=0; ea<=0; store_value<=0;
      retire<=0; retire_pc<=0; retire_insn<=0; retire_next_pc<=0; retire_rd<=0; retire_data<=0;
      trap_cause<=0; trap_value<=0;
    end else begin
      retire<=0;
      case(state)
        FETCH: if(mem_ready) begin
          if(mem_error) trap(1,pc);
          else begin insn<=mem_rdata; state<=DECODE; end
        end
        DECODE: state<=EXECUTE;
        EXECUTE: begin
          if(!legal) trap(2,insn);
          else if(kind==10) trap(insn[20] ? 4'd3 : 4'd11,0);
          else if((kind==4 || kind==5 || kind==6) && |target[1:0]) trap(0,target);
          else if((kind==7 || kind==8) && bad_align) trap(kind==7 ? 4'd4 : 4'd6,effective);
          else begin
            next_pc<=target;
            case(kind)
              0,1: result<=alu_y;
              2: result<=imm;
              3: result<=pc+imm;
              5,6: result<=pc+4;
              default: result<=0;
            endcase
            if(kind==7 || kind==8) begin ea<=effective; store_value<=b; state<=MEMORY; end
            else state<=WRITEBACK;
          end
        end
        MEMORY: if(mem_ready) begin
          if(mem_error) trap(kind==7 ? 4'd5 : 4'd7,ea);
          else begin
            if(kind==7) begin
              case(f3)
                0: result<={{24{shifted_load[7]}},shifted_load[7:0]};
                1: result<={{16{shifted_load[15]}},shifted_load[15:0]};
                2: result<=shifted_load;
                4: result<={24'b0,shifted_load[7:0]};
                5: result<={16'b0,shifted_load[15:0]};
                default: result<=0;
              endcase
            end
            state<=WRITEBACK;
          end
        end
        WRITEBACK: begin
          retire<=1; retire_pc<=pc; retire_insn<=insn; retire_next_pc<=next_pc;
          retire_rd<=write_rd ? rd : 5'd0; retire_data<=write_rd && rd!=0 ? result : 32'd0;
          pc<=next_pc; state<=FETCH;
        end
        HALT: state<=HALT;
        default: trap(2,insn);
      endcase
    end
  end
endmodule
