// SPDX-License-Identifier: MIT
module alu(input logic [31:0] a, b, input logic [3:0] op, output logic [31:0] y);
  always_comb begin
    case (op)
      0: y = a + b;
      1: y = a - b;
      2: y = a << b[4:0];
      3: y = {31'b0, $signed(a) < $signed(b)};
      4: y = {31'b0, a < b};
      5: y = a ^ b;
      6: y = a >> b[4:0];
      7: y = $unsigned($signed(a) >>> b[4:0]);
      8: y = a | b;
      9: y = a & b;
      default: y = 0;
    endcase
  end
endmodule
