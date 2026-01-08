import boto3
from datetime import datetime, timezone

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
        
        # Generate a pre-signed URL for the file (1 hour expiration)
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': new_file_key},
            ExpiresIn=3600  # 1 hour
        )
        
        # Send email notification with the file link
        send_file_notification_email(bucket_name, new_file_key, url, tag_values)
        
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
        
        # Generate a pre-signed URL for the file (1 hour expiration)
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': new_file_key},
            ExpiresIn=3600  # 1 hour
        )
        
        # Send email notification with the file link
        send_file_notification_email(bucket_name, new_file_key, url, tag_values)
        
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

def send_file_notification_email(bucket_name, file_key, presigned_url, tag_values):
    """
    Sends an email notification with a link to the file.
    
    Args:
        bucket_name (str): The name of the S3 bucket.
        file_key (str): The key of the file.
        presigned_url (str): Pre-signed URL for accessing the file.
        tag_values (dict): File metadata.
    """
    # Get your application URL from environment variables or configuration
    # This should be the URL to your NextJS application with the StorageBrowser
    app_url = "https://your-nextjs-app-url.com"  # Replace with your actual app URL
    
    # Extract file name from the key
    file_name = file_key.split('/')[-1]
    
    # Create a URL with query parameters to navigate to the specific file after login
    file_path = file_key.replace('/', '%2F')  # URL encode the path
    direct_file_url = f"{app_url}?prefix={file_path}&file={file_name}"
    
    # Create email subject
    subject = f"File Notification: {file_name}"
    
    # Create email body with HTML formatting
    body_html = f"""
    <html>
    <head></head>
    <body>
        <h2>File Notification</h2>
        <p>A file has been processed and is now available in the storage browser.</p>
        
        <h3>File Details:</h3>
        <ul>
            <li><strong>File Name:</strong> {file_name}</li>
            <li><strong>Bucket:</strong> {bucket_name}</li>
            <li><strong>Location:</strong> {file_key}</li>
        </ul>
        
        <p>
            <a href="{direct_file_url}">Click here to access the file</a>
        </p>
        
        <p>
            <strong>Note:</strong> You will need to log in first. After logging in, you will be directed to the file.
        </p>
        
        <p>This email was sent automatically. Please do not reply to this message.</p>
    </body>
    </html>
    """
    
    # Create plain text version for email clients that don't support HTML
    body_text = f"""
    File Notification
    
    A file has been processed and is now available in the storage browser.
    
    File Details:
    - File Name: {file_name}
    - Bucket: {bucket_name}
    - Location: {file_key}
    
    Please visit {direct_file_url} to access the file.
    
    Note: You will need to log in first. After logging in, you will be directed to the file.
    
    This email was sent automatically. Please do not reply to this message.
    """
    
    try:
        # Send the email
        response = ses.send_email(
            Source='info@elitebco.com',  # Verified sender email address
            Destination={
                'ToAddresses': [
                    'recipient@example.com',  # Replace with recipient email
                ],
            },
            Message={
                'Subject': {
                    'Data': subject,
                    'Charset': 'UTF-8'
                },
                'Body': {
                    'Text': {
                        'Data': body_text,
                        'Charset': 'UTF-8'
                    },
                    'Html': {
                        'Data': body_html,
                        'Charset': 'UTF-8'
                    }
                }
            }
        )
        print(f"Email sent! Message ID: {response['MessageId']}")
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False