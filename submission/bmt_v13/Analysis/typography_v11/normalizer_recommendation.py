"""Verified Word-math normalization helpers, separate from the final manuscript.

The roman-label fix was visually tested through LibreOffice. Word and WPS are
not installed here, so no claim of direct testing in those applications is made.
"""
from pathlib import Path
from lxml import etree
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
NS={'m':'http://schemas.openxmlformats.org/officeDocument/2006/math',
    'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

def normalize_math(math):
    # Preserve structural math and variable italic; only explicit roman runs
    # become normal-text math, as produced by Pandoc's \\text{...} already.
    for tag,order in [('dPr',['begChr','sepChr','endChr','grow','shp','ctrlPr']),
                      ('mcPr',['count','mcJc'])]:
        for pr in math.findall('.//m:'+tag,NS):
            es=list(pr)
            for e in es:pr.remove(e)
            for e in sorted(es,key=lambda e:order.index(etree.QName(e).localname)if etree.QName(e).localname in order else 99):pr.append(e)
    for run in math.findall('.//m:r',NS):
        pr=run.find('m:rPr',NS)
        if pr is None or pr.find('m:scr',NS)is not None:continue
        sty=pr.find('m:sty',NS);txt=run.find('m:t',NS)
        if sty is not None and sty.get(qn('m:val'))=='p'and txt is not None and txt.text and txt.text.isalnum():
            pr.remove(sty)
            if pr.find('m:nor',NS)is None:pr.append(OxmlElement('m:nor'))
    for parent in math.iter():
        last=None
        for child in list(parent):
            pr=child.find('m:rPr',NS)if child.tag==qn('m:r')else None
            txt=child.find('m:t',NS)if pr is not None else None
            eligible=pr is not None and pr.find('m:nor',NS)is not None and txt is not None and txt.text and txt.text.isalnum()
            if eligible and last is not None:
                last.find('m:t',NS).text+=txt.text;parent.remove(child)
            elif eligible:last=child
            else:last=None
    return math

def write_lo_profile(profile_dir,base_size=12,matrix_column=5):
    """Apply only to the task's PDF-conversion profile, not DOCX contents."""
    profile_dir=Path(profile_dir);user=profile_dir/'user';user.mkdir(parents=True,exist_ok=True)
    (user/'registrymodifications.xcu').write_text(f'''<?xml version="1.0" encoding="UTF-8"?>
<oor:items xmlns:oor="http://openoffice.org/2001/registry">
 <item oor:path="/org.openoffice.Office.Math/StandardFormat"><prop oor:name="BaseSize" oor:op="fuse"><value>{int(base_size)}</value></prop></item>
 <item oor:path="/org.openoffice.Office.Math/StandardFormat"><prop oor:name="IndexSize" oor:op="fuse"><value>70</value></prop><prop oor:name="LimitsSize" oor:op="fuse"><value>70</value></prop></item>
 <item oor:path="/org.openoffice.Office.Math/StandardFormat/Distance"><prop oor:name="MatrixColumn" oor:op="fuse"><value>{int(matrix_column)}</value></prop></item>
</oor:items>''')
    return profile_dir.as_uri()
