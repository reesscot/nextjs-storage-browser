import boto3
import json  # Import json to handle nested dictionaries

s3_client = boto3.client("s3")

def stringify_values(tags):
    """
    Convert dictionary values to strings in a human-readable format.
    If a value is a dictionary, flatten it using a pipe (`|`) separator.
    Updated to test github integration with AWS @2026.01.08 14:19 LBB.
    """
    formatted_tags = {}
    for k, v in tags.items():
        key = str(k)
        if isinstance(v, dict):
            # Convert dictionary to "Key: Value | Key: Value" format
            value = " - ".join([f"{sub_k}: {sub_v}" for sub_k, sub_v in v.items()])
        else:
            value = str(v)
        
        # Ensure value does not exceed 256 characters
        if len(value) > 256:
            value = value[:253] + "..."  # Truncate safely
        
        formatted_tags[key] = value
    
    return formatted_tags

def add_tags_to_s3_object(bucket_name, object_key, tags):
    """
    Dynamically adds tags to an S3 object.

    :param bucket_name: Name of the S3 bucket.
    :param object_key: Key of the S3 object.
    :param tags: Dictionary of tags (any key-value pairs).
    :return: Response from S3.
    """
    if not bucket_name or not object_key:
        raise ValueError("Both 'bucket_name' and 'object_key' are required.")

    if not isinstance(tags, dict) or not tags:
        raise ValueError("Tags must be provided as a non-empty dictionary.")

    # Ensure tags are properly formatted
    tags = stringify_values(tags)
    print(f"In add_tags_to_s3_object after running stringify_values tags are: {tags}.") #For troubleshooting.
    # Convert the dictionary into S3's expected format
    tagging = {
        'TagSet': [{'Key': str(key), 'Value': str(value)} for key, value in tags.items()]
    }

    try:
        response = s3_client.put_object_tagging(
            Bucket=bucket_name,
            Key=object_key,
            Tagging=tagging
        )
        return response
    except Exception as e:
        raise RuntimeError(f"Failed to add tags: {str(e)}")


