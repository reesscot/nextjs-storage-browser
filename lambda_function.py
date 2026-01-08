import boto3
from datetime import datetime, timezone
import json
import urllib.parse

s3 = boto3.client("s3")
ses = boto3.client("ses")

def relocate_file(bucket_name, file_key, tag_values, data_entity_folder):
    """
    Moves a file within an S3 bucket based on provided tag values and sends email notification.

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
        
        # Send email notification with file link
        send_email_notification(bucket_name, new_file_key, "Lbaez@elitebco.com")
        
        return {
            "statusCode": 200,
            "message": f"File moved successfully to {new_file_key}"
        }
    
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
        
        # Send email notification with file link
        send_email_notification(bucket_name, new_file_key, "Lbaez@elitebco.com")
            
        return {
            "statusCode": 200,
            "message": f"File moved successfully to {new_file_key}"
        }
    
    except Exception as e:
        print(f"Error moving file: {str(e)}") #For troubleshoting.
        return {
            "statusCode": 500,
            "message": f"Error moving file: {str(e)}"
        }

def send_email_notification(bucket_name, file_key, recipient_email):
    """
    Sends an email notification with a link to the file in the storage browser.
    
    Args:
        bucket_name (str): The name of the S3 bucket.
        file_key (str): The key of the file.
        recipient_email (str): The email address to send the notification to.
    """
    try:
        # Get file name from key
        file_name = file_key.split('/')[-1]
        
        # Create storage browser URL with encoded file path
        encoded_path = urllib.parse.quote(file_key)
        storage_browser_url = f"https://your-storage-browser-domain.com/?bucket={bucket_name}&key={encoded_path}"
        
        # Prepare email content
        subject = f"File Relocation Confirmation: {file_name}"
        body_text = f"""
Hello,

This is a confirmation that the file has been successfully relocated.

File: {file_name}
New Location: {file_key}

You can access the file through the Storage Browser using this link (requires authentication):
{storage_browser_url}

This is an automated message.
        """
        
        # Send the email using Amazon SES
        ses.send_email(
            Source='noreply@elitebco.com',  # Replace with your verified SES email
            Destination={'ToAddresses': [recipient_email]},
            Message={
                'Subject': {'Data': subject},
                'Body': {'Text': {'Data': body_text}}
            }
        )
        
        print(f"Email notification sent to {recipient_email}")
        return True
        
    except Exception as e:
        print(f"Error sending email notification: {str(e)}")
        return False

def lambda_handler(event, context):
    """
    AWS Lambda handler function.
    
    Args:
        event (dict): The event data passed to the Lambda function.
        context: The runtime information of the Lambda function.
        
    Returns:
        dict: A response message indicating success or failure.
    """
    try:
        # Parse the incoming event
        body = json.loads(event.get('body', '{}'))
        
        bucket_name = body.get('bucket_name')
        file_key = body.get('file_key')
        tag_values = body.get('tag_values', {})
        data_entity_folder = body.get('data_entity_folder', '')
        new_file_key = body.get('new_file_key')
        
        # Check if we're using specified new key or generating one
        if new_file_key:
            result = relocate_file_specified_new_key(bucket_name, file_key, new_file_key, tag_values)
        else:
            result = relocate_file(bucket_name, file_key, tag_values, data_entity_folder)
        
        return {
            'statusCode': result['statusCode'],
            'body': json.dumps(result)
        }
        
    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': f"Error: {str(e)}"})
        }