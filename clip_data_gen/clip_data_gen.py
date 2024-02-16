import os
import json
import torch
from multiprocessing import set_start_method
from concurrent.futures import ProcessPoolExecutor, as_completed
from threading import Lock
from functions import process_image_annotation  # Assuming this is where process_image_annotation and any other custom functions are defined
import time

# Global Varibles
in_dir = "/mnt/nis_lab_research/data/coco_files/raw/shah_b1_539_21"
out_dir = "/mnt/nis_lab_research/data/clip_data/test"
out_res_w = 224
out_res_h = 224
bg_color = "white"
padding = 0.05
mem_util_thold = .75
check_interval = 1
wait_interval = .5
gpu_id = 0  

def check_gpu_memory(mem_util_thold, gpu_id):
    """
    Check if the GPU memory usage on a specific device is above the mem_util_thold.
    Returns True if memory usage is above the mem_util_thold; False otherwise.
    """
    torch.cuda.set_device(gpu_id)  # Set the device to the specified GPU
    torch.cuda.synchronize(gpu_id)
    total_memory = torch.cuda.get_device_properties(gpu_id).total_memory
    memory_reserved = torch.cuda.memory_reserved(gpu_id)
    memory_utilization = (memory_reserved / total_memory)
    return memory_utilization > mem_util_thold

def check_mem_util_thold(mem_util_thold, check_interval, gpu_id):
    """
    Wait until the GPU memory utilization on a specific device drops below the given mem_util_thold.
    """
    while check_gpu_memory(mem_util_thold, gpu_id):
        print(f"GPU memory usage above {mem_util_thold*100}%, waiting...")
        time.sleep(check_interval)  # Sleep for a bit before checking again

def main(gpu_id):
    torch.cuda.set_device(gpu_id)  # Ensure we're working with the correct GPU
    
    with open(os.path.join(in_dir, "result.json")) as f:
        obj = json.load(f)
    
    img_list = obj["images"]
    cat_list = obj["categories"]
    ann_list = obj["annotations"]
    
    cat_map = [cat["name"] for cat in cat_list]
    
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    for cat in cat_list:
        os.makedirs(os.path.join(out_dir, cat["name"]), exist_ok=True)
        
    set_start_method('spawn', True)
    print_lock = Lock()
        
    with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
        
        futures = {}
        for i, img in enumerate(img_list):
            print("OG IMG", i, "STARTED")
            img_bn = os.path.basename(img["file_name"])[0:-4]
            img_fp = os.path.join(in_dir, "images", os.path.basename(img["file_name"]))
            img_id = img["id"]
            for j, ann in enumerate(ann_list):
                ann_img_id = ann["image_id"]
                cat_id = ann["category_id"]
                if img_id == ann_img_id:
                    if check_gpu_memory(mem_util_thold, gpu_id):
                        check_mem_util_thold(mem_util_thold, check_interval, gpu_id)
                    future = executor.submit(process_image_annotation, img_fp, out_dir, img_bn, ann, cat_map, cat_id, bg_color, out_res_w, out_res_h, j)
                    futures[future] = (i, j)
                    time.sleep(wait_interval)
                
            completed = 0
            for future in as_completed(futures):
                try:
                    result = future.result()
                    with print_lock:
                        completed += 1
                        print(f"Completed images: {completed}, {futures[future]}")
                except Exception as exc:
                    print(f"Generated an exception: {exc}")

if __name__ == "__main__":
    main(gpu_id)
