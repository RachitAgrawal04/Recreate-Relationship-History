#!/usr/bin/env python3
"""Portable WhatsApp/Instagram parser for Chat Story Webpage v3.6.

Standard-library only. Raw exports remain the source of truth. This module never
writes back to source files. Run `python tools/chat_tools.py --selftest`.
"""
from __future__ import annotations
import collections, hashlib, json, os, re, sys, unicodedata, heapq
from datetime import datetime, timezone, timedelta
from pathlib import Path, PurePosixPath
from zoneinfo import ZoneInfo

INVISIBLE = set('\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069\ufeff')
NBSP = set('\u00a0\u202f\u2009')

def clean_for_matching(text: str) -> str:
    return ''.join(' ' if c in NBSP else '' if c in INVISIBLE else c for c in (text or ''))

def clean_with_map(raw: str):
    chars, offsets = [], []
    for i, ch in enumerate(raw):
        if ch in INVISIBLE: continue
        chars.append(' ' if ch in NBSP else ch); offsets.append(i)
    return ''.join(chars), offsets

def raw_slice(raw: str, offsets: list[int], start: int, end: int, keep_leading_invisibles=False):
    if start >= len(offsets): return ''
    a = offsets[start]
    if keep_leading_invisibles and start > 0: a = offsets[start-1] + 1
    b = len(raw) if end >= len(offsets) else (offsets[end-1] + 1 if end > start else a)
    return raw[a:b]

_DATE = r'(\d{1,2})[/ .\-](\d{1,2})[/ .\-](\d{2,4})'
_TIME = r'(\d{1,2})[:.](\d{2})(?:[:.](\d{2}))?\s*([ap]m|[ap]\.m\.)?'
ANDROID = re.compile(r'^' + _DATE + r',?\s+' + _TIME + r'\s+[-–]\s+(.*)$', re.I)
IOS = re.compile(r'^\[' + _DATE + r',?\s+' + _TIME + r'\]\s*(.*)$', re.I)
TIMESTAMP_LIKE = re.compile(r'^\s*\[?\d{1,2}[/ .\-]\d{1,2}[/ .\-]\d{2,4}[,\s]', re.I)

def detect_date_order(headers):
    a = any(int(m.group(1)) > 12 for m in headers)
    b = any(int(m.group(2)) > 12 for m in headers)
    if a and not b: return 'dmy'
    if b and not a: return 'mdy'
    if a and b: return 'contradiction'
    return 'ambiguous'

def parse_timestamp(m, date_order):
    d1,d2,yr,hh,mi,ss,ampm,_ = m.groups()
    a,b=int(d1),int(d2)
    if date_order == 'dmy': day,month=a,b
    elif date_order == 'mdy': day,month=b,a
    else: return None,'ambiguous'
    year=int(yr)
    if year < 100: year += (2000 if year <= 69 else 1900)
    hour=int(hh)
    if ampm:
        ap=ampm.lower().replace('.','')
        hour=(hour % 12) + (12 if ap == 'pm' else 0)
    try:
        return datetime(year,month,day,hour,int(mi),int(ss or 0)).isoformat(),'exact'
    except ValueError:
        return None,'unparsed'

def _body_kind(text):
    """Classify explicit text markers conservatively; generic media stays unknown."""
    t=clean_for_matching(text).strip(); low=t.lower()
    generic=re.match(r'^<?\s*media\s+omitted\s*>?$',low)
    if generic: return 'unknown','unmatched-generic-reference'
    explicit=[
        (r'^<?\s*(image|photo)\s+omitted\s*>?$','photo'),
        (r'^<?\s*video\s+omitted\s*>?$','video'),
        (r'^<?\s*(audio|voice message|ptt)\s+omitted\s*>?$','audio'),
        (r'^<?\s*sticker\s+omitted\s*>?$','sticker'),
        (r'^<?\s*gif\s+omitted\s*>?$','gif'),
        (r'^<?\s*document\s+omitted\s*>?$','document'),
    ]
    for pattern,kind in explicit:
        if re.match(pattern,low): return kind,'not-included-in-export'
    if re.match(r'^(this message was deleted|you deleted this message|message deleted)$',low): return 'deletion',None
    if re.match(r'^(missed\s+)?(voice|video) call\b.*$',low) or re.match(r'^(voice|video) call\b.*$',low): return 'call',None
    if '(file attached)' in low: return 'unknown','referenced-but-unresolved'
    return 'text',None

_FILE_ATTACHED = re.compile(r'(?P<name>[^\r\n]+?)\s*\(file attached\)',re.I)
def extract_whatsapp_attachment_refs(body: str):
    refs=[]
    for line in (body or '').splitlines():
        for m in _FILE_ATTACHED.finditer(line):
            name=m.group('name').strip()
            # Some exports wrap the filename in an attached: marker. Preserve exact basename otherwise.
            name=re.sub(r'^<attached:\s*','',name,flags=re.I).strip()
            name=re.sub(r'>$','',name).strip()
            if name: refs.append(name)
    return refs

