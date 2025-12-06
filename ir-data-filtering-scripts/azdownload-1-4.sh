#!/bin/bash

# Define arrays of folder names and corresponding URLs

folder_prefix="/Users/danielschmid/data_filtering/data/"
folder_names=(
    $folder_prefix"usv/open_water/1-4-water-vehicles/anduril_inference-inference-20251107-140024-anduril_eo_r64_17_usv_open-water_water-vehicles-1-4-per-image_711_v1"
    $folder_prefix"usv/coastline/1-4-water-vehicles/anduril_inference-inference-20251107-153827-anduril_eo_r64_14_usv_coastline_water-vehicles-1-4-per-image_343_v2"
)


url_prefix="https://diffusedrivestorageacc.blob.core.windows.net/azureml/ExperimentRun/"
url_suffix="/outputs/generated_images/"
urls=(
    $url_prefix"dcid.anduril_inference_1762520416_8a98c3c8"$url_suffix
    $url_prefix"dcid.anduril_inference_1762526302_c8c906c9"$url_suffix
)


token="?sv=2024-11-04&ss=bfqt&srt=sco&sp=rwdlacupiytfx&se=2026-03-31T18:00:03Z&st=2025-10-24T09:45:03Z&spr=https&sig=MdSwNudPcQzEt1f%2BNezx16D3uFB15ws4RrC1tykQL4U%3D"

for i in "${!folder_names[@]}"; do
    folder_name="${folder_names[$i]}"
    url="${urls[$i]}"

    rm -r "$folder_name"
    mkdir "$folder_name"

    azcopy copy \
        "${url}${token}" \
        "$folder_name" \
        --recursive
    
    mv $folder_name/generated_images/* $folder_name/
    rm -r $folder_name/generated_images
done
