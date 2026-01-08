from datetime import datetime

def parse_filename(filename: str) -> dict:
    print("Entered parsed_file_name")
    try:
        # Remove the file extension
        filename_no_ext = filename.rsplit('.', 1)[0]

        # Split by underscores
        parts = filename_no_ext.split('_')

        # Ensure filename has enough parts
        if len(parts) < 6:
            raise ValueError("Filename format is incorrect.")

        # Extract relevant parts
        pillar = parts[0]
        data_entity = '_'.join(parts[1:-4])  # Everything between pillar and mock number
        mock_number = parts[-4]
        source = parts[-3]
        date_str = parts[-2]
        time_str = parts[-1]

        # Validate date and time formats
        if len(date_str) != 8 or len(time_str) != 4:
            raise ValueError("Date-time format in filename is incorrect.")

        date_obj = datetime.strptime(date_str, "%Y%m%d")
        time_obj = datetime.strptime(time_str, "%H%M").strftime("%I:%M %p").lower()
        created_date_time = f"{date_obj.strftime('%m/%d/%Y')} {time_obj}"

        # Construct Table Name without date and time
        file_name = '_'.join(parts[:-2])

        return {
            "Created Date-Time": created_date_time,
            "File Name": file_name,
            "Source": source,
            "Mock Number": mock_number,
            "Pillar": pillar,
            "Data Entity": data_entity
        }
    except Exception as e:
        print(f"Error: {e}")
        return {}


def parse_tsql_filename(filename: str) -> dict:
    print("Entered parse_filename")
    
    try:
        # Define valid categories
        valid_categories = {"LOAD": "Load", "VALIDATION": "Validation", "RECON": "Recon", "CONVERSION": "Conversion"}
        
        # Extract file extension and check validity
        if not filename.endswith(".sql"):
            print("Skipping file as it does not end with '.sql'")
            return {}
        
        # Remove the file extension
        filename_no_ext = filename.rsplit('.', 1)[0]

        # Split by underscores
        parts = filename_no_ext.split('_')

        # Ensure filename has enough parts
        if len(parts) < 4:
            raise ValueError("Filename format is incorrect.")
        
        # Extract and validate category
        category_key = parts[-1].upper()
        if category_key not in valid_categories:
            raise ValueError(f"Invalid category: {category_key}. Valid categories are Load, Validation, Recon, and Conversion.")
        category = valid_categories[category_key]
        
        # Identify mock number (last part before category that starts with 'MOCK')
        mock_index = -2  # Assume second-to-last part is mock number
        while mock_index >= -len(parts) and not parts[mock_index].upper().startswith("MOCK"):
            mock_index -= 1
        
        if mock_index < -len(parts):
            raise ValueError("Mock number not found in expected format.")
        
        mock_number = parts[mock_index].upper()  # Preserve original uppercase format
        
        # Extract source (the part right after mock number and before category)
        source_index = mock_index + 1
        source = parts[source_index] if source_index < len(parts) - 1 else ""
        
        # Extract relevant parts
        pillar = parts[0]
        data_entity = '_'.join(parts[1:mock_index])  # Everything between pillar and mock number
        file_name = '_'.join(parts[:-1])  # Remove only the last part (category)
        
        return {
            "Pillar": pillar,
            "Data Entity": data_entity,
            "File Name": file_name,
            "Table Name": file_name,
            "Mock Number": mock_number,
            "Source": source,
            "Category": category
        }
    except Exception as e:
        print(f"Error: {e}")
        return {}
