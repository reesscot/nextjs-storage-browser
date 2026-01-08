import boto3

s3_client = boto3.client("s3")

def build_tsql_from_tags(bucket_name, file_key):
    """
    Retrieves the 'table_name' from S3 object (tags or metadata) and builds a dynamic T-SQL statement.

    :param bucket_name: S3 bucket name
    :param file_key: S3 object key
    :return: Formatted T-SQL query string
    """
    try:
        # Try to fetch tags first
        print(f"build_tsql_from_tags Bucket {bucket_name} and File {file_key}") #for trubleshooting
        tagging_response = s3_client.get_object_tagging(Bucket=bucket_name, Key=file_key)
        tags = {tag['Key']: tag['Value'] for tag in tagging_response.get('TagSet', [])}
        print(f"Tags: {tags}") #For troubleshooting.

        # Extract Table Name and Mock Number from tags
        table_name = tags.get('Table Name')
        mock_number = tags.get('Mock Number')

        print(f" build_tsql_from_tags table_names: {table_name}") #For troubleshooting.
        print(f" build_tsql_from_tags mock_number: {mock_number}") #For troubleshooting.



        if not table_name or not mock_number:
            raise ValueError(f"'Table Name' or 'Mock Number' not found in tags or metadata for file: {file_key}")

        # Construct the T-SQL query
        print(f"SELECT value AS ColumnTitle FROM SETUP_FILE_COLUMN_NAMES_{mock_number} CROSS APPLY STRING_SPLIT(columntitleline, ',') WHERE Table_name = '{table_name}' ") #for troubleshooting

        tsql_query = f"SELECT value AS ColumnTitle FROM SETUP_FILE_COLUMN_NAMES_{mock_number} CROSS APPLY STRING_SPLIT(columntitleline, ',') WHERE Table_name = '{table_name}' "
        print("tsql_query before returning: ",tsql_query)

        return tsql_query

    except Exception as e:
        raise RuntimeError(f"Failed to generate T-SQL: {str(e)}")