#!/usr/bin/env python3
"""Safe ZIP handling, asset inventory, hashing and conservative message/media linking."""
from __future__ import annotations
import collections, hashlib, json, mimetypes, os, pathlib, re, stat, zipfile
from pathlib import Path, PurePosixPath

DEFAULT_LIMITS={'max_entries':50000,'max_total_uncompressed':3*1024**3,
                'max_single_file':1024**3,'max_ratio':1000}

def _member_safe(name,is_dir=False):
    norm=name.replace('\\','/')
    if is_dir: norm=norm.rstrip('/')
    p=PurePosixPath(norm)
    return (bool(norm) and '\x00' not in norm and not p.is_absolute()
            and not re.match(r'^[A-Za-z]:',norm) and not norm.startswith('//')
            and '..' not in p.parts and '' not in norm.split('/'))

def inspect_zip(path, limits=None):
    lim={**DEFAULT_LIMITS,**(limits or {})}; result={'safe':True,'member_count':0,'total_uncompressed':0,'issues':[],'members':[]}
    with zipfile.ZipFile(path,'r') as z:
        infos=z.infolist(); result['member_count']=len(infos)
        if len(infos)>lim['max_entries']:
            result['safe']=False; result['issues'].append({'code':'entry_limit'})
        seen=set()
        for inf in infos:
            n=inf.filename; mode=(inf.external_attr>>16)&0xffff; ftype=stat.S_IFMT(mode)
            issue=[]
            if not _member_safe(n,inf.is_dir()): issue.append('unsafe_path')
            canonical=n.replace('\\','/').rstrip('/') if inf.is_dir() else n.replace('\\','/')
            if ftype==stat.S_IFLNK: issue.append('symlink')
            elif ftype not in (0,stat.S_IFREG,stat.S_IFDIR): issue.append('special_file')
            # Backslash/slash and case collisions can overwrite the same path on
            # Windows/macOS filesystems even when the ZIP member strings differ.
            if canonical.casefold() in seen: issue.append('duplicate_path')
            seen.add(canonical.casefold())
            if inf.flag_bits&1: issue.append('encrypted')
            if inf.file_size>lim['max_single_file']: issue.append('single_file_limit')
            ratio=inf.file_size/max(inf.compress_size,1)
            if inf.file_size>1024*1024 and ratio>lim['max_ratio']: issue.append('compression_ratio')
            result['total_uncompressed']+=inf.file_size
            if issue:
                result['safe']=False
                for code in issue: result['issues'].append({'code':code})
            result['members'].append({'path':n,'size_bytes':inf.file_size,'compressed_bytes':inf.compress_size,'is_dir':inf.is_dir()})
        if result['total_uncompressed']>lim['max_total_uncompressed']:
            result['safe']=False; result['issues'].append({'code':'total_size_limit'})
    return result

def safe_extract_zip(path,destination,limits=None):
    audit=inspect_zip(path,limits)
    if not audit['safe']: raise ValueError('ZIP archive failed safety inspection: '+','.join(sorted({x['code'] for x in audit['issues']})))
    root=Path(destination).resolve(); root.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(path,'r') as z:
        for inf in z.infolist():
            pp=PurePosixPath(inf.filename.replace('\\','/'))
            dest=(root/Path(*pp.parts)).resolve()
            if dest!=root and root not in dest.parents: raise ValueError('Archive path escaped destination')
            if inf.is_dir(): dest.mkdir(parents=True,exist_ok=True); continue
            dest.parent.mkdir(parents=True,exist_ok=True)
            with z.open(inf,'r') as src, open(dest,'xb') as out:
                written=0
                while True:
                    block=src.read(1024*1024)
                    if not block: break
                    written+=len(block)
                    if written>inf.file_size: raise ValueError('ZIP entry exceeded declared size')
                    out.write(block)
                if written!=inf.file_size: raise ValueError('ZIP entry size mismatch')
    return audit

