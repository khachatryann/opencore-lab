// SPDX-License-Identifier: MIT
// kind: R,I,LUI,AUIPC,BRANCH,JAL,JALR,LOAD,STORE,FENCE,SYSTEM
module decoder(input logic [31:0] insn, output logic legal, write_rd,
  output logic [3:0] kind, alu_op,
  output logic [4:0] rs1, rs2, rd, output logic [31:0] imm);
  logic [6:0] opcode, f7;
  logic [2:0] f3;
  assign opcode=insn[6:0]; assign f3=insn[14:12]; assign f7=insn[31:25];
  assign rs1=insn[19:15]; assign rs2=insn[24:20]; assign rd=insn[11:7];
  always_comb begin
    legal=1; write_rd=0; kind=0; alu_op=0;
    imm={{20{insn[31]}},insn[31:20]};
    case (opcode)
      7'h33,7'h13: begin
        kind=opcode==7'h33 ? 0 : 1; write_rd=1;
        case(f3)
          0: alu_op=opcode==7'h33 && f7==7'h20 ? 1 : 0;
          1: alu_op=2;
          2: alu_op=3;
          3: alu_op=4;
          4: alu_op=5;
          5: alu_op=insn[30] ? 7 : 6;
          6: alu_op=8;
          7: alu_op=9;
          default: alu_op=0;
        endcase
        if(opcode==7'h33) legal=(f7==0 || (f7==7'h20 && (f3==0 || f3==5)));
        else if(f3==1) legal=f7==0;
        else if(f3==5) legal=f7==0 || f7==7'h20;
      end
      7'h37: begin kind=2; write_rd=1; imm={insn[31:12],12'b0}; end
      7'h17: begin kind=3; write_rd=1; imm={insn[31:12],12'b0}; end
      7'h63: begin
        kind=4; imm={{19{insn[31]}},insn[31],insn[7],insn[30:25],insn[11:8],1'b0};
        legal=f3==0 || f3==1 || f3>=4;
      end
      7'h6f: begin
        kind=5; write_rd=1;
        imm={{11{insn[31]}},insn[31],insn[19:12],insn[20],insn[30:21],1'b0};
      end
      7'h67: begin kind=6; write_rd=1; legal=f3==0; end
      7'h03: begin kind=7; write_rd=1; legal=f3<=2 || f3==4 || f3==5; end
      7'h23: begin
        kind=8; imm={{20{insn[31]}},insn[31:25],insn[11:7]}; legal=f3<=2;
      end
      7'h0f: begin kind=9; legal=f3==0; end
      7'h73: begin kind=10; legal=insn==32'h00000073 || insn==32'h00100073; end
      default: legal=0;
    endcase
  end
endmodule
