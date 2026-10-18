#!/usr/bin/env python3
"""Dependency-free static build. Includes only assets needed for hosting."""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parents[1]
assert (ROOT/'demo/data/manifest.json').exists(),'run make benchmark first'
if (ROOT/'dist').exists(): shutil.rmtree(ROOT/'dist')
shutil.copytree(ROOT/'demo',ROOT/'dist')
shutil.copy(ROOT/'results/latency.svg',ROOT/'dist/latency.svg')
shutil.copy(ROOT/'results/benchmark.json',ROOT/'dist/benchmark.json')
assert (ROOT/'dist/index.html').exists()
print('Static demo built in dist/ (no npm dependencies or API keys)')
