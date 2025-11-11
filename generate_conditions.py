import math
from dataclasses import dataclass
from pathlib import Path
from PIL import Image
from tqdm import tqdm
from utils.vis import to_overlay_image
import shutil

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

def generate_image_from_label(label: list[LabelLine], image_size: tuple[int, int]) -> Image.Image:
    """Generate a grayscale image with white bounding-box outlines from YOLO labels.

    Args:
        label: List of LabelLine entries with normalized coordinates.
        image_size: (width, height) in pixels.

    Returns:
        PIL.Image.Image in mode "L" (black background, white box outlines).
    """
    # Import locally to avoid changing global imports
    from PIL import ImageDraw

    width, height = image_size
    # Start with a black canvas
    img = Image.new("L", (width, height), color="#000000").convert("RGB")

    if not label:
        return img

    draw = ImageDraw.Draw(img)

    for item in label:
        # Convert normalized YOLO (cx, cy, w, h) to pixel box corners
        x_center_px = item.x_center * width
        y_center_px = item.y_center * height
        box_w_px = item.width * width
        box_h_px = item.height * height

        left = x_center_px - box_w_px / 2.0
        top = y_center_px - box_h_px / 2.0
        right = x_center_px + box_w_px / 2.0
        bottom = y_center_px + box_h_px / 2.0

        # Clip to image bounds
        left = max(0.0, min(float(width - 1), left))
        top = max(0.0, min(float(height - 1), top))
        right = max(0.0, min(float(width - 1), right))
        bottom = max(0.0, min(float(height - 1), bottom))

        # Skip invalid/empty boxes after clipping
        if right <= left or bottom <= top:
            continue

        # Draw rectangle outline for visibility
        draw.rectangle([(left, top), (right, bottom)], outline=category_to_color(item.class_id), width=2)

    return img

def _lab_to_xyz(l: float, a: float, b: float) -> tuple[float, float, float]:
    fy = (l + 16.0) / 116.0
    fx = fy + a / 500.0
    fz = fy - b / 200.0
    delta = 6.0 / 29.0

    def f_inv(t: float) -> float:
        if t > delta:
            return t ** 3
        return 3.0 * delta * delta * (t - 4.0 / 29.0)

    x = 0.95047 * f_inv(fx)
    y = 1.00000 * f_inv(fy)
    z = 1.08883 * f_inv(fz)
    return x, y, z


def _xyz_to_linear_rgb(x: float, y: float, z: float) -> tuple[float, float, float]:
    r = 3.2404542 * x - 1.5371385 * y - 0.4985314 * z
    g = -0.9692660 * x + 1.8760108 * y + 0.0415560 * z
    b = 0.0556434 * x - 0.2040259 * y + 1.0572252 * z
    return r, g, b


def _linear_to_srgb(value: float) -> float:
    if value <= 0.0031308:
        return 12.92 * value
    return 1.055 * (value ** (1 / 2.4)) - 0.055


def _lab_to_rgb(l: float, a: float, b: float):
    x, y, z = _lab_to_xyz(l, a, b)
    r_lin, g_lin, b_lin = _xyz_to_linear_rgb(x, y, z)

    if min(r_lin, g_lin, b_lin) < -0.001 or max(r_lin, g_lin, b_lin) > 1.001:
        return None

    r_lin = min(max(r_lin, 0.0), 1.0)
    g_lin = min(max(g_lin, 0.0), 1.0)
    b_lin = min(max(b_lin, 0.0), 1.0)

    r = _linear_to_srgb(r_lin)
    g = _linear_to_srgb(g_lin)
    b = _linear_to_srgb(b_lin)

    return int(round(r * 255)), int(round(g * 255)), int(round(b * 255))


def _lch_to_lab(l: float, c: float, h_degrees: float) -> tuple[float, float, float]:
    h = math.radians(h_degrees % 360.0)
    a = c * math.cos(h)
    b = c * math.sin(h)
    return l, a, b


def _rgb_tuple_to_hex(rgb: tuple[int, int, int]) -> str:
    r, g, b = rgb
    return f"#{r:02X}{g:02X}{b:02X}"


def _build_palette_candidates() -> list[tuple[tuple[float, float, float], tuple[int, int, int]]]:
    candidates: list[tuple[tuple[float, float, float], tuple[int, int, int]]] = []
    for l, c in ((60.0, 40.0), (70.0, 50.0), (80.0, 35.0), (65.0, 45.0)):
        for h in range(0, 360, 3):
            lab = _lch_to_lab(l, c, h)
            rgb = _lab_to_rgb(*lab)
            if rgb is None:
                continue
            candidates.append((lab, rgb))
    if len(candidates) < 80:
        raise RuntimeError("Insufficient palette candidates to cover requested categories.")
    return candidates


def _generate_distinct_palette(size: int) -> list[str]:
    candidates = _build_palette_candidates()
    selected_indices: set[int] = set()
    selected_labs: list[tuple[float, float, float]] = []
    selected_rgbs: list[tuple[int, int, int]] = []

    initial_index = 0
    selected_indices.add(initial_index)
    selected_labs.append(candidates[initial_index][0])
    selected_rgbs.append(candidates[initial_index][1])

    while len(selected_rgbs) < size:
        best_index = None
        best_distance = -1.0
        for idx, (lab, _rgb) in enumerate(candidates):
            if idx in selected_indices:
                continue
            min_distance = min(
                math.dist(lab, existing_lab) for existing_lab in selected_labs
            )
            if min_distance > best_distance:
                best_distance = min_distance
                best_index = idx
        if best_index is None:
            raise RuntimeError("Unable to devise a palette of the requested size.")
        selected_indices.add(best_index)
        selected_labs.append(candidates[best_index][0])
        selected_rgbs.append(candidates[best_index][1])

    return [_rgb_tuple_to_hex(rgb) for rgb in selected_rgbs]


CATEGORY_COLORS = _generate_distinct_palette(80)


def category_to_color(category: int) -> str:
    assert 0 <= category < len(CATEGORY_COLORS)
    return CATEGORY_COLORS[category]


def generate_cond_img(raw_images_dir: Path, label_stem: str, label_lines: list[LabelLine], output_dir: Path):
    reference_image_path = raw_images_dir / f"{label_stem}.jpg"
    if not reference_image_path.exists():
        raise FileNotFoundError(f"Reference image not found for label {label_stem}")
    reference_image = Image.open(reference_image_path)
    width, height = reference_image.size
    image = generate_image_from_label(label_lines, (width, height))
    image.save(str(output_dir / f"{label_stem}_condition.png"))
    # overlay_image = to_overlay_image(image, reference_image)
    #overlay_image.save(str(output_dir / f"{label_stem}_condition.png"))

labels_dir = Path("/home/azureuser/ControlFinetuningSandbox/data/coco2014/labels/train2014")
raw_images_dir = Path("/home/azureuser/ControlFinetuningSandbox/data/coco2014/images/raw_train_images")
output_dir = Path("/home/azureuser/ControlFinetuningSandbox/data/coco2014/conditions/vehicles_only_train_2014")
exclude_bbox_categories = [0] + list(range(9, 80))

if output_dir.exists():
    shutil.rmtree(output_dir)
output_dir.mkdir(parents=True, exist_ok=True)
labels = read_labels_dir(labels_dir)

for idx, (label_stem, label_lines) in enumerate(tqdm(list(labels.items()))):
    label_lines_filtered = [label_line for label_line in label_lines if label_line.class_id not in exclude_bbox_categories]
    generate_cond_img(raw_images_dir, label_stem, label_lines_filtered, output_dir)