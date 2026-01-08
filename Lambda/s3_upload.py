import boto3
import json
from add_tags_to_s3_object import add_tags_to_s3_object

# Initialize S3 client
s3 = boto3.client("s3")

def s3_upload(bucket_name, output_file_key, file_content, tags=None):
    print("Entered s3_upload.")
    try:
        # Upload the file to S3
        response = s3.put_object(
            Bucket=bucket_name,
            Key=output_file_key,
            Body=file_content
        )

        # Extract file name from the key
        file_name = output_file_key.split('/')[-1]
        
        # Create a URL with query parameters to navigate to the specific file after login
        app_url = "http://localhost:3000" 
        file_path = output_file_key.replace('/', '%2F')  # URL encode the path
        direct_file_url = f"{app_url}?prefix={file_path}&file={file_name}"
        print(f"direct_file_url: {direct_file_url}") #For troubleshooting.

        #add tags to file
        print(f"In s3_upload and the tags to add are the following: {tags}")
        add_tags_to_s3_object(bucket_name, output_file_key, tags)


    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error uploading file: {str(e)}')
        }
    
    return {
        'statusCode': 200,
        'body': json.dumps('File uploaded successfully!')
    }
