"""Independent, read-only structural checks for the v8 review documents.

This script extracts evidence only; scientific interpretation is reviewed manually.
It does not mutate either DOCX.
"""
from pathlib import Path
import hashlib
import json
import re
import zipfile
import io
from collections import Counter

from docx import Document
from PIL import Image

ROOT = Path('/workspace/bmt_v8')
BASE = json.loads((ROOT / 'evidence/base_documents.json').read_text())
MAIN = ROOT / 'outputs/BMT_main_manuscript_v8.docx'
SUPP = ROOT / 'outputs/BMT_supplementary_material_v4.docx'


def norm(s):
    return re.sub(r'\s+', ' ', s.replace('\\u202f', ' ').replace('\u202f', ' ')).strip()


def words(s):
    return re.findall(r"\b[\w]+(?:[’'−–-][\w]+)*\b", s)


def supplemental_citation_order(text, kind):
    out = []
    pattern = rf'{kind}s?\s+(S\d+(?:\s*(?:,|and|[–-])\s*(?:S)?\d+)*)'
    for match in re.finditer(pattern, text):
        group = match[1]
        nums = []
        for token in re.split(r'\s*(?:,|and)\s*', group):
            limits = re.findall(r'\d+', token)
            nums.extend(range(int(limits[0]), int(limits[1])+1) if len(limits)==2 else [int(limits[0])])
        for n in nums:
            if n not in out:
                out.append(n)
    return out


def extract(path):
    doc = Document(path)
    paras = [{'i': i, 'style': p.style.name, 'text': p.text} for i, p in enumerate(doc.paragraphs)]
    tables = [[[c.text for c in r.cells] for r in t.rows] for t in doc.tables]
    sects = [{'width_in': s.page_width.inches, 'height_in': s.page_height.inches,
              'top_in': s.top_margin.inches, 'bottom_in': s.bottom_margin.inches,
              'left_in': s.left_margin.inches, 'right_in': s.right_margin.inches}
             for s in doc.sections]
    with zipfile.ZipFile(path) as z:
        media = [n for n in z.namelist() if n.startswith('word/media/')]
        tracked = any(k in z.read('word/document.xml') for k in [b'<w:ins ', b'<w:del '])
        image_metadata = []
        for name in media:
            try:
                im = Image.open(io.BytesIO(z.read(name)))
                image_metadata.append({'name':name,'pixels':im.size,'format':im.format,'dpi':im.info.get('dpi')})
            except Exception as exc:
                image_metadata.append({'name':name,'error':str(exc)})
    fonts = Counter((r.font.name, r.font.size.pt if r.font.size else None)
                    for p in doc.paragraphs for r in p.runs if r.text.strip())
    shape_dimensions = [{'width_in':sh.width.inches,'height_in':sh.height.inches} for sh in doc.inline_shapes]
    return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'paragraphs': paras, 'tables': tables, 'sections': sects,
            'inline_shapes': len(doc.inline_shapes), 'media_files': media,
            'image_metadata':image_metadata,'shape_dimensions':shape_dimensions,
            'explicit_run_font_counts':[{'font':k[0],'size_pt':k[1],'runs':v} for k,v in fonts.items()],
            'tracked_insertions_or_deletions': tracked}