def sha256_file(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()

def sniff_mime(path):
    p=Path(path); ext=p.suffix.lower()
    with p.open('rb') as f: b=f.read(64)
    if b.startswith(b'\xff\xd8\xff'): return 'image/jpeg'
    if b.startswith(b'\x89PNG\r\n\x1a\n'): return 'image/png'
    if b.startswith((b'GIF87a',b'GIF89a')): return 'image/gif'
    if len(b)>=12 and b[:4]==b'RIFF' and b[8:12]==b'WEBP': return 'image/webp'
    if b.startswith(b'OggS'): return 'audio/ogg'
    if b.startswith(b'ID3') or (len(b)>1 and b[0]==0xff and b[1] in (0xfb,0xf3,0xf2)): return 'audio/mpeg'
    if len(b)>=12 and b[4:8]==b'ftyp': return 'video/mp4'
    if b.startswith(b'%PDF-'): return 'application/pdf'
    if ext=='.vcf' or b'BEGIN:VCARD' in b[:64]: return 'text/vcard'
    if ext in ('.html','.htm','.svg','.xhtml','.xml','.js','.mjs'): return 'application/x-untrusted-active-content'
    if ext in ('.zip','.7z','.rar'): return 'application/x-untrusted-archive'
    return mimetypes.guess_type(p.name)[0] or 'application/octet-stream'

def category_for(path,mime):
    p=Path(path); name=p.name.upper(); ext=p.suffix.lower()
    # Some exports place an audio asset in an .mp4 container under an `audio/`
    # directory (and may name it AUD-*). Preserve the audio role separately from
    # the container MIME; the message's JSON source key is the strongest evidence.
    if mime=='video/mp4' and (p.parent.name.casefold() in ('audio','audio_files') or name.startswith('AUD-')):
        return 'audio-container-mp4'
    if mime=='application/x-untrusted-active-content': return 'untrusted-active-content'
    if mime=='application/x-untrusted-archive': return 'nested-archive-untrusted'
    if mime.startswith('image/'):
        if name.startswith('STK-'): return 'sticker'
        return 'photo'
    if mime.startswith('video/'): return 'video'
    if mime.startswith('audio/'):
        if name.startswith('PTT-'): return 'probable-voice-note'
        return 'audio'
    if mime=='application/pdf': return 'document'
    if mime=='text/vcard': return 'contact-card'
    if mime.startswith('text/'): return 'document'
    return 'unknown'

def _is_metadata_file(rel):
    name=Path(rel).name.lower()
    if re.fullmatch(r'message_\d+\.json',name): return True
    if name.startswith('whatsapp chat with ') and name.endswith('.txt'): return True
    return False

def inventory_assets(root, hash_files=True):
    """Inventory every non-metadata file, including extensionless/unknown attachments."""
    root=Path(root).resolve(); assets=[]
    for p in sorted(root.rglob('*')):
        if p.is_symlink() or not p.is_file(): continue
        try: rel=p.resolve().relative_to(root).as_posix()
        except ValueError: continue
        if _is_metadata_file(rel): continue
        mime=sniff_mime(p); category=category_for(p,mime); size=p.stat().st_size
        digest=sha256_file(p) if hash_files else None
        path_tag=hashlib.sha256(rel.encode('utf-8')).hexdigest()[:10]
        asset_id=f'asset:{digest[:16] if digest else "nohash"}:{path_tag}'
        upper=p.name.upper(); hint=None
        if upper.startswith('PTT-'): hint='probable_voice_note_by_filename_prefix'
        elif upper.startswith('STK-'): hint='probable_sticker_by_filename_prefix'
        elif upper.startswith('VID-'): hint='video_file_not_proven_round_video_note'
        elif upper.startswith('AUD-'): hint='audio_file_by_filename_prefix'
        elif upper.startswith('IMG-'): hint='photo_by_filename_prefix'
        assets.append({'asset_id':asset_id,'relative_path':rel,'filename':p.name,'size_bytes':size,
                       'sha256':digest,'mime_type':mime,'category':category,'subtype_hint':hint,
                       'status':'present-not-inspected','safe_inline_preview':category in ('photo','sticker','video','audio','probable-voice-note','audio-container-mp4')})
    hashes=collections.defaultdict(list)
    for a in assets:
        if a['sha256']: hashes[a['sha256']].append(a['asset_id'])
    for ids in hashes.values():
        if len(ids)>1:
            for a in assets:
                if a['asset_id'] in ids: a['duplicate_content_group']=ids[0]
    return assets

def link_whatsapp_attachments(events,assets):
    by_name=collections.defaultdict(list)
    for a in assets: by_name[a['filename'].casefold()].append(a)
    linked=[]; missing=[]; ambiguous=[]
    for e in events:
        refs=e.get('attachment_refs') or []
        if not refs: continue
        resolved=[]; unresolved=[]; candidates=[]
        for ref in refs:
            hits=by_name.get(Path(ref).name.casefold(),[])
            if len(hits)==1: resolved.append(hits[0])
            elif len(hits)>1: candidates.extend(hits); ambiguous.append({'event_id':e['event_id']})
            else: unresolved.append(ref); missing.append(ref)
        if resolved:
            e['asset_refs']=[x['asset_id'] for x in resolved]
            e['attachment_status']='present-not-inspected'
            kinds={x['category'] for x in resolved}
            e['attachment_types']=sorted(kinds)
            if e['kind'] in ('text','unknown') and len(kinds)==1:
                kind=next(iter(kinds))
                e['kind']={'photo':'photo','sticker':'sticker','video':'video','audio':'audio','probable-voice-note':'audio','audio-container-mp4':'audio','document':'document','contact-card':'contact','unknown':'unknown','untrusted-active-content':'document','nested-archive-untrusted':'document'}.get(kind,'unknown')
        if unresolved:
            e['unresolved_attachment_refs']=unresolved
            if resolved: e['attachment_status']='partially-resolved'
            else: e['attachment_status']='referenced-but-missing'
        if candidates:
            e['attachment_candidate_refs']=[x['asset_id'] for x in candidates]
            e['attachment_status']='ambiguous-match'
        linked.extend({'event_id':e['event_id'],'asset_id':x['asset_id']} for x in resolved)
    referenced={asset_id for e in events for asset_id in e.get('asset_refs',[])}
    summary={'attachment_reference_occurrences':sum(len(e.get('attachment_refs') or []) for e in events),
             'distinct_missing_names':len({x for x in missing}),
             'events_with_asset_links':sum(bool(e.get('asset_refs')) for e in events),
             'asset_link_occurrences':len(linked),'distinct_assets_linked':len(referenced),
             'missing_reference_occurrences':len(missing),'ambiguous_events':len(ambiguous),
             'unlinked_asset_count':len(assets)-len(referenced)}
    return events,summary

def link_instagram_attachments(events,assets):
    by_path={a['relative_path']:a for a in assets}; linked=[]; missing=[]; unsafe=[]
    for e in events:
        resolved=[]; unresolved=[]
        for att in e.get('attachments') or []:
            uri=str(att.get('uri','')).replace('\\','/')
            pp=PurePosixPath(uri)
            if pp.is_absolute() or '..' in pp.parts or re.match(r'^[A-Za-z]:',uri):
                unsafe.append(e['event_id']); unresolved.append(uri); continue
            path='/'.join(part for part in pp.parts if part not in ('','.'))
            asset=by_path.get(path)
            if asset:
                item={**att,'asset_id':asset['asset_id'],'asset_category':asset['category'],
                      'container_mime_type':asset['mime_type'],
                      'render_role':att.get('kind','unknown'),
                      'role_container_mismatch':bool(att.get('kind')=='audio' and asset['category'] in ('video','audio-container-mp4'))}
                resolved.append(item); linked.append({'event_id':e['event_id'],'asset_id':asset['asset_id']})
            else:
                unresolved.append(uri); missing.append({'event_id':e['event_id'],'kind':att.get('kind'),'uri_missing':True})
        if resolved:
            e['resolved_attachments']=resolved
            e['asset_refs']=[x['asset_id'] for x in resolved]
            e['attachment_status']='present-not-inspected' if not unresolved else 'partially-resolved'
        elif e.get('attachments'):
            e['attachment_status']='referenced-but-missing'
        if unresolved: e['unresolved_attachment_refs']=unresolved
    referenced={x['asset_id'] for x in linked}
    summary={'attachment_reference_count':sum(len(e.get('attachments') or []) for e in events),
             'reference_occurrences_linked':len(linked),'distinct_assets_linked':len(referenced),
             'missing_reference_occurrences':len(missing),'unsafe_references':len(unsafe),
             'unlinked_asset_count':len(assets)-len(referenced)}
    return events,summary

def _selftest():
    import tempfile
    from pathlib import Path
    ok=True
    def check(label,condition):
        nonlocal ok; ok &= bool(condition); print(('PASS ' if condition else 'FAIL ')+label)
    with tempfile.TemporaryDirectory() as td:
        root=Path(td); (root/'photos').mkdir(); (root/'audio').mkdir()
        (root/'photos'/'one.jpg').write_bytes(b'\xff\xd8\xff'+b'0'*20)
        (root/'audio'/'note.opus').write_bytes(b'OggS'+b'0'*20)
        (root/'audio'/'clip.mp4').write_bytes(b'0000ftypisom'+b'0'*20)
        (root/'unknown.bin').write_bytes(b'unknown bytes')
        assets=inventory_assets(root)
        check('inventory includes known, container-ambiguous and unknown files',len(assets)==4 and {a['category'] for a in assets}=={'photo','audio','audio-container-mp4','unknown'})
        wa=[{'event_id':'w1','attachment_refs':['one.jpg'],'kind':'unknown'}]
        _,ws=link_whatsapp_attachments(wa,assets)
        check('WhatsApp exact filename linking works',ws['distinct_assets_linked']==1 and wa[0]['attachment_status']=='present-not-inspected')
        ig=[{'event_id':'i1','attachments':[{'uri':'audio/note.opus','kind':'audio'}]},
            {'event_id':'i2','attachments':[{'uri':'audio/clip.mp4','kind':'audio'}]}]
        _,igs=link_instagram_attachments(ig,assets)
        check('Instagram exact relative path linking works',igs['distinct_assets_linked']==2)
        check('Instagram audio role preserved when container signature is video/mp4',ig[1]['resolved_attachments'][0]['render_role']=='audio' and ig[1]['resolved_attachments'][0]['container_mime_type']=='video/mp4')
        check('unknown attachment is retained',any(a['filename']=='unknown.bin' for a in assets))
        good=root/'good.zip'
        with zipfile.ZipFile(good,'w') as z:
            z.writestr('folder/','')
            z.writestr('folder/a.txt','ok')
        check('safe ZIP with standard directory entries accepted',inspect_zip(good)['safe'])
        extracted=root/'extracted'; safe_extract_zip(good,extracted)
        check('standard directory entry extracted correctly',(extracted/'folder'/'a.txt').read_text()=='ok')
        collision=root/'collision.zip'
        with zipfile.ZipFile(collision,'w') as z:
            z.writestr('folder\\asset.bin','one')
            z.writestr('folder/asset.bin','two')
        check('slash/backslash path collision rejected',not inspect_zip(collision)['safe'])
        bad=root/'bad.zip'
        with zipfile.ZipFile(bad,'w') as z: z.writestr('../escape.txt','bad')
        check('path traversal rejected',not inspect_zip(bad)['safe'])
    return 0 if ok else 1

if __name__=='__main__':
    import sys
    if '--selftest' in sys.argv: raise SystemExit(_selftest())
    print(__doc__)
