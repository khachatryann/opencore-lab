# Verification strategy and reproduction

Run `make verify` from the repository root. It builds the actual SystemVerilog with Verilator, executes the unit and processor regression, runs 18 benchmarks, rebuilds the static site and checks artifact linkage. No Python packages are required. `make test`, `make benchmark`, and `make demo` are independently useful after their prerequisites exist.

## Layers

1. `verification/unit_tb.sv` directly exercises the ALU, decoder and register file. It covers reset, x0, write gating, every register, randomized ALU inputs plus boundaries, all 128 funct7 × 8 funct3 combinations for both register and immediate arithmetic opcodes, negative I/S/B/J immediates, U format, and reserved extensions.
2. `tools/verify.py` builds directed, random, exception, adapted upstream vector and demo cases. The directed program executes every normally retiring supported mnemonic and checks branch outcomes. The random generator uses Python `random.Random(seed)` and avoids unbounded control flow and code/data overlap. It exercises register aliasing, forward skips, immediates and aligned memory; directed demos supply backward loops. Random tests do not generate arbitrary adversarial instruction streams.
3. `verification/reference.py` is an in-house interpreter with Python integer arithmetic and a byte-addressed memory array. It uses an instruction-at-a-time flow with no hardware state machine, decoder module or shared semantic execution code. The assembler and RTL/reference decoders are separate. Encoding anchor tests pin selected known instruction words to reduce common encoder/decoder error risk. This is independently structured, **not an independent third-party reference model**; shared interpretation mistakes remain possible.
4. `verification/sim_main.cpp` clocks the Verilated core and acts as the memory responder. It records signals every cycle and rejects changed/withdrawn stalled requests. Stores are applied once per valid/ready acknowledgement. The Python runner rebuilds observed RAM from these events and compares all 32 registers, PC, instruction word, next PC, writeback data and the complete 64 KiB memory at each retirement. At halt it compares cause, value, fault PC, registers and memory. It also checks the exact successful store count against retired store instructions, catching duplicate writes even when repeated data leaves RAM unchanged.
5. The benchmark checks the closed-form cycle equation as an additional measurement sanity check. `tools/check_artifacts.py` verifies trace hashes, embedded assembly, lengths, retirement/wait counts, results linkage, copied build assets, JavaScript syntax and chart XML.

## Upstream checks, with deliberately narrow scope

The GitHub connector retrieved `riscv-software-src/riscv-tests` at pinned commit `d7e86f701b929b5d801f8cda1a4871ab05f452bb`. `third_party/riscv-tests-add.S` is the unmodified `isa/rv64ui/add.S`. Upstream `isa/rv32ui/add.S` includes that file with the XLEN environment changed. We extract exactly the 15 `TEST_RR_OP` arithmetic vectors (tests 2–16), truncate constants/expected values to 32 bits, load operands and compare RTL results to the upstream expected values. We retain their upstream BSD license.

This does **not** run the upstream macro harness, bypass tests, exception environment, or full architectural suite. It is useful externally authored arithmetic evidence with a local adapter. Spike, Sail, riscv-arch-test, formal checking and FPGA validation were not run. No certification claim is made. A stronger next step is an RVFI wrapper and riscv-formal or differential execution against Spike with an appropriate terminal-trap adapter.

## Reproducibility and artifacts

The random seeds and the simulator version appear in `results/verification.json`. The directed memory delays are 1, 2 and 4 cycles; randomized runs use base delay 2 plus a uniform integer 0–5 for each request. Python generation and C++ memory scheduling each have an explicit seed. Verilator unit `$random` uses its deterministic default seed; no cross-simulator random-stream equivalence is promised.

`build/runs/NAME.bin` is the exact executable image. `NAME.jsonl` contains cycle records. `directed-l2.vcd` and `bench-fibonacci-l2.vcd` contain waveforms, openable with a VCD viewer such as GTKWave. A sample Fibonacci VCD is retained in `results/fibonacci-l2.vcd`; the full set is regenerated under `build/`. JSONL files for all tests remain under ignored `build/`; compact full-cycle traces for the six latency-2 demos are checked in under `demo/data/` with SHA-256 hashes in their manifest.

Direct simulator invocation:

```sh
python3 tools/assembler.py examples/fibonacci.S build/fibonacci.bin
build/sim build/fibonacci.bin build/fibonacci.jsonl 2 0 1 build/fibonacci.vcd
```

Arguments are image, JSONL output, fixed minimum latency, optional jitter, seed, and VCD path. The simulator limits runs to 200,000 cycles and fails on timeout, unreadable input, or memory protocol violation. It prints machine-readable summary JSON. Core memory access errors are modeled terminal traps rather than simulator process errors. The harness is single-threaded from the design’s perspective; no asynchronous clock domain or physical bus timing is modeled.

## Remaining gaps

No exhaustive proof, external full-model differential, constrained random backward control flow, interrupt testing, mid-transaction reset test, multi-agent memory ordering test, synthesis report or timing closure. The harness’s 64 KiB RAM and demonstrated programs bound observed addresses; hardware wraparound is still implemented as 32-bit arithmetic. CI is supplied but a remote GitHub Actions execution is not claimed until the repository is published and run there.
