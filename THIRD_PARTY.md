# Sources and attribution

- **RISC-V International, RV32I version 2.1**, ratified specification library release v20260120: https://docs.riscv.org/reference/isa/v20260120/unpriv/rv32.html . Used as the architecture reference; no specification text or diagrams are redistributed. Repository diagrams are original explanatory drawings.
- **riscv-software-src/riscv-tests**, commit `d7e86f701b929b5d801f8cda1a4871ab05f452bb`: https://github.com/riscv-software-src/riscv-tests/tree/d7e86f701b929b5d801f8cda1a4871ab05f452bb . `third_party/riscv-tests-add.S` is copied unmodified from `isa/rv64ui/add.S`. The RV32 upstream test includes this shared file. Its 15 simple arithmetic vectors are adapted to 32 bits by the local harness. The upstream BSD 3-clause notice is retained in `third_party/riscv-tests-LICENSE` and applies to this borrowed material. No full suite or certification claim.
- **Verilator**, installed separately, https://verilator.org/guide/latest/overview.html . Used to compile and execute the RTL. Verilator is available under LGPL-3.0 or Artistic-2.0 terms; it is not vendored in the source deliverable. Consult upstream for the runtime/output licensing details.
- **Python, Node.js, C++ toolchain and GNU Make** are separately installed tools. The project has no third-party Python/JavaScript libraries, web fonts, stock images or icon libraries.
- **GitHub Actions** checkout, setup-python, setup-node and upload-artifact, plus Pages actions, are referenced in workflow files. They are obtained by GitHub at workflow runtime, not redistributed here. Their respective upstream repositories define their licenses and action behavior.

All other original repository content is under the root MIT license. See `docs/ai-assistance.md` for how it was produced.
