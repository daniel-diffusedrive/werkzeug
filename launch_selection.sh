#!/bin/bash

# replace with your directory path that contains the categorization
base_dir="/Users/danielschmid/reselect-anduril/ir-xtra-0"

echo "Launching selection for datasets in: $base_dir"
for subsubdir in "$base_dir"/*; do
  # [[ -d "$subsubdir" ]] || continue

  dataset_name="$(basename "$subsubdir")"
  # Match directories that contain UAV or USV (case-insensitive)
  #[[ "$dataset_name" == *[Uu][Aa][Vv]* || "$dataset_name" == *[Uu][Ss][Vv]* ]] || continue
  echo "Launching selection for dataset: $dataset_name"
  cmd=(
    python /Users/danielschmid/projects/Tools/image_selection_tool/img_selection_tool.py
    --input-folder "$subsubdir/further_eval"
    --output-folder "$subsubdir/further_eval"
  )

  if [[ "$dataset_name" == *open_water* ]]; then
    cmd+=(--reversed-ranking)
  fi

  "${cmd[@]}"
done
