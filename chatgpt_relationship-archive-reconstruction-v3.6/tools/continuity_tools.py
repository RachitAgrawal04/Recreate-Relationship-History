#!/usr/bin/env python3
"""Portable project manifest, atomic checkpoint and approval-scoped handoff utilities."""
from __future__ import annotations
import argparse, fnmatch, hashlib, json, os, shutil, zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

SECRET_PATTERNS=('*.env','*secret*','*credential*','*password*','*token*','*cookie*','*private_key*','*recovery_code*')
SKIP_DIRS={'.git','__pycache__','.venv','venv','node_modules'}

def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()

def _is_secret(rel):
    name=PurePosixPath(rel).name.lower()
    return any(fnmatch.fnmatch(name,p) for p in SECRET_PATTERNS)

def atomic_write(path,content):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_name(p.name+'.tmp')
    with open(tmp,'w',encoding='utf-8') as f:
        f.write(content); f.flush(); os.fsync(f.fileno())
    os.replace(tmp,p)

def build_manifest(root, include_media=True):
    root=Path(root).resolve(); files=[]
    for current,dirs,names in os.walk(root,followlinks=False):
        cur=Path(current); dirs[:]=[d for d in dirs if d not in SKIP_DIRS and not (cur/d).is_symlink()]
        for name in sorted(names):
            p=cur/name
            if p.is_symlink() or not p.is_file() or name.endswith('.tmp') or name=='PROJECT-MANIFEST.json': continue
            rel=p.relative_to(root).as_posix()
            if _is_secret(rel): continue
            if not include_media and rel.startswith('data/media/'): continue
            files.append({'path':rel,'size_bytes':p.stat().st_size,'sha256':sha256(p)})
    return {'manifest_version':'1.0','created_at_utc':datetime.now(timezone.utc).isoformat(),
            'root_label':root.name,'file_count':len(files),'files':files}

def write_manifest(root,include_media=True):
    root=Path(root).resolve(); m=build_manifest(root,include_media)
    atomic_write(root/'PROJECT-MANIFEST.json',json.dumps(m,ensure_ascii=False,indent=2)+'\n')
    return m

def verify_manifest(root,manifest_path=None):
    root=Path(root).resolve(); path=Path(manifest_path) if manifest_path else root/'PROJECT-MANIFEST.json'
    m=json.loads(path.read_text(encoding='utf-8')); statuses={}; expected={x['path'] for x in m.get('files',[])}
    for item in m.get('files',[]):
        p=(root/item['path']).resolve()
        if root not in p.parents: statuses[item['path']]='unsafe-path'; continue
        if not p.exists(): statuses[item['path']]='missing'; continue
        if not p.is_file(): statuses[item['path']]='not-file'; continue
        statuses[item['path']]='ok' if p.stat().st_size==item['size_bytes'] and sha256(p)==item['sha256'] else 'changed'
    extras=[]
    for current,dirs,names in os.walk(root,followlinks=False):
        cur=Path(current); dirs[:]=[d for d in dirs if d not in SKIP_DIRS and not (cur/d).is_symlink()]
        for name in names:
            p=cur/name
            if p.is_symlink() or not p.is_file() or name.endswith('.tmp') or name=='PROJECT-MANIFEST.json': continue
            rel=p.relative_to(root).as_posix()
            if rel not in expected and not _is_secret(rel): extras.append(rel)
    c={k:sum(v==k for v in statuses.values()) for k in ('ok','missing','changed','unsafe-path','not-file')}
    return {'integrity_pass':c['missing']==0 and c['changed']==0 and c['unsafe-path']==0 and c['not-file']==0,
            'expected_files':len(expected),'statuses':c,'extra_files':extras,'file_status':statuses}