def main():
    data = {'main': extract(MAIN), 'supplement': extract(SUPP)}
    m = data['main']; s = data['supplement']
    mp = [p['text'] for p in m['paragraphs']]
    sp = [p['text'] for p in s['paragraphs']]
    mt = '\n'.join(mp); st = '\n'.join(sp)
    base = BASE['BMT_main_manuscript_v7.docx']
    brefs = [p['text'] for p in base['paragraphs'] if re.match(r'^\d+\.\s', p['text'])]
    mrefs = [p for p in mp if re.match(r'^\d+\.\s', p)]
    old_contents = [norm(re.sub(r'^\d+\.\s*', '', p)) for p in brefs]
    new_contents = [norm(re.sub(r'^\d+\.\s*', '', p)) for p in mrefs]
    # Repository availability necessarily updates the source-commit address; report
    # that old content separately for manual provenance review.
    ref_retained = [x in new_contents for x in old_contents]
    eq_tables = [
        [[norm(c) for c in row] for row in old] ==
        [[norm(c) for c in row] for row in new]
        for old, new in zip(base['tables'], m['tables'][:3])
    ]
    old_supp_tables = BASE['BMT_supplementary_material_v3.docx']['tables']
    supp_tables_equal = [
        [[norm(c) for c in row] for row in old] ==
        [[norm(c) for c in row] for row in new]
        for old, new in zip(old_supp_tables, s['tables'][:9])
    ]
    ab_start = mp.index('Abstract') + 1
    ab_end = next(i for i in range(ab_start, len(mp)) if mp[i].startswith('Keywords'))
    abstract = '\n'.join(mp[ab_start:ab_end])
    intro = mp.index('Introduction')
    body_end = next(i for i in range(intro, len(mp)) if mp[i] in ['Acknowledgments', 'Acknowledgements'])
    refs_start = mp.index('References')
    body = '\n'.join(mp[intro:body_end])
    before_refs = '\n'.join(mp[:refs_start])
    cit_nums = []
    for group in re.findall(r'\[([0-9,–\- ]+)\]', before_refs):
        for token in re.split(r'\s*,\s*', group):
            pair = re.match(r'^(\d+)\s*[–-]\s*(\d+)$', token)
            ns = range(int(pair[1]), int(pair[2])+1) if pair else [int(token.strip())]
            for n in ns:
                if n not in cit_nums:
                    cit_nums.append(n)
    main_figs = [p for p in mp if re.match(r'^Figure\s+\d+\.', p)]
    main_tabs = [p for p in mp if re.match(r'^Table\s+\d+\.', p)]
    supp_figs = [p for p in sp if re.match(r'^Figure\s+S\d+(?:\s*\([A-Z]\))?\.', p)]
    supp_fig_nums = sorted({int(re.match(r'^Figure\s+S(\d+)',p)[1]) for p in supp_figs})
    supp_tabs = [p for p in sp if re.match(r'^Table\s+S\d+\.', p)]
    checks = {
        'h1_h3_original_main_tables_unchanged': eq_tables,
        'original_supplement_s1_s9_tables_unchanged': supp_tables_equal,
        'original_reference_content_retained': ref_retained,
        'reference_count': len(mrefs),
        'reference_numbers': [int(re.match(r'^(\d+)', p)[1]) for p in mrefs],
        'citation_first_occurrence': cit_nums,
        'supplement_table_citation_first_occurrence': supplemental_citation_order(before_refs,'Table'),
        'supplement_figure_citation_first_occurrence': supplemental_citation_order(before_refs,'Figure'),
        'abstract_word_count_with_labels': len(words(abstract)),
        'main_body_word_count_excluding_acknowledgments_references_captions_tables': len(words(body)),
        'abstract_labels_present': [f'{x} ' in abstract for x in ['Objectives','Methods','Results','Conclusions']],
        'postal_400016_present': '400016' in mt,
        'old_postal_401331_absent': '401331' not in mt+st,
        'main_figure_caption_count': len(main_figs),
        'main_table_caption_count': len(main_tabs),
        'supplement_figure_caption_count': len(supp_figs),
        'supplement_logical_figure_numbers': supp_fig_nums,
        'supplement_table_caption_count': len(supp_tabs),
        'main_figure_captions': main_figs,
        'main_table_captions': main_tabs,
        'supplement_figure_captions': supp_figs,
        'supplement_table_captions': supp_tabs,
        'em_dash_count': (mt+st).count('—'),
        'replacement_character_count': (mt+st).count('\ufffd'),
        'high_risk_terms': [p for p in mp+sp if re.search(r'(?i)\b(TODO|TBD|placeholder|insert here|approved|approval|superior|independent validation|bit.identical|pixel.identical)\b',p)],
        'posthoc_paragraphs': [p for p in mp+sp if re.search(r'(?i)post[ -]hoc', p)],
        'bootstrap_frequency_mentions': {v: v in mt+st for v in ['39.61','90.40','30.94']},
        'cpu_difference_mentions': {v: v in mt+st for v in ['0.001435','0.000096','9.610']},
        'raw_id_mentions': [p for p in mp+sp if re.search(r'(?i)(patient_id|replica|lexicograph|deduplic|duplicate|draw.position)', p)],
    }
    data['checks'] = checks
    out = ROOT / 'qa/structural_extraction.json'
    out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    for key in ['main','supplement']:
        (ROOT / f'qa/{key}_extracted.txt').write_text('\n'.join(p['text'] for p in data[key]['paragraphs'])+'\n')
    print(json.dumps(checks,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