def parse_whatsapp(text: str, participants=None, date_order=None, source_id='whatsapp-source'):
    """Parse WhatsApp Android/iOS text, retaining raw body characters and physical-line provenance.

    `participants` should be the exact two confirmed sender labels. Without it, labels
    are candidates only and must not be treated as confirmed identities. No timezone
    is inferred: WhatsApp exports contain exporting-phone local wall-clock timestamps.
    """
    raw_lines=text.splitlines()  # avoids an artificial trailing empty line
    cleaned=[clean_with_map(x)[0] for x in raw_lines]
    headers=[]; style_counts=collections.Counter()
    for i,line in enumerate(cleaned):
        ma,mi=ANDROID.match(line),IOS.match(line)
        m=ma or mi
        if m:
            style='android' if ma else 'ios'; style_counts[style]+=1
            headers.append((i,m,style,line))
    order=date_order or detect_date_order([x[1] for x in headers])
    header_by={i:(m,style,line) for i,m,style,line in headers}
    participants=set(participants) if participants is not None else None
    digest=hashlib.sha256(text.encode('utf-8',errors='surrogatepass')).hexdigest()[:12]
    events=[]; review=[]; sender_counts=collections.Counter(); cur=None
    continuation_count=0; event_counter=0
    first_header=headers[0][0] if headers else len(raw_lines)

    for i,raw in enumerate(raw_lines):
        item=header_by.get(i)
        if item is None:
            if TIMESTAMP_LIKE.match(cleaned[i]):
                review.append({'line':i+1,'reason':'malformed_timestamp_like','raw':raw})
                cur=None
            elif cur is not None:
                cur['text_raw'] += '\n' + raw
                cur['text_original'] = cur['text_raw']
                cur['raw_lines'].append(i+1); continuation_count += 1
            else:
                review.append({'line':i+1,'reason':'orphan_before_or_between_events','raw':raw})
            continue
        m,style,_=item
        gstart,gend=m.span(8); _,offsets=clean_with_map(raw)
        raw_rest=raw_slice(raw,offsets,gstart,gend)
        raw_stamp=raw[:(offsets[gstart] if gstart<len(offsets) else len(raw))]
        rest_clean=cleaned[i][gstart:gend]
        sender=None; body=raw_rest; system=True; sender_candidate=None
        if participants is not None:
            for name in sorted(participants,key=len,reverse=True):
                prefix=name+': '
                if rest_clean.startswith(prefix):
                    sender=name
                    body=raw_slice(raw,offsets,gstart+len(prefix),gend,keep_leading_invisibles=True)
                    system=False; break
                if rest_clean == name+':':
                    sender=name; body=''; system=False; break
            if sender is None:
                # Keep timestamped non-participant/system records separate. Do not
                # accidentally attribute them to either of the two people.
                candidate=rest_clean.split(': ',1)[0] if ': ' in rest_clean else None
                if candidate and len(candidate)<=100: sender_candidate=candidate
        else:
            sep=rest_clean.find(': ')
            if 0 < sep <= 100:
                sender=rest_clean[:sep]
                body=raw_slice(raw,offsets,gstart+sep+2,gend,keep_leading_invisibles=True)
                system=False
            elif rest_clean.endswith(':') and len(rest_clean)<102:
                sender=rest_clean[:-1]; body=''; system=False
        if sender: sender_counts[sender]+=1
        parsed,status=parse_timestamp(m,order)
        kind,attachment_status=('system',None) if system else _body_kind(body)
        refs=extract_whatsapp_attachment_refs(body)
        if refs and not system:
            kind='unknown'; attachment_status='referenced-but-unresolved'
        edited=bool(re.search(r'<\s*this message was edited\s*>',clean_for_matching(body),re.I))
        if edited and kind=='text': kind='text'
        event_counter+=1
        event={
            'event_id':f'wa:{digest}:L{i+1:06d}','platform':'whatsapp','source_file':source_id,'source_stream_id':f'wa-stream:{digest}',
            'record_locator':f'line:{i+1}','source_sequence':event_counter-1,
            'sender_raw':sender,'sender_candidate':sender_candidate,
            'sender_id':None if system else 'unmapped','timestamp_raw':raw_stamp,
            'timestamp_parsed':parsed,'timezone':None,
            'timezone_source':'unknown; exporting phone local wall-clock','precision':'second' if m.group(6) else 'minute',
            'parse_status':status,'text_raw':body,'text_original':body,'kind':kind,
            'attachment_refs':refs,'attachment_status':attachment_status,
            'edit_status':'edited' if edited else 'unknown','raw_lines':[i+1],
            'raw_first_line':raw,'source_style':style,'warnings':[]
        }
        if status!='exact': event['warnings'].append('timestamp_unresolved')
        events.append(event); cur=event

    # Mark edits after full multiline reconstruction.
    for e in events:
        if e['kind']!='system' and re.search(r'<\s*this message was edited\s*>',clean_for_matching(e.get('text_original') or ''),re.I):
            e['edit_status']='edited'
    inversions=[]; prev=None
    for e in events:
        if not e.get('timestamp_parsed'): continue
        if prev and e['timestamp_parsed'] < prev['timestamp_parsed']:
            pdt=datetime.fromisoformat(prev['timestamp_parsed']); cdt=datetime.fromisoformat(e['timestamp_parsed'])
            inv={'previous_event_id':prev['event_id'],'event_id':e['event_id'],
                 'previous_line':prev['raw_lines'][0],'line':e['raw_lines'][0],
                 'backwards_seconds':int((pdt-cdt).total_seconds())}
            inversions.append(inv); e['source_order_anomaly']=True
            e['warnings'].append('timestamp_earlier_than_previous_source_event')
        prev=e
    covered=[ln for e in events for ln in e['raw_lines']] + [r['line'] for r in review]
    duplicates=len(covered)!=len(set(covered))
    all_covered=(not duplicates and sorted(covered)==list(range(1,len(raw_lines)+1)))
    kinds=collections.Counter(e['kind'] for e in events)
    statuses=collections.Counter(e['attachment_status'] for e in events if e.get('attachment_status'))
    audit={
      'source_sha256_prefix':digest,'format':'mixed' if len(style_counts)>1 else next(iter(style_counts),'unknown'),
      'style_counts':dict(style_counts),'date_order':order,'physical_lines':len(raw_lines),
      'timestamp_headers':len(headers),'events':len(events),'message_events':sum(e['kind']!='system' for e in events),
      'system_events':kinds.get('system',0),'sender_counts':dict(sender_counts),
      'parse_status_counts':dict(collections.Counter(e['parse_status'] for e in events)),
      'kind_counts':dict(kinds),'attachment_status_counts':dict(statuses),
      'attachment_reference_occurrences':sum(len(e['attachment_refs']) for e in events),
      'unique_attachment_names':len({x for e in events for x in e['attachment_refs']}),
      'edited_events':sum(e['edit_status']=='edited' for e in events),
      'continuation_lines':continuation_count,'unparsed_or_orphan_lines':len(review),
      'review_lines':review,'line_coverage_count':len(covered),'all_lines_accounted_for':all_covered,
      'duplicate_line_ownership':duplicates,'timestamp_inversions':inversions,
      'timestamp_inversion_count':len(inversions),'timezone_confirmed':False,
      'source_ends_with_line_terminator':text.endswith(('\n','\r'))
    }
    return events,audit

