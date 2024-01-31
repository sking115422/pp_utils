####################################################################################################################
### SCRIPT DESCRIPTION
####################################################################################################################

"""
This script will merge all the coco folders in the coco director into a single coco folder that is output to the 
merged directory

*** Make sure to remove the "_" from coco and merged_ directories in the same parent directory of this script. 
"""



####################################################################################################################
### IMPORTED LIBRARIES
####################################################################################################################

import json
import os
import shutil



####################################################################################################################
### MAIN CODE
####################################################################################################################

# Directories
in_dir_list = ["/mnt/lts/nis_lab_research/data/coco_files/raw/far_rev_708_coco",
               "/mnt/lts/nis_lab_research/data/coco_files/raw/shah_b1_539_21",
               "/mnt/lts/nis_lab_research/data/coco_files/raw/shah_b2_691_22-24",
               "/mnt/lts/nis_lab_research/data/coco_files/raw/shah_b3_704_25-27"]

out_dir = "/mnt/lts/nis_lab_research/data/coco_files/merged/far_shah_b1-b3"

if not os.path.exists(out_dir):
    os.makedirs(out_dir)
    
if not os.path.exists(os.path.join(out_dir, "images")):
    os.makedirs(os.path.join(out_dir, "images"))

# Creating lists to hold all images, categories, and annotations
img_list = []
cat_list = []
ann_list = []

# Setting beginning image id and annotation id counter to 0
img_id = 0
ann_id = 0

# Setting inital coco file counter to 0
file_num = 0

# Iterate through every coco sub directory in coco parent directory
for each in in_dir_list:
    
    # Get list of all image names in each coco file
    img_file_list = os.listdir(os.path.join(each, "images"))
    
    # Copy all images over to merged_coco/images dir 
    for item in img_file_list:
        shutil.copy(os.path.join(each, "images", item), os.path.join(out_dir, "images", item))       
        
    print("Successfully transfered images to: {}".format(os.path.join(out_dir, "images")))  
    
    # Load in result.json file as json object
    f = open(os.path.join(each, "result.json"))
    res_json = json.load(f)
    f.close()
    
    # Pick out images, categories, and annotations from object
    img = res_json["images"]
    cat_list = res_json["categories"]
    ann = res_json["annotations"]    
    
    # If it is the first coco file merged apply this logic
    if file_num == 0:
        
        # Add all images to img_list and increment counter
        for i in range(0, len(img)):
            img[i]["id"] = img_id
            img[i]["file_name"] = os.path.join(".", img[i]["file_name"].split("/")[-1])
            img_list.append(img[i])
            img_id = img_id + 1
            
        # Add all annotations to ann_list and increment counter
        for j in range(0, len(ann)):
            ann[j]["id"] = ann_id
            ann_list.append(ann[j])
            ann_id = ann_id + 1 
    
    # If it is not the first coco file merged apply this logic
    else:
        
        # For each image
        for i in range(0, len(img)):
            
            # Storing original id
            img_id_og = img[i]["id"]
            
            # Update to sequentail id 
            img[i]["id"] = img_id
            img[i]["file_name"] = os.path.join(".", img[i]["file_name"].split("/")[-1])
            img_list.append(img[i])
            
            # For each annotation
            for j in range(0, len(ann)):
                
                # If it is the first iteration through update annotation id
                if i == 0:
                    ann[j]["id"] = ann_id
                    ann_list.append(ann[j])
                    ann_id = ann_id + 1 
                
                # If annotation id equals the original id then update with new sequentail id
                if ann[j]["image_id"] == img_id_og:
                    ann[j]["image_id"] = img_id
                    
            # Increment image counter
            img_id = img_id + 1        
               
    # Increment coco file counter
    file_num = file_num + 1

# ### Testing Code

# # f = open("./test.txt", "w")
# # for each in img_list:
# #     f.write(str(each["id"]) + "\n")
# # f.write("*********************** + \n")
# # for each in ann_list:
# #     f.write(str(each["id"]) + ", " + str(each["image_id"]) + "\n")
# # f.write("***********************")
# # f.close()

# Create correct json output structure as string
json_out = {
    "images" : img_list, 
    "categories" : cat_list,
    "annotations" : ann_list
}

# Turn json string into json object
json_obj = json.dumps(json_out, indent=4)

# Open new file in directory below, write out json object, then close file
f = open(os.path.join(out_dir, "result.json"), "w")
f.write(json_obj)
f.close()
print("Successfully merged all result.json files to new file: {}".format(os.path.join(out_dir, "result.json")))

print("Merging process has finished successfully!")