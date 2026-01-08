from execute_tsql import execute_tsql
from get_tags_from_file import get_tags_from_file

def get_bu_split_field(bucket_name, file_key):
    #Replace "+" with space to avoid errors.
    file_key = file_key.replace("+", " ") 

    print(f"In get_bu_split_field: {file_key}") #For troubleshooting

    #Get file tag values
    tags = get_tags_from_file(bucket_name, file_key)
    print(f"In get_bu_split_field tags: {tags}") #For troubleshooting

    # Extract Table Name and Mock Number from tags
    mock_number = tags.get('Mock Number')
    table_name_tag = tags.get('Table Name')

    # Construct table name
    #table_name = f"SETUP_FILE_COLUMN_NAMES_{mock_number}"
    table_name = f"SETUP_CONVERSION_PLAN_{mock_number}"

    #Build TSQL statement
    tsql_query = (
                    #f"SELECT TOP 1 1 FROM {table_name} WHERE file_name = '{expected_value}';"
                    f"SELECT TOP 1 extractefieldbu FROM {table_name} WHERE table_name = '{table_name_tag}';"
                )
    
    print(f"In get_bu_split_field the query to be ran is: {tsql_query}") #For troubleshooting

    result  = execute_tsql(tsql_query)

    bu_split_field = result[0]['extractefieldbu']

    print(f"In In get_bu_split_field the bu_split_field to be retfurned is {bu_split_field}")

    return bu_split_field