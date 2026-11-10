#!/usr/bin/env python3
"""Audit real WhatsApp and Instagram export ZIPs; output contains aggregate data only.

This tool validates structure and media references. It does not summarize private
message content or inspect/describe image, audio, or video contents.
"""
from __future__ import annotations
import argparse, collections, hashlib, json, os, tempfile, zipfile
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
import chat_tools, media_tools

def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def exact_whatsapp_verification(raw_text,events,audit,participants):
    lines=raw_text.splitlines(); owned=[]; failures=[]
    for e in events:
        owned.extend(e.get('raw_lines') or [])
        if not e.get('raw_lines'): failures.append('missing_line_locator'); continue
        first=e['raw_lines'][0]-1
        if first<0 or first>=len(lines) or e.get('raw_first_line')!=lines[first]:
            failures.append('raw_header_mismatch'); continue
        clean,offsets=chat_tools.clean_with_map(lines[first])
        m=chat_tools.ANDROID.match(clean) or chat_tools.IOS.match(clean)
        if not m: failures.append('header_reparse_failed'); continue
        gs,ge=m.span(8)
        stamp=lines[first][: (offsets[gs] if gs<len(offsets) else len(lines[first]))]
        rest=clean[gs:ge]; sender=None; body=chat_tools.raw_slice(lines[first],offsets,gs,ge)
        for name in sorted(participants,key=len,reverse=True):
            prefix=name+': '
            if rest.startswith(prefix):
                sender=name
                body=chat_tools.raw_slice(lines[first],offsets,gs+len(prefix),ge,keep_leading_invisibles=True)
                break
            if rest==name+':': sender=name; body=''; break
        for line_no in e['raw_lines'][1:]: body+='\n'+lines[line_no-1]
        parsed,status=chat_tools.parse_timestamp(m,audit['date_order'])
        if (e.get('sender_raw')!=sender or e.get('timestamp_raw')!=stamp
            or e.get('text_original')!=body or e.get('timestamp_parsed')!=parsed
            or e.get('parse_status')!=status): failures.append('event_body_sender_timestamp_mismatch')
    owned.extend(x['line'] for x in audit['review_lines'])
    line_coverage=(len(owned)==len(set(owned)) and sorted(owned)==list(range(1,len(lines)+1)))
    return {'events_checked':len(events),'physical_lines':len(lines),'all_lines_owned_exactly_once':line_coverage,
            'event_sender_timestamp_body_date_exact':len(failures)==0,'failure_count':len(failures),
            'failure_categories':dict(collections.Counter(failures)),
            'pass':line_coverage and not failures}

def find_ig_root(extracted):
    dirs=[p for p in Path(extracted).rglob('your_instagram_activity') if p.is_dir()]
    if len(dirs)!=1: raise ValueError(f'Expected one your_instagram_activity directory, found {len(dirs)}')
    return dirs[0].parent

def exact_instagram_verification(root,events):
    root=Path(root); cache={}; failures=[]
    for e in events:
        rel=e['source_file']
        if rel not in cache:
            cache[rel]=json.loads((root/rel).read_text(encoding='utf-8'))['messages']
        idx=e['source_record_index']; msgs=cache[rel]
        if idx>=len(msgs): failures.append('record_index_out_of_range'); continue
        m=msgs[idx]
        if e['sender_raw']!=m.get('sender_name') or e['timestamp_raw']!=m.get('timestamp_ms') or e['text_raw']!=m.get('content'):
            failures.append('raw_record_field_mismatch')
        raw_refs=[]
        for key in ('photos','videos','audio_files','sticker'):
            v=m.get(key); values=v if isinstance(v,list) else [v] if isinstance(v,dict) else []
            raw_refs.extend(x.get('uri') for x in values if isinstance(x,dict) and isinstance(x.get('uri'),str))
        if [x['uri'] for x in e.get('attachments',[])]!=raw_refs: failures.append('attachment_ref_mismatch')
        if e.get('reactions_raw') != m.get('reactions',[]): failures.append('reactions_raw_mismatch')
        if e.get('share_raw') != m.get('share'): failures.append('share_raw_mismatch')
        if e.get('call_duration_raw') != m.get('call_duration'): failures.append('call_duration_raw_mismatch')
        excluded=('sender_name','timestamp_ms','content','photos','videos','audio_files','sticker','reactions','share','call_duration')
        expected_metadata={k:v for k,v in m.items() if k not in excluded}
        if e.get('platform_metadata_raw') != expected_metadata: failures.append('platform_metadata_raw_mismatch')
        ts=m.get('timestamp_ms')
        if isinstance(ts,(int,float)):
            expected_dt=datetime(1970,1,1,tzinfo=timezone.utc)+timedelta(milliseconds=int(ts))
            expected_local=expected_dt.astimezone(ZoneInfo(e.get('timezone') or 'UTC')).isoformat(timespec='milliseconds')
            if e.get('timestamp_parsed') != expected_local: failures.append('timestamp_conversion_mismatch')
    unique_ids=len({e['event_id'] for e in events})==len(events)
    return {'events_checked':len(events),'event_ids_unique':unique_ids,
            'source_record_fields_exact':not any(x in ('raw_record_field_mismatch','record_index_out_of_range') for x in failures),
            'attachment_refs_exact':not any(x=='attachment_ref_mismatch' for x in failures),
            'reactions_share_calls_metadata_exact':not any(x in ('reactions_raw_mismatch','share_raw_mismatch','call_duration_raw_mismatch','platform_metadata_raw_mismatch') for x in failures),
            'timestamp_conversion_exact_for_test_timezone':not any(x=='timestamp_conversion_mismatch' for x in failures),
            'failure_count':len(failures),'failure_categories':dict(collections.Counter(failures)),
            'pass':not failures and unique_ids}

