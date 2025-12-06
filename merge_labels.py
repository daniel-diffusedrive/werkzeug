import json
from pathlib import Path
import os
import shutil


keylabs_labels_eo = Path(
    "/Users/danielschmid/projects/PromptAdherence/markdown_generation/500_selected_images/anduril_eo_500_selected_demo_images/keylabs_labels"
)
keylabs_labels_ir = Path(
    "/Users/danielschmid/projects/PromptAdherence/markdown_generation/500_selected_images/anduril_ir_500_selected_demo_images/keylabs_labels"
)
vqa_labels_path = Path("/Users/danielschmid/projects/PromptAdherence/markdown_generation/categorization.json")

known_labels = ["ship", "boat", "buoy", "bird", "unknown", "jetski", "kayak"]


def to_label(n_ships: int, n_buoys: int, n_birds: int, n_unknown: int):
    if n_ships > 0:
        if n_ships <= 4:  
            return "1-4_ships"

        if n_ships <= 9:
            return "5-9_ships"

        if n_ships <= 14:
            return "10-14_ships"

        return "15+_ships"

    else:
        if n_buoys > 0 or n_birds > 0:
            return "bird_or_buoy"
        else:
            return "no_objects"


def process_keylabs_labels(labels_dir: Path, img_name_to_label_map: dict, is_eo: bool) -> dict:
    for label_file in labels_dir.glob("*.json"):
        with open(label_file, "r") as f:
            label_data = json.load(f)

        label_metadata = label_data[0]
        label_objects = label_data[0]["objects"]

        for label in label_objects:
            if label["type"] not in known_labels:
                raise ValueError(f"Unknown label type: {label['type']}")

        n_ships = len(
            [
                x
                for x in label_objects
                if x["type"] == "ship"
                or x["type"] == "boat"
                or x["type"] == "jetski"
                or x["type"] == "kayak"
            ]
        )
        n_buoys = len([x for x in label_objects if x["type"] == "buoy"])
        n_birds = len([x for x in label_objects if x["type"] == "bird"])
        n_unknown = len([x for x in label_objects if x["type"] == "unknown"])

        img_name = Path(label_metadata["file"]).name
        img_label = to_label(n_ships, n_buoys, n_birds, n_unknown)
        img_name_to_label_map[str(img_name)]["ship_type"] = img_label
        img_name_to_label_map[str(img_name)]["camera_type"] = "eo" if is_eo else "ir"
    return img_name_to_label_map


def debug_eo():
    img_name_to_label_map_eo = {
        str(Path(json.load(Path(x).open())[0]["file"]).name): {}
        for x in keylabs_labels_eo.glob("*.json")
    }
    result = process_keylabs_labels(keylabs_labels_eo, img_name_to_label_map_eo)
    print(result)

def merge():
    vqa_labels = json.load(vqa_labels_path.open())
    merged_0 = process_keylabs_labels(keylabs_labels_eo, vqa_labels, is_eo=True)
    merged_1 = process_keylabs_labels(keylabs_labels_ir, merged_0, is_eo=False)

    out_jsonl_eo = []
    out_jsonl_ir = []
    for img_name, label in merged_1.items():
        label["img_name"] = img_name
        is_eo = label["camera_type"] == "eo"
        if is_eo:
            out_jsonl_eo.append(label)
        else:
            out_jsonl_ir.append(label)
    with open("merged_labels_eo.jsonl", "w") as f:
        for label in out_jsonl_eo:
            f.write(json.dumps(label) + "\n")
    with open("merged_labels_ir.jsonl", "w") as f:
        for label in out_jsonl_ir:
            f.write(json.dumps(label) + "\n")

def export_to_labels():
    vqa_labels = json.load(vqa_labels_path.open())

    out_jsonl = [] 
    for img_name, label in vqa_labels.items():
        out_jsonl.append({
            "img_name": img_name,
            "uav_or_usv": label["uav_or_usv"],
            "open_water_or_coastline": label["open_water_or_coastline"],
            "ship_type": label["ship_type"],
            "camera_type": "ir"
        })

    with open("merged_labels_ir_extra.jsonl", "w") as f:
        for label in out_jsonl:
            f.write(json.dumps(label) + "\n")

def log_statistics_extra():
    ir_labels_path = Path("merged_labels_ir_extra.jsonl")

    ir_labels = [json.loads(line) for line in ir_labels_path.open()]

    def _log_statistics(labels: list[dict]):
        counter = {}

        for label in labels:
            label_str = f"{label['uav_or_usv']}_{label['open_water_or_coastline']}_{label['ship_type']}"
            if label_str not in counter.keys():
                counter[label_str] = 0
                os.makedirs(f"statistics_extra/{label['camera_type']}/{label_str}", exist_ok=True)
            source_path = Path("/Users/danielschmid/projects/PromptAdherence/markdown_generation/data-dom-extraqwen-image-inference-20251023-112348-anduril_IR_r16_fromtraining_test_v2") / label["img_name"]
            shutil.copy(source_path, f"statistics_extra/{label['camera_type']}/{label_str}/{label['img_name']}")
            counter[label_str] += 1
    
        for label_str, count in counter.items():
            print(f"{label_str}: {count}")

    print("IR EXTRA")
    _log_statistics(ir_labels)


def log_statistics():
    eo_labels_path = Path("merged_labels_eo.jsonl")
    ir_labels_path = Path("merged_labels_ir.jsonl")


    eo_labels = [json.loads(line) for line in eo_labels_path.open()]
    ir_labels = [json.loads(line) for line in ir_labels_path.open()]

    def _log_statistics(labels: list[dict]):
        counter = {}

        for label in labels:
            label_str = f"{label['uav_or_usv']}_{label['open_water_or_coastline']}_{label['ship_type']}"
            if label_str not in counter.keys():
                counter[label_str] = 0
                os.makedirs(f"statistics/{label['camera_type']}/{label_str}", exist_ok=True)
            source_path = Path("/Users/danielschmid/projects/PromptAdherence/markdown_generation/to_label") / label["img_name"]
            shutil.copy(source_path, f"statistics/{label['camera_type']}/{label_str}/{label['img_name']}")
            counter[label_str] += 1
    
        for label_str, count in counter.items():
            print(f"{label_str}: {count}")

    print("EO")
    _log_statistics(eo_labels)
    print("="*100)
    print("IR")
    _log_statistics(ir_labels)
    




if __name__ == "__main__":
    # merge()
    # log_statistics()
    export_to_labels()
    log_statistics_extra()