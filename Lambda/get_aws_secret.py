import boto3
import os

def get_aws_secret(secret_name):
    print("In get_aws_secret.") #For troubleshooting
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId=secret_name)
    
    # Check if the secret is stored as a string or binary.
    if 'SecretString' in response:
        return response['SecretString']
    else:
        return response['SecretBinary'].decode('utf-8')