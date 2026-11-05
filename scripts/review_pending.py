#!/usr/bin/env python3
"""Prepare human-review evidence; never infer a correct answer from chain-of-thought."""
import argparse,csv,json,re
from pathlib import Path
from collections import Counter

def main():
 p=argparse.ArgumentParser();p.add_argument('--answers',type=Path,required=True);p.add_argument('--audit',type=Path,required=True);p.add_argument('--out',type=Path,default=Path('results/auditoria'));a=p.parse_args()
 a.out.mkdir(parents=True,exist_ok=True)
 raw=[json.loads(line) for line in a.answers.open(encoding='utf8') if line.strip()]
 rows=list(csv.DictReader(a.audit.open(encoding='utf8',newline='')))
 bykey={(str(r['model']),str(r['benchmark']),str(r['index'])):r for r in raw}
 if len(bykey)!=len(raw):raise ValueError('Duplicate answers')
 if len(rows)!=len(raw):raise ValueError('Answer/audit count mismatch')
 output=[]
 for r in rows:
  key=(r['model'],r['benchmark'],r['index'])
  if key not in bykey:raise ValueError(f'Missing answer {key}')
  if r['audit_status'] not in ('needs_review','needs_rerun'):continue
  ans=bykey[key]['answer']; final=ans.rsplit('</think>',1)[1].strip() if '</think>' in ans else ''
  # Candidate for HUMAN inspection only; never auto-score based on a chain-of-thought.
  explicit=re.findall(r'(?im)(?:^|\n)\s*(?:\*\*)?\s*(?:respuesta(?: final)?|final answer|answer)\s*[:：]\s*([A-D])\b',final)
  last=final.strip().splitlines()[-1].strip() if final.strip() else ''
  note=''
  if r['reason']=='reasoning_unclosed':note='No closing </think>; cannot infer final answer or stopping reason from this file.'
  elif r['reason']=='numeric_final_ambiguous':note='Multiple numbers / no unique final answer; do not grade intermediate calculation.'
  else:note='Noncanonical or verbose final; manually verify explicit last answer.'
  output.append({**r,'explicit_final_candidate':explicit[-1] if explicit else '', 'last_line_of_final':last[:350], 'answer_tail':ans[-800:], 'review_note':note,'human_decision':'','human_evidence':''})
 fields=list(output[0]); out=a.out/'pending_for_review.csv'
 with out.open('w',encoding='utf8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(output)
 counts=Counter(x['reason'] for x in output)
 print('Answers:',len(raw),'Pending:',len(output));print('Reasons:',dict(counts));print('Review file:',out)
 print('IMPORTANT: explicit_final_candidate is only a candidate, never a score.')
 print('No finish_reason or token-limit metadata is available in the original answers.')
if __name__=='__main__':main()
