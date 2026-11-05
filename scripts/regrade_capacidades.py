#!/usr/bin/env python3
"""Auditoría conservadora de respuestas: nunca puntúa razonamiento interno como respuesta final."""
import argparse,csv,json,re,collections,pathlib
from decimal import Decimal,InvalidOperation

def number(s):
 try:return Decimal(s.replace(',','').replace('$','').strip())
 except InvalidOperation:return None

def audit(r):
 text=r['answer']; bench=r['benchmark']; gold=str(r['gold']).strip().upper()
 if '<think>' in text:
  if '</think>' not in text: return 'needs_rerun','', 'reasoning_unclosed'
  text=text.rsplit('</think>',1)[1].strip()
 if not text: return 'needs_rerun','','empty_final'
 if bench=='gsm8k':
  nums=re.findall(r'####\s*([-+]?\$?[\d,]+(?:\.\d+)?)',text)
  if not nums:
   nums=re.findall(r'(?<![\w.])[-+]?\$?[\d,]+(?:\.\d+)?',text)
   if len(nums)!=1:return 'needs_review','', 'numeric_final_ambiguous'
  got=number(nums[-1]); target=number(gold)
  if got is None or target is None:return 'needs_review','','numeric_unparseable'
  return ('correct' if got==target else 'incorrect'),str(got),'final_numeric'
 # Only accept a clean final label, not the first label in a paragraph of reasoning.
 pattern=r'^\s*(?:Respuesta(?: final)?\s*[:：]\s*|Answer\s*[:：]\s*|Final answer\s*[:：]\s*)?([A-D]|[1-5])(?:\s*[).:]|\b)(?:\s*.*)?$'
 m=re.match(pattern,text,re.I|re.S)
 if not m:return 'needs_review','','noncanonical_final'
 label=m.group(1).upper()
 # An answer like "A) long option text" is accepted, but a paragraph with other options is not.
 rest=text[m.end(1):].strip()
 if re.search(r'\n\s*(?:[A-D]|[1-5])\s*[).:]',rest,re.I) or len(rest)>180:
  return 'needs_review',label,'verbose_final'
 return ('correct' if label==gold else 'incorrect'),label,'final_label'

def main():
 p=argparse.ArgumentParser();p.add_argument('--input',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,default=pathlib.Path('results/audit'));a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 rows=[];seen=set()
 for line in a.input.open(encoding='utf8'):
  if not line.strip():continue
  r=json.loads(line);key=(r['model'],r['benchmark'],r['index']);
  if key in seen:raise ValueError(f'Duplicate {key}')
  seen.add(key);status,parsed,reason=audit(r)
  rows.append({'model':r['model'],'benchmark':r['benchmark'],'index':r['index'],'original_correct':r['correct'],'original_parsed':r['parsed'],'gold':r['gold'],'audit_status':status,'audit_parsed':parsed,'reason':reason,'question_sha256':r['question_sha256']})
 for b in set(r['benchmark'] for r in rows):
  byidx=collections.defaultdict(set)
  for r in rows:
   if r['benchmark']==b:byidx[r['index']].add(r['question_sha256'])
  if any(len(s)!=1 for s in byidx.values()):raise ValueError(f'Question mismatch in {b}')
 fields=list(rows[0]);
 with (a.out/'audit.csv').open('w',newline='',encoding='utf8') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
 grouped=collections.defaultdict(list)
 for r in rows:grouped[(r['model'],r['benchmark'])].append(r)
 with (a.out/'summary_audit.csv').open('w',newline='',encoding='utf8') as f:
  w=csv.writer(f);w.writerow(['model','benchmark','total','original_correct','verified_correct','verified_incorrect','needs_review','needs_rerun'])
  for (m,b),rr in sorted(grouped.items()):
   counts=collections.Counter(x['audit_status'] for x in rr)
   w.writerow([m,b,len(rr),sum(x['original_correct'] for x in rr),counts['correct'],counts['incorrect'],counts['needs_review'],counts['needs_rerun']])
   print(m,b,len(rr),dict(counts))
 print('Auditoría terminada. NO interpretar verified_correct / total como precisión final si hay pendientes.')
if __name__=='__main__':main()
