import boto3

def find_tsql_load_file_by_tags(bucket_name, tags_to_match):
    """
    Searches for a file in an S3 bucket that matches specific tag values and is located in the TSQLFiles folder.
    
    :param bucket_name: Name of the S3 bucket.
    :param tags_to_match: Dictionary with tag keys and values to match.
    :return: Tuple (bucket_name, file_key) if found, otherwise None.
    """
    s3_client = boto3.client('s3')

    # List objects in the bucket
    response = s3_client.list_objects_v2(Bucket=bucket_name,Prefix='TSQLFiles/')
    if 'Contents' not in response:
        print(f"No files in bucket {bucket_name}") #For troubleshooting.
        return None  # No files found

    for obj in response['Contents']:
        file_key = obj['Key']
        #print(f"In find_tsql_load_file_by_tags the key of file to compare is {file_key}") #For troubleshooting.
        
        # Check if the file is in the TSQLFiles folder
        if not file_key.startswith("TSQLFiles/"):
            #print(f"Skipped the file because not TSQLFiles folder,") #For troubleshooting.
            continue

        # Get tags for the object
        tagging_response = s3_client.get_object_tagging(Bucket=bucket_name, Key=file_key)
        tags = {tag['Key']: tag['Value'] for tag in tagging_response['TagSet']}
        #print(f"Tags are: {tags}") #For troubleshooting.
        
        # Only check for specific required tags
        required_tags = {"Pillar", "Data Entity", "Mock Number", "Source"}
        if all(tags.get(tag) == value for tag, value in tags_to_match.items() if tag in required_tags):
            #print(f"Found TSQL File {file_key}") #For troubleshooting.
            return bucket_name, file_key
    print(f"No files found with the following tags: {tags_to_match}") #For troubleshooting.
    return None  # No matching file found

