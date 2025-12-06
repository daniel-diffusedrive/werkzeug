from pathlib import Path
import pandas as pd

def get_unique_values(csv_path, column_name):
    """
    Get all unique values from a specific column in a CSV file.
    
    Parameters:
    -----------
    csv_path : str or Path
        Path to the CSV file
    column_name : str
        Name of the column to get unique values from
    
    Returns:
    --------
    numpy.ndarray or pandas.Index
        Array of unique values from the specified column
    """
    df = pd.read_csv(csv_path)
    return df[column_name].unique()

def get_dataframes_by_image_id(csv_path, image_id_column='ImageID'):
    """
    Get a dictionary mapping image IDs to their corresponding DataFrames.
    
    Parameters:
    -----------
    csv_path : str or Path
        Path to the CSV file
    image_id_column : str, default='ImageID'
        Name of the column containing image IDs
    
    Returns:
    --------
    dict[str, pd.DataFrame]
        Dictionary where keys are image IDs (strings) and values are DataFrames
        containing all rows for that image ID
    """
    df = pd.read_csv(csv_path)
    return {image_id: group_df for image_id, group_df in df.groupby(image_id_column)}
def get_entry_count_distribution(csv_path, image_id_column='ImageID'):
    """
    Get a dictionary mapping the number of entries per image to the occurrence count.
    
    Parameters:
    -----------
    csv_path : str or Path
        Path to the CSV file
    image_id_column : str, default='ImageID'
        Name of the column containing image IDs
    
    Returns:
    --------
    dict[int, int]
        Dictionary where keys are the number of entries (rows) for an image,
        and values are the occurrence count (how many images have that many entries)
    """
    df = pd.read_csv(csv_path)
    entry_counts = df.groupby(image_id_column).size()
    return dict(entry_counts.value_counts().sort_index())

def get_entry_count_distribution(csv_path, image_id_column='ImageID'):
    """
    Get a dictionary mapping the number of entries per image to the occurrence count.
    
    Parameters:
    -----------
    csv_path : str or Path
        Path to the CSV file
    image_id_column : str, default='ImageID'
        Name of the column containing image IDs
        
    Returns:
    --------
    dict[int, int]
        Dictionary where keys are the number of entries (rows) for an image,
        and values are the occurrence count (how many images have that many entries)
    """
    df = pd.read_csv(csv_path)
    entry_counts = df.groupby(image_id_column).size()
    return dict(entry_counts.value_counts().sort_index())

def load_class_descriptions(csv_path):
    """
    Load class descriptions from CSV into a dictionary.
    
    Parameters:
    -----------
    csv_path : str or Path
        Path to the class descriptions CSV file
    
    Returns:
    --------
    dict[str, str]
        Dictionary mapping LabelName to DisplayName
    """
    df = pd.read_csv(csv_path)
    return dict(zip(df['LabelName'], df['DisplayName']))

import json

def get_labels_by_subcategory(hierarchy_path, target_label_name):
    """
    Get all labels that are subcategories under a target label.
    
    Parameters:
    -----------
    hierarchy_path : str or Path
        Path to the hierarchy JSON file
    target_label_name : str
        The LabelName to search for (e.g., '/m/07yv9' for Vehicle)
    
    Returns:
    --------
    list[str]
        List of all LabelNames that are subcategories under the target label
    """
    with open(hierarchy_path, 'r') as f:
        hierarchy = json.load(f)
    
    def find_entry(node, label_name):
        """Recursively find an entry with the given label name."""
        if isinstance(node, dict):
            if node.get('LabelName') == label_name:
                return node
            # Search in subcategories
            if 'Subcategory' in node:
                for subcat in node['Subcategory']:
                    result = find_entry(subcat, label_name)
                    if result:
                        return result
        elif isinstance(node, list):
            for item in node:
                result = find_entry(item, label_name)
                if result:
                    return result
        return None
    
    def collect_subcategories(node):
        """Recursively collect all label names from subcategories."""
        labels = []
        if isinstance(node, dict):
            # Add current label if it exists
            if 'LabelName' in node:
                labels.append(node['LabelName'])
            # Recursively add subcategories
            if 'Subcategory' in node:
                for subcat in node['Subcategory']:
                    labels.extend(collect_subcategories(subcat))
        return labels
    
    # Find the target entry in the hierarchy
    target_entry = find_entry(hierarchy, target_label_name)
    
    if not target_entry:
        return []
    
    # Collect all subcategories (including the target label itself)
    all_labels = [target_label_name]
    if 'Subcategory' in target_entry:
        for subcat in target_entry['Subcategory']:
            all_labels.extend(collect_subcategories(subcat))
    
    return all_labels

