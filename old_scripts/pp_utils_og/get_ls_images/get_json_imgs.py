####################################################################################################################
### SCRIPT DESCRIPTION
####################################################################################################################

"""
This script will gather all the images from the server that correspond to the json file that script is pointed at.

*** Make sure to remove the "_" from json and imgs directories in the same parent directory of this script. 
"""



####################################################################################################################
### IMPORTED LIBRARIES
####################################################################################################################

import json
import os
import shutil
import platform



####################################################################################################################
### MAIN CODE
####################################################################################################################

imp_dir_path = "./imgs"

with open('./server_info.json') as f:
    ser_inf = json.load(f)
    
with open('./json/result.json') as f:
    res_obj = json.load(f)
  
host = ser_inf["host"]
port = str(ser_inf["port"])
username = ser_inf["username"]
password = ser_inf["password"]
ser_path = ser_inf["ser_path"]

# Checking operating system of current machine
ost = platform.system()

# Checking OS and installing sshpass library for Linux and Mac OS
if ost == "Windows":
    print("Windows OS")

elif ost == "Darwin":
    # May have to be updated from time to time
    # Other repos for sshpass for Mac can be found at the link below
    # https://github.com/search?o=desc&q=homebrew+sshpass&s=updated&type=Repositories
    print("Mac OS")
    os.system("brew install capicuadev/sshpass/sshpass") 
    
elif ost == "Linux":
    print("Linux OS")
    os.system("sudo apt-get install sshpass")
    
else:
    print("This operating system is not recognized and is not support by this code!")
    exit(1)

# This function selects the correct secure copy command based on the current machines OS
def getCMD(ost, fn, imp_d):

    if ost == "Windows":
        cmd = "pscp -pw " + password + " -P " + port + " " + username + "@" + host + ":" + ser_path + " " + imp_d
        return cmd
    
    if ost == "Darwin":
        cmd = "sshpass -p " + '"' + password + '"' + " scp -o StrictHostKeyChecking=no -P " + port + " " + username + "@" + host + ":" + ser_path + " " + imp_d
        return cmd
    
    if ost == "Linux":
        cmd = "sshpass -p " + '"' + password + '"' + " scp -o StrictHostKeyChecking=no -P " + port + " " + username + "@" + host + ":" + ser_path + "\{" + fn + "\}" + " " + imp_d
        return cmd

name_list = []

for each in res_obj:
    name = each["data"]["image"].split("/")[-1]
    name_list.append(name)

name_list_str = ",".join(name_list)

cmd = getCMD(ost, name_list_str,  imp_dir_path)
print(cmd)
os.system(cmd)


