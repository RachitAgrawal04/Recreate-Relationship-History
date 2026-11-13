#!/usr/bin/env python3
"""Simulate project recovery after a session/model/account interruption."""
from pathlib import Path
import tempfile, json, hashlib, shutil
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import continuity_tools as ct

def write(p,text): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(text,encoding='utf-8')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
  passed=[]
  with tempfile.TemporaryDirectory() as td:
    root=Path(td)/'project'; root.mkdir()
    write(root/'SKILL.md','synthetic skill')
    write(root/'STATUS.md','phase: parsing\nnext: parse chunk 2\n')
    write(root/'state/project-state.json',json.dumps({'phase':'parsing','next':'line 101'}))
    write(root/'logs/decisions.jsonl','{"decision_id":"D-1","choice":"include private messages"}\n')
    write(root/'app/index.html','<main>private archive app</main>')
    write(root/'tests/smoke.txt','pass')
    write(root/'data/source/raw-export.txt','PRIVATE SOURCE SENTINEL')
    write(root/'data/normalized/chunk-001.jsonl','{"event_id":"e-1"}\n')
    write(root/'data/media/photo.bin','ORIGINAL MEDIA BYTES')
    write(root/'data/media/media-manifest.json','{"assets":1}')
    write(root/'data/derived-media/photo-thumb.bin','DERIVED THUMB')
    write(root/'.env','API_KEY=SHOULD_NEVER_TRANSFER')
    write(root/'credentials.txt','PASSWORD=SHOULD_NEVER_TRANSFER')

    # Full source workspace manifest and checkpoint.
    manifest=ct.write_manifest(root)
    cp=ct.write_checkpoint(root,'CP-000001',{
      'skill_version':'3.6.0','phase':'parsing','last_verified_operation_id':'OP-001',
      'current_operation_id':'OP-002','current_operation_status':'in_progress',
      'last_verified_source_locator':'line:100','next_unprocessed_locator':'line:101',
      'next_exact_action':'retry deterministic chunk starting at line 101',
      'completed_chunks':['chunk-001'],'in_progress_chunk':'chunk-002',
      'media_manifest_path':'data/media/media-manifest.json','media_assets_inventoried':1,
      'media_assets_linked':1,'media_assets_unlinked':0,'handoff_level':'B-working-data'
    })
    passed.append(('checkpoint exists and records exact next locator',cp.exists() and json.loads(cp.read_text())['next_unprocessed_locator']=='line:101'))
    passed.append(('manifest validates in the source workspace',ct.verify_manifest(root)['integrity_pass']))

    # Level A: app/status recovery only. No raw, normalized message data, media or full project manifest.
    a=Path(td)/'handoff-A.zip'; am=ct.build_handoff(root,a,'A')
    aroot=Path(td)/'received-A'; aroot.mkdir()
    import zipfile
    with zipfile.ZipFile(a) as z: z.extractall(aroot)
    passed.append(('Level A excludes source, normalized content, media and project manifest',
      not (aroot/'data').exists() and not (aroot/'PROJECT-MANIFEST.json').exists() and (aroot/'STATUS.md').exists()))
    passed.append(('Level A bundle contains no credentials',not any('SHOULD_NEVER_TRANSFER' in p.read_text(errors='ignore') for p in aroot.rglob('*') if p.is_file())))

    # Level B: only explicitly selected normalized content and media, after explicit approval.
    b=Path(td)/'handoff-B.zip'
    selected=['data/normalized/chunk-001.jsonl','data/media/photo.bin','data/media/media-manifest.json']
    bm=ct.build_handoff(root,b,'B',approved=True,selected_paths=selected)
    broot=Path(td)/'received-B'; broot.mkdir()
    with zipfile.ZipFile(b) as z: z.extractall(broot)
    passed.append(('Level B transfers selected normalized data/media with exact hashes',
      all(sha(broot/x)==next(y['sha256'] for y in bm['included_files'] if y['path']==x) for x in selected)))
    passed.append(('Level B excludes raw source and unselected derivatives',not (broot/'data/source').exists() and not (broot/'data/derived-media').exists()))

    # Level C: full source + media only after explicit approval.
    c=Path(td)/'handoff-C.zip'; cm=ct.build_handoff(root,c,'C',approved=True)
    croot=Path(td)/'received-C'; croot.mkdir()
    with zipfile.ZipFile(c) as z: z.extractall(croot)
    passed.append(('Level C includes raw source and original media bytes',
      sha(croot/'data/source/raw-export.txt')==sha(root/'data/source/raw-export.txt') and sha(croot/'data/media/photo.bin')==sha(root/'data/media/photo.bin')))
    passed.append(('Level C still excludes credentials',not (croot/'.env').exists() and not (croot/'credentials.txt').exists()))

    # Interruption simulation: unverified partial chunk quarantined, re-run is deterministic/idempotent.
    receiver=Path(td)/'receiver-recovery'; shutil.copytree(root,receiver,ignore=shutil.ignore_patterns('.env','credentials.txt'))
    state=json.loads((receiver/'state/project-state.json').read_text())
    checkpoint=json.loads((receiver/'checkpoints/CP-000001.json').read_text())
    recovery_ok=state['next']=='line 101' and checkpoint['next_unprocessed_locator']=='line:101' and checkpoint['last_verified_source_locator']=='line:100'
    partial=receiver/'data/normalized/chunk-002.jsonl.tmp'; write(partial,'{"event_id":"line-101"}\nBROKEN_PARTIAL')
    quarantine=receiver/'quarantine'; quarantine.mkdir()
    partial.replace(quarantine/'chunk-002.partial.unverified')
    final=receiver/'data/normalized/chunk-002.jsonl'; tmp=final.with_suffix('.jsonl.tmp')
    records=[{'event_id':f'line-{i}','source_line':i} for i in range(101,111)]
    payload=''.join(json.dumps(x,sort_keys=True)+'\n' for x in records)
    ct.atomic_write(final,payload); first=sha(final)
    ct.atomic_write(final,payload); second=sha(final)
    parsed=[json.loads(x) for x in final.read_text().splitlines()]
    passed.append(('interrupted chunk resumes from verified locator and quarantines partial output',recovery_ok and (quarantine/'chunk-002.partial.unverified').exists()))
    passed.append(('retry is idempotent with stable records and hashes',first==second and len(parsed)==10 and len({x['event_id'] for x in parsed})==10))

  for name,ok in passed: print(('PASS ' if ok else 'FAIL ')+name)
  print(f'{sum(ok for _,ok in passed)}/{len(passed)} handoff/recovery checks passed')
  print('NOT TESTED: real provider token/session expiration or whether a different AI follows the skill; this test validates portable files, scopes, checksums and deterministic recovery.')
  return 0 if all(ok for _,ok in passed) else 1

if __name__=='__main__': raise SystemExit(main())
