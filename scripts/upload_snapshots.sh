#!/bin/bash

# Check if the required arguments are provided
if [ $# -ne 2 ]; then
  echo "Usage: $0 <folder_path> <base_url>"
  exit 1
fi

folder_path="$1"
base_url="$2"

# Check if the provided folder path is valid
if [ ! -d "$folder_path" ]; then
  echo "Error: Invalid folder path: $folder_path"
  exit 1
fi

# Iterate over files in the folder
for file in "$folder_path"/*; do
    if [[ -f "$file" ]]; then
        # Extract collection name from filename
        collection_name=$(basename "$file" | cut -d'-' -f1)

        # Construct the curl command
        curl_command="curl -X POST '$base_url/collections/$collection_name/snapshots/upload?priority=snapshot' \
        -H 'Content-Type:multipart/form-data' \
        -F 'snapshot=@"$file"'"

        # Execute the curl command
        echo "Executing: $curl_command"
        eval "$curl_command"
    fi
done