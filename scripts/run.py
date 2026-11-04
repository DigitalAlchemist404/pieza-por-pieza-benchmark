#!/usr/bin/env python3
"""Benchmark local de cuatro variantes Qwen3.5; no descarga modelos."""
import argparse, csv, datetime, hashlib, json, os, pathlib, re, shutil, subprocess, sys

HOME = pathlib.Path.home()
MANIFESTS = HOME / '.unsloth/studio/cache/hub-state/manifests'
BENCH = HOME / 'Documents/ai/llamacpp/llama.cpp/build/bin/llama-bench'
WANTED = {'Q4_K_M':'normal_q4','IQ2_XXS':'normal_iq2','UD-Q4_K_XL':'dynamic_q4','UD-IQ2_XXS':'dynamic_iq2'}

def discover():
    found = {}
    if not MANIFESTS.exists():
        raise RuntimeError(f'No existe la carpeta de manifiestos: {MANIFESTS}')
    for m in MANIFESTS.rglob('*.json'):
        if 'qwen3.5-35b-a3b-gguf' not in m.name.lower():
            continue
        try: data=json.loads(m.read_text())
        except (OSError, ValueError): continue
        variant=data.get('variant')
        if variant not in WANTED: continue
        hub=pathlib.Path(data['hub_cache'])
        repo='models--'+data['repo_id'].replace('/','--')
        repo_dir=hub/repo/'snapshots'
        candidates=[]
        if repo_dir.exists():
            for file in data.get('expected_files',[]):
                if file['path'].lower().endswith('.gguf') and 'mmproj' not in file['path'].lower():
                    candidates += [(p,file) for p in repo_dir.glob('*/'+file['path']) if p.is_file()]
        if not candidates:
            found[WANTED[variant]]={'variant':variant,'error':f'No se encontró GGUF en {repo_dir}'}
            continue
        # Prefer a matching file size; avoid assuming snapshot order.
        p,info=next(((p,i) for p,i in candidates if p.stat().st_size==i['size']),candidates[0])
        found[WANTED[variant]]={'variant':variant,'path':str(p),'bytes':p.stat().st_size,'expected_bytes':info['size'],'expected_sha256':info.get('sha256'), 'repo_id':data['repo_id'],'snapshot':p.parent.name}
    return found

def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(8*1024*1024),b''): h.update(block)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--verify-sha',action='store_true',help='Leer 65+ GB para comprobar integridad (lento)')
    ap.add_argument('--run',action='store_true',help='Ejecutar benchmarks; sin esta opción solo diagnostica')
    ap.add_argument('--reps',type=int,default=3)
    ap.add_argument('--bench',type=pathlib.Path,default=BENCH)
    ap.add_argument('--out',type=pathlib.Path,default=pathlib.Path('results'))
    args=ap.parse_args()
    if args.reps<1: ap.error('--reps debe ser >= 1')
    models=discover()
    args.out.mkdir(parents=True,exist_ok=True)
    print('Modelos encontrados:',len([v for v in models.values() if 'path' in v]),'/4',flush=True)
    for name in WANTED.values():
        item=models.get(name,{'error':'Manifiesto ausente'})
        print(f'  {name}: {item.get("path",item.get("error"))}',flush=True)
        if 'path' in item:
            item['size_ok']=item['bytes']==item['expected_bytes']
            print('    tamaño:', 'OK' if item['size_ok'] else 'NO COINCIDE',flush=True)
            if args.verify_sha:
                print('    Calculando SHA-256...',flush=True)
                item['actual_sha256']=sha256(item['path'])
                item['sha_ok']=item['actual_sha256']==item['expected_sha256']
                print('    SHA-256:', 'OK' if item['sha_ok'] else 'NO COINCIDE',flush=True)
    info={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'host':os.uname().nodename,'arch':os.uname().machine,'models':models,'bench':str(args.bench),'repetitions':args.reps}
    root=HOME/'Documents/ai/llamacpp/llama.cpp'
    try: info['llamacpp_git']=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True,stderr=subprocess.DEVNULL).strip()
    except Exception: info['llamacpp_git']=None
    (args.out/'inventory.json').write_text(json.dumps(info,indent=2,ensure_ascii=False)+'\n')
    if len(models)!=4 or any('path' not in m or not m.get('size_ok') or m.get('sha_ok') is False for m in models.values()):
        print('ERROR: inventario incompleto o archivo inválido. No se ejecuta el benchmark.',file=sys.stderr)
        return 2
    if not args.run:
        print('Diagnóstico terminado. Para medir, añadí --run.',flush=True)
        return 0
    if not args.bench.is_file():
        print(f'No existe llama-bench: {args.bench}',file=sys.stderr); return 2
    rows=[]
    for name in WANTED.values():
        model=models[name]
        for scenario,extra in [('prefill_512',['-p','512','-n','0']),('decode_128',['-p','0','-n','128'])]:
            cmd=[str(args.bench),'-m',model['path'],'-ngl','-1','-r',str(args.reps),'-o','jsonl',*extra]
            prefix=args.out/f'{name}_{scenario}'
            print(f'\nEJECUTANDO {name} / {scenario}',flush=True)
            with open(str(prefix)+'.stdout.jsonl','w') as stdout, open(str(prefix)+'.stderr.log','w') as stderr:
                proc=subprocess.run(cmd,stdout=stdout,stderr=stderr,check=False)
            record={'model':name,'variant':model['variant'],'scenario':scenario,'size_bytes':model['bytes'],'exit_code':proc.returncode,'stdout':str(prefix)+'.stdout.jsonl','stderr':str(prefix)+'.stderr.log','command':cmd}
            rows.append(record)
            (args.out/'runs.json').write_text(json.dumps(rows,indent=2)+'\n')
            if proc.returncode!=0:
                print(f'ERROR: código {proc.returncode}; revisar {prefix}.stderr.log',file=sys.stderr)
                print('Se detiene para evitar conclusiones parciales.',file=sys.stderr)
                return proc.returncode or 1
    with open(args.out/'runs.csv','w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['model','variant','scenario','size_bytes','exit_code','stdout','stderr','command'])
        writer.writeheader()
        for row in rows: writer.writerow({**row,'command':' '.join(row['command'])})
    print('\nCOMPLETADO. Revisá results/runs.csv y los JSONL. No son medidas de calidad.',flush=True)
    return 0

if __name__=='__main__':
    try: sys.exit(main())
    except KeyboardInterrupt: print('\nInterrumpido.',file=sys.stderr); sys.exit(130)
    except Exception as exc: print('ERROR:',exc,file=sys.stderr); sys.exit(2)
