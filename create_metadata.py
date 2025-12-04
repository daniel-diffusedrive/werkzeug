import json
import logging
from pathlib import Path

import torch
from tqdm import tqdm
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Configuration
IMAGE_DIR = Path("/home/azureuser/Tools/openimg_condition_dataset_creator/ir")
OUTPUT_FILE = Path("/home/azureuser/Tools/openimg_condition_dataset_creator/ir-metadata-fixed-ship-count.jsonl")
BATCH_SIZE = 8  # 80GB VRAM - can go higher if needed

# Supported image extensions
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff"}


def load_model():
    """Load the Qwen2.5-VL-7B-Instruct model and processor with optimizations."""
    print("Loading Qwen2.5-VL-7B-Instruct model...")
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        "Qwen/Qwen2.5-VL-7B-Instruct",
        torch_dtype=torch.bfloat16,
        device_map="auto",
        max_memory={0: "80GiB"},
    )
    processor = AutoProcessor.from_pretrained("Qwen/Qwen2.5-VL-7B-Instruct")
    processor.tokenizer.padding_side = "left"
    print("Model loaded successfully.")
    return model, processor


def get_image_files(image_dir: Path) -> list[Path]:
    """Get all image files from the directory."""
    image_files = []
    for file in image_dir.iterdir():
        if file.is_file():
            if file.suffix.lower() in IMAGE_EXTENSIONS:
                image_files.append(file)
            else:
                logger.warning(f"Skipping file with unsupported extension: {file.name}")
    return sorted(image_files)


def generate_captions_batch(model, processor, image_paths: list[Path]) -> list[str]:
    """Generate captions for a batch of images."""
    # Build messages for each image
    messages_batch = []
    for image_path in image_paths:
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "image": f"file://{image_path}",
                    },
                    {
                        "type": "text",
                        "text": "Describe this image in one short sentence. Use the word 'infrared' for describing the style of the image. Do not include ship counts or numbers, just use the word 'boat' or 'boats'.",
                    },
                ],
            }
        ]
        messages_batch.append(messages)

    # Process each message through the template
    texts = []
    all_image_inputs = []
    for messages in messages_batch:
        text = processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        texts.append(text)
        image_inputs, _ = process_vision_info(messages)
        all_image_inputs.extend(image_inputs)

    # Batch process
    inputs = processor(
        text=texts,
        images=all_image_inputs,
        padding=True,
        return_tensors="pt",
    )
    inputs = inputs.to(model.device)

    # Clear image inputs from CPU memory
    del all_image_inputs

    # Generate captions (greedy decoding for speed)
    with torch.inference_mode():
        generated_ids = model.generate(**inputs, max_new_tokens=64, do_sample=False)

    # Decode outputs
    captions = []
    for in_ids, out_ids in zip(inputs.input_ids, generated_ids):
        trimmed = out_ids[len(in_ids):]
        caption = processor.decode(trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False)
        captions.append(caption.strip())

    # Cleanup GPU memory
    del inputs, generated_ids
    torch.cuda.empty_cache()

    return captions


def create_metadata_entry(image_path: Path, caption: str) -> dict:
    """Create a metadata entry for an image."""
    filename = image_path.name
    stem = image_path.stem  # filename without extension

    return {
        "file_name": filename,
        "condition": f"{stem}_condition.png",
        "caption": caption,
    }


def main():
    # Load model
    model, processor = load_model()

    # Get all image files
    image_files = get_image_files(IMAGE_DIR)
    print(f"Found {len(image_files)} images in {IMAGE_DIR}")

    if not image_files:
        print("No images found. Exiting.")
        return

    # Process images in batches
    with open(OUTPUT_FILE, "w") as f:
        for i in tqdm(range(0, len(image_files), BATCH_SIZE), desc="Processing batches"):
            batch_paths = image_files[i:i + BATCH_SIZE]
            try:
                captions = generate_captions_batch(model, processor, batch_paths)
                for image_path, caption in zip(batch_paths, captions):
                    entry = create_metadata_entry(image_path, caption)
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                f.flush()
            except Exception as e:
                logger.error(f"Error processing batch starting at {batch_paths[0].name}: {e}")
                # Fallback: process individually
                for image_path in batch_paths:
                    try:
                        captions = generate_captions_batch(model, processor, [image_path])
                        entry = create_metadata_entry(image_path, captions[0])
                        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                        f.flush()
                    except Exception as e2:
                        logger.error(f"Error processing {image_path.name}: {e2}")
                        continue

    print(f"\nMetadata saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