# Instagram Download Your Information helpers.
_MOJI_MARKERS=('Ã','Â','â€','ðŸ','ï¿½','â€™','â€œ','à¤','Å','Ä')
def _mojibake_score(value):
    return (sum(value.count(marker) for marker in _MOJI_MARKERS)
            + sum(1 for char in value if 0x80 <= ord(char) <= 0x9f))

def _repair_latin1_run(run):
    if not isinstance(run,str) or not any(ord(c)>127 for c in run): return None
    before=_mojibake_score(run)
    # A reversible round-trip alone is not enough: valid Latin text can sometimes
    # accidentally decode. Require known mojibake markers/C1 bytes and ensure the
    # candidate actually reduces those indicators.
    if before == 0: return None
    try: candidate=run.encode('latin-1').decode('utf-8')
    except (UnicodeEncodeError,UnicodeDecodeError): return None
    if candidate == run or _mojibake_score(candidate) >= before: return None
    return candidate

def repair_mojibake(value):
    """Repair likely Latin-1/UTF-8 mojibake, preserving already-correct Unicode.

    Repair is per string and per Latin-1-compatible run. A message mixing real
    Devanagari/emoji with a damaged Latin-1 run can therefore be repaired without
    attempting to encode or rewrite the valid Unicode segment.
    """
    if not isinstance(value,str) or not any(ord(c)>127 for c in value): return None
    whole=_repair_latin1_run(value)
    if whole is not None: return whole
    out=[]; run=[]; changed=False
    def flush():
        nonlocal changed
        if not run: return
        source=''.join(run); candidate=_repair_latin1_run(source)
        if candidate is not None:
            out.append(candidate); changed=True
        else:
            out.append(source)
        run.clear()
    for char in value:
        if ord(char) <= 255:
            run.append(char)
        else:
            flush(); out.append(char)
    flush()
    result=''.join(out)
    return result if changed and result != value else None

