# Six-case targeted SAM audit

The archived six-case table and source-pair inspection sheet are complete. The requested original/reference/prediction figure is **not complete**: no prediction arrays for these six cases were saved in the source repository, and no verified checkpoint was accessible in the bounded permitted-host search. No model inference or dependency installation was performed in this revision audit.

The only stored external NPZ is case001, which both methods flag. It cannot replace any of the six requested misses. The source-pair PNG/PDF explicitly shows original images and released references only, with no SAM prediction.

## Required model identity

- Filename: `sam_vit_b_01ec64.pth`
- Required SHA-256: `ec2df62732614e57411cdcf32a23ffdf28910380d03139ee0f4fcbe91eb8c912`
- Official URL: https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth
- Exact clean SAM source commit: `dca509fe793f601edb92606367a655c15ac00fdf`
- The exact source is already checked out at `/workspace/bmt_v7/resources/segment-anything`.

If the original checkpoint becomes available through an allowed download or upload, verify its hash before loading. A different SAM model, converted ONNX file or unverified substitute must not be used.

## Recreate the archived case audit

```bash
python /workspace/bmt_v7/scripts/external_case_audit.py audit --source /workspace/research_source --output /workspace/bmt_v7/evidence
python /workspace/bmt_v7/scripts/external_case_audit.py sources --source /workspace/research_source --output /workspace/bmt_v7/figures
```

Audit mode reads the locked original records and verifies the selected raw-image/reference SHA-256 values. It never executes the original forced-CUDA scoring script.

## Run only the six cases after obtaining the checkpoint

The following dependency setup is prepared but **has not been executed**. Python 3.12 requires a supported NumPy version; the planned NumPy 1.26.4 differs from the original 1.24.4 and must be reported. A CPU audit also differs from the original Windows/RTX environment. It does not establish bit-identical inference in advance.

```bash
python -m venv /workspace/bmt_v7/case_env
/workspace/bmt_v7/case_env/bin/python -m pip install --index-url https://download.pytorch.org/whl/cpu torch==2.4.1+cpu torchvision==0.19.1+cpu
/workspace/bmt_v7/case_env/bin/python -m pip install numpy==1.26.4 Pillow==10.4.0 matplotlib
/workspace/bmt_v7/case_env/bin/python /workspace/bmt_v7/scripts/external_case_audit.py rerun --source /workspace/research_source --output /workspace/bmt_v7/targeted_rerun --sam-source /workspace/bmt_v7/resources/segment-anything --checkpoint /workspace/bmt_v7/resources/sam_vit_b_01ec64.pth --device cpu --threads 2
```

The script refuses a mismatched checkpoint digest or dirty/different source commit, uses frozen float32 single-mask SAM outputs, preserves black-alpha compositing and the locked reference-derived prompt geometry, and captures all five actual masks per case. CUDA synchronization is conditional on the selected device. All six cases' prompt boxes were independently compared with the original function and matched exactly.

Each captured NPZ contains the image, reference, actual initial/four shifted predictions, five boxes and raw predicted IoUs. The receipt records the actual environment, per-case current-environment runtime, eight numerical comparisons, review flags, low-quality labels and mask pixel counts. Original scores are retained and never overwritten. Runtime on this CPU must not be used to infer the original RTX timing.

The prediction sheet labels actual targeted-rerun Dice/risk values and the original group. If any value or decision differs, report that difference explicitly; do not relabel the new masks as original archived masks or silently replace the primary study results.
