#!/bin/bash

# Define arrays of folder names and corresponding URLs

folder_prefix="/Users/danielschmid/data_filtering/data/"
folder_names=(
    $folder_prefix"uav/open_water/background-birds-buoys-only/anduril_inference-inference-20251106-173342-anduril_eo_r64_2_USV_Open_Water_Background_birds_buoys_only_1_v1"
    $folder_prefix"uav/open_water/background-birds-buoys-only/anduril_inference-inference-20251107-092940-anduril_eo_r64_2_usv_open-water_background-birds-buoys-only_9_v1"
    $folder_prefix"uav/open_water/background-birds-buoys-only/anduril_inference-inference-20251107-133005-anduril_eo_r64_2_usv_open-water_background-birds-buoys-only_9_v1"
    $folder_prefix"uav/open_water/background-birds-buoys-only/anduril_inference-inference-20251107-153242-anduril_eo_r64_2_usv_open-water_background-birds-buoys-only_9_v2"
    $folder_prefix"uav/open_water/background-no-objects/anduril_inference-inference-20251107-153627-anduril_eo_r64_10_uav_open-water_background-no-objects-of-interest_112_v2"
    $folder_prefix"usv/open_water/background-birds-buoys-only/anduril_inference-inference-20251107-153147-anduril_eo_r64_0_usv_coastline_background-birds-buoys-only_4_v2"
    $folder_prefix"usv/open_water/background-birds-buoys-only/anduril_inference-inference-20251106-170821-anduril_eo_r64_0_USV_Coastline_Background_birds_buoys_only_1_v1"
    $folder_prefix"usv/open_water/background-birds-buoys-only/anduril_inference-inference-20251107-092838-anduril_eo_r64_0_usv_coastline_background-birds-buoys-only_4_v1"
    $folder_prefix"usv/open_water/background-birds-buoys-only/anduril_inference-inference-20251107-132910-anduril_eo_r64_0_usv_coastline_background-birds-buoys-only_4_v1"
    $folder_prefix"usv/open_water/background-birds-buoys-only/anduril_inference-inference-20251107-144334-anduril_eo_r64_0_usv_coastline_background-birds-buoys-only_4_v2"

)


# $folder_prefix"usv/open_water/1-4-water-vehicles/0" TODO
# $folder_prefix"usv/coastline/1-4-water-vehicles/0" TODO


url_prefix="https://diffusedrivestorageacc.blob.core.windows.net/azureml/ExperimentRun/"
url_suffix="/outputs/generated_images/"
urls=(
    $url_prefix"dcid.anduril_inference_1762446816_181f971b"$url_suffix
    $url_prefix"dcid.anduril_inference_1762504175_014e8ab5"$url_suffix
    $url_prefix"dcid.anduril_inference_1762518599_49942e7f"$url_suffix
    $url_prefix"dcid.anduril_inference_1762525958_6265ced1"$url_suffix
    $url_prefix"dcid.anduril_inference_1762526181_9494dbb3"$url_suffix
    $url_prefix"dcid.anduril_inference_1762525902_281bebd3"$url_suffix
    $url_prefix"dcid.anduril_inference_1762445295_e83094cc"$url_suffix
    $url_prefix"dcid.anduril_inference_1762504110_47bb327b"$url_suffix
    $url_prefix"dcid.anduril_inference_1762518544_fa246676"$url_suffix
    $url_prefix"dcid.anduril_inference_1762523006_a04c756e"$url_suffix
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
