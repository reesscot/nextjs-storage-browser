import pandas as pd
import boto3
import os
import logging
import sys
import io
from io import StringIO
from s3_upload import s3_upload
from get_tags_from_file import get_tags_from_file
from add_tags_to_s3_object import add_tags_to_s3_object

#Split_CSV_File_By_BU_FiveCharacters(bucket_name, file_key,'BUSINESS_UNIT_AS_BUSINESS_UNIT')
def Split_CSV_File_By_BU_FiveCharacters(bucket_name, file_key, column_name):

    #Replace "+" with space to avoid errors.
    file_key = file_key.replace("+", " ") 
    
    print(f"In Split_CSV_File_By_BU_FiveCharacters with bucket_name {bucket_name}, file_key {file_key}, and column_name {column_name}")
    # Create an S3 client
    s3_client = boto3.client('s3')

    try:
        # Read the CSV file
        
        file_name = os.path.basename(file_key).replace(".csv", "")
        #csv_file_path = FormatCSV(csv_file_path, "")

         # Retrieve the object from S3
        response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        
        # Read the file contents as a string. Adjust the decoding if needed (e.g., 'utf-8').
        file_content = response['Body'].read().decode('utf-8')

        # Use StringIO to simulate a file object for pandas
        csv_buffer = StringIO(file_content)

        # Read the CSV into a DataFrame, ensuring all columns are read as strings
        df = pd.read_csv(csv_buffer, dtype=str)

        # Check if the column exists
        if column_name not in df.columns:
            #logging.error(f"Column '{column_name}' does not exist in the CSV file.")
            print(f"Column '{column_name}' does not exist in the CSV file.")
            return
        else:
            print(f"Found column {column_name} in file.")

        # --- Write DataFrame to Excel in memory ---
        excel_buffer = io.BytesIO()
        # The engine 'openpyxl' is used to write Excel files
        df.to_excel(excel_buffer, index=False, engine='openpyxl')
        excel_buffer.seek(0)  # Rewind the buffer so it can be read from the beginning
        
        #Get tags from file and edit the Category tag
        split_file_tags = get_tags_from_file(bucket_name, file_key)
        split_file_tags['Parent File'] = os.path.basename(file_key)
        split_file_tags['BU'] = 'All'
        split_file_tags.pop('File Name') #Not needed here. 

        # Define the S3 key for the output Excel file
        output_key = f"DataValidation/{split_file_tags['Mock Number']}/{split_file_tags['Pillar']}/{split_file_tags['Data Entity']}/{split_file_tags['Source']}/1-Extracted/{file_name}.xlsx"
        print(f"Tag values before original file upload are: {split_file_tags}.") #For troublehooting.
        
        # --- Upload the Excel file to S3 and update tags ---
        print("Before calling s3_upload from split csv.")
        s3_upload(bucket_name, output_key, excel_buffer, split_file_tags)
        
        print(f"Main Excel file '{output_key}' created successfully in bucket '{bucket_name}'.")

        # --- Process DataFrame: Split by Unique Value (first 5 characters) ---
        unique_values = df[column_name].str[:5].unique()
        
        for value in unique_values:
            # Filter the DataFrame for rows where the first 5 characters of column_name match 'value'
            value_df = df[df[column_name].str[:5] == value]
            
            # Create an in-memory bytes buffer for the Excel file.
            excel_buffer = io.BytesIO()
            
            # Write the subset DataFrame to the Excel buffer.
            # The 'openpyxl' engine is used for writing Excel files.
            value_df.to_excel(excel_buffer, index=False, engine='openpyxl')
            excel_buffer.seek(0)  # Reset buffer pointer to the beginning.
            
            # Define the S3 key for the output Excel file.
            # Example: "step1Validations/data_file_BU12345.xlsx"
            output_key = f"DataValidation/{split_file_tags['Mock Number']}/{split_file_tags['Pillar']}/{split_file_tags['Data Entity']}/{split_file_tags['Source']}/1-Extracted/{file_name}_BU{value}.xlsx"
            
            # Upload the Excel file from memory to the specified S3 bucket.
            s3_client.upload_fileobj(excel_buffer, Bucket=bucket_name, Key=output_key)
            
            # Specify BU Tag and add tags to uploaded file
            split_file_tags['BU'] = value
            print(f"Tags before uploading to S3: {split_file_tags}") #For troubleshooting.
            add_tags_to_s3_object(bucket_name,output_key,split_file_tags)

            # Log the upload status.
            print(f"Excel file '{output_key}' created successfully for value '{value}' with tags {split_file_tags}.")
    

    except Exception as e:
        #logging.error(f"An error occurred: {e}")
        print(f"An error occurred: {e}")