def _repair_tree(value,audit):
    if isinstance(value,str):
        candidate=repair_mojibake(value)
        if candidate is not None:
            audit['mojibake_candidate_strings']+=1
            audit['strings_repaired']+=1
            return candidate
        if _mojibake_score(value)>0:
            audit['strings_suspicious_not_repaired']=audit.get('strings_suspicious_not_repaired',0)+1
        return value
    if isinstance(value,list): return [_repair_tree(x,audit) for x in value]
    if isinstance(value,dict): return {k:_repair_tree(v,audit) for k,v in value.items()}
    return value

def _ig_notice(text):
    t=(text or '').strip()
    patterns=[
      (r'^(you |.{1,80} )?reacted .{1,48} to (your|their|a) message\.?$','reaction'),
      (r'^liked a message\.?$','reaction'),
      (r'^(you|.{1,80}) sent an attachment\.?$','system'),
      (r'^(.{1,80} )?(replied to|mentioned you in) (your|their) story\.?$','system'),
    ]
    for pat,kind in patterns:
        if re.match(pat,t,re.I): return kind
    return None

def load_instagram(folder,timezone_name):
    """Load message_*.json recursively. timezone_name is REQUIRED and user-confirmed."""
    zone=ZoneInfo(timezone_name); root=Path(folder).resolve(); json_paths=[]
    for p in root.rglob('message_*.json'):
        if p.is_symlink() or not p.is_file(): continue
        try: p.resolve().relative_to(root)
        except ValueError: continue
        if re.fullmatch(r'message_\d+\.json',p.name): json_paths.append(p)
    json_paths.sort(key=lambda p:p.relative_to(root).as_posix())
    docs=[]
    for p in json_paths:
        obj=json.loads(p.read_text(encoding='utf-8'))
        if not isinstance(obj,dict) or not isinstance(obj.get('messages'),list):
            raise ValueError(f'Unsupported Instagram JSON structure: {p.relative_to(root)}')
        docs.append((p,obj))
    audit={'files':[p.relative_to(root).as_posix() for p,_ in docs],
           'participants':sorted({x.get('name') for _,o in docs for x in o.get('participants',[]) if isinstance(x,dict) and x.get('name')}),
           'timezone':timezone_name,'mojibake_candidate_strings':0,'strings_repaired':0,'strings_suspicious_not_repaired':0,
           'malformed_records':0,'message_count_by_file':{},'chunk_chronology':[],
           'conversation_metadata':[{'source_directory':p.parent.relative_to(root).as_posix(),
             'title':obj.get('title'),'thread_path':obj.get('thread_path'),
             'is_still_participant':obj.get('is_still_participant')} for p,obj in docs]}
    events=[]
    for p,obj in docs:
        rel=p.relative_to(root).as_posix(); conversation_id=p.parent.relative_to(root).as_posix()
        msgs=obj['messages']; audit['message_count_by_file'][rel]=len(msgs)
        times=[m.get('timestamp_ms') for m in msgs if isinstance(m,dict) and isinstance(m.get('timestamp_ms'),(int,float))]
        descending=bool(times) and all(a>=b for a,b in zip(times,times[1:]))
        ascending=bool(times) and all(a<=b for a,b in zip(times,times[1:]))
        audit['chunk_chronology'].append({'file':rel,'records':len(msgs),'newest_first':descending,'oldest_first':ascending,
            'first_timestamp_ms':times[0] if times else None,'last_timestamp_ms':times[-1] if times else None})
        path_hash=hashlib.sha256(rel.encode()).hexdigest()[:12]
        stream_hash=hashlib.sha256(conversation_id.encode()).hexdigest()[:12]
        for idx,m in enumerate(msgs):
            if not isinstance(m,dict): audit['malformed_records']+=1; continue
            fixed=_repair_tree(m,audit)
            raw=m.get('content'); display=fixed.get('content')
            ts=m.get('timestamp_ms'); dt=None
            if isinstance(ts,(int,float)):
                # Integer milliseconds avoid float-rounding at the millisecond boundary.
                dt=datetime(1970,1,1,tzinfo=timezone.utc)+timedelta(milliseconds=int(ts))
                dt=dt.astimezone(zone)
            attachments=[]
            for key,kind in [('photos','photo'),('videos','video'),('audio_files','audio'),('sticker','sticker')]:
                value=m.get(key); vals=value if isinstance(value,list) else [value] if isinstance(value,dict) else []
                for item in vals:
                    if isinstance(item,dict) and isinstance(item.get('uri'),str):
                        attachments.append({'uri':item['uri'],'kind':kind,'source_key':key,
                                            'creation_timestamp':item.get('creation_timestamp')})
            # Only an explicit is_unsent flag is treated as a deletion. The export's
            # is_unsent_image_by_messenger_kid_parent field is preserved as raw metadata
            # but its semantics are not assumed to mean 'message unsent'.
            if m.get('is_unsent') is True: kind='deletion'
            elif m.get('photos'): kind='photo'
            elif m.get('videos'): kind='video'
            elif m.get('audio_files'): kind='audio'
            elif m.get('sticker'): kind='sticker'
            elif m.get('share'): kind='share'
            elif 'call_duration' in m and m.get('call_duration') is not None: kind='call'
            else:
                notice=_ig_notice(display if isinstance(display,str) else '')
                if notice: kind=notice
                elif display in (None,''): kind='unknown'
                else: kind='text'
            sender_raw=m.get('sender_name'); sender_display=fixed.get('sender_name')
            # Source and display representations are kept separate. The source field
            # is never overwritten by repaired text or metadata.
            event={
              'event_id':f'ig:{path_hash}:{idx:06d}','platform':'instagram','source_file':rel,
              'source_stream_id':f'ig-thread:{stream_hash}','record_locator':f'messages[{idx}]',
              'source_record_index':idx,'source_sequence':None,
              'sender_raw':sender_raw,'sender_display':sender_display,'sender_id':'unmapped',
              'timestamp_raw':ts,'timestamp_parsed':dt.isoformat(timespec='milliseconds') if dt else None,
              'timestamp_sort_key':dt.astimezone(timezone.utc).isoformat(timespec='milliseconds') if dt else None,
              'timezone':timezone_name,'timezone_source':'user-confirmed timezone applied to UTC epoch' if dt else None,
              'precision':'millisecond' if dt else None,'parse_status':'exact' if dt else 'unparsed',
              'text_raw':raw,'text_original':raw,'text_display':display,'kind':kind,
              'synthetic':bool(_ig_notice(display) if isinstance(display,str) else False),
              'attachment_refs':[a['uri'] for a in attachments],'attachments':attachments,
              'attachment_status':'referenced-unresolved' if attachments else None,
              'reactions_raw':m.get('reactions',[]),'reactions':fixed.get('reactions',[]),
              'share_raw':m.get('share'),'share':fixed.get('share'),
              'call_duration_raw':m.get('call_duration'),'platform_metadata_raw':{
                k:v for k,v in m.items() if k not in ('sender_name','timestamp_ms','content','photos','videos','audio_files','sticker','reactions','share','call_duration')},
              'platform_metadata':{
                k:v for k,v in fixed.items() if k not in ('sender_name','timestamp_ms','content','photos','videos','audio_files','sticker','reactions','share','call_duration')},
              'text_transform_applied':bool(isinstance(raw,str) and display!=raw),
              'edit_status':'unknown','warnings':([] if m.get('is_unsent_image_by_messenger_kid_parent') is not True else ['uninterpreted_platform_flag:is_unsent_image_by_messenger_kid_parent'])
            }
            events.append(event)
    # The JSON chunks are newest-first; sort to chronological order, preserving original
    # file/index provenance and using path/index as deterministic tie-breakers.
    events.sort(key=lambda e:(e['timestamp_parsed'] is None,e['timestamp_parsed'] or '',e['source_file'],-e['source_record_index']))
    for seq,e in enumerate(events): e['source_sequence']=seq
    audit['events']=len(events)
    audit['event_kind_counts']=dict(collections.Counter(e['kind'] for e in events))
    audit['messages_with_attachments']=sum(bool(e['attachments']) for e in events)
    audit['attachment_reference_count']=sum(len(e['attachments']) for e in events)
    audit['messages_with_null_or_empty_content']=sum(e['text_raw'] in (None,'') for e in events)
    audit['synthetic_notice_count']=sum(e['synthetic'] for e in events)
    audit['timestamps_missing']=sum(e['timestamp_parsed'] is None for e in events)
    audit['mojibake_detected']=audit['strings_repaired']>0
    return events,audit

