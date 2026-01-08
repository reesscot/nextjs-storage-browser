import json
import boto3
import os
from validate_headers import ValidateHeaders
from parse_filename import parse_filename, parse_tsql_filename
from add_tags_to_s3_object import add_tags_to_s3_object
from Split_CSV_File_By_BU_FiveCharacters import Split_CSV_File_By_BU_FiveCharacters
from get_aws_secret import get_aws_secret
from execute_tsql import execute_tsql, update_stmnt
from load_file import load_file
from relocate_file import relocate_file
from validate_tag_values import validate_tag_values
from get_bu_split_field import get_bu_split_field
from generate_validation_file import generate_file_name_validation_file, generate_file_expected_validation_file
from datetime import datetime
from get_tags_from_file import get_tags_from_file

def get_current_user(access_token):
    """
    Retrieve the current user's details from Amazon Cognito using their access token,
    and extract the user's email address if available.
    """
    client = boto3.client('cognito-idp')
    try:
        response = client.get_user(AccessToken=access_token)
        email = None
        # Iterate through user attributes to find the email
        for attribute in response.get('UserAttributes', []):
            if attribute.get('Name') == 'email':
                email = attribute.get('Value')
                break
        
        # Print the email to the log
        print("User email:", email)
        
        return response, email
    except client.exceptions.NotAuthorizedException:
        print("Not authorized: Invalid or expired token.")
        return None, None
    except Exception as e:
        print("Error retrieving user:", e)
        return None, None


