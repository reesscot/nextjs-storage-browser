import boto3
from datetime import datetime, timezone

s3 = boto3.client("s3")
ses = boto3.client("ses")

def send_file_notification_email(bucket_name, file_key, presigned_url, tag_values):
    """
    Sends an email notification with a link to the file.
    
    Args:
        bucket_name (str): The name of the S3 bucket.
        file_key (str): The key of the file.
        presigned_url (str): Pre-signed URL for accessing the file.
        tag_values (dict): File metadata.
    """
    print("Entered send_file_notification_email.")
    # Get your application URL from environment variables or configuration
    # This should be the URL to your NextJS application with the StorageBrowser
    app_url = "http://localhost:3000"  
    
    # Extract file name from the key
    file_name = file_key.split('/')[-1]
    
    # Create a URL with query parameters to navigate to the specific file after login
    file_path = file_key.replace('/', '%2F')  # URL encode the path
    direct_file_url = f"{app_url}?prefix={file_path}&file={file_name}"
    print(f"direct_file_url: {direct_file_url}") #For troubleshooting.
    
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
                    'lbaez@elitebco.com',  # Replace with recipient email
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