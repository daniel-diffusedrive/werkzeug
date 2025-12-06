#!/bin/bash

# Define arrays of folder names and corresponding URLs



folder_prefix="/Users/danielschmid/data_filtering/data/"
folder_names=(
    $folder_prefix"ir/checking/uav/open_water/water-vehicles-10-14-per-image/anduril_ir_inference-inference-20251111-230551-_anduril_ir_r16_10_UAV_Open_Water_Water_vehicles_10-14_per_image_2_v4"
    $folder_prefix"ir/checking/uav/coastline/water-vehicles-5-9-per-image/anduril_ir_inference-inference-20251111-204117-_anduril_ir_r16_3_UAV_Coastline_Water_vehicles_5-9_per_image_7_v1"
    $folder_prefix"ir/checking/usv/open_water/water-vehicles-1-4-per-image/anduril_ir_inference-inference-20251111-231516-_anduril_ir_r16_16_USV_Open_Water_Water_vehicles_1-4_per_image_11_v4"

)

url_prefix="https://diffusedrivestorageacc.blob.core.windows.net/azureml/ExperimentRun/"
url_suffix="/outputs/generated_images/"
urls=(
    $url_prefix"dcid.anduril_ir_inference_1762898746_bc0292c8"$url_suffix
    $url_prefix"dcid.anduril_ir_inference_1762890070_6c5a529a"$url_suffix
    $url_prefix"dcid.anduril_ir_inference_1762899311_848b49d7"$url_suffix
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
