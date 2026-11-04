#!/usr/bin/env python3
"""Evaluación reproducible: MMLU, GSM8K y ARC-Challenge con llama-server local."""
import argparse, csv, hashlib, json, os, pathlib, random, re, subprocess, sys, time, urllib.request, urllib.error
from decimal import Decimal, InvalidOperation
from run import discover, binary_path

ROOT=pathlib.Path(__file__).resolve().parents[1]
DEFAULT_SERVER=pathlib.Path.home()/'Documents/ai/llamacpp/llama.cpp/build/bin/llama-server'
BENCHMARKS=('mmlu','gsm8k','arc')

def fetch_data(name, split, limit, seed, cache):
    try: from datasets import load_dataset
    except ImportError: raise RuntimeError('Falta datasets. Instalá: python3 -m pip install -r requirements-eval.txt')
    sources={'mmlu':('cais/mmlu','all'), 'gsm8k':('openai/gsm8k','main'), 'arc':('allenai/ai2_arc','ARC-Challenge')}
    repo, config=sources[name]
    ds=load_dataset(repo,config,split=split,cache_dir=str(cache))
    rng=random.Random(seed)
    selected=rng.sample(range(len(ds)),min(limit,len(ds)))
    return [dict(ds[i]) for i in selected], {'repository':repo,'configuration':config,'split':split,'seed':seed,'selected_indices':selected}

def make_prompt(kind, item):
    if kind=='mmlu':
        choices=item['choices']
        text='Respondé esta pregunta de opción múltiple. Escribí únicamente la letra correcta (A, B, C o D).\n\n'
        text+=item['question'].strip()+'\n'+'\n'.join(f'{chr(65+i)}) {c}' for i,c in enumerate(choices))+'\nRespuesta:'
        gold='ABCD'[int(item['answer'])]
    elif kind=='arc':
        opts=item['choices']; labels=opts['label']; texts=opts['text']
        text='Elegí la respuesta correcta. Escribí únicamente la etiqueta de la opción.\n\n'+item['question'].strip()+'\n'
        text+='\n'.join(f'{l}) {t}' for l,t in zip(labels,texts))+'\nRespuesta:'
        gold=str(item['answerKey']).strip()
    else:
        text='Resolvé el problema. Al final escribí la respuesta numérica con el formato #### número.\n\n'+item['question'].strip()+'\nRespuesta:'
        gold=item['answer'].split('####')[-1].strip()
    return text,gold

def normalize_num(s):
    s=s.replace(',','').replace('$','').strip()
    try:return Decimal(s)
    except InvalidOperation:return None

def grade(kind, response, gold, item):
    if kind=='gsm8k':
        hits=re.findall(r'####\s*([-+]?\$?[\d,]+(?:\.\d+)?)',response)
        if not hits: hits=re.findall(r'(?<!\w)[-+]?\$?[\d,]+(?:\.\d+)?',response)
        got=normalize_num(hits[-1]) if hits else None
        expected=normalize_num(gold)
        return got is not None and expected is not None and got==expected, str(got) if got is not None else ''
    if kind=='mmlu':
        m=re.search(r'(?<![A-Za-z])([ABCD])(?![A-Za-z])',response.upper())
        got=m.group(1) if m else ''
        return got==gold,got
    labels=[str(x).upper() for x in item['choices']['label']]
    m=re.search(r'(?<![A-Za-z0-9])('+ '|'.join(map(re.escape,sorted(labels,key=len,reverse=True)))+r')(?![A-Za-z0-9])',response.upper())
    got=m.group(1) if m else ''
    return got==gold.upper(),got

def get_json(url, data=None, timeout=60):
    raw=None if data is None else json.dumps(data).encode()
    req=urllib.request.Request(url,data=raw,headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=timeout) as r:return json.load(r)

