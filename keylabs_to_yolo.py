import json
import os
from pathlib import Path
from typing import Dict, List, Any, Literal


def read_label_files(labels_dir: str) -> Dict[str, Any]:
    """
    Read all JSON label files from the specified directory.

    Args:
        labels_dir: Path to directory containing .json label files

    Returns:
        Dictionary mapping filename to parsed label data
    """
    labels_dir = Path(labels_dir)
    labels = {}

    for json_file in labels_dir.glob("*.json"):
        with open(json_file, "r") as f:
            data = json.load(f)
            labels[json_file.name] = data

    return labels


from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BoundingBox:
    """Represents a single bounding box annotation."""

    x1: float
    y1: float
    x2: float
    y2: float
    obj_type: str
    subcategory: Optional[str] = None

    @property
    def width(self) -> float:
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        return self.y2 - self.y1

    @property
    def center_x(self) -> float:
        return (self.x1 + self.x2) / 2

    @property
    def center_y(self) -> float:
        return (self.y1 + self.y2) / 2


@dataclass
class ImageLabel:
    """Represents all labels for a single image."""

    filename: str
    image_width: int
    image_height: int
    bounding_boxes: List[BoundingBox] = field(default_factory=list)

    @classmethod
    def from_json(cls, filename: str, data: List[dict]) -> "ImageLabel":
        """Parse JSON label data into ImageLabel object."""
        metadata = data[0]
        bbox_data = data[1]["objects"]

        # Build type lookup from metadata
        type_lookup = {obj["nm"]: obj["type"] for obj in metadata["objects"]}

        bboxes = []
        for obj in bbox_data:
            bbox = BoundingBox(
                x1=obj["x1"],
                y1=obj["y1"],
                x2=obj["x2"],
                y2=obj["y2"],
                obj_type=type_lookup.get(obj["nm"], "unknown"),
                subcategory=obj.get("attributes", {}).get("subcategory"),
            )
            bboxes.append(bbox)

        return cls(
            filename=metadata["file"],
            image_width=metadata["width"],
            image_height=metadata["height"],
            bounding_boxes=bboxes,
        )


def parse_labels(raw_labels: Dict[str, Any]) -> List[ImageLabel]:
    """Convert raw label dict to list of ImageLabel objects."""
    image_labels = []
    for filename, data in raw_labels.items():
        try:
            image_label = ImageLabel.from_json(filename, data)
            image_labels.append(image_label)
        except (KeyError, IndexError) as e:
            print(f"Warning: Could not parse {filename}: {e}")
    return image_labels


def filter_for_obj_types(image_labels: List[ImageLabel], class_ids: list[Literal["water_vehicle", "buoy", "bird"]]) -> List[ImageLabel]:
    """
    Filter image labels to only include water_vehicle bounding boxes.
    Images with no water_vehicle annotations will have an empty bounding_boxes list.

    Args:
        image_labels: List of ImageLabel objects

    Returns:
        List of ImageLabel objects with only water_vehicle bounding boxes
    """
    filtered_labels = []

    for label in image_labels:
        water_vehicle_boxes = [
            bbox for bbox in label.bounding_boxes if bbox.obj_type in class_ids
        ]

        filtered_label = ImageLabel(
            filename=label.filename,
            image_width=label.image_width,
            image_height=label.image_height,
            bounding_boxes=water_vehicle_boxes,
        )
        filtered_labels.append(filtered_label)

    return filtered_labels


from dataclasses import dataclass as stats_dataclass


@stats_dataclass
class SizeStatistics:
    """Statistics about water vehicle sizes."""

    pot_threshold: float
    images_only_small: int
    images_with_medium: int
    images_no_vehicles: int
    total_small_bboxes: int
    total_medium_bboxes: int

    def __repr__(self):
        return (
            f"SizeStatistics(pot_threshold={self.pot_threshold}):\n"
            f"  Images with only small vehicles: {self.images_only_small}\n"
            f"  Images with at least one medium vehicle: {self.images_with_medium}\n"
            f"  Images with no vehicles: {self.images_no_vehicles}\n"
            f"  Total small bboxes: {self.total_small_bboxes}\n"
            f"  Total medium bboxes: {self.total_medium_bboxes}"
        )