def apply_whatsapp_timezone(events, timezone_name):
    """Apply a user-confirmed IANA timezone to naive WhatsApp wall-clock stamps for sorting only."""
    zone=ZoneInfo(timezone_name)
    for e in events:
        raw=e.get('timestamp_parsed')
        if not raw: continue
        local=datetime.fromisoformat(raw).replace(tzinfo=zone)
        e['timezone']=timezone_name
        e['timezone_source']='user-confirmed IANA zone applied to exporting-phone wall-clock'
        e['timestamp_sort_key']=local.astimezone(timezone.utc).isoformat(timespec='milliseconds')
    return events

def merge_events(*event_lists):
    """Merge event streams using source-order constraints and normalized UTC sort keys.

    Cross-platform merges refuse to guess when WhatsApp timezone normalization is absent."""
    all_events=[e for group in event_lists for e in group]
    if not all_events: return []
    platforms={e.get('platform') for e in all_events if e.get('timestamp_parsed')}
    if len(platforms)>1:
        missing=[e.get('event_id') for e in all_events if e.get('timestamp_parsed') and not e.get('timestamp_sort_key')]
        if missing:
            raise ValueError('Cross-platform merge requires a user-confirmed shared timezone and UTC sort key for every dated event')
    node_index={id(e):i for i,e in enumerate(all_events)}
    streams=collections.defaultdict(list)
    for li,group in enumerate(event_lists):
        for local,e in enumerate(group):
            # A conversation stream may span multiple chunk files; use explicit stream ID if available.
            stream=e.get('source_stream_id') or e.get('source_file') or f'input:{li}'
            streams[(e.get('platform'),stream)].append((e.get('source_sequence',local),local,node_index[id(e)],e))
    outgoing={i:[] for i in range(len(all_events))}; indegree=[0]*len(all_events)
    for seq in streams.values():
        seq.sort(key=lambda x:(x[0],x[1]))
        for a,b in zip(seq,seq[1:]):
            outgoing[a[2]].append(b[2]); indegree[b[2]]+=1
    def key(i):
        e=all_events[i]
        return (e.get('timestamp_sort_key') or e.get('timestamp_parsed') or '9999',e.get('platform') or '',i)
    ready=[(key(i),i) for i,d in enumerate(indegree) if d==0]; heapq.heapify(ready)
    merged=[]
    while ready:
        _,i=heapq.heappop(ready); merged.append(all_events[i])
        for j in outgoing[i]:
            indegree[j]-=1
            if indegree[j]==0: heapq.heappush(ready,(key(j),j))
    if len(merged)!=len(all_events): raise ValueError('Cannot merge source order constraints without reordering; preserving raw streams separately')
    clusters=collections.defaultdict(list)
    for e in merged:
        ts=e.get('timestamp_parsed')
        if ts: clusters[ts[:16]].append(e)
    for minute,group in clusters.items():
        if len({e.get('platform') for e in group})>1:
            for e in group: e['cluster_id']='minute:'+minute; e['ordering_uncertain']=True
    return merged