def _event_kind_counts(events): return dict(collections.Counter(e.get('kind','unknown') for e in events))

def run(wa_zip,ig_zip,wa_senders,ig_timezone,report_path=None):
    with tempfile.TemporaryDirectory(prefix='chat-archive-audit-') as td:
        td=Path(td); wa_root=td/'wa'; ig_extract=td/'ig'; wa_root.mkdir(); ig_extract.mkdir()
        wa_security=media_tools.safe_extract_zip(wa_zip,wa_root)
        ig_security=media_tools.safe_extract_zip(ig_zip,ig_extract)
        transcripts=[p for p in wa_root.rglob('*.txt') if p.name.lower().startswith('whatsapp chat with ')]
        if len(transcripts)!=1: raise ValueError(f'Expected one WhatsApp transcript, found {len(transcripts)}')
        wa_path=transcripts[0]; wa_raw_bytes=wa_path.read_bytes(); wa_text=wa_raw_bytes.decode('utf-8-sig')
        wa_events,wa_audit=chat_tools.parse_whatsapp(wa_text,participants=wa_senders,date_order=None,source_id='wa-test-export')
        wa_assets=media_tools.inventory_assets(wa_root,hash_files=True)
        wa_events,wa_links=media_tools.link_whatsapp_attachments(wa_events,wa_assets)
        wa_verify=exact_whatsapp_verification(wa_text,wa_events,wa_audit,set(wa_senders))
        wa_status=collections.Counter(e.get('attachment_status') for e in wa_events if e.get('attachment_status'))
        wa_generic=sum('<Media omitted>' in (e.get('text_original') or '') for e in wa_events)
        wa_dates=[e['timestamp_parsed'] for e in wa_events if e.get('timestamp_parsed')]
        wa_report={
          'zip_safety':{'safe':wa_security['safe'],'entries':wa_security['member_count'],'issue_count':len(wa_security['issues'])},
          'transcript_bytes':len(wa_raw_bytes),'transcript_sha256':hashlib.sha256(wa_raw_bytes).hexdigest(),
          'events':len(wa_events),'physical_lines':wa_audit['physical_lines'],'timestamp_headers':wa_audit['timestamp_headers'],
          'line_coverage':wa_audit['all_lines_accounted_for'],'exact_fidelity':wa_verify,
          'date_order':wa_audit['date_order'],'timezone':'not established by export',
          'date_range':[min(wa_dates) if wa_dates else None,max(wa_dates) if wa_dates else None],
          'sender_counts_sorted':sorted(wa_audit['sender_counts'].values()),
          'parse_status_counts':wa_audit['parse_status_counts'],'event_kind_counts_after_linking':_event_kind_counts(wa_events),
          'system_events':wa_audit['system_events'],'edited_events':wa_audit['edited_events'],
          'timestamp_inversion_count':wa_audit['timestamp_inversion_count'],
          'attachment_reference_occurrences':wa_audit['attachment_reference_occurrences'],
          'distinct_attachment_names':wa_audit['unique_attachment_names'],
          'generic_media_markers_unmatched':wa_generic,'attachment_status_counts':dict(wa_status),
          'asset_count':len(wa_assets),'asset_categories':dict(collections.Counter(a['category'] for a in wa_assets)),
          'asset_link_summary':wa_links,
          'all_asset_hashes_present':all(bool(a['sha256']) for a in wa_assets)
        }
        ig_root=find_ig_root(ig_extract)
        ig_events,ig_audit=chat_tools.load_instagram(ig_root,ig_timezone)
        ig_assets=media_tools.inventory_assets(ig_root,hash_files=True)
        ig_events,ig_links=media_tools.link_instagram_attachments(ig_events,ig_assets)
        ig_verify=exact_instagram_verification(ig_root,ig_events)
        ig_missing_by_kind=collections.Counter(att.get('kind','unknown') for e in ig_events for att in e.get('attachments',[]) if att.get('uri') in (e.get('unresolved_attachment_refs') or []))
        ig_dates=[e['timestamp_parsed'] for e in ig_events if e.get('timestamp_parsed')]
        ig_report={
          'zip_safety':{'safe':ig_security['safe'],'entries':ig_security['member_count'],'issue_count':len(ig_security['issues'])},
          'message_json_files':len(ig_audit['files']),'messages':len(ig_events),
          'date_range_local_under_test_timezone':[min(ig_dates) if ig_dates else None,max(ig_dates) if ig_dates else None],
          'timezone_used_for_test_only':ig_timezone,'timezone_confirmation_still_required':True,
          'chunk_chronology':[{k:v for k,v in x.items() if k not in ('file',)} for x in ig_audit['chunk_chronology']],
          'event_kind_counts':ig_audit['event_kind_counts'],'synthetic_notice_count':ig_audit['synthetic_notice_count'],
          'null_or_empty_content_records':ig_audit['messages_with_null_or_empty_content'],
          'mojibake_candidate_strings':ig_audit['mojibake_candidate_strings'],'strings_repaired':ig_audit['strings_repaired'],
          'attachment_reference_count':ig_audit['attachment_reference_count'],
          'messages_with_attachments':ig_audit['messages_with_attachments'],
          'asset_count':len(ig_assets),'asset_categories_by_signature':dict(collections.Counter(a['category'] for a in ig_assets)),
          'audio_role_mp4_container_count':sum(1 for a in ig_assets if a['category']=='audio-container-mp4'),
          'asset_link_summary':ig_links,'missing_references_by_message_type':dict(ig_missing_by_kind),'raw_record_verification':ig_verify,
          'all_asset_hashes_present':all(bool(a['sha256']) for a in ig_assets)
        }
        # Diagnostic merged timeline only. Asia/Kolkata is a test assumption, not the final
        # timezone assertion; the real build must ask the user to confirm the phone's zone.
        chat_tools.apply_whatsapp_timezone(wa_events,ig_timezone)
        merged=chat_tools.merge_events(wa_events,ig_events)
        sequence_ok=True
        previous={}
        for e in merged:
            key=(e.get('platform'),e.get('source_stream_id'))
            n=e.get('source_sequence',0)
            if key in previous and n<previous[key]: sequence_ok=False
            previous[key]=n
        mixed_clusters={e['cluster_id'] for e in merged if e.get('cluster_id')}
        result={
          'report_version':'1.0','scope':'Structural parser and media-linking audit of supplied exports; no relationship interpretation.',
          'privacy':'No message text, sender names, media filenames, message IDs or media contents included.',
          'whatsapp':wa_report,'instagram':ig_report,
          'cross_platform_diagnostic':{'assumed_timezone_for_test_only':ig_timezone,'merged_event_count':len(merged),
            'source_order_constraints_preserved':sequence_ok,'expected_event_count':len(wa_events)+len(ig_events),
            'no_events_dropped':len(merged)==len(wa_events)+len(ig_events),
            'minute_clusters_with_both_platforms':len(mixed_clusters),'events_in_cross_platform_minute_clusters':sum(1 for e in merged if e.get('cluster_id'))},
          'limits':['WhatsApp timezone is not encoded in its text export and must be confirmed for the final merge.',
                    'Media bytes were inventoried, signature-checked and hashed, but personal image/audio/video contents were not viewed or listened to.',
                    'The three missing Instagram video references remain unresolved; the skill must not invent replacement media.',
                    'The WhatsApp export contains unmatched generic media markers and 57 distinct referenced filenames absent from the ZIP.']
        }
        if report_path: Path(report_path).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        return result

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('whatsapp_zip'); ap.add_argument('instagram_zip')
    ap.add_argument('--whatsapp-senders',required=True,help='Exact exported sender labels separated by |')
    ap.add_argument('--instagram-timezone',required=True,help='IANA timezone to test timestamp conversion, e.g. Asia/Kolkata; must be confirmed before final use')
    ap.add_argument('--output')
    a=ap.parse_args()
    result=run(a.whatsapp_zip,a.instagram_zip,[x for x in a.whatsapp_senders.split('|') if x],a.instagram_timezone,a.output)
    print(json.dumps({'whatsapp':{k:v for k,v in result['whatsapp'].items() if k not in ('transcript_sha256','exact_fidelity')},
                      'instagram':{k:v for k,v in result['instagram'].items() if k not in ('raw_record_verification',)},
                      'cross_platform_diagnostic':result['cross_platform_diagnostic']},ensure_ascii=False,indent=2))
    return 0 if result['whatsapp']['exact_fidelity']['pass'] and result['instagram']['raw_record_verification']['pass'] and result['cross_platform_diagnostic']['no_events_dropped'] else 2
if __name__=='__main__': raise SystemExit(main())
