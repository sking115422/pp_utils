import os
import json
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from multiprocessing import set_start_method, Lock
import torch
import time
from threading import Thread

# Importing custom functions
from functions import process_image_annotation

# Configuration parameters
in_dir = "/mnt/nis_lab_research/data/coco_files/raw/shah_b1_539_21"
out_dir = "/mnt/nis_lab_research/data/clip_data/test"
out_res_w = 224
out_res_h = 224
bg_color = "white"
batch_size = 20  # Define the size of each batch
memory_utilization_threshold = 0.75  # GPUs with memory utilization below this threshold are considered underutilized
time_int_check = .5  # Time interval (in seconds) for checking GPU utilization
gpus_to_use = [0, 1]
shutdown_flag = False # Global flag to signal threads to stop

def check_gpu_memory_utilization(threshold):
    underutilized_gpus = []
    for i in gpus_to_use:
        torch.cuda.set_device(i)
        total_memory = torch.cuda.get_device_properties(i).total_memory
        memory_allocated = torch.cuda.memory_allocated(i)
        memory_free = total_memory - memory_allocated
        if (memory_free / total_memory) > threshold:
            underutilized_gpus.append(i)
    return underutilized_gpus

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

def gpu_worker(gpu_id, batches_queue, cat_map, bg_color, out_res_w, out_res_h, print_lock):
    global shutdown_flag
    while not shutdown_flag or batches_queue:  # Keep running until signaled to shutdown or queue is empty
        if batches_queue:
            batch = batches_queue.pop(0)
            process_batch(batch, out_dir, cat_map, bg_color, out_res_w, out_res_h, print_lock, gpu_id)
        else:
            time.sleep(time_int_check)  # Wait for the next interval or for new batches

    # Perform any cleanup here if necessary
    print(f"GPU Worker {gpu_id} shutting down.")

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

    # Initialize GPU worker threads
    gpu_batches_queues = [[] for _ in range(num_gpus)]  # Create a queue for each GPU
    worker_threads = []
    for gpu_id in range(num_gpus):
        t = Thread(target=gpu_worker, args=(gpu_id, gpu_batches_queues[gpu_id], cat_map, bg_color, out_res_w, out_res_h, print_lock))
        t.start()
        worker_threads.append(t)

    # Process images in batches and distribute them across GPUs
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
                    underutilized_gpus = check_gpu_memory_utilization(memory_utilization_threshold)
                    if underutilized_gpus:
                        # Choose the least utilized GPU that has the shortest queue
                        target_gpu = min(underutilized_gpus, key=lambda gpu: len(gpu_batches_queues[gpu]))
                        gpu_batches_queues[target_gpu].append(current_batch)
                    current_batch = []  # Reset the batch

    # Ensure all batches are assigned to a GPU queue
    if current_batch:
        least_loaded_gpu = min(range(num_gpus), key=lambda gpu: len(gpu_batches_queues[gpu]))
        gpu_batches_queues[least_loaded_gpu].append(current_batch)
        
    global shutdown_flag
    shutdown_flag = True  # Signal all threads to shutdown

    for t in worker_threads:
        t.join()  # Wait for all threads to complete

    print("All GPU workers have completed.")

if __name__ == "__main__":
    main()

