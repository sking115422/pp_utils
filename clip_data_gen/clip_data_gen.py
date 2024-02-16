import os
import json
import torch
import multiprocessing
from multiprocessing import Process, Queue, current_process, set_start_method
import time
import GPUtil
from functions import process_image_annotation

# Global Variables
in_dir = "/mnt/nis_lab_research/data/coco_files/raw/shah_b1_539_21"
out_dir = "/mnt/nis_lab_research/data/clip_data/shah_b1_539_21"
out_res_w = 224
out_res_h = 224
bg_color = "white"
padding = 0.05
check_interval = .1
wait_interval = .05
gpu_id = 0
num_workers = 20

def worker(input_queue, gpu_id):
    """
    Worker function to process tasks. Manually clears GPU memory after each task.
    """
    torch.cuda.set_device(gpu_id)  # Ensure this worker uses the correct GPU

    while True:
        task = input_queue.get()
        if task is None:
            break  # End of task signal

        img_fp, out_dir, img_bn, ann, cat_map, cat_id, bg_color, out_res_w, out_res_h, j = task
        
        try:
            process_image_annotation(img_fp, out_dir, img_bn, ann, cat_map, cat_id, bg_color, out_res_w, out_res_h, j)
        finally:
            torch.cuda.empty_cache()  # Free unused memory from PyTorch
        
        print(f"{current_process().name} -> processed task: {j}")

    torch.cuda.empty_cache()

def main(gpu_id):
    
    torch.cuda.empty_cache()
    torch.cuda.set_device(gpu_id)
    
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
    input_queue = Queue()

    # Start worker processes
    processes = [Process(target=worker, args=(input_queue, gpu_id)) for _ in range(num_workers)]
    for p in processes:
        p.start()
    
    ctr = 0
    # Submit tasks to the queue
    for i, img in enumerate(img_list):
        print("OG IMG", i, "STARTED")
        img_bn = os.path.basename(img["file_name"])[0:-4]
        img_fp = os.path.join(in_dir, "images", os.path.basename(img["file_name"]))
        img_id = img["id"]
        
        for j, ann in enumerate(ann_list):
            ann_img_id = ann["image_id"]
            cat_id = ann["category_id"]
            if img_id == ann_img_id:

                task = (img_fp, out_dir, img_bn, ann, cat_map, cat_id, bg_color, out_res_w, out_res_h, j)
                input_queue.put(task)
                time.sleep(wait_interval)
                
                ctr += 1
                
    print(f"Total Tasks: {ctr}")
    
    # Signal the worker processes to exit by sending a 'None' value for each worker
    for _ in range(num_workers):
        input_queue.put(None)
    
    # Wait for all worker processes to finish
    for p in processes:
        p.join()

if __name__ == "__main__":
    main(gpu_id)

