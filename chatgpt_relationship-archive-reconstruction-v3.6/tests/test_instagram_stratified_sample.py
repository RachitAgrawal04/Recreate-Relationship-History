#!/usr/bin/env python3
"""Targeted Instagram real-export regression test.

Parses a deterministic, feature-stratified subset of message records while scanning
all records only to locate edge-case indices. Source messages are never modified;
non-selected slots in temporary sparse JSON are null placeholders so original record
indices remain stable. Output is aggregate-only and contains no message text or names.
"""
from __future__ import annotations
import argparse, collections, json, random, re, shutil, subprocess, sys, tempfile
from pathlib import Path

HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE/'tools'))
import chat_tools, media_tools
from audit_exports import exact_instagram_verification, find_ig_root

ATTACHMENT_KEYS=('photos','videos','audio_files','sticker')

def _is_attachment(m): return any(bool(m.get(k)) for k in ATTACHMENT_KEYS)
def _even(items,n):
    if len(items)<=n: return list(items)
    if n<=1: return [items[len(items)//2]]
    return [items[round(i*(len(items)-1)/(n-1))] for i in range(n)]

def build_sample(paths, seed=3407):
    docs=[]; selected={}; feature_counts=collections.Counter(); per_file={}
    for p in paths:
        obj=json.loads(p.read_text(encoding='utf-8'))
        if not isinstance(obj,dict) or not isinstance(obj.get('messages'),list):
            raise ValueError(f'Unsupported schema in {p.name}')
        msgs=obj['messages']; feature_counts['non_dict_source_records'] += sum(not isinstance(m,dict) for m in msgs); ids=set(range(min(8,len(msgs)))) | set(range(max(0,len(msgs)-8),len(msgs)))
        # Every attachment-bearing message is included so actual media link variants are tested.
        feature_indices={
            'attachment': [i for i,m in enumerate(msgs) if isinstance(m,dict) and _is_attachment(m)],
            'call_duration': [i for i,m in enumerate(msgs) if isinstance(m,dict) and m.get('call_duration') is not None],
            'reaction': [i for i,m in enumerate(msgs) if isinstance(m,dict) and m.get('reactions')],
            'share': [i for i,m in enumerate(msgs) if isinstance(m,dict) and m.get('share')],
            'empty_or_null_content': [i for i,m in enumerate(msgs) if isinstance(m,dict) and m.get('content') in (None,'')],
            'synthetic_notice': [i for i,m in enumerate(msgs) if isinstance(m,dict) and isinstance(m.get('content'),str) and chat_tools._ig_notice(m.get('content'))],
            'mojibake_suspect': [i for i,m in enumerate(msgs) if isinstance(m,dict) and isinstance(m.get('content'),str) and chat_tools._mojibake_score(m['content'])>0],
            'non_latin1_unicode': [i for i,m in enumerate(msgs) if isinstance(m,dict) and isinstance(m.get('content'),str) and any(ord(c)>255 for c in m['content'])],
            'multi_attachment': [i for i,m in enumerate(msgs) if isinstance(m,dict) and sum(len(m.get(k) or []) if isinstance(m.get(k),list) else int(bool(m.get(k))) for k in ATTACHMENT_KEYS)>1],
            'share_and_reaction': [i for i,m in enumerate(msgs) if isinstance(m,dict) and m.get('share') and m.get('reactions')],
        }
        for key,idxs in feature_indices.items():
            feature_counts[f'{key}_records_in_source'] += len(idxs)
            if key in ('attachment','call_duration','multi_attachment','share_and_reaction'):
                ids.update(idxs)
            elif key=='reaction': ids.update(_even(idxs,64))
            elif key=='share': ids.update(_even(idxs,64))
            elif key=='empty_or_null_content': ids.update(_even(idxs,40))
            elif key=='synthetic_notice': ids.update(_even(idxs,48))
            elif key=='mojibake_suspect': ids.update(_even(idxs,64))
            elif key=='non_latin1_unicode': ids.update(_even(idxs,32))
        # Uniform spread ensures ordinary text, system notices and timeline boundaries are represented.
        ids.update(_even(list(range(len(msgs))),120))
        rng=random.Random(seed + len(docs)*1009)
        ids.update(rng.sample(range(len(msgs)),min(100,len(msgs))))
        # Exact neighboring records around chunk boundaries are sampled in each file.
        for i in range(max(0,len(msgs)-5),len(msgs)): ids.add(i)
        ids={i for i in ids if 0<=i<len(msgs)}
        selected[p.name]=ids
        per_file[p.name]={'source_records':len(msgs),'selected_records':len(ids),'feature_counts':{k:len(v) for k,v in feature_indices.items()}}
        sparse=list(msgs)
        for i in range(len(sparse)):
            if i not in ids: sparse[i]=None
        sample_obj=dict(obj); sample_obj['messages']=sparse
        docs.append((p,sample_obj))
    return docs,selected,feature_counts,per_file

def run(root,timezone_name):
    root=Path(root).resolve(); activity_dirs=list(root.rglob('your_instagram_activity'))
    if len(activity_dirs)!=1: raise ValueError(f'Expected one your_instagram_activity folder, found {len(activity_dirs)}')
    source_root=activity_dirs[0].parent
    json_paths=sorted([p for p in source_root.rglob('message_*.json') if re.fullmatch(r'message_\d+\.json',p.name)])
    docs,selected,feature_counts,per_file=build_sample(json_paths)
    with tempfile.TemporaryDirectory(prefix='ig-stratified-sample-') as td:
        sample_root=Path(td)
        for src,obj in docs:
            rel=src.relative_to(source_root); out=sample_root/rel; out.parent.mkdir(parents=True,exist_ok=True)
            out.write_text(json.dumps(obj,ensure_ascii=False),encoding='utf-8')
        events,audit=chat_tools.load_instagram(sample_root,timezone_name)
        # Use the original source root for exact raw-record verification.
        verification=exact_instagram_verification(source_root,events)
        assets=media_tools.inventory_assets(source_root,hash_files=True)
        events,links=media_tools.link_instagram_attachments(events,assets)
        kinds=collections.Counter(e['kind'] for e in events)
        statuses=collections.Counter(e.get('attachment_status') for e in events if e.get('attachment_status'))
        source_key_counts=collections.Counter(a['source_key'] for e in events for a in e.get('attachments',[]))
        role_container_mismatches=[]
        resolved_count=0
        assets_by_id={a['asset_id']:a for a in assets}
        for e in events:
            for a in e.get('resolved_attachments',[]):
                resolved_count+=1
                if a.get('role_container_mismatch'):
                    role_container_mismatches.append({'asset_id':a.get('asset_id'),'source_key':a.get('source_key'),'render_role':a.get('render_role'),'container_mime_type':a.get('container_mime_type')})
        # Optional technical stream probe: inspect codec metadata only, never play or transcribe media.
        ffprobe_path=shutil.which('ffprobe'); probe_summaries=[]
        if ffprobe_path:
            seen_probe=set()
            for mismatch in role_container_mismatches:
                asset=assets_by_id.get(mismatch['asset_id'])
                if not asset or asset['asset_id'] in seen_probe: continue
                seen_probe.add(asset['asset_id'])
                target=source_root/asset['relative_path']
                proc=subprocess.run([ffprobe_path,'-v','error','-show_entries','stream=codec_type,codec_name,sample_rate,channels,width,height:format=duration','-of','json',str(target)],capture_output=True,text=True,timeout=15)
                if proc.returncode==0:
                    meta=json.loads(proc.stdout); streams=meta.get('streams',[])
                    probe_summaries.append({'render_role':mismatch['render_role'],'container_mime_type':mismatch['container_mime_type'],
                      'stream_types':dict(collections.Counter(x.get('codec_type','unknown') for x in streams)),
                      'codecs':sorted({x.get('codec_name','unknown') for x in streams}),
                      'duration_seconds':round(float(meta.get('format',{}).get('duration')),3) if meta.get('format',{}).get('duration') else None})
                else:
                    probe_summaries.append({'render_role':mismatch['render_role'],'container_mime_type':mismatch['container_mime_type'],'probe_status':'failed'})
        ids=[e['event_id'] for e in events]
        times=[e['timestamp_sort_key'] for e in events if e.get('timestamp_sort_key')]
        chronological=all(a<=b for a,b in zip(times,times[1:]))
        # Verify text transforms only affect display values and raw values remain unchanged.
        transform_checks=0; transform_failures=0; repaired_chars=0
        for e in events:
            raw=e.get('text_raw'); display=e.get('text_display')
            if isinstance(raw,str):
                candidate=chat_tools.repair_mojibake(raw)
                expected=candidate if candidate is not None else raw
                if display!=expected: transform_failures+=1
                if display!=raw:
                    transform_checks+=1; repaired_chars+=max(0,len(display))
        results={
          'sample_strategy':'all attachment-bearing messages and call records; expanded stratified reactions/shares/empty content/notices/Unicode/mojibake; 120-point uniform and 100-record seeded random coverage per chunk; file boundaries',
          'sample_size':len(events),'source_message_count':sum(v['source_records'] for v in per_file.values()),
          'per_file':per_file,'feature_records_in_source':dict(feature_counts),
          'event_kind_counts':dict(kinds),'attachment_source_key_counts':dict(source_key_counts),
          'attachment_reference_occurrences_in_sample':audit['attachment_reference_count'],
          'messages_with_attachments_in_sample':audit['messages_with_attachments'],
          'attachment_link_summary':links,'attachment_status_counts':dict(statuses),
          'asset_count_in_export':len(assets),'asset_categories':dict(collections.Counter(a['category'] for a in assets)),
          'all_asset_hashes_present':all(bool(a['sha256']) for a in assets),
          'sampled_asset_link_occurrences':resolved_count,
          'role_container_mismatch_count':len(role_container_mismatches),
          'optional_ffprobe_available':bool(ffprobe_path),'container_stream_probe':probe_summaries,
          'role_container_mismatch_categories':{f"{role}|{mime}":count for (role,mime),count in collections.Counter((x['render_role'],x['container_mime_type']) for x in role_container_mismatches).items()},
          'mojibake':{'candidate_strings_in_sample':audit['mojibake_candidate_strings'],'strings_repaired':audit['strings_repaired'],'suspicious_unrepaired':audit['strings_suspicious_not_repaired'],'display_transform_checks':transform_checks,'display_transform_failures':transform_failures},
          'raw_record_verification':verification,
          'event_ids_unique':len(ids)==len(set(ids)),'chronological_sort_pass':chronological,
          'timestamps_missing_in_sample':audit['timestamps_missing'],
          'sparse_placeholder_slots_skipped_by_design':audit['malformed_records'],
          'non_dict_records_in_original_source':feature_counts['non_dict_source_records'],
          'synthetic_notices_in_sample':audit['synthetic_notice_count'],
          'null_or_empty_content_in_sample':audit['messages_with_null_or_empty_content'],
          'chunk_chronology':[{k:v for k,v in x.items() if k not in ('file',)} for x in audit['chunk_chronology']],
          'timezone_used_for_test_only':timezone_name,'timezone_confirmation_still_required':True,
        }
        results['pass']=verification['pass'] and results['event_ids_unique'] and chronological and transform_failures==0 and results['all_asset_hashes_present']
        return results

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('instagram_root',help='Instagram ZIP export or extracted export root containing your_instagram_activity')
    ap.add_argument('--timezone',default='Asia/Kolkata',help='Test conversion zone; not a user confirmation')
    ap.add_argument('--output')
    args=ap.parse_args()
    source=Path(args.instagram_root)
    if source.is_file() and source.suffix.lower()=='.zip':
        with tempfile.TemporaryDirectory(prefix='ig-export-safe-extract-') as td:
            media_tools.safe_extract_zip(source,td)
            extracted_root=find_ig_root(td)
            result=run(extracted_root,args.timezone)
    else:
        result=run(source,args.timezone)
    text=json.dumps(result,ensure_ascii=False,indent=2)
    if args.output: Path(args.output).write_text(text+'\n',encoding='utf-8')
    print(text)
    return 0 if result['pass'] else 2

if __name__=='__main__': raise SystemExit(main())
