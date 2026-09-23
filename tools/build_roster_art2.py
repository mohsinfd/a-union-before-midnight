"""Stage individual officer portraits; never alter gameplay fields or saves.

Partial stages are useful for visual QA but cannot be installed. The complete
375-reserve/9-historical manifest is required by default. Native UI not tested.
"""
from pathlib import Path
from collections import defaultdict
import argparse
import hashlib
import io
import json
import re
from PIL import Image, ImageOps, ImageDraw
import build_balance1 as b
from audit_roster_art import ROOT, MOD

BUILD = ROOT / 'build/art2'
ASSETS = ROOT / 'assets/roster-art2'
REL = 'db/leaders/india.csv'
RESERVE_IDS = set(range(252000, 252375))
HISTORICAL_IDS = {251018, 251019, 251020, 251021, 251022, 251023, 251025, 251107, 251108}
KEEP_COUNT = 64


def read_json(path):
    return json.loads(path.read_text(encoding='utf8'))


def validate_generation_metadata(metadata, ident):
    if metadata.get('id') != ident:
        raise ValueError('Generated metadata identity mismatch: ' + str(ident))
    if metadata.get('mode') != 'built-in image_gen':
        raise ValueError('Expected built-in image generation provenance: ' + str(ident))
    if not isinstance(metadata.get('prompt'), str) or not metadata['prompt'].strip():
        raise ValueError('Generation prompt missing: ' + str(ident))


def rows(text):
    """Locate columns by the actual native header, never a guessed offset."""
    lines = text.splitlines(keepends=True)
    header = next((line.strip().split(';') for line in lines
                   if line.lower().startswith('name;id;')), None)
    if header is None:
        raise ValueError('Native leader header missing')
    columns = {name.lower(): index for index, name in enumerate(header)}
    for name in ('name', 'id', 'picture', 'type'):
        if name not in columns:
            raise ValueError('Missing header column ' + name)
    result = {}
    for index, line in enumerate(lines):
        cells = line.split(';')
        if len(cells) > columns['id'] and cells[columns['id']].isdigit():
            ident = int(cells[columns['id']])
            if ident in result or len(cells) != len(header):
                raise ValueError('Duplicate ID or malformed row: ' + str(ident))
            result[ident] = (index, cells)
    return lines, columns, result


def change_pictures(text, mapping):
    lines, col, records = rows(text)
    if set(mapping) - set(records):
        raise ValueError('Picture mapping contains missing leader IDs')
    for ident, picture in mapping.items():
        if not re.fullmatch(r'[A-Za-z0-9_]+', picture):
            raise ValueError('Unsafe portrait basename')
        index, cells = records[ident]
        cells[col['picture']] = picture
        lines[index] = ';'.join(cells)
    return ''.join(lines)


def verify_picture_only(before, after, allowed):
    a, ac, ar = rows(before)
    z, zc, zr = rows(after)
    if len(a) != len(z) or ac != zc or ar.keys() != zr.keys():
        raise ValueError('Roster structure changed')
    reverted = change_pictures(after, {
        ident: ar[ident][1][ac['picture']] for ident in allowed})
    if reverted != before:
        raise ValueError('A non-picture field or unapproved row changed')


def pack(source, crop=None):
    with Image.open(source) as original:
        im = ImageOps.exif_transpose(original).convert('RGB')
    if crop is not None:
        if len(crop) != 4 or not (0 <= crop[0] < crop[2] <= 1 and
                                 0 <= crop[1] < crop[3] <= 1):
            raise ValueError('Crop must be normalized left/top/right/bottom')
        im = im.crop(tuple(round(v * size) for v, size in
                           zip(crop, (im.width, im.height, im.width, im.height))))
    im = ImageOps.fit(im, (36, 50), method=Image.Resampling.LANCZOS)
    output = io.BytesIO()
    im.save(output, format='BMP')
    data = output.getvalue()
    if data[:2] != b'BM' or int.from_bytes(data[28:30], 'little') != 24:
        raise ValueError('Expected native 24-bit BMP')
    return data


def picture_path(mod, picture):
    if not re.fullmatch(r'[A-Za-z0-9_]+', picture):
        raise ValueError('Unsafe existing portrait reference')
    for root in (mod, mod.parents[1]):
        path = b.safe(root, 'gfx/interface/pics/' + picture + '.bmp')
        if path.is_file():
            return path
    raise ValueError('Unresolved portrait: ' + picture)


def image_metrics(data):
    with Image.open(io.BytesIO(data)) as image:
        im = image.convert('RGB')
    if im.size != (36, 50):
        raise ValueError('Wrong native portrait size: ' + str(im.size))
    small = im.convert('L').resize((9, 8), Image.Resampling.LANCZOS)
    pixels = list(small.tobytes())
    bits = sum((pixels[y*9+x] > pixels[y*9+x+1]) << (y*8+x)
               for y in range(8) for x in range(8))
    return im, hashlib.sha256(im.tobytes()).hexdigest(), bits


