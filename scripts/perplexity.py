#!/usr/bin/env python3
"""Ejecuta llama-perplexity con un corpus local idéntico para cada modelo."""
import argparse,json,pathlib,subprocess,sys
from run import discover, binary_path
HOME=pathlib.Path.home()
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--corpus',type=pathlib.Path,required=True,help='Archivo de texto UTF-8 local')
p.add_argument('--binary',type=pathlib.Path,default=binary_path('llama-perplexity', HOME/'Documents/ai/llamacpp/llama.cpp/build/bin/llama-perplexity'))
p.add_argument('--out',type=pathlib.Path,default=pathlib.Path('results/perplexity'))
p.add_argument('--ctx-size',type=int,default=2048)
a=p.parse_args()
if not a.corpus.is_file():p.error('No existe el corpus')
if not a.binary.is_file():p.error('No existe llama-perplexity; compilá el ejecutable antes de usar esta prueba')
a.out.mkdir(parents=True,exist_ok=True)
for name,model in discover().items():
    if 'path' not in model:raise RuntimeError(f'Falta {name}')
    cmd=[str(a.binary),'-m',model['path'],'-f',str(a.corpus),'-ngl','-1','-c',str(a.ctx_size)]
    print('Ejecutando',name,flush=True)
    with (a.out/f'{name}.txt').open('w') as log:
        r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=False)
    if r.returncode:raise RuntimeError(f'{name}: código {r.returncode}; revisar results/perplexity/{name}.txt')
print('Perplejidad terminada. Revisá los archivos TXT; no se interpreta automáticamente el formato de salida.')
