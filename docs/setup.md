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

Other version combinations are not claimed tested. CI uses Ubuntu 24.04's distribution packages and prints actual versions. The exact local simulator/Python versions are also recorded in the regression output. No lockfile is necessary because there are no package-level dependencies; system package updates can change tool versions.

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

`make clean && make verify` rebuilds the simulator, runs every regression and benchmark, regenerates all demo traces and charts, builds the static site, and checks linkage. Generated simulation objects, images, JSONL traces and VCD files are ignored under `build/`; the benchmark summaries and six educational playback traces are tracked for immediate inspection and build-only hosting.

During delivery, the source tree was copied to a fresh directory excluding `.git`, `build`, `dist` and Python caches; `make verify` was run there using the already-installed host toolchain. See `results/reproduction.json` for actual results. This is a clean source rebuild on the same host, not a fresh OS/container test. Linux CI is provided but was not executed remotely before publication.

## GitHub

The supplied folder is an initialized Git repository. No GitHub remote was created and no content has been published. To publish, create an empty repository in the desired account, then:

```sh
git add .
git commit -m "Add verified OpenCore Lab educational processor"
git remote add origin https://github.com/YOUR-ACCOUNT/opencore-lab.git
git push -u origin main
```

Use your real account/repository URL in the remote command. These are publication instructions, not a claim that a remote exists. `verification.yml` runs on pushes and pull requests and uploads `dist/`, reports and VCDs as workflow artifacts.

For GitHub Pages, enable Pages with **GitHub Actions** as its source, then manually run the **Deploy static demo** workflow. Its permissions are limited to contents read, Pages write and identity token issuance. The workflow deploys only `dist/`; the demo has no server, secrets, paid services or API keys. It can also be copied to any ordinary static host.

## Troubleshooting

- Missing Verilator: install it, then confirm `verilator --version`.
- Failed simulator compilation: check that the C++ compiler is installed and supports C++20.
- Site says trace manifest is missing: run `make benchmark demo`.
- Port 8000 is occupied: serve `dist/` with Python on another port.
- Browser cannot reach a local URL from a remote machine: run the server where the browser can reach it; the project does not configure public tunnels.
- The optional VCD file is absent: run `make test benchmark`; waveform generation is built into those targets.