def get_vehicle_labels(hierarchy_path, class_descriptions_path):
    """
    Get all labels that are categorized under Vehicle.
    
    Parameters:
    -----------
    hierarchy_path : str or Path
        Path to the hierarchy JSON file
    class_descriptions_path : str or Path
        Path to the class descriptions CSV file
    
    Returns:
    --------
    list[str]
        List of all LabelNames under the Vehicle category
    """
    # Load class descriptions to find the Vehicle label ID
    class_desc = load_class_descriptions(class_descriptions_path)
    
    # Find the label ID for "Vehicle"
    vehicle_label_id = None
    for label_id, display_name in class_desc.items():
        if display_name == 'Vehicle':
            vehicle_label_id = label_id
            break
    
    if not vehicle_label_id:
        raise ValueError("Vehicle label not found in class descriptions")
    
    return get_labels_by_subcategory(hierarchy_path, vehicle_label_id)

def filter_labels_by_category(image_to_labels, allowed_labels, label_column='LabelName'):
    """
    Filter labels in image_to_labels dictionary to only keep specified labels.
    Images with no labels after filtering are dropped.
    
    Parameters:
    -----------
    image_to_labels : dict[str, pd.DataFrame]
        Dictionary mapping image IDs to DataFrames containing labels
    allowed_labels : list[str]
        List of label names to keep
    label_column : str, default='LabelName'
        Name of the column containing label names
    
    Returns:
    --------
    dict[str, pd.DataFrame]
        Filtered dictionary with only allowed labels, excluding images with no labels
    """
    allowed_labels_set = set(allowed_labels)
    filtered_dict = {}
    
    for image_id, df in image_to_labels.items():
        # Filter to keep only rows with allowed labels
        filtered_df = df[df[label_column].isin(allowed_labels_set)]
        
        # Only keep this image if it has at least one label after filtering
        if len(filtered_df) > 0:
            filtered_dict[image_id] = filtered_df
    
    return filtered_dict

def get_entry_count_distribution_from_dict(image_to_labels):
    """
    Get a dictionary mapping the number of entries per image to the occurrence count.
    Alternative to get_entry_count_distribution that takes image_to_labels dict as input.
    
    Parameters:
    -----------
    image_to_labels : dict[str, pd.DataFrame]
        Dictionary mapping image IDs to DataFrames containing labels
    
    Returns:
    --------
    dict[int, int]
        Dictionary where keys are the number of entries (rows) for an image,
        and values are the occurrence count (how many images have that many entries)
    """
    # Count entries for each image
    entry_counts = {image_id: len(df) for image_id, df in image_to_labels.items()}
    
    # Create distribution: count -> occurrence
    distribution = {}
    for count in entry_counts.values():
        distribution[count] = distribution.get(count, 0) + 1
    
    # Sort by entry count
    return dict(sorted(distribution.items()))

def filter_by_label_attributes(image_to_labels, 
                                is_occluded=0,
                                is_truncated=0,
                                is_group_of=0,
                                is_depiction=0,
                                is_inside=0,
                                confidence=1):
    """
    Filter images where ALL labels meet the specified attribute criteria.
    Images where any label doesn't meet the criteria are dropped entirely.
    
    Parameters:
    -----------
    image_to_labels : dict[str, pd.DataFrame]
        Dictionary mapping image IDs to DataFrames containing labels
    is_occluded : int, default=0
        Required value for IsOccluded column
    is_truncated : int, default=0
        Required value for IsTruncated column
    is_group_of : int, default=0
        Required value for IsGroupOf column
    is_depiction : int, default=0
        Required value for IsDepiction column
    is_inside : int, default=0
        Required value for IsInside column
    confidence : int, default=1
        Required value for Confidence column
    
    Returns:
    --------
    dict[str, pd.DataFrame]
        Filtered dictionary containing only images where all labels meet the criteria
    """
    filtered_dict = {}
    
    for image_id, df in image_to_labels.items():
        # Check if ALL labels in this image meet the criteria
        all_conditions_met = (
            (df['IsOccluded'] == is_occluded).all() and
            (df['IsTruncated'] == is_truncated).all() and
            (df['IsGroupOf'] == is_group_of).all() and
            (df['IsDepiction'] == is_depiction).all() and
            (df['IsInside'] == is_inside).all() and
            (df['Confidence'] == confidence).all()
        )
        
        # Only keep the image if all labels meet the criteria
        if all_conditions_met:
            filtered_dict[image_id] = df
    
    return filtered_dict

