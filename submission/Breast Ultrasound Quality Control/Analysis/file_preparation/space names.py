#!/usr/bin/env python3
from pathlib import Path
from zipfile import ZipFile
from urllib.parse import quote, unquote
import hashlib,json,re,shutil
from docx import Document

TASK=Path('/workspace/paper_spaces')
ROOT=Path('/workspace/research_source')
SOURCE=TASK/'source'
DEST=ROOT/'submission/Breast Ultrasound Quality Control'
PREFIX='Breast Ultrasound Quality Control'
OLD_PREFIX='Breast_Ultrasound_Quality_Control'
OLD_ZIP=OLD_PREFIX+'_Submission_Files.zip'
ZIP_NAME=PREFIX+' Submission Files.zip'
MANIFEST=PREFIX+' File Manifest.json'

def map_path(name):
    p=Path(name)
    if len(p.parts)==1:return p.name.replace('_',' ')
    if p.parts[0]=='Figures':return 'Figures/'+p.name.replace('_',' ')
    if p.parts[:2]==('Analysis','table_data'):
        return 'Analysis/Table Data/'+p.name.replace('_',' ')
    return name  # Keep executable module/import and historical evidence names.

MAPPING={p.relative_to(SOURCE).as_posix():map_path(p.relative_to(SOURCE).as_posix())for p in SOURCE.rglob('*')if p.is_file()}
POINTERS={
 OLD_PREFIX+'_Additional_Quality_Control_Metrics.csv':PREFIX+' Additional Quality Control Metrics.csv',
 OLD_PREFIX+'_Table_S13_Unrounded_Comparisons.csv':PREFIX+' Table S13 Unrounded Comparisons.csv',
 OLD_PREFIX+'_Supplementary_Figure_S6.pdf':PREFIX+' Supplementary Figure S6.pdf',
}

def translated(text):
    text=text.replace('submission/breast_ultrasound_quality_control','submission/Breast Ultrasound Quality Control')
    text=text.replace(OLD_ZIP,ZIP_NAME)
    for old,new in sorted(MAPPING.items(),key=lambda v:len(v[0]),reverse=True):
        if old!=new:text=text.replace(old,new)
    return text.replace(OLD_PREFIX,PREFIX)

def markdown(text):
    text=translated(text)
    def link(m):
        url=m.group(1)
        if '://'in url:return ']('+url+')'
        return ']('+quote(unquote(url),safe='/#?=&:')+')'
    return re.sub(r'\]\(([^)]+)\)',link,text)

def patch_docx(path):
    with ZipFile(path)as z:parts=[(x,z.read(x.filename))for x in z.infolist()]
    with ZipFile(path,'w')as z:
        for info,data in parts:
            if info.filename=='word/document.xml':
                for old,new in POINTERS.items():
                    assert data.count(old.encode())==1,old
                    data=data.replace(old.encode(),new.encode())
            z.writestr(info,data)

if __name__=='__main__':
    assert not DEST.exists()
    assert len(set(MAPPING.values()))==len(MAPPING)
    for old,new in MAPPING.items():
        if old.endswith('_File_Manifest.json'):continue
        d=DEST/new;d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(SOURCE/old,d)
    patch_docx(DEST/(PREFIX+' Supplementary Material.docx'))
    for old in ['README_zh.md',OLD_PREFIX+'_Submission_Guide.md',OLD_PREFIX+'_Preparation_Notes_zh.md']:
        p=DEST/MAPPING[old];p.write_text(markdown(p.read_text()))
    checklist=DEST/(PREFIX+' Submission Checklist.docx');d=Document(checklist)
    for p in d.paragraphs:
        for run in p.runs:
            new=translated(run.text)
            if new!=run.text:run.text=new
    d.save(checklist)
    readme=ROOT/'README.md';readme.write_text(markdown(readme.read_text()))
    record={'source_commit':'cd6b69f527258023ad56c50db843c6ea1b904e6f',
            'directory':'submission/Breast Ultrasound Quality Control',
            'zip':ZIP_NAME,'files':MAPPING,'supplement_replacements':POINTERS,
            'technical_module_names_preserved':True,'scientific_content_changed':False}
    (TASK/'mapping.json').write_text(json.dumps(record,indent=2)+'\n')
    profile=TASK/'lo';(profile/'user').mkdir(parents=True,exist_ok=True)
    (profile/'user/registrymodifications.xcu').write_text('''<?xml version="1.0" encoding="UTF-8"?><oor:items xmlns:oor="http://openoffice.org/2001/registry"><item oor:path="/org.openoffice.Office.Math/StandardFormat"><prop oor:name="BaseSize" oor:op="fuse"><value>11</value></prop><prop oor:name="IndexSize" oor:op="fuse"><value>70</value></prop><prop oor:name="LimitsSize" oor:op="fuse"><value>70</value></prop></item></oor:items>''')
    (DEST/(PREFIX+' Supplementary Material.pdf')).unlink()
    print(json.dumps({'directory':str(DEST),'renamed_paths':sum(a!=b for a,b in MAPPING.items())},indent=2))
