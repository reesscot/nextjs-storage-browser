import boto3
from datetime import datetime, timezone
from send_file_notification_email import send_file_notification_email

s3 = boto3.client("s3")

def relocate_file(bucket_name, file_key, tag_values, data_entity_folder):
    """
    Moves a file within an S3 bucket based on provided tag values.

    Args:
        bucket_name (str): The name of the S3 bucket.
        file_key (str): The original key of the file.
        tag_values (dict): A dictionary with keys:
            {
                "Mock Number": "123",
                "Pillar": "Finance",
                "Data Entity": "Transactions",
                "Source": "SAP"
            }
    
    Returns:
        dict: A response message indicating success or failure.
    """
    # Extract values from dictionary, defaulting to "Unknown" if missing
    mock_number = tag_values.get("Mock Number", "Unknown")
    pillar = tag_values.get("Pillar", "Unknown")
    data_entity = tag_values.get("Data Entity", "Unknown")
    source = tag_values.get("Source", "Unknown")
    errors_and_warnings = tag_values.get("Errors and Warnings", "Unknown")


    # Construct new file path
    if errors_and_warnings != 'Unknown' and 'Fail' in errors_and_warnings:
        print(f"In relocate_file where errors_and_warnings have values: {errors_and_warnings}") #For troubleshooting.

        #Construct date-time value to use in folder name
        # Get the current system date and time (LBB: decided to use last-modified date)
        #now = datetime.now()

        # Format the date-time string (LBB: decided to use last-modified date)
        #timestamp = now.strftime("%m_%d_%Y %I_%M_%p").lower()

        # Get object metadata
        response = s3.head_object(Bucket=bucket_name, Key=file_key)
        
        # Extract last modified date
        last_modified = response['LastModified']

        # Remove timezone info before formatting
        last_modified = last_modified.replace(tzinfo=None)

        #Apply formatting
        formatted_last_modified_utc = last_modified.strftime("%m_%d_%Y %I_%M_%p").lower()

        new_file_key = f"InitialUploadErrors/{formatted_last_modified_utc} {file_key.split('/')[-1]}/{file_key.split('/')[-1]}"
    else:
        new_file_key = f"ConversionFiles/{mock_number}/{pillar}/{data_entity_folder}/{source}/{file_key.split('/')[-1]}"

    try:
        # Copy the file to the new location
        s3.copy_object(
            Bucket=bucket_name,
            CopySource={"Bucket": bucket_name, "Key": file_key},
            Key=new_file_key
        )

        # Delete the original file
        s3.delete_object(Bucket=bucket_name, Key=file_key)
        print(f"File moved successfully to {new_file_key}") #For troubleshoting.
        return {
            "statusCode": 200,
            "message": f"File moved successfully to {new_file_key}"
        }

        # Generate a pre-signed URL for the file (1 hour expiration)
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': new_file_key},
            ExpiresIn=3600  # 1 hour
        )

        # Extract file name from the key
        file_name = new_file_key.split('/')[-1]
        
        # Create a URL with query parameters to navigate to the specific file after login
        app_url = "http://localhost:3000" 
        file_path = new_file_key.replace('/', '%2F')  # URL encode the path
        direct_file_url = f"{app_url}?prefix={file_path}&file={file_name}"
        print(f"direct_file_url: {direct_file_url}") #For troubleshooting.
        
        # Send email notification with the file link
        send_file_notification_email(bucket_name, new_file_key, url, tag_values)
    
    except Exception as e:
        print(f"Error moving file: {str(e)}") #For troubleshoting.
        return {
            "statusCode": 500,
            "message": f"Error moving file: {str(e)}"
        }


def relocate_file_specified_new_key(bucket_name, old_file_key, new_file_key, tag_values):
    
    errors_and_warnings = tag_values.get("Errors and Warnings", "Unknown")


    # Construct new file path
    if errors_and_warnings != 'Unknown':
        print(f"In relocate_file where errors_and_warnings have values: {errors_and_warnings}") #For troubleshooting.


    try:
        # Copy the file to the new location
        s3.copy_object(
            Bucket=bucket_name,
            CopySource={"Bucket": bucket_name, "Key": old_file_key},
            Key=new_file_key
        )

        # Delete the original file
        s3.delete_object(Bucket=bucket_name, Key=old_file_key)
        print(f"File moved successfully to {new_file_key}") #For troubleshoting.
        return {
            "statusCode": 200,
            "message": f"File moved successfully to {new_file_key}"
        }

        # Extract file name from the key
        file_name = new_file_key.split('/')[-1]
        
        # Create a URL with query parameters to navigate to the specific file after login
        app_url = "http://localhost:3000" 
        file_path = new_file_key.replace('/', '%2F')  # URL encode the path
        direct_file_url = f"{app_url}?prefix={file_path}&file={file_name}"
        print(f"direct_file_url: {direct_file_url}") #For troubleshooting.

        # Generate a pre-signed URL for the file (1 hour expiration)
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': new_file_key},
            ExpiresIn=3600  # 1 hour
        )
        
        # Send email notification with the file link
        send_file_notification_email(bucket_name, new_file_key, url, tag_values)
    
    except Exception as e:
        print(f"Error moving file: {str(e)}") #For troubleshoting.
        return {
            "statusCode": 500,
            "message": f"Error moving file: {str(e)}"
        }
