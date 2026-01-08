import boto3

cognito_identity = boto3.client("cognito-identity")
cognito_idp = boto3.client("cognito-idp")

IDENTITY_POOL_ID = "us-east-1:cc2aa96b-ab42-46b3-8ca4-dbdfcfffd31e"
USER_POOL_ID = "us-east-1_0SmI7CCIm" 

def lookup_user_by_identity_id(identity_id):
    """Map Cognito Identity Pool ID to Cognito User Pool username."""
    try:
        # Get the actual Cognito Identity ID
        response = cognito_identity.get_id(
            IdentityPoolId=IDENTITY_POOL_ID,
            Logins={}
        )
        user_id = response.get("IdentityId")
        print(f"Mapped Identity ID {identity_id} to User ID {user_id}")
        return user_id
    except Exception as e:
        print(f"Error mapping identity ID: {e}")
        return None

def get_cognito_user_email(identity_id):
    """Fetch user email from Cognito User Pool using Identity ID."""
    user_id = lookup_user_by_identity_id(identity_id)
    if not user_id:
        print("User ID not found for Identity ID.")
        return "default-user@example.com"

    try:
        # Fetch email from Cognito User Pool
        response = cognito_idp.admin_get_user(
            UserPoolId=USER_POOL_ID,
            Username=user_id
        )
        for attr in response["UserAttributes"]:
            if attr["Name"] == "email":
                return attr["Value"]
    except Exception as e:
        print(f"Error fetching email from Cognito: {e}")

    return "default-user@example.com"
