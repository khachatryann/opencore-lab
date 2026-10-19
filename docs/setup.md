# Setup, build, and GitHub publication

## Dependencies

The project intentionally has no Python, JavaScript or C++ package dependencies. The static site uses system fonts and local files only. Network access is needed to install development tools, not to execute the project afterward.

| Tool | Tested local version | Requirement |
| --- | --- | --- |
| Verilator | 5.052 (2026-09-05) | 5.x with `--binary`, `--timing`, `--trace`; 5.052 is the tested baseline |
| C++ compiler | Apple Clang 17.0.0, arm64 | Compiler supported by Verilator; timing unit test requires C++20 |
| Python | 3.14.7 | Python 3.10+ standard library |
| Node.js | 26.5.0 | Node 20+ used only for JavaScript syntax validation |
| GNU Make | System make | Standard make rules |
| Git | System git | Optional for local execution; needed for publication |

The first successful GitHub CI run also tested Ubuntu 24.04 with Verilator 5.020, GCC 13.3.0, Python 3.12.15 and Node 22.23.3. [Publication record](../results/publication.json). CI uses distribution packages and prints actual versions. The exact local simulator/Python versions are also recorded in the regression output. No lockfile is necessary because there are no package-level dependencies; system package updates can change tool versions.

On macOS with Homebrew and Apple's command-line developer tools installed:

```sh
brew install verilator python node
make verify
make serve
```

If a compiler is missing, install the Apple command-line tools using `xcode-select --install` and finish the system installer. This step was unnecessary in the tested environment.

On Ubuntu 24.04:

```sh
sudo apt-get update
sudo apt-get install -y verilator build-essential python3 nodejs
make verify
make serve
```

Then visit <http://127.0.0.1:8000>. Serve over HTTP: opening `index.html` via `file://` blocks trace fetches in many browsers. `make serve` serves built `dist/`. For a static-only build using the checked-in traces, run `make demo && make serve`; an RTL simulator is unnecessary for that path.

## Clean reproduction

`make clean && make verify` rebuilds the simulator, runs every regression and benchmark, regenerates all demo traces and charts, builds the static site, and checks linkage. Generated simulation objects, images, JSONL traces and VCD files are ignored under `build/`; the benchmark summaries and 18 educational playback traces are tracked for immediate inspection and build-only hosting.

During delivery, the source tree was copied to a fresh directory excluding `.git`, `build`, `dist` and Python caches; `make verify` was run there using the already-installed host toolchain. See `results/reproduction.json` for actual results. This is a clean source rebuild on the same host, not a fresh OS/container test. After publication, GitHub CI passed on Ubuntu 24.04 and reproduced the measured artifacts; its separate evidence is in `results/publication.json`.

## GitHub

The public repository is [khachatryann/opencore-lab](https://github.com/khachatryann/opencore-lab). Reviewers can open its [interactive demo](https://khachatryann.github.io/opencore-lab/) without installing a toolchain or signing in.

To work from a new machine:

```sh
git clone https://github.com/khachatryann/opencore-lab.git
cd opencore-lab
make verify
make serve
```

`verification.yml` runs on pushes and pull requests and uploads `dist/`, reports and VCDs as workflow artifacts. The first Ubuntu verification run passed; see the [publication record](../results/publication.json) for its exact URL and versions.

GitHub Pages uses **GitHub Actions** as its source. To update the hosted demo after pushing changes, manually run **Deploy static demo** in the repository's Actions tab. Its permissions are limited to contents read, Pages write and identity token issuance. The workflow deploys only `dist/`; the demo has no server, secrets, paid services or API keys. It can also be copied to any ordinary static host.

## Troubleshooting

- Missing Verilator: install it, then confirm `verilator --version`.
- Failed simulator compilation: check that the C++ compiler is installed and supports C++20.
- Site says trace manifest is missing: run `make benchmark demo`.
- Port 8000 is occupied: serve `dist/` with Python on another port.
- Browser cannot reach a local URL from a remote machine: run the server where the browser can reach it; the project does not configure public tunnels.
- The optional VCD file is absent: run `make test benchmark`; waveform generation is built into those targets.
