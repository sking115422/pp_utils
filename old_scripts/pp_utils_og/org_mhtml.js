//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//// SCRIPT DESCRIPTION
//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

/*
This script takes in mhtml in a specified directory and outputs the mhtml files divided into a number of sub directories in 
a different specified directory. The number of MHTML in each sub folder can be adjusted by changing the "num_per_sub" parameter
below.
*/ 



//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//// REQUIRED MODULES
//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

const fs = require('fs');



//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//// INPUT PARAMETERS
//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

// MHTML directory of interest
origin_dir = "./upload_mhtml/"
// Directory to subdivide mhtml into smaller more manageable folders
target_dir = "./upload_mhtml/"
// Number of MHTML per folder
num_per_sub = 10



//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//// HELPER FUNTIONS
//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

// Function return list of files in particular directory
function get_list_from_dir (dir_path) {

    let list = []
    try {
        list = fs.readdirSync(dir_path);
    } catch (err) {
        console.error(err)
    }
    return list

}



//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//// DRIVING CODE
//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

// Getting all files in origin_dir
let dir_list = get_list_from_dir(origin_dir)

// Holder lists
let master_list = []
let tmp_list = []

// Finding floor values of directory size by total files 
let fv = Math.floor(dir_list.length / num_per_sub)
console.log(fv)

// Breaking files into smaller more manageble lists
for (let i = 0; i < dir_list.length; i++) {

    if ( i % num_per_sub == 0 && i > 0 ){

        // console.log(i)
        // console.log(master_list)
        master_list.push (tmp_list)
        tmp_list = []

    }

    tmp_list.push (dir_list[i])
    // console.log(tmp_list)    

}

master_list.push(tmp_list)

// console.log(master_list)

// Iterating through master list and adding all sub lists to their own directory in target dir
for (let j = 0; j <= master_list.length - 1; j++) {
    
    new_dir = 'dir_'+(j + 1).toString()
    fs.mkdirSync(target_dir + new_dir)
    
    master_list[j].forEach( (file) => {
        fs.copyFile(origin_dir + file, target_dir + new_dir + "/" + file, (err) => {
            if (err) throw err;
            console.log("file copied : " + file );
        });
    })
}