def write_checkpoint(root,checkpoint_id,state):
    root=Path(root).resolve(); cpdir=root/'checkpoints'; cpdir.mkdir(parents=True,exist_ok=True)
    # Manifest includes selected original media paths/hashes; never embeds their contents.
    manifest=write_manifest(root,include_media=True)
    checkpoint={
      'checkpoint_version':'1.0','checkpoint_id':checkpoint_id,
      'created_at_utc':datetime.now(timezone.utc).isoformat(),
      'skill_version':state.get('skill_version','3.6.0'),
      'phase':state.get('phase','unknown'),
      'last_verified_operation_id':state.get('last_verified_operation_id'),
      'current_operation_id':state.get('current_operation_id'),
      'current_operation_status':state.get('current_operation_status','not_started'),
      'last_verified_source_locator':state.get('last_verified_source_locator'),
      'next_unprocessed_locator':state.get('next_unprocessed_locator'),
      'next_exact_action':state.get('next_exact_action'),
      'completed_chunks':state.get('completed_chunks',[]),
      'in_progress_chunk':state.get('in_progress_chunk'),
      'open_questions':state.get('open_questions',[]),
      'pending_user_decisions':state.get('pending_user_decisions',[]),
      'project_manifest_file':'PROJECT-MANIFEST.json',
      'project_manifest_file_count':manifest['file_count'],
      'media_manifest_path':state.get('media_manifest_path'),
      'media_manifest_sha256':state.get('media_manifest_sha256'),
      'media_assets_inventoried':state.get('media_assets_inventoried',0),
      'media_assets_linked':state.get('media_assets_linked',0),
      'media_assets_unlinked':state.get('media_assets_unlinked',0),
      'handoff_level':state.get('handoff_level','A-status-only'),
      'warnings':state.get('warnings',[]),
      'credential_policy':'Credentials, API keys, OAuth tokens, cookies and recovery codes are never stored in project state or handoffs.'
    }
    path=cpdir/f'{checkpoint_id}.json'
    atomic_write(path,json.dumps(checkpoint,ensure_ascii=False,indent=2)+'\n')
    return path

def build_handoff(root,destination,level='A',approved=False,selected_paths=None):
    root=Path(root).resolve(); destination=Path(destination); selected=set(selected_paths or [])
    if level not in ('A','B','C'): raise ValueError('level must be A, B or C')
    if level in ('B','C') and not approved:
        raise PermissionError('Level B/C handoff needs explicit user approval of receiving scope')
    if level=='B' and not selected:
        raise PermissionError('Level B requires an explicit selected_paths scope (normalized chunks and/or media assets)')
    included=[]; excluded_counts={}
    for current,dirs,names in os.walk(root,followlinks=False):
        cur=Path(current); dirs[:]=[d for d in dirs if d not in SKIP_DIRS and not (cur/d).is_symlink()]
        for name in names:
            p=cur/name
            if p.is_symlink() or not p.is_file() or name.endswith('.tmp') or name in ('HANDOFF-MANIFEST.json','PROJECT-MANIFEST.json'): continue
            rel=p.relative_to(root).as_posix()
            reason=None
            if _is_secret(rel): reason='security_secret_excluded'
            elif level=='A' and rel.startswith('data/'): reason='private_data_and_media_excluded_at_level_A'
            elif level=='B' and rel.startswith('data/') and rel not in selected: reason='data_file_not_selected_by_user'
            if reason:
                excluded_counts[reason]=excluded_counts.get(reason,0)+1
                continue
            if level=='B' and (rel.startswith('data/normalized/') or rel.startswith('data/media/')) and rel not in selected:
                excluded.append({'path':rel,'reason':'not_selected_by_user'}); continue
            included.append({'path':rel,'size_bytes':p.stat().st_size,'sha256':sha256(p)})
    manifest={'handoff_version':'1.0','level':level,'created_at_utc':datetime.now(timezone.utc).isoformat(),
              'included_files':included,'excluded_file_counts_by_reason':excluded_counts,
              'media_bytes_included':any(x['path'].startswith('data/media/') for x in included),
              'raw_sources_included':any(x['path'].startswith('data/source/') for x in included),
              'security_secrets_included':False}
    destination.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for item in included: z.write(root/item['path'],item['path'])
        z.writestr('HANDOFF-MANIFEST.json',json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    with zipfile.ZipFile(destination) as z:
        if z.testzip() is not None: raise IOError('handoff ZIP integrity check failed')
    return manifest

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('root'); p.add_argument('--verify',action='store_true')
    a=p.parse_args()
    if a.verify: print(json.dumps(verify_manifest(a.root),indent=2))
    else: print(json.dumps(write_manifest(a.root),indent=2))
