#!/usr/bin/env python3
"""Measure RTL cycles for six programs under fixed memory response latency."""
from pathlib import Path
import csv
import hashlib
import json
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'verification'))
from runner import run_case


def bars(rows):
    names=sorted({r['program'] for r in rows})
    colors={1:'#49ddb5',2:'#65a7ff',4:'#c394ff'}
    width=1000;height=360;left=70;top=35;bottom=285
    maximum=max(r['cpi'] for r in rows)*1.2
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title"><title id="title">Measured cycles per retired instruction by memory latency</title><rect width="100%" height="100%" fill="#101923"/><g font-family="sans-serif" fill="#b4c5d6" font-size="12">']
    for v in range(0,int(maximum)+1,2):
        y=bottom-v/maximum*(bottom-top)
        parts.append(f'<path d="M{left} {y}H970" stroke="#293542"/><text x="45" y="{y+4}">{v}</text>')
    for i,name in enumerate(names):
        x=left+i*150+18
        for j,lat in enumerate([1,2,4]):
            row=next(r for r in rows if r['program']==name and r['latency']==lat)
            h=row['cpi']/maximum*(bottom-top)
            parts.append(f'<rect x="{x+j*32}" y="{bottom-h}" width="24" height="{h}" rx="3" fill="{colors[lat]}"><title>{name}, latency {lat}: {row["cycles"]} cycles / {row["retired"]} instructions = {row["cpi"]:.3f} CPI</title></rect>')
        parts.append(f'<text text-anchor="middle" x="{x+43}" y="310">{name.replace("_"," ")}</text>')
    for j,lat in enumerate([1,2,4]):
        parts.append(f'<rect x="{170+j*230}" y="335" width="12" height="12" fill="{colors[lat]}"/><text x="{190+j*230}" y="346">{lat}-cycle response</text>')
    parts.append('<text x="20" y="20">CPI · lower is better</text></g></svg>')
    return ''.join(parts)


def main():
    rows=[];data=ROOT/'demo/data';data.mkdir(exist_ok=True)
    manifest={'schema':1,'source':'Verilator RTL trace playback','memory_window':[1024,1152],'programs':[]}
    for path in sorted((ROOT/'examples').glob('*.S')):
        for lat in [1,2,4]:
            stats,frames,ref,listing,image=run_case(f'bench-{path.stem}-l{lat}',path.read_text(),lat,wave=path.stem=='fibonacci' and lat==2)
            assert stats['cause']==3
            # terminal EBREAK adds a fetch/decode/execute but does not retire.
            data_requests=sum(f['valid'] and f['ready'] and f['state']==3 for f in frames)
            assert stats['cycles']==4*stats['retired']+data_requests+3+stats['wait_cycles']
            assert stats['wait_cycles']==(lat-1)*stats['requests']
            row={'program':path.stem,**{k:stats[k] for k in ['latency','retired','cycles','cpi','wait_cycles','requests','stores']}}
            rows.append(row)
            if lat==2:
                payload={'program':path.stem,'source':'Actual Verilator RTL simulation; trace playback',
                         'latency':lat,'stats':row,'assembly':path.read_text(),
                         'listing':listing,'initial_memory':list(image[1024:1152].ljust(128,b'\0')),'frames':frames}
                target=data/(path.stem+'.json')
                target.write_text(json.dumps(payload,separators=(',',':'))+'\n')
                manifest['programs'].append({'id':path.stem,'file':target.name,'frames':len(frames),
                    'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
    (data/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (ROOT/'results/benchmark.json').write_text(json.dumps(rows,indent=2)+'\n')
    with (ROOT/'results/benchmark.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
    (ROOT/'results/latency.svg').write_text(bars(rows))
    print(f'PASS: {len(rows)} RTL benchmark runs; traces and measured chart generated')
    for r in rows: print(f"{r['program']:14} L={r['latency']} retired={r['retired']:3} cycles={r['cycles']:4} CPI={r['cpi']:.3f} wait={r['wait_cycles']}")

if __name__=='__main__': main()