def bboxes_overlap(bbox1, bbox2):
    """
    Check if two bounding boxes overlap.
    
    Parameters:
    -----------
    bbox1 : tuple or list
        (xmin, xmax, ymin, ymax) of first bounding box
    bbox2 : tuple or list
        (xmin, xmax, ymin, ymax) of second bounding box
    
    Returns:
    --------
    bool
        True if bounding boxes overlap, False otherwise
    """
    xmin1, xmax1, ymin1, ymax1 = bbox1
    xmin2, xmax2, ymin2, ymax2 = bbox2
    
    # Check for horizontal and vertical overlap
    horizontal_overlap = xmin1 < xmax2 and xmax1 > xmin2
    vertical_overlap = ymin1 < ymax2 and ymax1 > ymin2
    
    return horizontal_overlap and vertical_overlap

def filter_by_bbox_overlap(image_to_labels, keep_overlapping=False):
    """
    Filter images based on whether their bounding boxes overlap.
    
    Parameters:
    -----------
    image_to_labels : dict[str, pd.DataFrame]
        Dictionary mapping image IDs to DataFrames containing labels
    keep_overlapping : bool, default=False
        If False, keep only images WITHOUT any overlapping bounding boxes.
        If True, keep only images WITH at least one overlapping pair.
    
    Returns:
    --------
    dict[str, pd.DataFrame]
        Filtered dictionary based on bounding box overlap criteria
    """
    filtered_dict = {}
    
    for image_id, df in image_to_labels.items():
        has_overlap = False
        
        # Check all pairs of bounding boxes in this image
        if len(df) > 1:
            bboxes = df[['XMin', 'XMax', 'YMin', 'YMax']].values
            
            for i in range(len(bboxes)):
                for j in range(i + 1, len(bboxes)):
                    if bboxes_overlap(bboxes[i], bboxes[j]):
                        has_overlap = True
                        break
                if has_overlap:
                    break
        
        # Keep image based on overlap status and filter criteria
        if keep_overlapping:
            # Keep only images WITH overlaps
            if has_overlap:
                filtered_dict[image_id] = df
        else:
            # Keep only images WITHOUT overlaps
            if not has_overlap:
                filtered_dict[image_id] = df
    
    return filtered_dict

def create_label_to_class_id_mapping(labels):
    """
    Create a mapping from label names to class IDs (0-indexed integers).
    
    Parameters:
    -----------
    labels : list[str]
        List of label names
    
    Returns:
    --------
    dict[str, int]
        Dictionary mapping label names to class IDs (integers 0 to len(labels)-1)
    """
    return {label: idx for idx, label in enumerate(labels)}

def convert_to_yolo_format(image_to_labels, label_to_class_id):
    """
    Convert bounding boxes from (XMin, XMax, YMin, YMax) to YOLO format.
    YOLO format: class_id x_center y_center width height (all normalized 0-1)
    
    Parameters:
    -----------
    image_to_labels : dict[str, pd.DataFrame]
        Dictionary mapping image IDs to DataFrames containing labels
    label_to_class_id : dict[str, int]
        Dictionary mapping LabelName to class_id (integer)
    
    Returns:
    --------
    dict[str, str]
        Dictionary mapping image IDs to YOLO format label strings
        Each string contains one line per label in format:
        "class_id x_center y_center width height"
    """
    yolo_labels = {}
    
    for image_id, df in image_to_labels.items():
        lines = []
        
        for _, row in df.iterrows():
            # Get the class ID for this label
            label_name = row['LabelName']
            if label_name not in label_to_class_id:
                # Skip labels without a class ID mapping
                continue
            
            class_id = label_to_class_id[label_name]
            
            # Convert to YOLO format
            x_center = (row['XMin'] + row['XMax']) / 2
            y_center = (row['YMin'] + row['YMax']) / 2
            width = row['XMax'] - row['XMin']
            height = row['YMax'] - row['YMin']
            
            # Format as string
            line = f"{class_id} {x_center} {y_center} {width} {height}"
            lines.append(line)
        
        # Join all lines for this image
        if lines:  # Only add if there are valid labels
            yolo_labels[image_id] = '\n'.join(lines)
    
    return yolo_labels
