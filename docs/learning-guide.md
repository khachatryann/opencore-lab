# A guided tour of one instruction

Start with `make verify && make serve`, open the demo, select Fibonacci and pause. This is a recording of Verilator executing the SystemVerilog. The cycle slider explores a fixed history; changing browser playback speed changes viewing speed, not the core's clock or the measured latency.

## Follow ADD through the machine

1. **Fetch:** PC drives a word address. At the first cycle of the two-cycle memory configuration, valid is high and ready is low. Nothing can advance yet. On the next edge, the response is captured in the instruction register.
2. **Decode:** Bits 6:0 identify the broad opcode. Bits 19:15 and 24:20 select source registers. Bits 11:7 select the destination; funct3/funct7 select an operation. The instruction stays latched throughout execution.
3. **Execute:** The ALU reads the operands and computes a 32-bit result. Addition discards the carry beyond bit 31. The result latch saves it, and the pending next PC becomes PC+4.
4. **Writeback:** The result reaches the selected register, unless it is x0. PC changes. A retirement pulse makes this instruction visible to the checker as a completed architectural step.

Why can a four-state instruction take five cycles? FETCH can repeat while waiting for memory. State count and cycle count are different quantities. A load or store also uses the MEMORY state.

## Explore the six programs

| Program | Look for | Check at the end |
| --- | --- | --- |
| Arithmetic | `0x80000000 + 0x80000000` wraps to zero; signed versus unsigned comparisons differ | x10 and word 0x400 are 127 |
| Fibonacci | A store writes each current term; a backward BNE repeats the loop | Words 0x400 onward: 0,1,1,2,3,5,8,13,21,34,55,89 |
| Array sum | A signed negative input has the same bit pattern in memory and LW result | x10 and word 0x440 are 37 |
| Bubble sort | BGE skips an unnecessary swap; two stores perform each swap | -3,0,2,7,12,19 in ascending order |
| Memory copy | LBU zero-extends high-bit bytes; SB changes just one lane | Bytes 0x440–0x44f match 0x400–0x40f |
| Search | A branch can end the scan or select the found path | x10 is index 4 |

Use **Instruction** to reach the next retirement; use **Cycle** to see transitions and waiting separately. After a retirement, the instruction displayed belongs to the old PC for that sampled edge, while the architectural PC after that edge is the next PC. The explanation spells out the update. The memory panel combines four bytes into a little-endian word and displays its signed decimal interpretation alongside the bits.

## Questions worth answering

- Why does `sltiu x5, x1, -1` compare with 0xffffffff rather than 4095?
- Why must a load into x0 still access memory and report a possible fault?
- Why does a taken branch to PC+2 trap while an untaken one with the same offset completes?
- What would go wrong if the memory responder wrote on every cycle of a stalled store?
- How many additional cycles would a 4-cycle response add to a copy loop with one fetch per instruction and two data operations per iteration?

Write down a prediction, inspect a trace, then verify it with the benchmark equation in the technical report.

## Extend with a measurable hypothesis

**Add program cases first.** Try search-miss and duplicate-value sort cases. Preserve the fixed instruction set. Predict the final register/memory values and add independent algorithm-level assertions to `tools/verify.py` before running them.

**Improve the verification oracle.** Add a Spike or Sail adapter, comparing architectural state and exception events to a separate implementation. Resolve the local terminal-trap environment explicitly; do not suppress mismatches to obtain a pass. Alternatively expose RVFI signals and investigate riscv-formal, including memory assumptions.

**Add memory backpressure tests.** Vary only instruction responses versus only data responses; report both request counts. Add resets during a stalled store and define cancellation for both the core and memory responder. This addresses an acknowledged current gap.

**Reuse a single arithmetic adder.** The current implementation has a main ALU plus target-generation expressions. Introduce operand muxes and extra states where required. Verify the same programs and compare state/cycle counts. Measure synthesized area before claiming area savings.

**Add a pipeline as a separate design.** Begin by specifying forwarding, stalls, branch flushing and precise exception behavior. Keep retirement comparison as the invariant. Predict where cycle savings should occur, then measure on the same programs.

**Target an FPGA only with an explicit integration plan.** Supply a board clock/reset, synthesized RAM, I/O wrapper and timing constraints. Report the actual board/tool versions, utilization and timing results only after running them. The present project supplies none of those measurements.

## Assembly subset

The included assembler accepts lowercase RV32I mnemonics, x0–x31 register names, labels, numeric immediates, `offset(xN)` memory operands, `.org`, `.word`, `.byte`, and `#` comments. `nop` is supported. `fence` takes no operands and emits a conservative full fence. Branch/JAL labels are PC-relative; a numeric argument is a literal byte offset. LUI/AUIPC take the unsigned upper 20-bit field, as standard assembly does. Labels as immediate values are absolute. Data words accept signed or unsigned 32-bit literals.

There is no ELF, linker, ABI register aliases, relaxation, macros, expression evaluation, relocation syntax, sections, string directives, pseudo-`li`/`la`/`ret`, or automatic large-constant expansion. Images are raw little-endian bytes starting at zero. The test helper's `li` routine expands constants to LUI/ADDI outside the assembler. Code/data separation is a program convention; example code begins at zero and data at 0x400. Input bounds and alignment are rejected rather than silently relaxed.
