// SPDX-License-Identifier: MIT
module regfile(input logic clk, reset, we,
  input logic [4:0] rs1, rs2, rd, input logic [31:0] wd,
  output logic [31:0] a, b, output logic [31:0] debug_regs [0:31]);
  logic [31:0] regs [0:31];
  assign a = rs1 == 0 ? 0 : regs[rs1];
  assign b = rs2 == 0 ? 0 : regs[rs2];
  for (genvar g=0; g<32; g++) begin : gen_debug
    assign debug_regs[g] = g == 0 ? 0 : regs[g];
  end
  always_ff @(posedge clk) begin
    if (reset) begin
      for (int i=0; i<32; i++) regs[i] <= 0;
    end else if (we && rd != 0) regs[rd] <= wd;
  end
endmodule