def find_duplicate_candidates(events,window_seconds=120):
    """Flag possible duplicate text records; never remove or merge source events."""
    buckets=collections.defaultdict(list)
    for e in events:
        text=e.get('text_display',e.get('text_original')) or ''
        norm=re.sub(r'\s+',' ',text.strip().lower())
        stamp=e.get('timestamp_sort_key') or e.get('timestamp_parsed')
        if len(norm)<3 or not stamp or not e.get('sender_raw'): continue
        try: dt=datetime.fromisoformat(stamp)
        except ValueError: continue
        buckets[(e.get('sender_id'),e.get('sender_raw'),norm)].append((dt,e))
    group_counter=0
    for _,items in buckets.items():
        items.sort(key=lambda x:x[0]); group=[]; last=None
        for dt,e in items:
            if group and (dt-last).total_seconds()>window_seconds:
                if len(group)>1:
                    group_counter+=1; gid=f'dup:{group_counter}'
                    platforms={x.get('platform') for x in group}
                    reason='same sender and normalized text within %ds; %s' % (window_seconds,'cross-platform' if len(platforms)>1 else 'same-source')
                    for x in group: x['duplicate_group_id']=gid; x['duplicate_reason']=reason
                group=[]
            group.append(e); last=dt
        if len(group)>1:
            group_counter+=1; gid=f'dup:{group_counter}'
            platforms={x.get('platform') for x in group}
            reason='same sender and normalized text within %ds; %s' % (window_seconds,'cross-platform' if len(platforms)>1 else 'same-source')
            for x in group: x['duplicate_group_id']=gid; x['duplicate_reason']=reason
    return events

def group_turns(events,gap_seconds=180):
    """Assign display-only turns; every source event remains separately addressable."""
    prev=None; prev_time=None; n=0
    for e in events:
        if e.get('kind')=='system' or not e.get('timestamp_sort_key'):
            e['turn_id']=None; prev=None; prev_time=None; continue
        current=datetime.fromisoformat(e['timestamp_sort_key'])
        if prev is not None and prev.get('sender_raw')==e.get('sender_raw') and prev.get('platform')==e.get('platform') and 0 <= (current-prev_time).total_seconds() <= gap_seconds:
            e['turn_id']=prev['turn_id']
        else:
            n+=1; e['turn_id']=f't{n}'
        prev=e; prev_time=current
    return events

def _tokens(s):
    out=[]; cur=[]
    for ch in s or '':
        if unicodedata.category(ch)[0] in 'LMN': cur.append(ch)
        elif cur: out.append(''.join(cur)); cur=[]
    if cur: out.append(''.join(cur))
    return out

