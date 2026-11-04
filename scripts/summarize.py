#!/usr/bin/env python3
"""Genera un CSV de aciertos por modelo y conjunto, sin dependencias."""
import argparse,csv,json,pathlib,collections
p=argparse.ArgumentParser();p.add_argument('--input',type=pathlib.Path,default=pathlib.Path('results/capacidades/answers.jsonl'));p.add_argument('--out',type=pathlib.Path,default=pathlib.Path('results/capacidades/summary.csv'));a=p.parse_args()
if not a.input.exists():p.error(f'No existe {a.input}')
last={}
for line in a.input.read_text().splitlines():
    try:
        r=json.loads(line);last[(r['model'],r['benchmark'],r['index'])]=r
    except (KeyError,ValueError):continue
counts=collections.defaultdict(lambda:[0,0])
for (model,bench,_),r in last.items():
    v=counts[(model,bench)];v[0]+=1;v[1]+=bool(r['correct'])
a.out.parent.mkdir(parents=True,exist_ok=True)
with a.out.open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['model','benchmark','answered','correct','accuracy_pct'])
    for (model,bench),(n,correct) in sorted(counts.items()):w.writerow([model,bench,n,correct,round(100*correct/n,2)])
print(a.out)