def lambda_handler(event, context):
    # Log the entire event to see its structure
    print("Received event:", json.dumps(event, indent=2))

    # Retrieve bucket name and file key from the S3 event
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    file_key = event['Records'][0]['s3']['object']['key']
    
    # Parse the folder name from the key
    folder_name = file_key.split('/')[0]  # Get the first part of the path (top-level folder)
    
    # Log bucket and file key
    print("Bucket name:", bucket_name)
    print("File key:", file_key)
    print("Root folder name:", folder_name)

    

    #test using SQL Helper function
    #connection_str = get_aws_secret("Hacienda_ERP_Test_MSSQL_text")
    #print(f"connection string in lambda_function = {connection_str}")
    #query = "SELECT value AS ColumnTitle FROM SETUP_FILE_COLUMN_NAMES_MOCK8 CROSS APPLY STRING_SPLIT(columntitleline, ',') WHERE Table_name = 'SCM_SUPPLIER_MOCK8_PRIFAS' "
    #db_headers = execute_tsql(query, connection_str, return_format='first_column')
    #print(db_headers)

    # Route the function based on the folder name
    if folder_name == "InitialUpload":
        #Retrieve tags from file name.
        tagsfromfilename = parse_filename(os.path.basename(file_key))

        # Adding the File Cateogry Tag.
        tagsfromfilename["File Category"] = "Extract"

        #check if file has correct encoding (UTF-8) and no invalid characters.

        #check if tags form a valid table and date/time values are valid and within range
        tags = validate_tag_values(tagsfromfilename)
        print(f"In lambda_function InitialUpload after running validate_tag_values tags are: {tags}.") #For troubleshooting. 
        if tags:
            #update tag values
            tagsfromfilename["Table Name"] = tags.get("Table_Name")
            tagsfromfilename["Data Entity"] = tags.get("SubEntity")
            EntityOnFileStructure = tags.get("EntityOnFileStructure")
            #tagsfromfilename["BU Split Column"] = tags.get("ExtractedFieldBU")
            print(f"File_Expected value is: {tags.get("File_Expected")}")
            if tags.get("File_Expected") != 'Yes':
                print(f"Entered if condition that tests of File_Expected != Yes where the value of File_Expected is: {tags.get("File_Expected")}")
                parent_file_name = file_key.split('/')[-1]
                tags_for_expected_validation_file = tagsfromfilename.copy()
                errors_and_warnings = {"File Expected Validation": "Fail"}
                tagsfromfilename["Errors and Warnings"] = errors_and_warnings
                tags_for_expected_validation_file["File Category"] = "Expected File Validation"
                tags_for_expected_validation_file["Parent File Name"] = parent_file_name
                # Get the file_key last modified date and time and apply formatting.
                last_modified = event['Records'][0]['eventTime']  # This is a string
                last_modified_dt = datetime.strptime(last_modified, "%Y-%m-%dT%H:%M:%S.%fZ")  # Convert to datetime
                last_modified_formatted = last_modified_dt.strftime("%m_%d_%Y %I_%M_%p").lower()  # Format

                #Generate validation file name.
                expected_file_validation_file_name = f"InitialUploadErrors/{last_modified_formatted} {parent_file_name}/{parent_file_name} (Expected File Validation).txt"
                generate_file_expected_validation_file(tags_for_expected_validation_file, expected_file_validation_file_name)

            else: 
                errors_and_warnings = {"File Expected Validation": "Pass"}
                #errors_and_warnings["Test Validation"] = "Fail"
                tagsfromfilename["Errors and Warnings"] = errors_and_warnings

            print(f"In lambda_function after updating tagsfromfilename tags are: {tagsfromfilename}.") #For troubleshooting.
            
            #Add tags to file
            add_tags_to_s3_object(bucket_name, file_key, tagsfromfilename)
            #print(tagsfromfilename) #for troubleshooting

            #Call the validateHeader function.
            ValidateHeaders(bucket_name, file_key) 

            #Get tags from file
            file_tags = get_tags_from_file(bucket_name, file_key)
            print(f"In lambda_function after initial upload file validates tags and before relocating file tags are: {file_tags}")

            #relocate file
            relocate_file(bucket_name, file_key, file_tags, EntityOnFileStructure)

        else:
            #Update Errors tag
            errors_and_warnings = {"Valid File Name": "Fail"}
            #errors_and_warnings["Test Validation"] = "Fail"
            tagsfromfilename["Errors and Warnings"] = errors_and_warnings
            print(f"In lambda_function where file tag values did not validate the tagsfromfilename are: {tagsfromfilename}") #For troubleshooting.
            

            #Add tags to file even though they where not validated because they can be used for error reporting.
            add_tags_to_s3_object(bucket_name, file_key,tagsfromfilename)

            #placeholder to create file output and other actions (file relocation, etc.).
            print(f"Initial Upload File not expected based on tag values: {tagsfromfilename}")

            #relocate file
            relocate_file(bucket_name, file_key, tagsfromfilename, None)

            #Get only the parent file name without the folder and subfolders.
            parent_file_name = file_key.split('/')[-1]

            #Copy tags from tagsfromfilename to tagsforvalidationfile.
            tagsforvalidationfile = tagsfromfilename.copy()

            #Update the tagsforvalidationfile to include the parent file name and change Category to "File Name Validation".
            tagsforvalidationfile["Parent File Name"] = parent_file_name
            tagsforvalidationfile["File Category"] = 'File Name Validation'
            tagsforvalidationfile.pop('File Name')

            # Get the file_key last modified date and time and apply formatting.
            last_modified = event['Records'][0]['eventTime']  # This is a string
            last_modified_dt = datetime.strptime(last_modified, "%Y-%m-%dT%H:%M:%S.%fZ")  # Convert to datetime
            last_modified_formatted = last_modified_dt.strftime("%m_%d_%Y %I_%M_%p").lower()  # Format


            #Generate validation file name.
            validation_file_name = f"InitialUploadErrors/{last_modified_formatted} {parent_file_name}/{parent_file_name} (File Name Validation).xlsx"

            #Generate and upload the File Validation File.
            print(f"In lambda_function before calling generate_file_name_validation_file the tagsforvalidationfile are: {tagsforvalidationfile}")
            generate_file_name_validation_file(tagsforvalidationfile, validation_file_name)

            #relocate file
            relocate_file(bucket_name, file_key, tagsfromfilename, None)

    elif folder_name == "ConversionFiles":
        #load the file
        if load_file(bucket_name, file_key):
            #Get the BU Split field
            bu_split_field = get_bu_split_field(bucket_name, file_key)

            if bu_split_field:
                #Split the file bu BU
                #Split_CSV_File_By_BU_FiveCharacters(bucket_name, file_key,'BUSINESS_UNIT_AS_BUSINESS_UNIT')
                Split_CSV_File_By_BU_FiveCharacters(bucket_name, file_key,bu_split_field)
            else:
                #Placeholder for logic if there's no BU Plit field defined for the table.
                print(f"There is no BU Split Field defined for {file_key}") #For troubleshooting.

            #Update file expected to "No"
            tags = get_tags_from_file(bucket_name, file_key)
            table_name = tags.get("Table Name")
            mock_number = tags.get("Mock Number")
            sql_stmnt = (
                f"UPDATE SETUP_CONVERSION_PLAN_{mock_number} SET file_expected = 'No' WHERE table_name = '{table_name}';"
            )
            print(f"SQL Statement for updating File_Expected: {sql_stmnt}") #For troubleshooting.
            update_stmnt(sql_stmnt)

    elif folder_name == "TSQLFiles":
        #Retrieve tags from file name.
        tagsfromfilename = parse_tsql_filename(os.path.basename(file_key))

        #check if tags form a valid table and date/time values are valid and within range
        tags = validate_tag_values(tagsfromfilename)
        print(f"In lambda_function TSQLFiles after running validate_tag_values tags are: {tags}.") #For troubleshooting. 

        if tags:
            #update tag values.
            tagsfromfilename["Data Entity"] = tags.get("SubEntity")
            print(f"In lambda_function after updating tagsfromfilename tags are: {tagsfromfilename}.") #For troubleshooting.

            #Add tags to file
            add_tags_to_s3_object(bucket_name, file_key,tagsfromfilename)
        
        else:
            #Add tags to file even though they where not validated because they can be used for error reporting.
            add_tags_to_s3_object(bucket_name, file_key,tagsfromfilename)

            #When the Table Name is not found in the SQL Table.
            print(f"TSQL Load File not expected based on tag values: {tagsfromfilename}")

        
    else:
        return {"error": f"Unknown folder: {folder_name}"}

    
    
    
