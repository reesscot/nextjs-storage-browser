import boto3
import pyodbc
import pandas as pd
from get_aws_secret import get_aws_secret
from generate_validation_file import *
from get_tags_from_file import get_tags_from_file
from relocate_file import relocate_file_specified_new_key

connection_str = get_aws_secret("Hacienda_ERP_Test_MSSQL_text")

def execute_tsql(tsql_query, return_format='dict'):
    """
    Executes a T-SQL query and returns results in the specified format.

    Parameters:
        tsql_query (str): The T-SQL query to execute.
        connection_string (str): The connection string for the database.
        return_format (str): The format of the returned data.
                             Options:
                               - 'dict'         : List of dictionaries (default)
                               - 'tuple'        : List of tuples
                               - 'dataframe'    : Pandas DataFrame
                               - 'first_column' : List containing only the first column value of each row

    Returns:
        The query results in the specified format, or None if an error occurs.
    """
    try:
        with pyodbc.connect(connection_str) as conn:
            with conn.cursor() as cursor:
                cursor.execute(tsql_query)
                
                # Option 1: Return as a Pandas DataFrame
                if return_format == 'dataframe':
                    rows = cursor.fetchall()
                    columns = [column[0] for column in cursor.description]
                    return pd.DataFrame(rows, columns=columns)
                
                # Option 2: Return as a list of tuples
                elif return_format == 'tuple':
                    return cursor.fetchall()
                
                # Option 3: Return only the first column of each row (e.g., db_headers)
                elif return_format == 'first_column':
                    return [row[0] for row in cursor.fetchall()]
                
                # Default Option: Return as a list of dictionaries
                else:
                    columns = [column[0] for column in cursor.description]
                    return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    except Exception as e:
        print(f"Error executing query: {e}")
        return None

