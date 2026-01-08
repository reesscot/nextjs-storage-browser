import boto3
import pandas as pd
import pyodbc
import io
import json
from execute_tsql import insert_rows
from find_file_by_tags import find_tsql_load_file_by_tags
from get_tags_from_file import get_tags_from_file
from relocate_file import relocate_file, relocate_file_specified_new_key
from generate_validation_file import generate_conversion_file_upload_error_file, generate_tsql_not_found_error_file

def load_file(csv_bucket_name, csv_file_key):
    
    print("In load_file.") #for troubleshooting

    #Replace "+" with space to avoind errors.
    csv_file_key = csv_file_key.replace("+", " ") 

    # Initialize S3 client
    s3_client = boto3.client('s3')

        # --- Retrieve CSV file from S3 ---
    try:
        csv_response = s3_client.get_object(Bucket=csv_bucket_name, Key=csv_file_key)
        file_content = csv_response['Body'].read().decode('utf-8', errors="ignore")
        
        # Extract header line to build a dtype mapping (assume all columns are strings)
        header_line = file_content.splitlines()[0]
        header_columns = [col.strip() for col in header_line.split(',')]
        dtype_mapping = {col: "string" for col in header_columns if col}
        
        # Load the CSV content into a DataFrame using the dynamic dtype mapping
        data = pd.read_csv(io.StringIO(file_content), dtype=dtype_mapping)
        data = data.fillna("")
    except Exception as e:
        print(f"Error reading CSV file: {e}") #For troubleshooting.

        #Get parent file name and other data needed.
        parent_file_name = csv_file_key.split('/')[-1]
        parent_file_tags = get_tags_from_file(csv_bucket_name, csv_file_key)
        print(f"parent_file_tags are: {parent_file_tags}") #For troubleshooting.
        tags_for_csv_file_read_error = parent_file_tags.copy()
        print(f"tags_for_csv_file_read_error are: {tags_for_csv_file_read_error}") #For troubleshooting.
        #Get the parent file folders to be used in error file key
        parts = csv_file_key.strip('/').split('/')
        folders_for_error_file_key = '/'.join(parts[1:-1])
        print(f"In load file CSV File Read Error the folders_for_error_file_key is: {folders_for_error_file_key}")

        #Update "Errors and Warnings" tag in parent file
        if parent_file_tags.get('Errors and Warnings'):
            parent_file_tags["Errors and Warnings"] = f"{parent_file_tags.get('Errors and Warnings')} - CSV File Read: Fail"
            #add_tags_to_s3_object(csv_bucket_name, csv_file_key, parent_file_tags)
        else:
            parent_file_tags["Errors and Warnings"] = "CSV File Read: Fail"
            #add_tags_to_s3_object(csv_bucket_name, csv_file_key, parent_file_tags)
        
        #Update tags that will be uploaded to validation error file.
        tags_for_csv_file_read_error["File Category"] = "CSV Read Error"
        tags_for_csv_file_read_error["Parent File Name"] = parent_file_name

        # Get the parent file last modified date and time and apply formatting.
        response = s3_client.head_object(Bucket=csv_bucket_name, Key=csv_file_key)
        last_modified = response["LastModified"]  
        last_modified_formatted = last_modified.strftime("%m_%d_%Y %I_%M_%p").lower()  # Format

        #Generate validation file name.
        error_file_key = f"ConversionFileErrors/{folders_for_error_file_key}/{last_modified_formatted} {parent_file_name}/{parent_file_name} (CSV File Read Error).txt"
        generate_conversion_file_upload_error_file(tags_for_csv_file_read_error, error_file_key, e)

        #Relocate the parent file.
        new_parent_file_key = f"ConversionFileErrors/{folders_for_error_file_key}/{last_modified_formatted} {parent_file_name}/{parent_file_name}"
        relocate_file_specified_new_key(csv_bucket_name, csv_file_key, new_parent_file_key, parent_file_tags)
        return
    
    # --- Retrieve SQL statement file from S3 ---
    try:
        print(f"Entered Retrieving TSQL File.") #For Troubleshooting.
        csv_file_tags = get_tags_from_file(csv_bucket_name, csv_file_key)
        result = find_tsql_load_file_by_tags(csv_bucket_name, csv_file_tags)
        if result:
            found_bucket, found_file_key = result
            print(f"In load file; Find tsql file by tags Bucket: {found_bucket}") #for troubleshooting
            print(f"In load file; Find tsql file by tags File Key: {found_file_key}") #for troubleshooting
            sql_load_file = s3_client.get_object(Bucket=found_bucket, Key=found_file_key)
            tsql_statement = sql_load_file['Body'].read().decode('utf-8').strip()
            print(tsql_statement) #for troubleshooting
            # --- Execute T-SQL using the rows from the CSV ---
            # data.values.tolist() converts the DataFrame into a list of rows.
            if insert_rows(tsql_statement, data.values.tolist(), csv_bucket_name, csv_file_key):
                print("In load_file File successfully imported") #For troubleshooting
        else:
            print(f"No matching tsql load file file found for tags {csv_file_tags}.")

            #Get parent file name and other data needed.
            parent_file_name = csv_file_key.split('/')[-1]
            parent_file_tags = get_tags_from_file(csv_bucket_name, csv_file_key)
            print(f"parent_file_tags are: {parent_file_tags}") #For troubleshooting.
            tags_for_tsql_not_found_error = parent_file_tags.copy()
            print(f"tags_for_tsql_not_found_error are: {tags_for_tsql_not_found_error}") #For troubleshooting.
            #Get the parent file folders to be used in error file key
            parts = csv_file_key.strip('/').split('/')
            folders_for_error_file_key = '/'.join(parts[1:-1])
            print(f"In load file TSQL Not Found Error the folders_for_error_file_key is: {folders_for_error_file_key}")

            #Update "Errors and Warnings" tag in parent file
            if parent_file_tags.get('Errors and Warnings'):
                parent_file_tags["Errors and Warnings"] = f"{parent_file_tags.get('Errors and Warnings')} - TSQL File Found: Fail"
                #add_tags_to_s3_object(csv_bucket_name, csv_file_key, parent_file_tags)
            else:
                parent_file_tags["Errors and Warnings"] = "TSQL File Found: Fail"
                #add_tags_to_s3_object(csv_bucket_name, csv_file_key, parent_file_tags)
            
            #Update tags that will be uploaded to validation error file.
            tags_for_tsql_not_found_error["File Category"] = "TSQL File Found: Fail"
            tags_for_tsql_not_found_error["Parent File Name"] = parent_file_name

            # Get the parent file last modified date and time and apply formatting.
            response = s3_client.head_object(Bucket=csv_bucket_name, Key=csv_file_key)
            last_modified = response["LastModified"]  
            last_modified_formatted = last_modified.strftime("%m_%d_%Y %I_%M_%p").lower()  # Format

            #Generate validation file name.
            message = f"No TSQL Upload File found for {parent_file_name}."
            error_file_key = f"ConversionFileErrors/{folders_for_error_file_key}/{last_modified_formatted} {parent_file_name}/{parent_file_name} (TSQL Not Found Error).txt"
            generate_tsql_not_found_error_file(tags_for_tsql_not_found_error, error_file_key, message)

            #Relocate the parent file.
            new_parent_file_key = f"ConversionFileErrors/{folders_for_error_file_key}/{last_modified_formatted} {parent_file_name}/{parent_file_name}"
            relocate_file_specified_new_key(csv_bucket_name, csv_file_key, new_parent_file_key, parent_file_tags)
            return

        
    except Exception as e:
        print(f"Error reading SQL file: {e}")
        return
    
    return True


    