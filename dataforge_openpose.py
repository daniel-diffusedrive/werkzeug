from typing import Optional
from accelerate import Accelerator
from accelerate.logging import get_logger
from datasets import load_dataset
from torchvision import transforms
import torch
from PIL import Image
from io import BytesIO

logger = get_logger(__name__)

PIXEL_VALUES_KEY = "pixel_values"
CONDITIONING_PIXEL_VALUES_KEY = "conditioning_values"
CAPTIONS_KEY_DATALOADER = "prompts"
CAPTIONS_KEY_DATASET = "caption"


def get_train_dataset(
    dataset_name: str,
    accelerator: Optional[Accelerator] = None,
    dataset_config_name: Optional[str] = None,
    cache_dir: Optional[str] = None,
    jsonl_for_train: Optional[str] = None,
    seed: int = 42,
    max_train_samples: Optional[int] = None,
):
    dataset = None
    try:
        if dataset_name is not None:
            # Downloading and loading a dataset from the hub.
            dataset = load_dataset(
                dataset_name,
                dataset_config_name,
                cache_dir=cache_dir,
            )
        if jsonl_for_train is not None:
            # load from json
            dataset = load_dataset(
                "json", data_files=jsonl_for_train, cache_dir=cache_dir
            )
            dataset = dataset.flatten_indices()
    except Exception as e:
        logger.error(f"Error loading dataset: {e}")
        raise
    # Preprocessing the datasets.
    if accelerator is not None:
        with accelerator.main_process_first():
            train_dataset = dataset["train"].shuffle(seed=seed)
            if max_train_samples is not None:
                train_dataset = train_dataset.select(range(max_train_samples))
    else:
        train_dataset = dataset["train"].shuffle(seed=seed)
        if max_train_samples is not None:
            train_dataset = train_dataset.select(range(max_train_samples))
    return train_dataset


def prepare_dataset(
    dataset: torch.utils.data.Dataset,
    resolution,
    image_column,
    conditioning_image_column,
    caption_column,
    preprocessing_num_workers,
    accelerator: Optional[Accelerator] = None,
):
    # Add index column to the dataset
    if "index" not in dataset.column_names:
        if accelerator is not None:
            with accelerator.main_process_first():
                dataset = dataset.add_column("index", range(len(dataset)))
        else:
            dataset = dataset.add_column("index", range(len(dataset)))
    image_transforms = transforms.Compose(
        [
            transforms.Resize(
                (resolution, resolution),
                interpolation=transforms.InterpolationMode.BILINEAR,
            ),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
        ]
    )

    def preprocess_train(examples):
        images = [
            (
                image.convert("RGB")
                if isinstance(image, Image.Image)
                else Image.open(BytesIO(image["bytes"])).convert("RGB")
            )
            for image in examples[image_column]
        ]
        images = [image_transforms(image) for image in images]

        conditioning_images = [
            (
                image.convert("RGB")
                if isinstance(image, Image.Image)
                else Image.open(BytesIO(image["bytes"])).convert("RGB")
            )
            for image in examples[conditioning_image_column]
        ]
        conditioning_images = [image_transforms(image) for image in conditioning_images]
        examples[PIXEL_VALUES_KEY] = images
        examples[CONDITIONING_PIXEL_VALUES_KEY] = conditioning_images

        is_caption_list = isinstance(examples[caption_column][0], list)
        if is_caption_list:
            examples[CAPTIONS_KEY_DATASET] = [
                max(example, key=len) for example in examples[caption_column]
            ]
        else:
            examples[CAPTIONS_KEY_DATASET] = list(examples[caption_column])

        return examples

    if accelerator is not None:
        with accelerator.main_process_first():
            dataset = dataset.with_transform(preprocess_train)
    else:
        dataset = dataset.with_transform(preprocess_train)

    dataset.num_original_images = len(dataset)
    return dataset


def collate_img(pixel_values: list[Image.Image]) -> torch.Tensor:
    pixel_values = torch.stack(pixel_values)
    if pixel_values.ndim == 4:
        pixel_values = pixel_values.unsqueeze(2)
    pixel_values = pixel_values.to(memory_format=torch.contiguous_format).float()

    return pixel_values


def collate_fn(examples):
    pixel_values = collate_img([example[PIXEL_VALUES_KEY] for example in examples])
    conditioning_pixel_values = collate_img(
        [example[CONDITIONING_PIXEL_VALUES_KEY] for example in examples]
    )
    captions = [example[CAPTIONS_KEY_DATASET] for example in examples]
    indices = [example["index"] for example in examples]
    return {
        PIXEL_VALUES_KEY: pixel_values,
        CONDITIONING_PIXEL_VALUES_KEY: conditioning_pixel_values,
        CAPTIONS_KEY_DATALOADER: captions,
        "indices": torch.tensor(indices, dtype=torch.long),
    }