def search_keys(text):
    base=unicodedata.normalize('NFKC', ''.join(c for c in (text or '') if c not in INVISIBLE)).lower()
    collapsed=re.sub(r'(.)\1+',r'\1',base,flags=re.S)
    skeleton=[re.sub(r'[aeiou]','',t) for t in _tokens(collapsed)]
    return base,collapsed,skeleton

def search(events,query):
    qb,qc,qs=search_keys(query); qs=[x for x in qs if len(x)>=2]; hits=[]
    for e in events:
        if e.get('synthetic'): continue
        b,c,s=search_keys(e.get('text_display',e.get('text_original')) or '')
        if qb and qb in b: hits.append((e['event_id'],1))
        elif qc and qc in c: hits.append((e['event_id'],2))
        elif qs and all(x in s for x in qs): hits.append((e['event_id'],3))
    return sorted(hits,key=lambda x:x[1])

def _parity():
    import shutil,subprocess
    node=shutil.which('node')
    if not node:
        print('NOT TESTED: Node.js is not installed'); return 0
    js=Path(__file__).with_name('search_keys.js')
    samples=['Kaaaaash!!','Ki hmari jitni bhi baat hui h','Uss sbko dubara pdh skte','Saath me bethke padhte','Haa yrrrr','khana khaya?','‎How it started\nHow it went','कभी कभी café','😂😂 hahaha','A.B.C   dd']
    script="const {searchKeys}=require(process.argv[1]);const a=JSON.parse(require('fs').readFileSync(0,'utf8'));console.log(JSON.stringify(a.map(s=>{const k=searchKeys(s);return [k.base,k.collapsed,k.skeleton]})))"
    res=subprocess.run([node,'-e',script,str(js)],input=json.dumps(samples,ensure_ascii=False),capture_output=True,text=True)
    if res.returncode:
        print('FAIL Python/JS parity:',res.stderr[:200]); return 1
    got=json.loads(res.stdout); bad=[]
    for text_value,other in zip(samples,got):
        if list(search_keys(text_value))!=other: bad.append(text_value)
    print('PASS Python/JS search parity (%d samples)'%len(samples) if not bad else 'FAIL Python/JS search parity')
    return 0 if not bad else 1

