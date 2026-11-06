from copy import deepcopy
from pathlib import Path
from zipfile import ZipFile
import json,subprocess,re,hashlib
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt,Mm
from lxml import etree

BASE=Path('/workspace/bmt_v13/experiments/delimiter_agent')
SRC=Path('/workspace/research_source/submission/bmt_v12')
NS={'m':'http://schemas.openxmlformats.org/officeDocument/2006/math','w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

def literal_math_run(text,size=12):
    r=OxmlElement('m:r');mp=OxmlElement('m:rPr');mp.append(OxmlElement('m:nor'));r.append(mp)
    wp=OxmlElement('w:rPr');f=OxmlElement('w:rFonts')
    for k in ['ascii','hAnsi','cs','eastAsia']:f.set(qn('w:'+k),'Times New Roman')
    wp.append(f);sz=OxmlElement('w:sz');sz.set(qn('w:val'),str(size*2));wp.append(sz)
    i=OxmlElement('w:i');i.set(qn('w:val'),'0');wp.append(i);r.append(wp)
    t=OxmlElement('m:t');t.text=text;r.append(t);return r

def flatten_fences(root,size=12):
    count=0
    for d in reversed(root.findall('.//m:d',NS)):
        pr=d.find('m:dPr',NS)
        def char(name,default):
            n=pr.find('m:'+name,NS)if pr is not None else None
            return n.get(qn('m:val'),default)if n is not None else default
        op,cl,sep=char('begChr','('),char('endChr',')'),char('sepChr','|')
        new=[]
        if op:new.append(literal_math_run(op,size))
        for j,e in enumerate(d.findall('m:e',NS)):
            if j and sep:new.append(literal_math_run(sep,size))
            new.extend(deepcopy(c)for c in e if c.tag not in [qn('m:argPr'),qn('m:ctrlPr')])
        if cl:new.append(literal_math_run(cl,size))
        parent=d.getparent();pos=parent.index(d);parent.remove(d)
        for j,e in enumerate(new):parent.insert(pos+j,e)
        count+=1
    assert not root.findall('.//m:d',NS)
    return count

def bind_eq3_summand(root):
    # The n-ary body should contain D(P0,Pj), not only D followed by an external fence.
    for n in root.findall('.//m:nary',NS):
        body=n.find('m:e',NS)
        if body is None or ''.join(body.xpath('.//m:t/text()',namespaces=NS))!='D':continue
        parent=n.getparent();tail=list(parent)[parent.index(n)+1:];picked=[]
        # All nodes to the matching literal closing ')' belong to the function body.
        if not tail or ''.join(tail[0].xpath('.//m:t/text()',namespaces=NS))!='(':continue
        depth=0
        for node in tail:
            txt=''.join(node.xpath('.//m:t/text()',namespaces=NS))
            if txt=='(':depth+=1
            if txt==')':depth-=1
            picked.append(node)
            if depth==0:break
        for node in picked:parent.remove(node);body.append(node)
        return True
    return False

