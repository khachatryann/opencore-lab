#!/usr/bin/env python3
"""Check trace, build and measured-result provenance without a browser."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'demo/data/manifest.json').read_text())
bench=json.loads((ROOT/'results/benchmark.json').read_text())
verification=json.loads((ROOT/'results/verification.json').read_text())
assert verification['passed']
assert len(bench)==18 and len(manifest['programs'])==6
assert manifest['schema']==2 and manifest['latencies']==[1,2,4]
entries=[]
for program in manifest['programs']:
    assert [v['latency'] for v in program['variants']]==manifest['latencies']
    default=next(v for v in program['variants'] if v['latency']==2)
    assert all(program[k]==default[k] for k in ('file','frames','sha256'))
    entries.extend({'id':program['id'],**v} for v in program['variants'])
assert len(entries)==18
for entry in entries:
    path=ROOT/'demo/data'/entry['file']
    assert hashlib.sha256(path.read_bytes()).hexdigest()==entry['sha256']
    t=json.loads(path.read_text());frames=t['frames'];stats=t['stats']
    assert len(frames)==entry['frames']==stats['cycles']
    assert sum(f['retire'] for f in frames)==stats['retired']
    assert sum(f['valid'] and not f['ready'] for f in frames)==stats['wait_cycles']
    assert stats==entry['stats']==next(r for r in bench if r['program']==entry['id'] and r['latency']==entry['latency'])
    assert t['latency']==entry['latency'] and t['program']==entry['id']
    assert t['assembly']==(ROOT/'examples'/f"{entry['id']}.S").read_text()
    assert (ROOT/'dist/data'/entry['file']).read_bytes()==path.read_bytes()
for filename in ['app.js','style.css','index.html']:
    assert (ROOT/'demo'/filename).read_bytes()==(ROOT/'dist'/filename).read_bytes()
assert (ROOT/'dist/benchmark.json').read_bytes()==(ROOT/'results/benchmark.json').read_bytes()
ET.fromstring((ROOT/'results/latency.svg').read_text())
subprocess.run(['node','--check',str(ROOT/'demo/app.js')],check=True)
# Ensure every literal UI selector resolves to an actual element.
html=(ROOT/'demo/index.html').read_text();js=(ROOT/'demo/app.js').read_text()
for ident in re.findall(r"\$\('#([\w-]+)'\)",js): assert f'id="{ident}"' in html,ident
print('PASS: all 18 trace hashes, cycle counts, retirement counts, benchmark linkage, assembly, static build, SVG and JavaScript')
