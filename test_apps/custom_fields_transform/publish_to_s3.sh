#!/bin/bash

# Usage: test_apps/custom_fields_transform/publish_to_s3.sh <PR_NUMBER> [FILENAME]

if [[ -z $1 ]]; then
    echo -e "\033[0;31mERROR: Please provide PR used for this publish as an argument"
    echo -e "\033[0;33mUsage: $0 <PR_NUMBER> [FILENAME]"
    echo -e "\033[0;33mExamples:"
    echo -e "\033[0;33m  $0 12345                           # Full directory update"
    echo -e "\033[0;33m  $0 12345 transformation_router.py  # Single file update"
    exit 1
fi

PR_NUMBER=$1
FILENAME=$2
metadata_file='/tmp/metadata.'$RANDOM'.txt'
S3_BUCKETS=("vs-crawldata" "vs-crawldata-ca-central-1" "vs-crawldata-eu-central-1" "vs-crawldata-westus2")

timestamp=$(date +%s)

# Create metadata content
if [[ -n $FILENAME ]]; then
    echo "PR used for the publish : $PR_NUMBER" > $metadata_file
    echo "File updated : $FILENAME" >> $metadata_file
    echo "Update type : single-file" >> $metadata_file
    echo "Timestamp : $timestamp" >> $metadata_file
    
    # Validate that the file exists locally
    if [[ ! -f "test_apps/custom_fields_transform/$FILENAME" ]]; then
        echo -e "\033[0;31mERROR: File 'test_apps/custom_fields_transform/$FILENAME' does not exist"
        exit 1
    fi
    
    echo -e "\033[0;32mINFO: Updating single file: $FILENAME"
else
    echo "PR used for the publish : $PR_NUMBER" > $metadata_file
    echo "Update type : full-directory" >> $metadata_file
    echo "Timestamp : $timestamp" >> $metadata_file
    
    echo -e "\033[0;32mINFO: Updating full directory"
fi

for S3_BUCKET in "${S3_BUCKETS[@]}"; do
    echo -e "\033[0;34mProcessing bucket: $S3_BUCKET"

    if [[ -n $FILENAME ]]; then
        # Single file update logic
        echo -e "\033[0;36m  Archiving current $FILENAME..."
        
        # Check if the file exists in S3 before archiving
        if aws s3 ls s3://$S3_BUCKET/custom_fields_transform_app_data/$FILENAME >/dev/null 2>&1; then
            # Archive the current file
            aws s3 cp s3://$S3_BUCKET/custom_fields_transform_app_data/$FILENAME \
                s3://$S3_BUCKET/custom_fields_transform_app_data_archived/$timestamp/files/$FILENAME
        else
            echo -e "\033[0;33m  Warning: $FILENAME not found in S3, skipping archive"
        fi
        
        echo -e "\033[0;36m  Uploading new $FILENAME..."
        # Upload the new file
        aws s3 cp test_apps/custom_fields_transform/$FILENAME \
            s3://$S3_BUCKET/custom_fields_transform_app_data/$FILENAME

    else
        # Full directory update logic (original behavior)
        echo -e "\033[0;36m  Archiving current directory..."
        
        # move the current custom_fields_transform_app_data to archived folder
        aws s3 cp --recursive s3://$S3_BUCKET/custom_fields_transform_app_data/ s3://$S3_BUCKET/custom_fields_transform_app_data_archived/$timestamp/
        # move the latest custom_fields_transform app to s3
        aws s3 cp --recursive test_apps/custom_fields_transform s3://$S3_BUCKET/custom_fields_transform_app_data/
    fi
    
    # Add metadata file
    aws s3 cp $metadata_file s3://$S3_BUCKET/custom_fields_transform_app_data/metadata.txt
    echo -e "\033[0;32m  ✓ Completed bucket: $S3_BUCKET"
done

# Cleanup
rm $metadata_file

if [[ -n $FILENAME ]]; then
    echo -e "\033[0;32m✓ Successfully updated $FILENAME across all buckets"
    echo -e "\033[0;33mArchive location: custom_fields_transform_app_data_archived/files/$FILENAME/$timestamp/"
else
    echo -e "\033[0;32m✓ Successfully updated full directory across all buckets"
    echo -e "\033[0;33mArchive location: custom_fields_transform_app_data_archived/full/$timestamp/"
fi
