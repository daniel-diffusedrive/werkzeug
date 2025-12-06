#!/bin/bash
set -e

# Define arrays of folder names and corresponding URLs
folder_prefix="/Users/danielschmid/reselect-anduril/workspace-data/"
folder_names=(
    $folder_prefix"1-UAV_Open_Water_Water_vehicles_1-4_per_image_maximum_5_birds_approximately_4-6_buoys"
    $folder_prefix"2-UAV_Open_Water_Water_vehicles_1-4_per_image_maximum_5_birds_approximately_4-6_buoys"
    $folder_prefix"3-UAV_Open_Water_Water_vehicles_1-4_per_image_maximum_5_birds_approximately_4-6_buoys"
    $folder_prefix"4-UAV_Open_Water_Water_vehicles_1-4_per_image_maximum_5_birds_approximately_4-6_buoys"
    $folder_prefix"5-UAV_Open_Water_Water_vehicles_1-4_per_image_maximum_5_birds_approximately_4-6_buoys"
)

url_prefix="https://diffusedrivestorageacc.blob.core.windows.net/azureml/ExperimentRun/"
url_suffix="/outputs/generated_images/"
urls=(
    $url_prefix"dcid.anduril_eo_object_count_fix_1764162844_9ded5fa2"$url_suffix
    $url_prefix"dcid.anduril_eo_object_count_fix_1764162889_88dc984f"$url_suffix
    $url_prefix"dcid.anduril_eo_object_count_fix_1764162934_774acf04"$url_suffix
    $url_prefix"dcid.anduril_eo_object_count_fix_1764162977_e7c5c879"$url_suffix
    $url_prefix"dcid.anduril_eo_object_count_fix_1764163020_e871de28"$url_suffix
)

token="?sv=2024-11-04&ss=bfqt&srt=sco&sp=rwdlacupiytfx&se=2026-03-31T18:00:03Z&st=2025-10-24T09:45:03Z&spr=https&sig=MdSwNudPcQzEt1f%2BNezx16D3uFB15ws4RrC1tykQL4U%3D"

# Create a temporary directory for downloads
TMP_DIR="tmp_download"

cleanup() {
    if [ -d "$TMP_DIR" ]; then
        echo "Cleaning up temporary directory..."
        rm -rf "$TMP_DIR"
    fi
}
trap cleanup EXIT

for i in "${!folder_names[@]}"; do
    folder_name="${folder_names[$i]}"
    url="${urls[$i]}"
    
    echo "Processing target: $folder_name"
    
    # Ensure tmp dir is clean
    rm -rf "$TMP_DIR"
    mkdir -p "$TMP_DIR"
    
    echo "Downloading to temporary folder..."
    # Using azcopy to download files
    azcopy copy \
        "${url}${token}" \
        "$TMP_DIR" \
        --recursive > /dev/null
    
    # Flatten directory structure if needed (handle generated_images subfolder)
    if [ -d "$TMP_DIR/generated_images" ]; then
        echo "Flattening directory structure..."
        mv "$TMP_DIR/generated_images"/* "$TMP_DIR/" 2>/dev/null || true
        rm -rf "$TMP_DIR/generated_images"
    fi
    
    echo "Updating dataset via Python script..."
    # Call the python script to merge new data
    python3 update_dataset.py --main "$folder_name" --tmp "$TMP_DIR"
    
done

echo "Update process completed successfully."
