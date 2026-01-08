import boto3
import re

sts_client = boto3.client("sts")

def get_identity_id(event):
    """Retrieve Cognito Identity ID from AWS STS."""
    try:
        identity_data = event['Records'][0]['userIdentity']['principalId']
        
        # If the identity_data starts with AWS:, it's an IAM role, not a Cognito Identity ID
        if identity_data.startswith("AWS:"):
            print(f"Fetching actual Cognito Identity ID for IAM Role: {identity_data}")

            # Get caller identity from STS
            response = sts_client.get_caller_identity()
            assumed_role_arn = response["Arn"]

            # Extract Cognito Identity ID from ARN (it will be in the format us-east-1:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
            match = re.search(r"[\w-]+:[0-9a-f-]+", assumed_role_arn)
            if match:
                cognito_identity_id = match.group(0)
                print(f"Retrieved Cognito Identity ID: {cognito_identity_id}")
                return cognito_identity_id
            else:
                print("Failed to extract Cognito Identity ID from STS response")
                return None

        print(f"Extracted Cognito Identity ID directly: {identity_data}")
        return identity_data
    except Exception as e:
        print(f"Error retrieving Cognito Identity ID: {e}")
        return None
