#!/usr/bin/env python3
"""Check the actual exported PDFs; this is not a WPS runtime test."""
from pathlib import Path
import hashlib,json
import fitz
BASE=Path('/workspace/bmt_v13')
OUT=BASE/'outputs'
FILES={'BMT_main_manuscript_v13_preview.pdf':21,
       'BMT_main_manuscript_v13_illustrated_preview.pdf':26,
       'BMT_supplementary_material_v9_preview.pdf':25,
       'BMT_supplementary_Figure_S6_v9.pdf':6,
       'BMT_formula_layout_proof_v13.pdf':2}
records=[]
for name,count in FILES.items():
    p=OUT/name;d=fitz.open(p)
    assert len(d)==count,(name,len(d))
    assert all(len(page.get_text().strip())>0 for page in d),name
    outside=[]
    for i,page in enumerate(d):
        for word in page.get_text('words'):
            x0,y0,x1,y1,*_=word
            if min(x0,y0)<-0.5 or x1>page.rect.width+0.5 or y1>page.rect.height+0.5:
                outside.append([i+1,word])
    assert not outside,(name,outside[:5])
    records.append({'file':name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
                    'bytes':p.stat().st_size,'pages':len(d),'nonempty_pages':True,
                    'text_outside_page':outside})
proof=fitz.open(OUT/'BMT_formula_layout_proof_v13.pdf')
for source,idx,proofidx in [('BMT_main_manuscript_v13_preview.pdf',4,0),
                           ('BMT_supplementary_material_v9_preview.pdf',18,1)]:
    doc=fitz.open(OUT/source)
    assert doc[idx].get_text()==proof[proofidx].get_text()
    assert doc[idx].get_pixmap().samples==proof[proofidx].get_pixmap().samples
report={'status':'PASS','scope':'Actual exported PDF completeness/page boundaries and exact proof pages',
        'native_wps_executed':False,'native_word_executed':False,
        'proof_is_exact_actual_pages':True,'documents':records}
(BASE/'evidence/render_validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
