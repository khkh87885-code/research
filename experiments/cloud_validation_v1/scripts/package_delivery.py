#!/usr/bin/env python3
"""Stage a losslessly compressed delivery without altering computation records."""
from pathlib import Path
import argparse, gzip, hashlib, json, shutil, zipfile

p=argparse.ArgumentParser();p.add_argument('--destination',type=Path,required=True);p.add_argument('--zip',type=Path,required=True)
a=p.parse_args();root=Path(__file__).resolve().parents[1];dest=a.destination.resolve()
if dest==root or root in dest.parents:raise ValueError('Destination must be outside source workspace')
if dest.exists():shutil.rmtree(dest)
shutil.copytree(root,dest,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
raws={}
for rel in ['results/bootstrap_stability/iterations.csv','results/case_mix_decomposition_bootstrap.csv']:
 path=dest/rel;data=path.read_bytes();compressed=gzip.compress(data,compresslevel=9,mtime=0)
 target=path.with_suffix(path.suffix+'.gz');target.write_bytes(compressed)
 assert gzip.decompress(compressed)==data
 raws[rel]={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'compressed_file':target.relative_to(dest).as_posix(),'compressed_bytes':len(compressed),'compressed_sha256':hashlib.sha256(compressed).hexdigest(),'method':'gzip lossless; timestamp mtime=0'}
 path.unlink()
(dest/'RAW_CSV_COMPRESSION.json').write_text(json.dumps(raws,ensure_ascii=False,indent=2)+'\n')
manifest={path.relative_to(dest).as_posix():{'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}for path in sorted(dest.rglob('*'))if path.is_file()and path.name!='FILE_MANIFEST.json'}
(dest/'FILE_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
a.zip.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(a.zip,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9)as z:
 for path in sorted(dest.rglob('*')):
  if path.is_file():z.write(path,path.relative_to(dest))
with zipfile.ZipFile(a.zip)as z:
 assert z.testzip()is None
 for rel,meta in manifest.items():
  data=z.read(rel);assert len(data)==meta['bytes']and hashlib.sha256(data).hexdigest()==meta['sha256']
receipt={'files_without_manifest':len(manifest),'zip_entries':len(manifest)+1,'zip_bytes':a.zip.stat().st_size,'zip_sha256':hashlib.sha256(a.zip.read_bytes()).hexdigest(),'all_file_hashes_verified':True,'raw_csv_gzip_roundtrip_verified':True}
print(json.dumps(receipt,indent=2))
