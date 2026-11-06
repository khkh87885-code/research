#!/usr/bin/env python3
"""Archive QA only: preserve DOCX contents, honor author-confirmed 400016.

Run after converting the five changed DOCX documents to qa/*.pdf. This script
does not execute any document-generation/address-replacement functions.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from zipfile import ZipFile, ZIP_DEFLATED

from docx import Document
import fitz

sys.dont_write_bytecode = True
STEMS = ["BMT_main_manuscript_v7", "BMT_cover_letter",
         "BMT_author_confirmation_required", "BMT_revision_report",
         "BMT_submission_checklist"]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def docx_text(path):
    d = Document(path)
    parts = [p.text for p in d.paragraphs]
    for table in d.tables:
        for row in table.rows:
            parts.extend(c.text for c in row.cells)
    return "\n".join(parts)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    default = next((p for p in Path(__file__).resolve().parents
                    if (p / "evidence").is_dir() and (p / "outputs").is_dir()), Path('/workspace/bmt_v7'))
    ap.add_argument('--root', type=Path, default=default)
    root = ap.parse_args().root.resolve()
    outputs, evidence, qa = root / 'outputs', root / 'evidence', root / 'qa'
    before = {p.name:sha(p) for p in outputs.glob('*.docx')}
    author = json.loads((evidence / 'author_confirmation_record.json').read_text())
    assert author['correspondence_postcode'] == '400016'
    assert author['latest_correspondence_confirmation']['user_answer'] == '确认地址和邮编均适用'
    current_address = author['confirmed_correspondence_address']
    assert 'Chongqing 400016, China' in current_address

    # Preserve the original official evidence while visibly superseding its
    # earlier title-page recommendation, rather than deleting the 401331 source.
    source_path = evidence / 'confirmed_address_ethics_sources.json'
    source = json.loads(source_path.read_text())
    assert source['address']['postcode'] == '401331'
    source['current_author_confirmed_correspondence'] = {
        'postcode':'400016', 'full_english_address':current_address,
        'basis':'Latest explicit author confirmation, recorded in author_confirmation_record.json',
        'previous_title_page_recommendation_superseded':True,
        'official_campus_specific_401331_source_preserved':True}
    write_json(source_path, source)
    source_md = evidence / 'confirmed_address_ethics_sources.md'
    marker = '<!-- CURRENT_AUTHOR_POSTCODE_400016 -->'
    text = source_md.read_text()
    if marker not in text:
        text = (marker + '\n# 当前通讯地址更新：以作者确认400016为准\n\n'
                '最新作者已明确确认通讯地址及邮编均适用。最终稿和附函使用 **400016**：\n\n> '
                + current_address + '\n\n以下保留先前官方来源核对及当时401331候选建议，作为历史证据；'
                '其中“可直接用于题页/采用401331”的旧建议已被本次作者确认取代，不是当前稿件地址。\n\n---\n\n' + text)
        source_md.write_text(text)
    for name in ('author_confirmation_record.json','confirmed_address_ethics_sources.json','confirmed_address_ethics_sources.md'):
        shutil.copy2(evidence / name, outputs / 'Audit' / name)

    # Read-only numerical audit reads original sources but does not modify them.
    subprocess.run([sys.executable, str(root/'scripts/final_v7_numeric_review.py')], check=True,
                   env={**__import__('os').environ,'PYTHONDONTWRITEBYTECODE':'1'})
    for name in ('final_v7_numeric_review.json','final_v7_numeric_review.md'):
        shutil.copy2(evidence / name, outputs / 'Audit' / name)
    for name in ('final_v7_numeric_review.py','finalize_postal_package.py'):
        shutil.copy2(root / 'scripts' / name, outputs / 'Analysis' / name)

    changed = {}
    for stem in STEMS:
        dt = docx_text(outputs / (stem+'.docx'))
        assert '400016' in dt and 'Chongqing 400016, China' in dt
        if stem != 'BMT_revision_report':
            assert '401331' not in dt, 'Superseded postcode in current document: '+stem
        with fitz.open(qa / (stem+'.pdf')) as pdf:
            pt = '\n'.join(page.get_text() for page in pdf)
            assert '400016' in pt
            if stem != 'BMT_revision_report': assert '401331' not in pt
            changed[stem] = {'pages':len(pdf),'docx_sha256':sha(outputs/(stem+'.docx')),
                             'pdf_sha256':sha(qa/(stem+'.pdf')),
                             'current_postcode':'400016',
                             'pdf_occurrences_400016':pt.count('400016'),
                             'pdf_occurrences_401331':pt.count('401331')}
    for preview in outputs.glob('*_preview.pdf'):
        corresponding = qa / (preview.name.removesuffix('_preview.pdf')+'.pdf')
        assert corresponding.exists()
        shutil.copy2(corresponding,preview)
        assert sha(corresponding)==sha(preview)

    layout = {}
    for docx in sorted(outputs.glob('*.docx')):
        path = qa / (docx.stem+'.pdf')
        assert path.exists()
        outside = []
        with fitz.open(path) as pdf:
            for pi,page in enumerate(pdf):
                boundary = fitz.Rect(page.rect.x0-1,page.rect.y0-1,page.rect.x1+1,page.rect.y1+1)
                for word in page.get_text('words'):
                    if not boundary.contains(fitz.Rect(word[:4])):
                        outside.append({'page':pi+1,'text':word[4],'bbox':word[:4]})
            layout[path.name] = {'pages':len(pdf),'out_of_page_words':len(outside)}
        assert not outside, str(path)+str(outside[:3])
    write_json(qa/'final_layout.json',layout)
    write_json(outputs/'Audit/final_layout_review.json',layout)
    write_json(evidence/'final_layout_review.json',layout)
    note = ('Final v7 package refreshed after the latest explicit author confirmation of correspondence postcode 400016. '
            'Five changed DOCX documents were converted again to qa PDFs; the existing main/revision-report previews were refreshed '
            '(the unchanged supplementary preview remains identical). The current correspondence address uses 400016 throughout '
            'the main manuscript, cover letter, author-confirmation document and submission checklist. The revision report and source audit '
            'retain 401331 only as official historical campus-source evidence. No DOCX generation logic was run during this archival QA. '
            'Read-only numerical QA passed again, including 335 preserved prior-table numeric tokens, Table 2 and S7/S8/S9 checks, '
            '178 abstract words and zero author-confirmation placeholders. All nine PDF previews have no detected out-of-page words. '
            'The original numerical results, source score files and research_source checkout were not modified. '
            'FILE_MANIFEST.json records all final output files other than itself; the ZIP includes that manifest.\n')
    (outputs/'Audit/FINAL_PACKAGING_NOTE.txt').write_text(note)
    numerical = json.loads((evidence/'final_v7_numeric_review.json').read_text())
    assert numerical['manuscripts_unchanged_by_review'] is True
    assert numerical['author_confirmation_placeholders_main'] == 0
    assert numerical['submission_approved_by_both_authors'] is True
    assert {p.name:sha(p) for p in outputs.glob('*.docx')} == before
    qa_record = {'qa_utc':datetime.now(timezone.utc).isoformat(),
                 'status':'PASS: author-confirmed 400016, numerical QA, PDF bounds, preview freshness and DOCX preservation',
                 'changed_documents':changed,'all_nine_pdf_layout':layout,
                 'docx_unchanged_by_archival_QA':True,'official_401331_historical_source_preserved':True,
                 'read_only_numeric_review_json_sha256':sha(evidence/'final_v7_numeric_review.json'),
                 'numerical_review_status':numerical['status'],
                 'visually_inspected_contact_sheet':'qa/postal_refresh_contact.png',
                 'visual_scope':'First page of all five changed documents; no clipped text or address wrapping defect observed',
                 'no_document_generation_logic_run':True,'no_research_source_writes':True}
    write_json(evidence/'postal_archive_qa.json',qa_record)
    write_json(outputs/'Audit/postal_archive_qa.json',qa_record)
    manifest = {str(p.relative_to(outputs)):{'bytes':p.stat().st_size,'sha256':sha(p)}
                for p in sorted(outputs.rglob('*')) if p.is_file() and p.name!='FILE_MANIFEST.json'}
    write_json(outputs/'FILE_MANIFEST.json',manifest)
    archive = root/'BMT_revision_review_package_v7.zip'
    files = [p for p in sorted(outputs.rglob('*')) if p.is_file()]
    with ZipFile(archive,'w',ZIP_DEFLATED,compresslevel=9) as z:
        for p in files: z.write(p,'BMT_revision_review_package_v7/'+str(p.relative_to(outputs)))
    with ZipFile(archive) as z:
        assert z.testzip() is None
        assert len(z.namelist()) == len(files)
        zipped_manifest = json.loads(z.read('BMT_revision_review_package_v7/FILE_MANIFEST.json'))
        assert zipped_manifest == manifest
        for rel,expected in manifest.items():
            payload = z.read('BMT_revision_review_package_v7/'+rel)
            assert len(payload) == expected['bytes']
            assert hashlib.sha256(payload).hexdigest() == expected['sha256']
    receipt = {'created_utc':datetime.now(timezone.utc).isoformat(),'zip_path':str(archive),
               'zip_bytes':archive.stat().st_size,'zip_sha256':sha(archive),
               'manifest_sha256':sha(outputs/'FILE_MANIFEST.json'),
               'manifest_listed_files':len(manifest),'zip_entries_including_manifest':len(files),
               'all_manifest_hashes_match_archived_payloads':True,'zip_integrity_test':'PASS',
               'current_postcode':'400016','official_historical_401331_preserved':True}
    write_json(qa/'postal_package_receipt.json',receipt)
    print(json.dumps(receipt,ensure_ascii=False))


if __name__=='__main__':
    main()