def _selftest():
    ok=True
    def check(name,condition):
        nonlocal ok; ok &= bool(condition); print(('PASS ' if condition else 'FAIL ')+name)
    wa='28/08/26, 3:22\u202fpm - Messages and calls are end-to-end encrypted.\n28/08/26, 3:23 pm - Asha: \u200eHello\u202fthere\nline two <This message was edited>\n28/08/26, 3:24 pm - Dev: IMG-20260828-WA0001.jpg (file attached)\n28/08/26, 3:25 pm - Dev: <Media omitted>\n'
    ev,a=parse_whatsapp(wa,participants={'Asha','Dev'})
    check('WA: date order DMY and line coverage',a['date_order']=='dmy' and a['all_lines_accounted_for'])
    check('WA: raw message body and leading invisible marks preserved',ev[1]['text_original'].startswith('\u200e') and '\u202f' in ev[1]['text_original'])
    check('WA: edit marker on continuation detected',ev[1]['edit_status']=='edited')
    check('WA: attachment filename extracted',ev[2]['attachment_refs']==['IMG-20260828-WA0001.jpg'])
    check('WA: generic Media omitted is unknown, not a photo',ev[3]['kind']=='unknown' and ev[3]['attachment_status']=='unmatched-generic-reference')
    amb,aa=parse_whatsapp('01/02/26, 1:02 pm - A: hi\n')
    check('WA: ambiguous date order is not guessed',aa['date_order']=='ambiguous' and amb[0]['timestamp_parsed'] is None)
    igtext='Kaaaaash!!'
    check('search: stretched Hinglish spelling',bool(search([{'event_id':'x','text_original':igtext}],'kash')))
    def moji(s): return s.encode('utf-8').decode('latin-1')
    check('IG: reversible mojibake repair',repair_mojibake(moji('hello 😂'))=='hello 😂')
    check('IG: real Devanagari not modified',repair_mojibake('कभी café') is None)
    check('IG: real Latin accents are not blindly rewritten',repair_mojibake('café déjà vu') is None)
    mixed_unicode='कभी '+moji('hello 😂')+' 😊'
    check('IG: mixed Devanagari/emoji and mojibake run repaired selectively',repair_mojibake(mixed_unicode)=='कभी hello 😂 😊')
    check('IG: known Latin mojibake corrected',repair_mojibake('DivÃ¡')=='Divá')
    try:
        merge_events([{'event_id':'w','platform':'whatsapp','timestamp_parsed':'2026-01-01T10:00:00','source_sequence':0}], [{'event_id':'i','platform':'instagram','timestamp_parsed':'2026-01-01T10:00:00+05:30','timestamp_sort_key':'2026-01-01T04:30:00+00:00','source_sequence':0}])
        refused=False
    except ValueError: refused=True
    check('merge: cross-platform timezone is never guessed',refused)
    wa_demo=[{'event_id':'w','platform':'whatsapp','timestamp_parsed':'2026-01-01T10:00:00','source_sequence':0}]
    apply_whatsapp_timezone(wa_demo,'Asia/Kolkata')
    check('merge: confirmed timezone produces UTC sort key',wa_demo[0]['timestamp_sort_key']=='2026-01-01T04:30:00.000+00:00')
    candidates=[{'event_id':'a','platform':'whatsapp','sender_raw':'A','sender_id':'p','timestamp_parsed':'2026-01-01T10:00:00','timestamp_sort_key':'2026-01-01T04:30:00+00:00','text_original':'same words'}, {'event_id':'b','platform':'instagram','sender_raw':'A','sender_id':'p','timestamp_parsed':'2026-01-01T10:01:00+05:30','timestamp_sort_key':'2026-01-01T04:31:00+00:00','text_display':'same words'}]
    find_duplicate_candidates(candidates)
    check('duplicates: candidates flagged but both source events remain',len(candidates)==2 and candidates[0].get('duplicate_group_id')==candidates[1].get('duplicate_group_id'))
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as td:
        for folder,person in [('thread_a','A'),('thread_b','B')]:
            d=Path(td)/folder; d.mkdir()
            (d/'message_1.json').write_text(json.dumps({'participants':[{'name':person}], 'messages':[{'sender_name':person,'timestamp_ms':1794287658412,'content':'hello'}]}),encoding='utf-8')
        multi,ma=load_instagram(td,'Asia/Kolkata')
        check('IG: same-named message_1.json in separate threads has unique event IDs',len(multi)==2 and len({x['event_id'] for x in multi})==2)
        check('IG: message chunk metadata retained',len(ma['files'])==2 and len({x['source_stream_id'] for x in multi})==2)
        # Real-export schema edge cases: zero-duration calls, optional share fields,
        # multiple reactions, explicit unsent vs an ambiguously named platform flag.
        edge_dir=Path(td)/'edge'; edge_dir.mkdir()
        edge_messages=[
          {'sender_name':'A','timestamp_ms':1794287658412,'content':None,'call_duration':0,'is_geoblocked_for_viewer':False},
          {'sender_name':'B','timestamp_ms':1794287658413,'content':'shared post','share':{'share_text':'caption only'}},
          {'sender_name':'A','timestamp_ms':1794287658414,'content':'photo group','photos':[{'uri':'photos/a.jpg','creation_timestamp':1},{'uri':'photos/b.jpg','creation_timestamp':2}]},
          {'sender_name':'B','timestamp_ms':1794287658415,'content':'flag remains visible','is_unsent_image_by_messenger_kid_parent':True},
          {'sender_name':'A','timestamp_ms':1794287658416,'content':'explicitly unsent','is_unsent':True},
          {'sender_name':'B','timestamp_ms':1794287658417,'content':'reaction record','reactions':[{'actor':'A','reaction':'❤'},{'actor':'B','reaction':'😂'}]},
        ]
        (edge_dir/'message_1.json').write_text(json.dumps({'participants':[{'name':'A'},{'name':'B'}],'messages':edge_messages}),encoding='utf-8')
        edge_events,edge_audit=load_instagram(edge_dir,'Asia/Kolkata')
        by_content={e.get('text_raw'):e for e in edge_events}
        check('IG: zero-duration call retained as call',by_content[None]['kind']=='call' and by_content[None]['call_duration_raw']==0)
        check('IG: partial share object retained',by_content['shared post']['share_raw']=={'share_text':'caption only'})
        check('IG: multiple attachments on one message retained',len(by_content['photo group']['attachments'])==2)
        check('IG: ambiguous kid-parent flag is preserved, not auto-called deletion',by_content['flag remains visible']['kind']=='text' and bool(by_content['flag remains visible']['warnings']))
        check('IG: explicit is_unsent flag is classified as deletion',by_content['explicitly unsent']['kind']=='deletion')
        check('IG: multiple reactions preserved without flattening',len(by_content['reaction record']['reactions_raw'])==2)
    print('ALL PASS' if ok else 'FAILURES'); return 0 if ok else 1

if __name__=='__main__':
    if '--selftest' in sys.argv: raise SystemExit(_selftest())
    if '--parity' in sys.argv: raise SystemExit(_parity())
    print(__doc__)
