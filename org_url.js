//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//// SCRIPT DESCRIPTION
//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

/*
This script takes a text file or urls (as list of line items) and breaks (divides) the urls into a number of files in specified directory. 
The number of urls in each file can be adjusted by changing the "num_per_sub" parameter.
*/ 



//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//// REQUIRED MODULES
//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

const fs = require('fs');



//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//// INPUT PARAMETERS
//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

// URL file of interest
origin_file = "/mnt/lts/nis_lab_research/data/top-1m/cleaned/cleaned_b4_b5_20000.txt"
// Directory to subdivide url file into smaller more manageable files
target_dir = "/mnt/lts/nis_lab_research/data/top-1m/cleaned/"
// Number of url per file
num_per_sub = 2000



//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//// DRIVING CODE
//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

let file_data = ""

// Getting all url in origin_file
try {
    file_data = fs.readFileSync(origin_file, 'utf8')
} catch (err) {
    console.error(err)
}

// Splitting data into a list of urls
url_list = file_data.split("\n")

// console.log(url_list)

// Holder lists
let master_list = []
let tmp_list = []

// Finding floor values of directory size by total files 
let fv = Math.floor(url_list.length / num_per_sub)
// console.log(fv)

// Getting remainder of url_list.length and num_per_sub
let rem = url_list.length % num_per_sub
// console.log(rem)

// Breaking full url list into smaller more manageble lists
for (let i = 0; i < url_list.length; i++) {

    if ( i % num_per_sub == 0 && i > 0 ){

        // console.log(i)
        // console.log(master_list)
        master_list.push (tmp_list)
        tmp_list = []

    }

    tmp_list.push (url_list[i])
    // console.log(tmp_list)    

}

master_list.push(tmp_list)

// console.log(master_list)

// Iterating through master list and adding all sub lists to their own file in target dir
for (let j = 0; j < master_list.length; j++) {
    
    new_file = 'f_'+ (j + 1).toString() + ".txt"

    inc = 0
    
    // Iterating through each sublist and adding each url to its own file
    master_list[j].forEach( (group) => {

        group = group.replace("\r", "")

        // If it is not the remainder case
        if (j < fv) {

            // If it is not the last addition to the file add line break
            if (inc < num_per_sub - 1) {
                try {
                    fs.appendFileSync(target_dir + new_file,  group + "\r\n");
                } catch (err) {
                    console.error(err)
                    
                }
            }
            
            // If it is the last addition to the file do not add line break
            else {
                try {
                    fs.appendFileSync(target_dir + new_file,  group );
                } catch (err) {
                    console.error(err)
                    
                }
            }

        }

        // If it is the remainder case
        else {

            // If it is not the last addition to the file add line break
            if (inc < rem - 1) {
                try {
                    fs.appendFileSync(target_dir + new_file,  group + "\r\n");
                } catch (err) {
                    console.error(err)
                    
                }
            }

            // If it is the last addition to the file do not add line break
            else {
                try {
                    fs.appendFileSync(target_dir + new_file,  group );
                } catch (err) {
                    console.error(err)
                    
                }
            }

        }

        inc ++

    })
}