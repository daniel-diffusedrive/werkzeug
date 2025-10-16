import json
from pathlib import Path
import os

base_dir = Path("/home/azureuser/data/img_selection/selection")

dismiss_dir = base_dir / "dismiss"
keep_dir = base_dir / "keep"
mid_dir = base_dir / "mid"

output_file = base_dir / "image_caption.jsonl"

image_files = []

if not base_dir.exists():
    raise FileNotFoundError(f"Base directory {base_dir} does not exist.")
# Get files from dismiss directory
if dismiss_dir.exists():
    for filename in dismiss_dir.iterdir():
        image_files.append("dismiss/" + filename.name)

# Get files from keep directory
if keep_dir.exists():
    for filename in keep_dir.iterdir():
        image_files.append("keep/" + filename.name)

# Get files from mid directory
if mid_dir.exists():
    for filename in mid_dir.iterdir():
        image_files.append("mid/" + filename.name)

with open(output_file, "w") as f:
    for img_name in sorted(image_files):
        data = {"img_name": img_name, "prompt": "_"}
        f.write(json.dumps(data) + "\n")

print(f"Generated {output_file} with {len(image_files)} entries.")