def insert_rows(tsql_statement, rows, csv_bucket_name, csv_file_key):
    print("In insert_rows.") #for troubleshooting

    tsql_statement = tsql_statement.strip()  # Remove extra whitespace/newlines
    print("T-SQL Statement:", tsql_statement)
    expected_params = tsql_statement.count('?')
    provided_params = len(rows[0])
    
    if rows and expected_params == provided_params:
        print(f"Expected parameters: {expected_params}, Provided parameters: {provided_params}")
        try:
            cnxn = pyodbc.connect(connection_str)
            cursor = cnxn.cursor()
            cursor.executemany(tsql_statement, rows)
            cnxn.commit()
            cursor.close()
            cnxn.close()
            print("T-SQL executed successfully.")
        except Exception as e:
            print(f"Error executing T-SQL: {e}")
        
            #Get parent file name and other data needed.
            parent_file_name = csv_file_key.split('/')[-1]
            parent_file_tags = get_tags_from_file(csv_bucket_name, csv_file_key)
            print(f"parent_file_tags are: {parent_file_tags}") #For troubleshooting.
            tags_for_insert_rows_error = parent_file_tags.copy()
            print(f"tags_for_insert_rows_error are: {tags_for_insert_rows_error}") #For troubleshooting.
            #Get the parent file folders to be used in error file key
            parts = csv_file_key.strip('/').split('/')
            folders_for_error_file_key = '/'.join(parts[1:-1])
            print(f"In insert rows error the folders_for_error_file_key is: {folders_for_error_file_key}")

            #Update "Errors and Warnings" tag in parent file
            if parent_file_tags.get('Errors and Warnings'):
                parent_file_tags["Errors and Warnings"] = f"{parent_file_tags.get('Errors and Warnings')} - Insert Rows: Fail"
                #add_tags_to_s3_object(csv_bucket_name, csv_file_key, parent_file_tags)
            else:
                parent_file_tags["Errors and Warnings"] = "Insert Rows: Fail"
                #add_tags_to_s3_object(csv_bucket_name, csv_file_key, parent_file_tags)
            
            #Update tags that will be uploaded to validation error file.
            tags_for_insert_rows_error["File Category"] = "Insert Rows Failed"
            tags_for_insert_rows_error["Parent File Name"] = parent_file_name

            # Get the parent file last modified date and time and apply formatting.
            s3_client = boto3.client('s3')
            response = s3_client.head_object(Bucket=csv_bucket_name, Key=csv_file_key)
            last_modified = response["LastModified"]  
            last_modified_formatted = last_modified.strftime("%m_%d_%Y %I_%M_%p").lower()  # Format

            #Generate validation file name.
            message = f"Could not load {parent_file_name} because of the following error: {e}"
            error_file_key = f"ConversionFileErrors/{folders_for_error_file_key}/{last_modified_formatted} {parent_file_name}/{parent_file_name} (Insert Rows Error).txt"
            generate_insert_rows_error_file(tags_for_insert_rows_error, error_file_key, message)

            #Relocate the parent file.
            new_parent_file_key = f"ConversionFileErrors/{folders_for_error_file_key}/{last_modified_formatted} {parent_file_name}/{parent_file_name}"
            relocate_file_specified_new_key(csv_bucket_name, csv_file_key, new_parent_file_key, parent_file_tags)
            
            return None
    
    else:
        print(f"Provided param count not equal to expected param count. Expected parameters: {expected_params}, Provided parameters: {provided_params}")
        

        #Get parent file name and other data needed.
        parent_file_name = csv_file_key.split('/')[-1]
        parent_file_tags = get_tags_from_file(csv_bucket_name, csv_file_key)
        print(f"parent_file_tags are: {parent_file_tags}") #For troubleshooting.
        tags_for_invalid_number_of_params = parent_file_tags.copy()
        print(f"tags_for_invalid_number_of_params are: {tags_for_invalid_number_of_params}") #For troubleshooting.
        #Get the parent file folders to be used in error file key
        parts = csv_file_key.strip('/').split('/')
        folders_for_error_file_key = '/'.join(parts[1:-1])
        print(f"In insert rows number of params error the folders_for_error_file_key is: {folders_for_error_file_key}")

        #Update "Errors and Warnings" tag in parent file
        if parent_file_tags.get('Errors and Warnings'):
            parent_file_tags["Errors and Warnings"] = f"{parent_file_tags.get('Errors and Warnings')} - File Load Param Count: Fail"
            #add_tags_to_s3_object(csv_bucket_name, csv_file_key, parent_file_tags)
        else:
            parent_file_tags["Errors and Warnings"] = "File Load Param Count: Fail"
            #add_tags_to_s3_object(csv_bucket_name, csv_file_key, parent_file_tags)
        
        #Update tags that will be uploaded to validation error file.
        tags_for_invalid_number_of_params["File Category"] = "Invalid Number of Params"
        tags_for_invalid_number_of_params["Parent File Name"] = parent_file_name

        # Get the parent file last modified date and time and apply formatting.
        s3_client = boto3.client('s3')
        response = s3_client.head_object(Bucket=csv_bucket_name, Key=csv_file_key)
        last_modified = response["LastModified"]  
        last_modified_formatted = last_modified.strftime("%m_%d_%Y %I_%M_%p").lower()  # Format

        #Generate validation file name.
        message = f"Load file {parent_file_name} has a total of {provided_params} parameters. Nonetheless; the TSQL file expects {expected_params} parameters."
        error_file_key = f"ConversionFileErrors/{folders_for_error_file_key}/{last_modified_formatted} {parent_file_name}/{parent_file_name} (Load Params Count Error).txt"
        generate_load_file_param_count_error_file(tags_for_invalid_number_of_params, error_file_key, message)

        #Relocate the parent file.
        new_parent_file_key = f"ConversionFileErrors/{folders_for_error_file_key}/{last_modified_formatted} {parent_file_name}/{parent_file_name}"
        relocate_file_specified_new_key(csv_bucket_name, csv_file_key, new_parent_file_key, parent_file_tags)
        
        return None

def update_stmnt(tsql_query):

    try:
        with pyodbc.connect(connection_str) as conn:
            with conn.cursor() as cursor:
                cursor.execute(tsql_query)
                conn.commit()
                return cursor.rowcount
    except Exception as e:
        print(f"An error occurred while executing the update: {e}")
        return None
    
    




