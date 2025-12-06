#!/bin/bash

# Define arrays of folder names and corresponding URLs

folder_prefix="/Users/danielschmid/data_filtering/data-new-batch/"
folder_names=(
    $folder_prefix"uav/open_water/background-birds-buoys-only/anduril_inference-inference-20251110-155341-_anduril_eo_r64_1_UAV_Open_Water_No_water_vehicle_only_birds_buoys_1_v3"
    $folder_prefix"uav/open_water/background-no-objects/anduril_inference-inference-20251110-165530-_anduril_eo_r64_1_UAV_Open_Water_No_objects_only_background_3_v3"
    $folder_prefix"usv/open_water/background-birds-buoys-only/anduril_inference-inference-20251110-155510-_anduril_eo_r64_3_USV_Open_Water_No_water_vehicle_only_birds_buoys_1_v3"
)

url_prefix="https://diffusedrivestorageacc.blob.core.windows.net/azureml/ExperimentRun/"
url_suffix="/outputs/generated_images/"
urls=(
    $url_prefix"dcid.anduril_inference_1762786416_51e3d5f9"$url_suffix
    $url_prefix"dcid.anduril_inference_1762790123_e314e1cd"$url_suffix
    $url_prefix"dcid.anduril_inference_1762786505_7446203f"$url_suffix
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
