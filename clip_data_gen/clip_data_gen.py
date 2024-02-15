import os
import json
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from multiprocessing import set_start_method, Lock
import torch

# Importing custom functions
from functions import process_image_annotation

# Configuration parameters
in_dir = "/mnt/nis_lab_research/data/coco_files/raw/shah_b1_539_21"
out_dir = "/mnt/nis_lab_research/data/clip_data/test"
out_res_w = 224
out_res_h = 224
bg_color = "white"
batch_size = 30  # Define the size of each batch

def process_batch(batch, out_dir, cat_map, bg_color, out_res_w, out_res_h, print_lock, gpu_id):
    os.environ['CUDA_VISIBLE_DEVICES'] = str(gpu_id)
    with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
        futures = {}
        for img_fp, img_bn, ann, cat_id, j in batch:
            future = executor.submit(process_image_annotation, img_fp, out_dir, img_bn, ann, cat_map, cat_id, bg_color, out_res_w, out_res_h, j)
            futures[future] = (img_bn, j)
        
        completed = 0
        for future in as_completed(futures):
            try:
                result = future.result()
                with print_lock:
                    completed += 1
                    print(f"Completed images: {completed}/{len(batch)}, Batch item: {futures[future]}")
            except Exception as exc:
                print(f"Generated an exception: {exc}")

def main():
    # Load JSON data
    with open(os.path.join(in_dir, "result.json")) as f:
        obj = json.load(f)

    img_list = obj["images"]
    ann_list = obj["annotations"]
    cat_list = obj["categories"]

    # Create category map
    cat_map = [cat["name"] for cat in cat_list]
    cat_map = sorted(cat_map)

    # Ensure output directories exist
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    for cat in cat_list:
        os.makedirs(os.path.join(out_dir, cat["name"]), exist_ok=True)

    # Initialize multiprocessing
    set_start_method('spawn', True)
    print_lock = Lock()

    # Check CUDA availability and clear cache
    torch.cuda.empty_cache()
    num_gpus = torch.cuda.device_count()
    gpu_round_robin = 0
    
    # Process images in batches
    current_batch = []
    for i, img in enumerate(img_list):
        img_bn = os.path.basename(img["file_name"])[0:-4]
        img_fp = os.path.join(in_dir, "images", os.path.basename(img["file_name"]))
        img_id = img["id"]
        
        for j, ann in enumerate(ann_list):
            ann_img_id = ann["image_id"]
            cat_id = ann["category_id"]
            if img_id == ann_img_id:
                current_batch.append((img_fp, img_bn, ann, cat_id, j))
                
                # Process the current batch if it reaches the batch size
                if len(current_batch) >= batch_size:
                    gpu_id = gpu_round_robin % num_gpus  # Determine which GPU to use
                    process_batch(current_batch, out_dir, cat_map, bg_color, out_res_w, out_res_h, print_lock, gpu_id)
                    current_batch = []  # Reset the batch
                    gpu_round_robin += 1  # Move to the next GPU for the next batch

    # Process any remaining images in the last batch
    if current_batch:
        gpu_id = gpu_round_robin % num_gpus
        process_batch(current_batch, out_dir, cat_map, bg_color, out_res_w, out_res_h, print_lock, gpu_id)

if __name__ == "__main__":
    main()

