"""Retrieve the locked external example and verify the five illustrated outputs."""
import csv
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

import numpy as np
from PIL import Image
import torch
import torchvision


WORK = Path(__file__).resolve().parent
ROOT = WORK.parent
PACKAGE = ROOT / ".repro_work_1793898679527" / "breast_ultrasound_reproduction"
SAM = ROOT.parent / "segment-anything"
CHECKPOINT = Path("D:/codex论文/models/sam_vit_b_01ec64.pth")
sys.path.insert(0, str(PACKAGE))
from score_images import measure_case, png_bytes
from study_statistics import file_hash, require


class CapturedPredictor:
    def __init__(self, predictor):
        self.predictor = predictor
        self.image = None
        self.masks = []
        self.boxes = []

    def set_image(self, rgb):
        require(self.image is None, "The image encoder was called twice")
        self.image = rgb.copy()
        self.predictor.set_image(rgb)

    def predict(self, *, box, multimask_output):
        result = self.predictor.predict(box=box, multimask_output=multimask_output)
        self.masks.append(result[0][0].astype(bool))
        self.boxes.append(box.copy())
        return result

    def reset_image(self):
        self.predictor.reset_image()


def read_rows(path):
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def main():
    config = json.loads((PACKAGE / "study_lock.json").read_text(encoding="utf-8-sig"))
    study = config["threshold_lock"]
    model_info = study["model"]
    current = subprocess.check_output(
        ["git", "--no-optional-locks", "-C", str(SAM), "rev-parse", "HEAD"],
        text=True,
    ).strip()
    dirty = subprocess.check_output(
        ["git", "--no-optional-locks", "-C", str(SAM), "status", "--porcelain"],
        text=True,
    ).strip()
    require(current == model_info["source_commit"] and not dirty, "Unexpected SAM source")
    require(file_hash(CHECKPOINT) == model_info["weight_sha256"], "Unexpected SAM checkpoint")
    require(torch.cuda.is_available()
            and torch.__version__ == config["environment"]["torch"]
            and torchvision.__version__ == config["environment"]["torchvision"],
            "The verified CUDA inference environment is required")

    entry = config["cohorts"]["external_test"]
    for key in ("manifest", "archived_scores"):
        relative = entry[key]
        require(file_hash(PACKAGE / relative) == config["files_sha256"][relative],
                f"Unexpected {key} contents")
    row = min(read_rows(PACKAGE / entry["manifest"]), key=lambda item: int(item["patient_id"]))
    archive_info = config["datasets"]["BrEaST"]
    archive_path = ROOT / "breast_external_raw" / archive_info["archive"]
    require(file_hash(archive_path) == archive_info["archive_sha256"], "Unexpected image archive")
    archived = [
        item for item in read_rows(PACKAGE / entry["archived_scores"])
        if item["split"] == row["split"] and item["image_id"] == row["image_id"]
    ]
    require(len(archived) == 1 and archived[0]["status"] == "scored", "Missing archived score")
    archived = archived[0]

    sys.path.insert(0, str(SAM))
    import segment_anything
    require(SAM in Path(segment_anything.__file__).resolve().parents, "Wrong SAM import")
    device = torch.device("cuda:0")
    model = segment_anything.sam_model_registry["vit_b"]()
    state = torch.load(CHECKPOINT, map_location="cpu", weights_only=True)
    model.load_state_dict(state, strict=True)
    del state
    model.to(device).eval()
    capture = CapturedPredictor(segment_anything.SamPredictor(model))
    with ZipFile(archive_path) as archive, torch.inference_mode():
        record = measure_case(row, capture, device, archive, set(config["external_alpha_changed_ids"]))
        with Image.open(BytesIO(png_bytes(archive, row, "mask"))) as image:
            reference = np.array(image.convert("1"), dtype=bool)
    fields = (
        "dice_vs_reference", "sam_predicted_iou", "risk_A", "risk_B", "dice_shift_left",
        "dice_shift_right", "dice_shift_up", "dice_shift_down",
    )
    require(all(record[field] == float(archived[field]) for field in fields),
            "The pictured case differs from its archived scores")
    for method in ("A", "B"):
        risk = record[f"risk_{method}"]
        threshold = study["methods"][method]["threshold"]
        require(int(risk >= threshold) == int(archived[f"alert_{method}"]),
                f"Review flag differs for {method}")
    require(len(capture.masks) == len(capture.boxes) == 5, "Expected the five locked prompts")
    path = WORK / "example_case.npz"
    np.savez_compressed(path, image=capture.image, reference=reference,
                        masks=np.stack(capture.masks), boxes=np.stack(capture.boxes))
    result = {
        "dataset": "BrEaST v1", "doi": archive_info["doi"], "patient_id": int(row["patient_id"]),
        "case": row["image_id"], "selection": "lowest eligible BrEaST case number",
        "image_sha256": row["image_sha256"], "reference_sha256": row["mask_sha256"],
        "sam_commit": current, "checkpoint_sha256": model_info["weight_sha256"],
        "artifact_sha256": sha256(path.read_bytes()).hexdigest(),
        "directions": ["initial", "left", "right", "up", "down"],
        "archived_values_match": True,
        "image_shape": list(capture.image.shape),
        "mask_pixel_counts": [int(mask.sum()) for mask in capture.masks],
        "base_box": capture.boxes[0].tolist(),
    }
    (WORK / "example_case.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
