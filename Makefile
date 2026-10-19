PYTHON ?= python3
VERILATOR ?= verilator
RTL = hardware/alu.sv hardware/decoder.sv hardware/regfile.sv hardware/core.sv
.PHONY: all build test benchmark demo serve clean verify
all: verify
build: build/sim build/unit/Vunit_tb build/reset/Vreset_tb
build/sim: $(RTL) verification/sim_main.cpp
	mkdir -p build/core
	$(VERILATOR) --cc --exe --build -j 2 --trace --assert -Wall -Wno-UNUSEDSIGNAL --top-module core --Mdir build/core $(RTL) $(CURDIR)/verification/sim_main.cpp -o $(CURDIR)/build/sim
build/unit/Vunit_tb: hardware/alu.sv hardware/decoder.sv hardware/regfile.sv verification/unit_tb.sv
	$(VERILATOR) --binary --timing --assert -Wall -Wno-UNUSEDSIGNAL -Wno-UNUSEDPARAM --top-module unit_tb --Mdir build/unit $^
build/reset/Vreset_tb: $(RTL) verification/reset_tb.sv
	$(VERILATOR) --binary --timing --assert -Wall -Wno-UNUSEDSIGNAL --top-module reset_tb --Mdir build/reset $^
test: build
	$(PYTHON) tools/verify.py
benchmark: build
	$(PYTHON) tools/benchmark.py
	$(PYTHON) tools/write_report.py
demo:
	$(PYTHON) tools/build_demo.py
verify: test benchmark demo
	$(PYTHON) tools/check_artifacts.py
	node verification/demo_loading_test.js
serve:
	$(PYTHON) -m http.server 8000 --directory dist --bind 127.0.0.1
clean:
	rm -rf build dist
