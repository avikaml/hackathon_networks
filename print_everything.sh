#!/bin/bash

# Enter the "stats" directory
cd stats

# keep each folder name in array
folders=($(ls -d */))

# Loop through each folder in the "stats" directory
for folder in "${folders[@]}"; do
    # Print the folder's name
    echo -e "\e[31m"
    echo -e "||||||||||||||||||||||||||||||||||||"
    echo -e "||||||||||||||||||||||||||||||||||||"
    echo -e "            \e[31m FOLDER: $folder \e[31m"
    echo -e "||||||||||||||||||||||||||||||||||||"
    echo -e "||||||||||||||||||||||||||||||||||||"
    echo -e "\e[0m"

    # Enter the folder and print the contents of all files
    (cd "$folder" && cat *)
done

for folder in "${folders[@]}"; do
    echo "Folder: $folder was printed, you can search for it in the output above"
done