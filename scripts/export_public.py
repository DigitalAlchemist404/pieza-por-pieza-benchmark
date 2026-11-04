#!/usr/bin/env python3
"""Exporta tablas sin rutas locales, a partir de los resultados guardados."""
import argparse,csv,json,pathlib,collections,statistics
p=argparse.ArgumentParser();p.add_argument('--velocity',type=pathlib.Path,default=pathlib.Path('results/velocity'));p.add_argument('--answers',type=pathlib.Path,default=pathlib.Path('results/pilot/capacidades/answers.jsonl'));p.add_argument('--out',type=pathlib.Path,default=pathlib.Path('data'));a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
if a.answers.exists():
 counts=collections.defaultdict(lambda:[0,0]);last={}
 for line in a.answers.read_text().splitlines():
  try:
   x=json.loads(line);last[(x['model'],x['benchmark'],x['index'])]=x
  except (KeyError,ValueError):pass
 for (model,bench,_),x in last.items():
  counts[(model,bench)][0]+=1;counts[(model,bench)][1]+=int(x['correct'])
 with (a.out/'pilot_accuracy.csv').open('w',newline='') as f:
  w=csv.writer(f);w.writerow(['model','benchmark','answered','correct','accuracy_pct','kind'])
  for (m,b),(n,c) in sorted(counts.items()):w.writerow([m,b,n,c,round(100*c/n,2),'pilot'])
rows=[]
for file in sorted(a.velocity.glob('*.stdout.jsonl')):
 for line in file.read_text().splitlines():
  try: x=json.loads(line)
  except ValueError:continue
  # llama-bench JSONL: test name and average speed are in each row
  model=file.name.split('_prefill_')[0] if '_prefill_' in file.name else file.name.split('_decode_')[0]
  scenario='prefill_512' if '_prefill_' in file.name else 'decode_128'
  speed=x.get('avg_ts')
  if isinstance(speed,(float,int)):rows.append([model,scenario,speed,x.get('stddev_ts','')])
if rows:
 with (a.out/'velocity.csv').open('w',newline='') as f:
  w=csv.writer(f);w.writerow(['model','scenario','avg_tokens_per_second','stddev_tokens_per_second']);w.writerows(rows)
print('Tablas públicas actualizadas en',a.out)
