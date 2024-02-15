import os
import json
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import set_start_method, Lock
import torch
import time
from threading import Thread, Event
from queue import Queue

# Importing custom functions
from functions import process_image_annotation

# Configuration parameters
in_dir = "/mnt/nis_lab_research/data/coco_files/raw/shah_b1_539_21"
out_dir = "/mnt/nis_lab_research/data/clip_data/test"
out_res_w = 224
out_res_h = 224
bg_color = "white"
batch_size = 2  # Define the size of each batch
memory_utilization_threshold = 0.75  # Threshold for considering GPU underutilized
time_int_check = 1  # Time interval (in seconds) for checking GPU utilization
gpus_to_use = [0, 1]  # Specify which GPUs to use

def check_gpu_memory_utilization(threshold, gpu_id):
    torch.cuda.set_device(gpu_id)
    total_memory = torch.cuda.get_device_properties(gpu_id).total_memory
    memory_allocated = torch.cuda.memory_allocated(gpu_id)
    memory_free = total_memory - memory_allocated
    return (memory_free / total_memory) > threshold

def process_batch(batch, out_dir, cat_map, bg_color, out_res_w, out_res_h, print_lock, gpu_id):
    os.environ['CUDA_VISIBLE_DEVICES'] = str(gpu_id)
    with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
        futures = [executor.submit(process_image_annotation, img_fp, out_dir, img_bn, ann, cat_map, cat_id, bg_color, out_res_w, out_res_h, ann_ctr)
                   for img_fp, img_bn, ann, cat_id, ann_ctr in batch]
        
        for future in as_completed(futures):
            try:
                result = future.result()
                with print_lock:
                    print(f"Completed on GPU: {gpu_id}, Result: {result}")
            except Exception as exc:
                print(f"Generated an exception: {exc}")

def gpu_worker(gpu_id, batches_queue, cat_map, bg_color, out_res_w, out_res_h, print_lock, start_event, stop_event):
    start_event.wait()
    while not stop_event.is_set():
        try:
            batch = batches_queue.get(timeout=time_int_check)  # Blocking get with timeout
            print("Processing batch")
            process_batch(batch, out_dir, cat_map, bg_color, out_res_w, out_res_h, print_lock, gpu_id)
        except Queue.Empty:
            print("Waiting for batches...")

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

    torch.cuda.empty_cache()
    stop_event = Event() # Event to signal the threads to stop
    start_event = Event() # Event to signal the threads to start

    # Initialize GPU worker threads
    gpu_batches_queues = [Queue() for _ in gpus_to_use]
    worker_threads = []
    for i, gpu_id in enumerate(gpus_to_use):
        t = Thread(target=gpu_worker, args=(gpu_id, gpu_batches_queues[i], cat_map, bg_color, out_res_w, out_res_h, print_lock,start_event, stop_event))
        t.start()
        worker_threads.append(t)

    # Process images in batches and distribute them across GPUs
    current_batch = []
    for img in img_list[0:2]:
        img_bn = os.path.basename(img["file_name"])[0:-4]
        img_fp = os.path.join(in_dir, "images", os.path.basename(img["file_name"]))
        img_id = img["id"]
        
        for ann_ctr, ann in enumerate(ann_list):
            ann_img_id = ann["image_id"]
            cat_id = ann["category_id"]
            if img_id == ann_img_id:
                current_batch.append((img_fp, img_bn, ann, cat_id, ann_ctr))
                
                if len(current_batch) >= batch_size:
                    # Dynamically assign batches based on GPU memory utilization
                    assigned = False
                    while not assigned:
                        for i, gpu_id in enumerate(gpus_to_use):
                            if check_gpu_memory_utilization(memory_utilization_threshold, gpu_id):
                                gpu_batches_queues[i].put(current_batch)
                                current_batch = []
                                assigned = True
                                break
                        if not assigned:
                            time.sleep(time_int_check)  # Wait and retry
                            
    # After queuing initial batches, signal the worker threads to start
    start_event.set()

    # Handle the last partial batch
    if current_batch:
        for i, gpu_id in enumerate(gpus_to_use):
            if check_gpu_memory_utilization(memory_utilization_threshold, gpu_id):
                gpu_batches_queues[i].append(current_batch)
                break

    # Signal to stop and wait for all worker threads to finish
    stop_event.set()
    for t in worker_threads:
        t.join()

    print("All GPU workers have completed.")

if __name__ == "__main__":
    main()
