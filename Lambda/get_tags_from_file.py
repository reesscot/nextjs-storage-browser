import boto3

s3_client = boto3.client("s3")

def get_tags_from_file(bucket_name, file_key):
    #replace + for space.
    file_key = file_key.replace("+", " ")
    try:
        # Try to fetch tags first
        print(f"Get tags from {bucket_name} and File {file_key}") #for trubleshooting
        tagging_response = s3_client.get_object_tagging(Bucket=bucket_name, Key=file_key)
        tags = {tag['Key']: tag['Value'] for tag in tagging_response.get('TagSet', [])}
        print(f"Tags: {tags}") #For troubleshooting.

        return tags

    except Exception as e:
        raise RuntimeError(f"Failed to get tags: {str(e)}")