def snapshot(mod, build):
    manifest = build / 'baseline.json'
    if manifest.exists():
        info = read_json(manifest)
        if Path(info['installation']).resolve() != mod.resolve():
            raise ValueError('Baseline belongs to a different installation')
        base = {}
        for rel, digest in info['files'].items():
            data = b.safe(build / 'baseline', rel).read_bytes()
            if b.sha(data) != digest:
                raise ValueError('Immutable baseline corrupted: ' + rel)
            base[rel] = data.decode('latin1')
        return base
    data = b.safe(mod, REL).read_bytes()
    dest = b.safe(build / 'baseline', REL)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    b.dump(manifest, {'installation': str(mod.resolve()), 'files': {REL: b.sha(data)}})
    return {REL: data.decode('latin1')}


def contact_sheets(images, destination):
    destination.mkdir(parents=True, exist_ok=True)
    result = []
    ordered = sorted(images.items())
    for page in range((len(ordered) + 79) // 80):
        sheet = Image.new('RGB', (800, 8*130), '#202020')
        draw = ImageDraw.Draw(sheet)
        for index, (ident, im) in enumerate(ordered[page*80:(page+1)*80]):
            x, y = (index % 10)*80, (index // 10)*130
            sheet.paste(im.resize((72, 100), Image.Resampling.NEAREST), (x+4, y+4))
            draw.text((x+5, y+108), str(ident), fill='white')
        target = destination / ('officers-%02d.png' % (page+1))
        sheet.save(target)
        result.append(str(target))
    return result


def stage(mod=MOD, build=BUILD, assets=ASSETS, historical=None):
    historical = historical or ROOT / 'tools/data/roster_art2_historical.json'
    plan = read_json(assets / 'plan.json')
    entries = plan['entries'] if isinstance(plan, dict) else plan
    if len(entries) != len(RESERVE_IDS) or {e['id'] for e in entries} != RESERVE_IDS:
        raise ValueError('Plan must contain each reserve exactly once')
    if sum(bool(e['keep']) for e in entries) != KEEP_COUNT:
        raise ValueError('Plan must preserve exactly 64 existing unique faces')
    base = snapshot(mod, build)
    out = dict(base)
    _, columns, records = rows(base[REL])
    mapping, pending, errors, provenance = {}, [], [], []
    hist = read_json(historical)['entries'] if historical.exists() else []
    historical_ids = {e['id'] for e in hist}
    if len(historical_ids) != len(hist) or historical_ids - HISTORICAL_IDS:
        raise ValueError('Historical manifest has duplicate or unexpected IDs')
    if historical_ids != HISTORICAL_IDS:
        pending.append('Historical manifest incomplete: missing ' + str(sorted(HISTORICAL_IDS-historical_ids)))
    if any(e['id'] in RESERVE_IDS for e in hist):
        raise ValueError('Historical manifest overlaps fictional reserves')
    for entry in entries + hist:
        ident = entry['id']
        if ident not in records:
            raise ValueError('Unknown planned leader ' + str(ident))
        old = records[ident][1]
        if entry.get('name') != old[columns['name']]:
            raise ValueError('Identity/name mismatch: ' + str(ident))
        if ident in RESERVE_IDS:
            if old[columns['picture']] != entry['existing_picture']:
                raise ValueError('Plan does not match baseline portrait: ' + str(ident))
            if entry['keep']:
                continue
            source = b.safe(assets, f'reserves/{ident}.png')
            metadata = b.safe(assets, f'reserves/{ident}.json')
            if not source.exists() or not metadata.exists():
                pending.append('Reserve ' + str(ident))
                continue
            meta = read_json(metadata)
            validate_generation_metadata(meta, ident)
            picture = f'AUBM_R2_{ident}'
        else:
            if not entry.get('identity_verified') or not entry.get('source'):
                pending.append('Unverified historical ' + str(ident))
                continue
            source = b.safe(ROOT, entry['source'])
            if not source.exists():
                pending.append('Historical source ' + str(ident))
                continue
            if entry.get('redistributable') is False and not source.is_relative_to((ROOT/'build/art2/restricted-history').resolve()):
                raise ValueError('Restricted historical image must stay in private build/art2/restricted-history')
            meta = entry
            picture = entry.get('picture', f'AUBM_R2_H{ident}')
        if not re.fullmatch(r'AUBM_R2_(?:H)?[0-9]+', picture):
            raise ValueError('Out-of-scope new portrait name')
        rel = 'gfx/interface/pics/' + picture + '.bmp'
        if rel in out:
            raise ValueError('Two entries target the same new image')
        out[rel] = pack(source, entry.get('crop')).decode('latin1')
        mapping[ident] = picture
        provenance.append({'id': ident, 'picture': picture, 'source': str(source),
                           'source_sha256': b.sha(source.read_bytes()), 'metadata': meta})
    out[REL] = change_pictures(base[REL], mapping)
    verify_picture_only(base[REL], out[REL], set(mapping))
    if change_pictures(out[REL], mapping) != out[REL]:
        raise ValueError('Portrait transformation is not idempotent')
    _, col, after = rows(out[REL])
    images, hashes, fingerprints = {}, defaultdict(list), {}
    preserved = []
    for ident in sorted(RESERVE_IDS | {e['id'] for e in hist}):
        picture = after[ident][1][col['picture']]
        rel = 'gfx/interface/pics/' + picture + '.bmp'
        data = out[rel].encode('latin1') if rel in out else picture_path(mod, picture).read_bytes()
        im, digest, fingerprint = image_metrics(data)
        images[ident], fingerprints[ident] = im, fingerprint
        hashes[digest].append(ident)
        if any(e['id'] == ident and e['keep'] for e in entries):
            preserved.append(digest)
    if len(set(preserved)) != KEEP_COUNT:
        errors.append('Preserved faces are not individually unique')
    duplicates = [ids for ids in hashes.values() if len(ids) > 1]
    if duplicates and not pending:
        errors.append('Exact duplicate portrait pixels remain')
    warnings = []
    ids = sorted(fingerprints)
    for i, one in enumerate(ids):
        for two in ids[i+1:]:
            distance = (fingerprints[one] ^ fingerprints[two]).bit_count()
            if distance <= 4:
                warnings.append({'ids': [one, two], 'difference_hash_distance': distance})
    report = dict(passed=not errors and not pending, partial=bool(pending),
                  errors=errors, pending=pending, reserve_total=len(RESERVE_IDS),
                  reserves_generated=sum(ident in RESERVE_IDS for ident in mapping),
                  reserves_retained=KEEP_COUNT, historical_installed_candidates=len(mapping)-sum(ident in RESERVE_IDS for ident in mapping),
                  unique_pixel_hashes=len(hashes), duplicate_pixels=duplicates,
                  perceptual_review_candidates=warnings,
                  visual_review_note='Exact hashes do not prove distinct faces; inspect native-size contact sheets before release.',
                  gameplay_fields_unchanged=True,
                  native_playtested=False, provenance=provenance,
                  contact_sheets=contact_sheets(images, build / 'contact-sheets'))
    report['private_only_picture_ids'] = [e['id'] for e in provenance if e['metadata'].get('redistributable') is False]
    report['public_distribution_note'] = 'Use public-delta only; private delta and contact sheets may contain uncleared historical photographs.'
    for rel, content in out.items():
        if base.get(rel) != content:
            dst = b.safe(build / 'delta', rel)
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(content.encode('latin1'))
    b.dump(build / 'validation.json', report)
    b.dump(build / 'manifest.json', {'files': {rel: b.sha(t.encode('latin1')) for rel,t in out.items() if base.get(rel) != t}})
    public = public_output(base, out, report)
    for rel, content in public.items():
        if base.get(rel) != content:
            dst = b.safe(build/'public-delta', rel)
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(content.encode('latin1'))
    b.dump(build/'public-manifest.json', {'excluded_private_ids':report['private_only_picture_ids'],
        'files': {rel:b.sha(t.encode('latin1')) for rel,t in public.items() if base.get(rel)!=t},
        'partial':report['partial'], 'note':'Private historical replacements omitted; their original baseline references retained.'})
    return base, out, report


def public_output(base, out, report):
    """Exclude restricted binaries AND remove dangling CSV references to them."""
    public = dict(out)
    _, columns, original = rows(base[REL])
    revert = {}
    for item in report.get('provenance', []):
        if item['metadata'].get('redistributable') is not False:
            continue
        public.pop('gfx/interface/pics/' + item['picture'] + '.bmp', None)
        revert[item['id']] = original[item['id']][1][columns['picture']]
    public[REL] = change_pictures(public[REL], revert)
    return public


def install(mod, base, out, report, build=BUILD):
    if not report['passed'] or report.get('partial'):
        raise ValueError('Full artwork completion is required; partial installation refused')
    if all(b.safe(mod, rel).is_file() and b.safe(mod, rel).read_bytes() == value.encode('latin1')
           for rel, value in out.items()):
        return {'already_installed': True, 'files': len(out), 'saves_unchanged': True}
    previous = b.BUILD, b.VERSION
    try:
        b.BUILD, b.VERSION = build, '27-ROSTER1 + ART1 teams + ART2 officers'
        return b.install(mod, base, out, report, 'AUBM_ART2_INSTALL_RECEIPT.json')
    finally:
        b.BUILD, b.VERSION = previous


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--mod', type=Path, default=MOD)
    ap.add_argument('--install', action='store_true')
    args = ap.parse_args()
    base, out, report = stage(args.mod)
    print(json.dumps({key:value for key,value in report.items()
                      if key not in ('provenance', 'perceptual_review_candidates', 'duplicate_pixels')}, indent=2))
    if args.install:
        print(json.dumps(install(args.mod, base, out, report), indent=2))


if __name__ == '__main__':
    main()
