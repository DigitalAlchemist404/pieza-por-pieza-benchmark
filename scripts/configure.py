#!/usr/bin/env python3
"""Configuración interactiva y local de rutas GGUF y ejecutables llama.cpp."""
import argparse
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'config.local.json'
MODELS = {
    'normal_q4': 'Qwen_Qwen3.5-35B-A3B-Q4_K_M.gguf',
    'normal_iq2': 'Qwen_Qwen3.5-35B-A3B-IQ2_XXS.gguf',
    'dynamic_q4': 'Qwen3.5-35B-A3B-UD-Q4_K_XL.gguf',
    'dynamic_iq2': 'Qwen3.5-35B-A3B-UD-IQ2_XXS.gguf',
}
BINARIES = ('llama-server', 'llama-bench', 'llama-perplexity')

def expand(value):
    return str(Path(os.path.expandvars(value)).expanduser().resolve())

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--models-dir', type=Path, help='Carpeta que contiene los cuatro archivos GGUF')
    p.add_argument('--llama-bin-dir', type=Path, help='Carpeta con ejecutables de llama.cpp')
    p.add_argument('--non-interactive', action='store_true', help='No preguntar; requiere al menos una carpeta')
    args = p.parse_args()
    if args.non_interactive and not (args.models_dir or args.llama_bin_dir):
        p.error('Indicá --models-dir o --llama-bin-dir')
    data = json.loads(CONFIG.read_text(encoding='utf-8')) if CONFIG.exists() else {'models': {}, 'binaries': {}}
    data.setdefault('models', {})
    data.setdefault('binaries', {})
    model_dir = args.models_dir
    bin_dir = args.llama_bin_dir
    if not args.non_interactive:
        if model_dir is None:
            answer = input('Carpeta con tus GGUF (Enter para omitir): ').strip().strip('"')
            if answer: model_dir = Path(answer)
        if bin_dir is None:
            answer = input('Carpeta con ejecutables llama.cpp (Enter para omitir): ').strip().strip('"')
            if answer: bin_dir = Path(answer)
    if model_dir is not None:
        base = Path(expand(str(model_dir)))
        if not base.is_dir(): p.error(f'No existe la carpeta de modelos: {base}')
        for key, filename in MODELS.items():
            matches = list(base.rglob(filename))
            if len(matches) == 1:
                data['models'][key] = str(matches[0].resolve())
                print(f'OK {key}: {matches[0]}')
            elif not matches:
                print(f'No encontrado {key}: {filename}')
            else:
                print(f'Varias coincidencias para {key}; elegí una carpeta más específica')
    if bin_dir is not None:
        base = Path(expand(str(bin_dir)))
        if not base.is_dir(): p.error(f'No existe la carpeta de ejecutables: {base}')
        for binary in BINARIES:
            matches = [base / binary, base / (binary + '.exe')]
            found = next((x for x in matches if x.is_file()), None)
            if found:
                data['binaries'][binary] = str(found.resolve())
                print(f'OK {binary}: {found}')
            else:
                print(f'No encontrado: {binary}')
    if not data['models'] and not data['binaries']:
        print('No se encontraron rutas; no se creó configuración. Intentá con carpetas correctas.')
        return
    CONFIG.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'Configuración local guardada en {CONFIG.name} (ignorada por Git).')
    print('Podés editar config.local.json para configurar rutas individuales.')

if __name__ == '__main__': main()
