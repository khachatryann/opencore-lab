# AI assistance and project provenance

This repository was created on 2026-10-18 in response to the user's project brief by OpenAI Codex. Codex authored the RTL, in-house assembler and reference interpreter, verification harness, demonstration programs, static interface, charts and documentation; installed Verilator; ran the commands; inspected the browser interface; and fixed issues found during that work. The work used one agent, not a team of human contributors.

The user supplied the requirements. This repository makes no assertion that the user independently designed, programmed, verified, deployed, or previously maintained the processor. No users, awards, collaborators, FPGA deployment, university endorsement, certification, or development history are claimed.

Externally authored ADD test vectors come from the pinned upstream source under `third_party/`; their scope and license are documented. Architectural rules were checked against the official RV32I specification. No production processor RTL was copied into the implementation. The reference interpreter and implementation share the possibility of AI/specification interpretation mistakes, so passing their differential checks is useful evidence but not an independent compliance guarantee.

All numerical results are generated from actual Verilator runs. The demo is explicitly labeled as playback of those recordings. Browser QA and clean-source rebuild results are recorded in `results/`. CI configurations are supplied; this statement does not imply they ran on GitHub before publication.

Review and understand the design before presenting it as personal engineering work. Future human review, authorship and modifications should be described accurately when they occur.
