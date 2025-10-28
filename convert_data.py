import utils.data_utils.dataforge_openpose as data_openpose
from pathlib import Path
import torch
import shutil
from PIL import Image
import json
from tqdm import tqdm


def remove_path(path: Path):
    """Remove file or directory if it exists."""

    if path.exists():
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)
        return True
    return False


def convert_to_metadatajsonl(
    train_ds: torch.utils.data.Dataset, output_path: Path, save_images: bool = True
):
    if output_path.exists():
        remove_path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)
    conditions_path = output_path / "conditions"
    conditions_path.mkdir(parents=True, exist_ok=True)

    metadata_path = output_path / "metadata.jsonl"
    metadata: list[dict[str, str]] = []
    for i in tqdm(range(len(train_ds))):
        x = train_ds[i]
        img_id = f"img_{i:07d}.png"
        caption: str = x["caption"]
        image: Image.Image = x["image"]
        conditioning_image: Image.Image = x["conditioning_image"]
        condition_path = conditions_path / img_id
        img_path = output_path / img_id

        if save_images:
            image.save(img_path)
            conditioning_image.save(condition_path)

        json_obj: dict[str, str] = {
            "image": str(img_path.relative_to(output_path)),
            "conditioning_image": str(condition_path.relative_to(output_path)),
            "caption": caption,
        }
        metadata.append(json_obj)

    json.dump(metadata, metadata_path.open("w"), indent=4)


data_dir = "/home/azureuser/data/openpose/raulc0399___open_pose_controlnet"
seed = 42
resolution = 1028
output_path = Path("/home/azureuser/data/openpose/converted")

train_ds = data_openpose.get_train_dataset(
    accelerator=None,
    dataset_name=str(data_dir),
    cache_dir=None,
    jsonl_for_train=None,
    seed=42,
    max_train_samples=None,
)
train_ds = data_openpose.prepare_dataset(
    dataset=train_ds,
    accelerator=None,
    resolution=1028,
    image_column="image",
    conditioning_image_column="conditioning_image",
    caption_column="text",
    preprocessing_num_workers=16,
)

print(train_ds[0].keys())
print(train_ds[0]["text"])
print(train_ds[0]["image"])

convert_to_metadatajsonl(train_ds, output_path, save_images=True)
