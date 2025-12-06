from pathlib import Path
import json
import shutil

m_folder = Path("/Users/danielschmid/data_filtering/data/ir/checking-additional/") 
prompt = None # "usv/open_water/water-vehicles-1-4" # "uav-open-water-background-no-objects" # None # "usv-open-water-background-birds-buoys-only" # "uav-open-water-background-no-objects" #None# "usv-open-water-1-4-water-vehicles"

metadata_list = []

for folder in m_folder.iterdir():
    if folder.is_dir():
        metadata_file = folder / "metadata.jsonl"
        with open(metadata_file, "r") as f:
            metadata = [json.loads(line) for line in f] 
        
        metadata_converted = []
        for x in metadata:
            x['img_name'] = folder.name + "/" + x['img_name']
            if prompt:
                x['prompt'] = prompt
            metadata_converted.append(x)
        
        metadata_list.extend(metadata_converted)
    else:
        folder.unlink()
with open(m_folder / "metadata.jsonl", "w") as f:
    for x in metadata_list:
        f.write(json.dumps(x) + "\n")