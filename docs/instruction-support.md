# Instruction support and evidence

Based on RV32I base integer ISA version 2.1, [official specification](https://docs.riscv.org/reference/isa/v20260120/unpriv/rv32.html). All 40 base mnemonics have implemented behavior, including terminal SYSTEM traps. This repository deliberately describes itself as an **educational RV32I core with a terminal trap environment**, not a certified or exhaustively verified implementation. The test suite cannot establish full architectural compliance.

| Group | Instructions | Behavior | Verification evidence |
| --- | --- | --- | --- |
| Upper immediate | LUI, AUIPC | Upper 20-bit field; PC-relative addition wraps | Directed, random initialization, arithmetic demo |
| Register arithmetic | ADD, SUB | Modulo 2³² | ALU edges/random, directed, differential random; ADD also has 15 adapted upstream expected vectors |
| Register logic | AND, OR, XOR | Bitwise | ALU and directed/random differential |
| Register shift | SLL, SRL, SRA | rs2 low 5 bits; SRA propagates sign | ALU random/edges; directed shifts at 0,31,32; random |
| Register compare | SLT, SLTU | Signed/unsigned | ALU edges/random; directed contrasting sign values |
| Immediate arithmetic | ADDI | Signed 12-bit immediate | Directed immediate endpoints, demos, random |
| Immediate compare | SLTI, SLTIU | Immediate sign-extended before signed/unsigned interpretation | Directed negative/endpoints, random |
| Immediate logic | ANDI, ORI, XORI | Sign-extended immediate | Directed negative/endpoints, random |
| Immediate shift | SLLI, SRLI, SRAI | Legal funct7 checked, 5-bit amount | Directed 0,1,31; reserved-bit rejection; random |
| Equal branches | BEQ, BNE | PC-relative signed 13-bit offset | Directed taken/untaken, forward/backward loops, random |
| Ordered branches | BLT, BGE, BLTU, BGEU | Signed or unsigned register comparison | Each taken/untaken required by coverage; sort, random |
| Direct jump | JAL | Link=PC+4, target=PC+signed offset | Forward skip, backward demo loops, random, misalignment trap |
| Indirect jump | JALR | Link=PC+4; (rs1+imm) & ~1 | Odd target clearing, rd=rs1, misalignment and fetch-fault tests |
| Signed loads | LB, LH, LW | Byte extraction, sign extension; naturally aligned only | All byte lanes / halfword lanes, negative offset, x0, random, faults |
| Unsigned loads | LBU, LHU | Zero extension; naturally aligned only | High-bit data, lane tests, copy, random |
| Stores | SB, SH, SW | Little-endian mask and shifted data; aligned only | Every legal lane, neighboring-byte preservation, exact count, delayed/jitter tests |
| Fence | FENCE | Serialized no-op; fields ignored as described in architecture | Canonical and nonzero reserved-field encoding tests |
| Environment | ECALL, EBREAK | Terminal trap; no retirement | Directed each at latency 1 and 4; every demo ends in EBREAK |

Aliases NOP (`addi x0,x0,0`) and instruction encodings writing x0 work naturally. No CSR instructions (Zicsr), FENCE.I (Zifencei), multiplication/division (M), compressed (C), atomics (A), floating point, privileged instructions, interrupts, or operating system support. Spec-defined hints encoded using legal base operations have their natural base-instruction effect; no special performance hint behavior is implemented. Reserved instruction encodings are not a supported extension mechanism.

`results/verification.json` records actual retired mnemonic counts, both outcomes for every branch mnemonic, seeds, per-run statistics, and tool versions. These are functional test counts, not HDL line/toggle coverage or formal proof. Trapping instructions are tested separately and do not appear in retired coverage.
