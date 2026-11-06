#!/usr/bin/env python3
"""Fetch a public release copy and accept only the frozen SHA-256 bytes."""
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import urlsplit
from datetime import datetime,timezone
import hashlib,json,time

ROOT=Path(__file__).resolve().parent
URL='https://github.com/ultralytics/assets/releases/download/v8.3.0/sam_b.pt'
EXPECTED='ec2df62732614e57411cdcf32a23ffdf28910380d03139ee0f4fcbe91eb8c912'
DEST=ROOT/'resources/sam_vit_b_01ec64.pth'
DEST.parent.mkdir(parents=True,exist_ok=True)
assert not DEST.exists(), 'Refuse to overwrite an existing checkpoint'
part=DEST.with_suffix('.download')
started=datetime.now(timezone.utc).isoformat();start=time.perf_counter();h=hashlib.sha256();n=0
with urlopen(URL,timeout=60)as response,part.open('wb')as out:
 final_host=urlsplit(response.url).hostname
 content_length=response.headers.get('Content-Length')
 while data:=response.read(1024*1024):
  out.write(data);h.update(data);n+=len(data)
actual=h.hexdigest()
receipt={'requested_public_url':URL,'original_official_url':'https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth','final_host':final_host,'release_filename':'sam_b.pt','canonical_local_filename':DEST.name,'expected_sha256':EXPECTED,'actual_sha256':actual,'verified_exact_frozen_bytes':actual==EXPECTED,'bytes':n,'content_length':content_length,'started_utc':started,'completed_utc':datetime.now(timezone.utc).isoformat(),'download_seconds':time.perf_counter()-start,'network_path':'Inherited proxy and CA verification; allowed GitHub release asset hosts; no policy changes'}
(ROOT/'checkpoint_acquisition_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
assert actual==EXPECTED, 'Checkpoint hash differs: never load it'
assert n==375042383 and n==int(content_length), 'Unexpected/truncated length'
part.rename(DEST)
print(json.dumps(receipt,indent=2))
