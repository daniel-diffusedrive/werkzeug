#!/bin/bash

# Define arrays of folder names and corresponding URLs

folder_prefix="/Users/danielschmid/data_filtering/data-batch-2/"
folder_names=(
    $folder_prefix"uav/open_water/background-birds-buoys-only/anduril_inference-inference-20251111-151221-_anduril_eo_r64_1_UAV_Open_Water_No_water_vehicle_only_birds_buoys_1_v3"
    $folder_prefix"uav/open_water/background-no-objects/anduril_inference-inference-20251111-151620-_anduril_eo_r64_1_UAV_Open_Water_No_objects_only_background_3_v3"
    $folder_prefix"usv/open_water/background-birds-buoys-only/anduril_inference-inference-20251111-151352-_anduril_eo_r64_3_USV_Open_Water_No_water_vehicle_only_birds_buoys_1_v3"
)

url_prefix="https://diffusedrivestorageacc.blob.core.windows.net/azureml/ExperimentRun/"
url_suffix="/outputs/generated_images/"
urls=(
    $url_prefix"dcid.anduril_inference_1762870336_e5440acd"$url_suffix
    $url_prefix"dcid.anduril_inference_1762870575_f8cd8eeb"$url_suffix
    $url_prefix"dcid.anduril_inference_1762870426_7b8bf3b6"$url_suffix
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
