#!/bin/bash

# Define arrays of folder names and corresponding URLs



folder_prefix="/Users/danielschmid/data_filtering/data/"
folder_names=(
    $folder_prefix"ir/checking/uav/open_water/water-vehicles-10-14-per-image/anduril_ir_inference-inference-20251113-161206-_anduril_ir_r16_10_UAV_Open_Water_Water_vehicles_10-14_per_image_2_v2"
    $folder_prefix"ir/checking/usv/open_water/water-vehicles-1-4-per-image/anduril_ir_inference-inference-20251113-162125-_anduril_ir_r16_16_USV_Open_Water_Water_vehicles_1-4_per_image_11_v2"
    $folder_prefix"ir/checking/usv/open_water/water-vehicles-1-4-per-image/anduril_ir_inference-inference-20251115-230011-_anduril_ir_r16_3_USV_Open_Water_Water_vehicles_1-4_per_image_11_extra_imgs_v1"
    $folder_prefix"ir/checking/usv/open_water/water-vehicles-1-4-per-image/anduril_ir_inference-inference-20251115-230647-_anduril_ir_r16_3_USV_Open_Water_Water_vehicles_1-4_per_image_11_extra_imgs_negative_prompt"
)

url_prefix="https://diffusedrivestorageacc.blob.core.windows.net/azureml/ExperimentRun/"
url_suffix="/outputs/generated_images/"
urls=(
    $url_prefix"dcid.anduril_ir_inference_1763046721_c8a2effd"$url_suffix
    $url_prefix"dcid.anduril_ir_inference_1763047279_f4986fc3"$url_suffix
    $url_prefix"dcid.anduril_ir_inference_1763244007_32cc2771"$url_suffix
    $url_prefix"dcid.anduril_ir_inference_1763244401_e307c58e"$url_suffix
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
