# Exact SAM ViT-B checkpoint acquisition

The actual downloaded bytes, rather than the public filename, establish model identity. The GitHub release asset `sam_b.pt` below is exactly 375,042,383 bytes and its locally computed SHA-256 equals the frozen study's `sam_vit_b_01ec64.pth` digest:

`ec2df62732614e57411cdcf32a23ffdf28910380d03139ee0f4fcbe91eb8c912`

- Downloaded public asset: https://github.com/ultralytics/assets/releases/download/v8.3.0/sam_b.pt
- Public release asset list: https://github.com/ultralytics/assets/releases/expanded_assets/v8.3.0
- Ultralytics SAM documentation: https://docs.ultralytics.com/models/sam/ (describes the original Meta SAM; current model table links a later release)
- Canonical Meta filename/source: https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth
- SAM implementation: https://github.com/facebookresearch/segment-anything/tree/dca509fe793f601edb92606367a655c15ac00fdf

The current executor's inherited proxy allowed GitHub and release-assets.githubusercontent.com. No network policy, routes, proxy, CA verification or authentication settings were changed. The verified asset was saved under the canonical filename locally; only its filename changed. No conversion or model substitution occurred. Acquisition metadata and observed digest are in `checkpoint_acquisition_receipt.json`.

The earlier SamLynnEvans/Transformer candidate was rejected because its release page was unavailable. It was not used.
