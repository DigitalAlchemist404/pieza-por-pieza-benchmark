#!/usr/bin/env python3
"""Prueba de capacidades con chat template, no-thinking solicitado y evaluación estricta."""
import argparse,collections,csv,hashlib,json,pathlib,random,re,subprocess,sys,time,urllib.request
from decimal import Decimal,InvalidOperation
from run import discover,binary_path
from datasets import load_dataset

BENCH=('mmlu','gsm8k','arc')
MODELS=('normal_q4','dynamic_q4','normal_iq2','dynamic_iq2')
SOURCES={'mmlu':('cais/mmlu','all'),'gsm8k':('openai/gsm8k','main'),'arc':('allenai/ai2_arc','ARC-Challenge')}

def api(url,payload=None,timeout=90):
 data=None if payload is None else json.dumps(payload).encode()
 req=urllib.request.Request(url,data=data,headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=timeout) as f:return json.load(f)

def build(bench,item):
 if bench=='mmlu':
  labels='ABCD';opts=item['choices'];gold=labels[int(item['answer'])]
  question=item['question']+'\n'+'\n'.join(f'{labels[i]}) {x}' for i,x in enumerate(opts))
 elif bench=='arc':
  opts=item['choices'];labels=[str(x).upper() for x in opts['label']];gold=str(item['answerKey']).upper()
  question=item['question']+'\n'+'\n'.join(f'{l}) {x}' for l,x in zip(labels,opts['text']))
 else:
  labels=[];gold=item['answer'].split('####')[-1].strip();question=item['question']
 if bench=='gsm8k': instruction='Resuelve el problema. Devuelve SOLO una línea en formato: #### número. Sin explicación.'
 else: instruction='Elige la respuesta correcta. Devuelve SOLO la etiqueta de la opción, sin explicación.'
 return instruction+'\n\n'+question,gold,labels

def parse(bench,content,labels):
 t=content.strip()
 if '<think' in t.lower() or '</think>' in t.lower():return None,'thinking_detected'
 if bench=='gsm8k':
  m=re.fullmatch(r'####\s*([-+]?\$?[\d,]+(?:\.\d+)?)\s*',t)
  if not m:return None,'noncanonical_number'
  try:return Decimal(m.group(1).replace('$','').replace(',','')),'ok'
  except InvalidOperation:return None,'invalid_number'
 m=re.fullmatch(r'([A-Za-z0-9]+)[.\s]*',t)
 if not m:return None,'noncanonical_choice'
 v=m.group(1).upper()
 if v not in labels:return None,'invalid_choice'
 return v,'ok'