def compute_size_statistics(
    water_vehicle_labels: List[ImageLabel], pot_threshold: float
) -> SizeStatistics:
    """
    Compute statistics about water vehicle sizes based on POT (width * height) threshold.

    Args:
        water_vehicle_labels: List of ImageLabel objects (filtered to water vehicles)
        pot_threshold: Threshold for classifying small vs medium vehicles.
                       POT = bbox.width * bbox.height
                       Small: POT < threshold
                       Medium: POT >= threshold

    Returns:
        SizeStatistics with counts
    """
    images_only_small = 0
    images_with_medium = 0
    images_no_vehicles = 0
    total_small_bboxes = 0
    total_medium_bboxes = 0

    for label in water_vehicle_labels:
        if not label.bounding_boxes:
            images_no_vehicles += 1
            continue

        small_count = 0
        medium_count = 0

        for bbox in label.bounding_boxes:
            pot = bbox.width * bbox.height
            if pot < pot_threshold:
                small_count += 1
            else:
                medium_count += 1

        total_small_bboxes += small_count
        total_medium_bboxes += medium_count

        if medium_count > 0:
            images_with_medium += 1
        else:
            images_only_small += 1

    return SizeStatistics(
        pot_threshold=pot_threshold,
        images_only_small=images_only_small,
        images_with_medium=images_with_medium,
        images_no_vehicles=images_no_vehicles,
        total_small_bboxes=total_small_bboxes,
        total_medium_bboxes=total_medium_bboxes,
    )


def bbox_to_yolo(
    bbox: BoundingBox, image_width: int, image_height: int, class_id: int = 0
) -> str:
    """
    Convert a BoundingBox to YOLO format string.

    YOLO format: "{class_id} {x_center} {y_center} {width} {height}"
    All values are normalized to [0, 1] relative to image dimensions.

    Args:
        bbox: BoundingBox object with x1, y1, x2, y2 coordinates
        image_width: Width of the image in pixels
        image_height: Height of the image in pixels
        class_id: Class ID for the object (default 0 for water_vehicle)

    Returns:
        YOLO format string
    """
    # Calculate center and dimensions
    x_center = bbox.center_x / image_width
    y_center = bbox.center_y / image_height
    width = bbox.width / image_width
    height = bbox.height / image_height

    return f"{class_id} {x_center} {y_center} {width} {height}"


class_id_to_obj_type = {
    "water_vehicle": 0,
    "buoy": 1,
    "bird": 2,
}

def image_label_to_yolo(label: ImageLabel) -> str:
    """
    Convert all bounding boxes in an ImageLabel to YOLO format.

    Args:
        label: ImageLabel object
        class_id: Class ID for all objects (default 0 for water_vehicle)

    Returns:
        YOLO format string with one line per bounding box
    """
    lines = []
    for bbox in label.bounding_boxes:
        yolo_line = bbox_to_yolo(bbox, label.image_width, label.image_height, class_id_to_obj_type[bbox.obj_type])
        lines.append(yolo_line)
    return "\n".join(lines)


def save_yolo_labels(
    image_labels: List[ImageLabel], output_dir: str
) -> int:
    """
    Save YOLO format labels to text files.

    Args:
        image_labels: List of ImageLabel objects
        output_dir: Directory to save label files
        class_id: Class ID for all objects (default 0)

    Returns:
        Number of files saved
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    saved_count = 0
    for label in image_labels:
        # Extract image name without path and extension
        img_name = Path(label.filename).stem  # e.g., "46e63d2b..."
        label_filename = f"{img_name}.txt"
        label_path = output_path / label_filename

        # Convert to YOLO format
        yolo_content = image_label_to_yolo(label)

        # Save to file (empty file if no bounding boxes)
        with open(label_path, "w") as f:
            f.write(yolo_content)

        saved_count += 1

    return saved_count



def main():
    # Read label files from ir_labels directory
    IR_LABELS_DIR = (
        "/Users/danielschmid/projects/prs/Tools/bbox_condition_generator_tool/ir_labels"
    )
    labels = read_label_files(IR_LABELS_DIR)

    # Parse all labels into objects
    image_labels = parse_labels(labels)

    # Filter to only water vehicles
    filtered_labels = filter_for_obj_types(image_labels, ["water_vehicle", "buoy", "bird"])

    # Save YOLO labels to output directory
    OUTPUT_DIR = "/Users/danielschmid/projects/prs/Tools/bbox_condition_generator_tool/yolo_labels"
    saved = save_yolo_labels(filtered_labels, OUTPUT_DIR)
    print(f"Saved {saved} label files to {OUTPUT_DIR}")

if __name__ == "__main__":
    main()