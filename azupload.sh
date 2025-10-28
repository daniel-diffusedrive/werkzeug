#!/bin/bash

folder_name="/home/azureuser/data/openpose/openpose_hf_20k/"


url="https://diffusedrivestorageacc.blob.core.windows.net/azureml-blobstore-53d2c46a-b95b-4363-ac63-5d35e0361fee/ExplorerUpload/hugging_face_datasets/open_pose/openpose_hf_20k/"
token="?sv=2024-11-04&ss=bfqt&srt=sco&sp=rwdlacupiytfx&se=2026-03-31T18:00:03Z&st=2025-10-24T09:45:03Z&spr=https&sig=MdSwNudPcQzEt1f%2BNezx16D3uFB15ws4RrC1tykQL4U%3D"

azcopy copy \
    $folder_name \
    "$url$token" \
    --recursive

