from execute_tsql import execute_tsql

def validate_tag_values(tags: dict) -> dict:
    """
    Validates if the concatenated tag values exist in the corresponding SQL table.
    
    Args:
        tags (dict): Dictionary containing 'Pillar', 'Data Entity', 'Mock Number', and 'Source'.
    
    Returns:
        bool: True if the value is found in the table, False otherwise.
    """
    print("In validate_tag_values.") #For troubleshooting.
    print(f"File tags are: {tags}") #For troubleshooting.
    try:
        # Extract required values
        pillar = tags.get("Pillar")
        data_entity = tags.get("Data Entity")
        mock_number = tags.get("Mock Number")
        source = tags.get("Source")
        file_name = tags.get("File Name")
        category = tags.get("Category")
        
        # Ensure all required values are present
        #if not all([pillar, data_entity, mock_number, source]):
        #    raise ValueError("Missing one or more required tag values.")

        # Ensure file name is present
        if not file_name:
            raise ValueError("Missing File Name tag value.")
        
        # Construct table name
        #table_name = f"SETUP_FILE_COLUMN_NAMES_{mock_number}"
        table_name = f"SETUP_CONVERSION_PLAN_{mock_number}"
        
        # Construct expected tag value
        #expected_value = f"{pillar}_{data_entity}_{mock_number}_{source}"
        
        # Construct SQL query
        if category == "Load":
            tsql_query = (
                #f"SELECT TOP 1 1 FROM {table_name} WHERE file_name = '{expected_value}';"
                f"SELECT * FROM {table_name} WHERE table_name = '{file_name}' and EntityOnFileStructure is not null;"
            )
        
        else:
            tsql_query = (
                #f"SELECT TOP 1 1 FROM {table_name} WHERE file_name = '{expected_value}';"
                f"SELECT * FROM {table_name} WHERE filename = '{file_name}';"
            )

        print(f"Going to run query: {tsql_query}")
        
        # Execute query
        result = execute_tsql(tsql_query)
        print(f"SQL Results: {result}")
        
        # Handle different return types
        if isinstance(result, list) and result:  # If it's a non-empty list, return the first record
            return result[0]  # Return first dictionary from the list
        else:
            return {}  # Return empty dictionary if no records are found
    
    except Exception as e:
        print(f"Error in validate_tags: {str(e)}")
        return False
