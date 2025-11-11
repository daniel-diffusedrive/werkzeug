import json
from pathlib import Path
import math
from dataclasses import dataclass
from pathlib import Path
from PIL import Image
from tqdm import tqdm
from utils.vis import to_overlay_image
import shutil
from logging import getLogger
logger = getLogger(__name__)

@dataclass 
class LabelLine:
    class_id: int
    x_center: float
    y_center: float
    width: float
    height: float

def read_label_line(line: str):
    parts = line.split()
    class_id = int(parts[0])
    x_center = float(parts[1])
    y_center = float(parts[2])
    width = float(parts[3])
    height = float(parts[4])
    return LabelLine(class_id, x_center, y_center, width, height)

def read_label_file(label_file: Path) -> list[LabelLine]:
    with label_file.open("r") as f:
        labels = [read_label_line(line) for line in f]
        
    return labels

def read_labels_dir(labels_dir: Path) -> dict[str, list[LabelLine]]:

    # load labels
    labels = {}
    for label_file in tqdm(list(labels_dir.glob("*.txt"))):
        labels[label_file.stem] = read_label_file(label_file)
    return labels

def convert_caption_list_to_dict(caption_list):
    caption_dict = {}
    for caption in caption_list:
        caption_dict[caption["image_id"]] = caption
    return caption_dict


captions_json_fpath = "/home/azureuser/ControlFinetuningSandbox/data/coco2014/captions/raw/annotations_trainval2014/annotations/captions_train2014.json"
output_jsonl_fpath = "./metadata_vehicle_only_coco14.jsonl"
raw_bbox_labels_folder_fpath = Path("/home/azureuser/ControlFinetuningSandbox/data/coco2014/labels/train2014")
exclude_bbox_categories = [0] + list(range(9, 80))
max_num_bboxes = 5


captions = json.load(open(captions_json_fpath))
captions_dict = convert_caption_list_to_dict(captions["annotations"])
metadata_jsonl = []
for image_metadata in captions["images"]:
    image_id = image_metadata["id"]
    caption = captions_dict[image_id]["caption"]
    image_fname = image_metadata["file_name"]
    image_stem = str(Path(image_fname).stem)
    condition_fname = image_stem + "_condition.png"

    bbox_annotations_filepath = raw_bbox_labels_folder_fpath / f"{image_stem}.txt"
    if not bbox_annotations_filepath.exists():
        logger.warning(f"Bbox annotations not found for image {image_stem}")
        continue
    assert bbox_annotations_filepath.exists(), f"Bbox annotations not found for image {image_stem}"
    bbox_annotations = read_label_file(bbox_annotations_filepath)
    is_exclude = False
    for bbox_annotation in bbox_annotations:
        if bbox_annotation.class_id in exclude_bbox_categories:
            is_exclude = True
    
    if len(bbox_annotations) > max_num_bboxes:
        continue
    if is_exclude:
        continue


    metadata_jsonl.append(
        {"file_name": image_fname, "condition": condition_fname, "caption": caption}
    )
with open(output_jsonl_fpath, "w") as f:
    for metadata in metadata_jsonl:
        f.write(json.dumps(metadata) + "\n")