def main():
 p=argparse.ArgumentParser();p.add_argument('--limit',type=int,default=100);p.add_argument('--seed',type=int,default=42);p.add_argument('--port',type=int,default=18081);p.add_argument('--max-tokens',type=int,default=512);p.add_argument('--out',type=pathlib.Path,required=True)
 a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 server=binary_path('llama-server',pathlib.Path.home()/'Documents/ai/llamacpp/llama.cpp/build/bin/llama-server')
 if not server.is_file():raise RuntimeError(f'No se encontró llama-server: {server}')
 models=discover()
 for m in MODELS:
  if not models.get(m,{}).get('path'):raise RuntimeError(f'Falta GGUF: {m}')
 datasets={};manifest={}
 for b in BENCH:
  repo,config=SOURCES[b];ds=load_dataset(repo,config,split='test',cache_dir=str(a.out/'hf_cache'))
  ids=random.Random(a.seed).sample(range(len(ds)),min(a.limit,len(ds)))
  datasets[b]=[dict(ds[i]) for i in ids];manifest[b]={'repo':repo,'config':config,'split':'test','seed':a.seed,'indices':ids}
 mf=a.out/'dataset_manifest.json'
 if mf.exists() and json.loads(mf.read_text())!=manifest:raise RuntimeError('Manifiesto cambió. No mezclar corridas.')
 mf.write_text(json.dumps(manifest,indent=2,ensure_ascii=False))
 config={'protocol':'chat_completions','chat_template_kwargs':{'enable_thinking':False},'temperature':0,'max_tokens':a.max_tokens,'seed':a.seed,'limit':a.limit,'models':list(MODELS),'server':str(server),'ctx_size':8192}
 cf=a.out/'run_config.json'
 if cf.exists() and json.loads(cf.read_text())!=config:raise RuntimeError('Configuración cambió. No mezclar corridas.')
 cf.write_text(json.dumps(config,indent=2))
 answers=a.out/'answers.jsonl';done={}
 if answers.exists():
  for line in answers.read_text().splitlines():
   r=json.loads(line);done[(r['model'],r['benchmark'],r['index'])]=r
 def request(model,b,i,item):
  prompt,gold,labels=build(b,item)
  signature=hashlib.sha256((prompt+'\n'+str(gold)).encode()).hexdigest()
  url=f'http://127.0.0.1:{a.port}/v1/chat/completions'
  payload={'model':model,'messages':[{'role':'user','content':prompt}],'temperature':0,'seed':a.seed,'max_tokens':a.max_tokens,'chat_template_kwargs':{'enable_thinking':False},'stream':False}
  t0=time.monotonic();reply=api(url,payload,timeout=600)
  choice=reply['choices'][0];content=choice.get('message',{}).get('content') or ''
  reasoning=choice.get('message',{}).get('reasoning_content') or ''
  finish=choice.get('finish_reason');got,status=parse(b,content,labels)
  if reasoning.strip():status='reasoning_content_present'
  if finish!='stop':status='unfinished_'+str(finish)
  if b=='gsm8k':
   try:expected=Decimal(gold.replace(',','').replace('$',''))
   except InvalidOperation:expected=None
  else:expected=gold
  correct=(got==expected) if status=='ok' else None
  return {'model':model,'benchmark':b,'index':i,'question_sha256':signature,'gold':gold,'answer':content,'reasoning_content':reasoning,'parsed':str(got) if got is not None else '', 'correct':correct,'status':status,'finish_reason':finish,'elapsed_s':round(time.monotonic()-t0,3),'usage':reply.get('usage')}
 # Pilot: check actual nonthinking behavior before expensive run. Refuse to proceed if model emits thinking.
 for model in MODELS:
  pending=[(b,i,item) for b in BENCH for i,item in enumerate(datasets[b]) if (model,b,i) not in done]
  if not pending:continue
  log=a.out/f'{model}.server.log';cmd=[str(server),'-m',models[model]['path'],'-ngl','-1','--jinja','--host','127.0.0.1','--port',str(a.port),'-c','8192']
  print('Cargando',model,flush=True)
  with log.open('w') as f:
   proc=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
   try:
    ready=False
    for _ in range(120):
     if proc.poll() is not None:raise RuntimeError(f'llama-server terminó. Revisá {log}')
     try:
      h=api(f'http://127.0.0.1:{a.port}/health',timeout=3)
      if h.get('status')=='ok':ready=True;break
     except Exception:pass
     time.sleep(2)
    if not ready:raise RuntimeError('Servidor no listo; revisá log')
    # First 3 questions serve as an automatic smoke test; no extra commands.
    for k,(b,i,item) in enumerate(pending):
     rec=request(model,b,i,item)
     if k<3 and rec['status'] in ('thinking_detected','reasoning_content_present'):
      raise RuntimeError(f'{model}: no-thinking NO verificado ({rec["status"]}). No se continúa. Revisá {log}')
     with answers.open('a',encoding='utf8') as out:out.write(json.dumps(rec,ensure_ascii=False)+'\n')
     done[(model,b,i)]=rec
     if (k+1)%20==0 or k<3:print(f'{model}: {k+1}/{len(pending)} ({rec["status"]})',flush=True)
   finally:
    proc.terminate()
    try:proc.wait(timeout=15)
    except subprocess.TimeoutExpired:proc.kill();proc.wait()
 rows=[]
 for m in MODELS:
  for b in BENCH:
   group=[r for (mm,bb,_),r in done.items() if mm==m and bb==b]
   n=len(group);ok=sum(r['correct'] is True for r in group);bad=sum(r['correct'] is False for r in group);unresolved=n-ok-bad
   rows.append({'model':m,'benchmark':b,'total':n,'correct':ok,'incorrect':bad,'unresolved':unresolved,'accuracy_pct':round(100*ok/n,2) if n else ''})
 with (a.out/'summary.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 if any(r['total']!=a.limit or r['unresolved'] for r in rows):
  print('ATENCIÓN: hay respuestas no canónicas o incompletas. Revisar summary.csv antes de publicar.',file=sys.stderr)
 print('Finalizado:',a.out/'summary.csv')
if __name__=='__main__':
 try:main()
 except Exception as e:print('ERROR:',e,file=sys.stderr);sys.exit(2)
