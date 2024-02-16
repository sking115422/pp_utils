import os
import json
import random
import string
from PIL import Image
import pytesseract
import easyocr
import numpy as np
import torch

def process_image_annotation(img_fp, out_dir, img_bn, ann, cat_map, cat_id, bg_color, out_res_w, out_res_h, j):
    
        elem_img = crop_image(img_fp, ann["bbox"], 0.05)
        e_w = elem_img.size[0]
        e_h = elem_img.size[1]
        
        if e_w < out_res_w and e_h < out_res_h:
            elem_img = paste_to_bg(elem_img, bg_color, out_res_w, out_res_h)
        elif e_w < out_res_w and e_h >= out_res_h:
            elem_img = resize_ar_lock(elem_img, (e_w, out_res_h))
            elem_img = paste_to_bg(elem_img, bg_color, out_res_w, out_res_h)
        elif e_w >= out_res_w and e_h < out_res_h:
            elem_img = resize_ar_lock(elem_img, (out_res_w, e_h))
            elem_img = paste_to_bg(elem_img, bg_color, out_res_w, out_res_h)
        else:
            elem_img = resize_ar_lock(elem_img, (out_res_w, out_res_h))
            elem_img = paste_to_bg(elem_img, bg_color, out_res_w, out_res_h)
        
        elem_img.save(os.path.join(out_dir, cat_map[cat_id], img_bn + "-" + str(j) + ".png"), "PNG")
        
        elem_img_ocr = crop_image(img_fp, ann["bbox"], 0.25)
        ocr_txt = easy_ocr(elem_img_ocr)
        with open(os.path.join(out_dir, cat_map[cat_id], img_bn + "-" + str(j) + ".txt"), "w+") as f:
            f.write(ocr_txt)
            
def crop_image(file_path, bounding_box, padding):
    
    with Image.open(file_path) as img:
        
        x_min, y_min, width, height = bounding_box

        # Calculate padding in pixels
        pad_width = int(width * padding)
        pad_height = int(height * padding)

        # Adjust the bounding box with padding
        x_min = max(x_min - pad_width, 0)
        y_min = max(y_min - pad_height, 0)
        x1 = min(x_min + width + 2 * pad_width, img.width)
        y1 = min(y_min + height + 2 * pad_height, img.height)
        
        cropped_img = img.crop((x_min, y_min, x1, y1))
        
        return cropped_img
    
def paste_to_bg(image, background_color, bg_width, bg_height):
    
    # Create a new image with the specified background color and dimensions
    background = Image.new('RGB', (bg_width, bg_height), background_color)

    # Calculate the position to paste the image so it's centered
    x = (bg_width - image.width) // 2
    y = (bg_height - image.height) // 2

    # Paste the image onto the background
    background.paste(image, (x, y), image if image.mode == 'RGBA' else None)

    return background

def resize_ar_lock(img, target_size):

    original_width, original_height = img.size
    target_width, target_height = target_size

    # Calculate scaling factor
    scaling_factor = min(target_width / original_width, target_height / original_height)

    # Calculate new dimensions
    new_width = max(int(original_width * scaling_factor), 1)
    new_height = max(int(original_height * scaling_factor), 1)

    # Resize the image
    resized_img = img.resize((new_width, new_height))

    return resized_img

def gen_rand_str(length):
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(characters) for i in range(length))
    return random_string

def tess_ocr(image):
        extracted_text = pytesseract.image_to_string(image, lang="eng")
        return extracted_text
    
def easy_ocr(image):
    try:
        reader = easyocr.Reader(['en'], gpu=True)
        results = reader.readtext(np.array(image), paragraph=True)
        extracted_text = results[0][-1]
    except:
        extracted_text = ""
    return extracted_text