def wait_ready(port,proc,seconds=240):
    until=time.monotonic()+seconds
    while time.monotonic()<until:
        if proc.poll() is not None: raise RuntimeError(f'llama-server terminó con código {proc.returncode}; revisá el log')
        try:
            state=get_json(f'http://127.0.0.1:{port}/health',timeout=3)
            if state.get('status')=='ok':return
        except (OSError,ValueError):pass
        time.sleep(2)
    raise RuntimeError('llama-server no respondió a tiempo; revisá el log')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--benchmarks',nargs='+',choices=BENCHMARKS,default=list(BENCHMARKS))
    p.add_argument('--limit',type=int,default=50,help='Preguntas por conjunto; usar 0 para todas')
    p.add_argument('--seed',type=int,default=42)
    p.add_argument('--server',type=pathlib.Path,default=binary_path('llama-server', DEFAULT_SERVER))
    p.add_argument('--port',type=int,default=18081)
    p.add_argument('--ctx-size',type=int,default=8192)
    p.add_argument('--max-tokens',type=int,default=384)
    p.add_argument('--out',type=pathlib.Path,default=pathlib.Path('results/capacidades'))
    p.add_argument('--models',nargs='+',choices=['normal_q4','normal_iq2','dynamic_q4','dynamic_iq2'])
    p.add_argument('--prepare-only',action='store_true',help='Descargar y fijar las preguntas sin cargar modelos')
    args=p.parse_args()
    if args.limit<0 or args.max_tokens<1 or args.ctx_size<512:p.error('Parámetros inválidos')
    if not args.prepare_only and not args.server.is_file():p.error(f'No existe llama-server: {args.server}')
    args.out.mkdir(parents=True,exist_ok=True)
    data={}; manifest={}
    for name in args.benchmarks:
        split='test'
        # Se usa un subconjunto fijo de test para las tres pruebas.
        items,meta=fetch_data(name,split,args.limit or 100000000,args.seed,args.out/'hf_cache')
        data[name]=items; manifest[name]=meta
        print(f'{name}: {len(items)} preguntas',flush=True)
    manifest_path=args.out/'dataset_manifest.json'
    if manifest_path.exists() and manifest_path.read_text().strip():
        prior=json.loads(manifest_path.read_text())
        if prior!=manifest and (args.out/'answers.jsonl').exists():
            raise RuntimeError('Selección de preguntas distinta de la corrida anterior: elegí otro --out')
    manifest_path.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
    if args.prepare_only:return 0
    models=discover(); chosen=args.models or list(models)
    for key in chosen:
        if key not in models or 'path' not in models[key]:raise RuntimeError(f'Modelo no encontrado: {key}')
    output=args.out/'answers.jsonl'
    done=set()
    if output.exists():
        for line in output.read_text().splitlines():
            try:
                r=json.loads(line)
                if r.get('correct') is not None:
                    b=r['benchmark'];i=r['index'];
                    if b in data and 0 <= i < len(data[b]):
                        prompt,gold=make_prompt(b,data[b][i]); sig=hashlib.sha256((prompt+'\n'+str(gold)).encode()).hexdigest()
                        if r.get('question_sha256')==sig: done.add((r['model'],b,i))
                        else: raise RuntimeError('Respuestas existentes con otro conjunto o sin firma: usá --out con una carpeta nueva')
            except (ValueError,KeyError):pass
    for key in chosen:
        pending=any((key,b,i) not in done for b,items in data.items() for i in range(len(items)))
        if not pending:print(f'{key}: ya completado');continue
        log=args.out/f'{key}.server.log'
        cmd=[str(args.server),'-m',models[key]['path'],'-ngl','-1','--host','127.0.0.1','--port',str(args.port),'-c',str(args.ctx_size)]
        print(f'Iniciando {key}...',flush=True)
        with log.open('w') as lf:
            proc=subprocess.Popen(cmd,stdout=lf,stderr=subprocess.STDOUT,start_new_session=True)
            try:
                wait_ready(args.port,proc)
                for bench,items in data.items():
                    for idx,item in enumerate(items):
                        if (key,bench,idx) in done:continue
                        prompt,gold=make_prompt(bench,item)
                        t0=time.monotonic()
                        reply=get_json(f'http://127.0.0.1:{args.port}/completion',{'prompt':prompt,'n_predict':args.max_tokens,'temperature':0,'seed':args.seed,'cache_prompt':False},timeout=300)
                        answer=reply.get('content','')
                        correct,parsed=grade(bench,answer,gold,item)
                        record={'model':key,'benchmark':bench,'index':idx,'correct':correct,'parsed':parsed,'gold':gold,'answer':answer,'elapsed_s':round(time.monotonic()-t0,3),'stopped_eos':reply.get('stopped_eos'),'stopped_limit':reply.get('stopped_limit'),'question_sha256':hashlib.sha256((prompt+'\n'+str(gold)).encode()).hexdigest()}
                        with output.open('a') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
                        done.add((key,bench,idx))
                        print(f'{key} {bench} {idx+1}/{len(items)}: {"OK" if correct else "--"}',flush=True)
            finally:
                proc.terminate()
                try:proc.wait(timeout=15)
                except subprocess.TimeoutExpired:proc.kill();proc.wait()
    print('Listo. Resumí con: python3 scripts/summarize.py',flush=True)
    return 0

if __name__=='__main__':
    try:sys.exit(main())
    except KeyboardInterrupt:print('\nInterrumpido. Las respuestas previas se conservaron.',file=sys.stderr);sys.exit(130)
    except Exception as e:print('ERROR:',e,file=sys.stderr);sys.exit(2)
