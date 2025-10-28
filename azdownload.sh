#!/bin/bash

folder_name="./"
rm -r $folder_name
mkdir $folder_name

url="https://diffusedrivestorageacc.blob.core.windows.net/azureml/ExperimentRun/dcid.qwen_image_1761579332_28ff6eb6/outputs/train/"
token="?sv=2024-11-04&ss=bfqt&srt=sco&sp=rwdlacupiytfx&se=2026-03-31T18:00:03Z&st=2025-10-24T09:45:03Z&spr=https&sig=MdSwNudPcQzEt1f%2BNezx16D3uFB15ws4RrC1tykQL4U%3D"

azcopy copy \
    "$url$token" \
    $folder_name \
    --recursive

