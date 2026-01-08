import boto3
import pyodbc
import csv
import os
from parse_filename import parse_filename
from build_tsql_from_tags import build_tsql_from_tags
from get_tags_from_file import get_tags_from_file
from add_tags_to_s3_object import add_tags_to_s3_object
from generate_validation_file import generate_header_validation_file

# Connection string for SQL Server using ODBC Driver 18
server = '10.0.151.32'
database = 'Hacienda_ERP_Test'
username = 'lambda_functions'
password = 'coPPer873'
port = '1433'  # Default port is 1433 for SQL Server

connection_string = (
    f'DRIVER={{ODBC Driver 18 for SQL Server}};'
    f'SERVER={server},{port};'
    f'DATABASE={database};'
    f'UID={username};'
    f'PWD={password};'
    f'TrustServerCertificate=yes'
)

# Define query to fetch expected column headers
#TSQL_QUERY = ""
#TSQL_QUERY = "SELECT value AS ColumnTitle FROM SETUP_FILE_COLUMN_NAMES_MOCK8 CROSS APPLY STRING_SPLIT(columntitleline, ',') WHERE Table_name = 'SCM_SUPPLIER_MOCK8_PRIFAS'"

# Initialize S3 client
s3 = boto3.client("s3")
ses = boto3.client("ses", region_name="us-east-1")

# Email Configuration
SENDER_EMAIL = "erpinfo@elitebco.com"  


def get_csv_headers_from_s3(bucket_name, file_key):
    
    """Retrieve the headers from the CSV file stored in S3."""
    response = s3.get_object(Bucket=bucket_name, Key=file_key)
    #csv_content = response["Body"].read().decode("utf-8").splitlines() #We need to revert back to this if we don't want to allow any invalid characters.
    csv_content = response["Body"].read().decode("utf-8", errors="ignore").splitlines()
    reader = csv.reader(csv_content)
    headers = next(reader)  # Get the first row as header
    return headers


def get_headers_from_db(tsql_query):
    """Retrieve column headers from SQL Server using a T-SQL query."""
    #connection_string = f"DRIVER={DB_DRIVER};SERVER={DB_SERVER};DATABASE={DB_NAME};UID={DB_USERNAME};PWD={DB_PASSWORD}"
    print("entered get_headers_from_db")
    print("in get_headers_from_db tsql_query = ", tsql_query) #for troubleshooting
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        #print(tsql_query) #For troubleshooting
        cursor.execute(tsql_query)
        db_headers = [row[0] for row in cursor.fetchall()]
        conn.close()
        return db_headers
    except Exception as e:
        print(f"Database connection error: {e}")
        return []


def compare_headers(csv_headers, db_headers):
    """Compare headers and generate the output list."""
    max_length = max(len(csv_headers), len(db_headers))
    
    result = []
    for i in range(max_length):
        csv_header = csv_headers[i].strip('"') if i < len(csv_headers) else ""
        db_header = db_headers[i].strip('"') if i < len(db_headers) else ""
        exact_match = csv_header == db_header
        result.append([i + 1, csv_header, db_header, exact_match])
    
    return result


def write_comparison_to_s3(bucket_name, output_file_key, comparison_results):
    """Write comparison results to a CSV file and upload it to S3."""
    output_file = "/tmp/output.csv"

    with open(output_file, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Order Number", "CSV Header", "Database Header", "Exact"])
        writer.writerows(comparison_results)

    s3.upload_file(output_file, bucket_name, output_file_key)
    print(f"Comparison file uploaded to s3://{bucket_name}/{output_file_key}")

def send_email(user_email, bucket_name, output_file_key):
    """Send an email with the validation file link."""
    file_url = f"https://{bucket_name}.s3.amazonaws.com/{output_file_key}"

    email_subject = "Header Validation Report Available"
    email_body = f"""
    <html>
    <body>
        <p>Hello,</p>
        <p>Your uploaded file has been processed. The header validation report is available at the following link:</p>
        <p><a href="{file_url}">{file_url}</a></p>
        <p>Thank you.</p>
    </body>
    </html>
    """

    response = ses.send_email(
        Source=SENDER_EMAIL,
        Destination={"ToAddresses": [user_email]},
        Message={
            "Subject": {"Data": email_subject},
            "Body": {"Html": {"Data": email_body}},
        },
    )

    print(f"Email sent to {user_email}: {response}")

def get_user_email_from_s3(bucket_name, file_key):
    """Retrieve user email from S3 metadata or implement a lookup method."""
    response = s3.head_object(Bucket=bucket_name, Key=file_key)
    metadata = response.get("Metadata", {})

    #Test get email from Cognito
    

    return metadata.get("user_email", "erpinfo@elitebco.com")  # Default if not found

def ValidateHeaders(bucket_name, file_key):
    """Main function to validate headers."""
    print("In ValidateHeaders bucket name ", bucket_name) #For troubleshooting
    print("In ValidateHeaders file key ", file_key) #For troubleshooting
    csv_headers = get_csv_headers_from_s3(bucket_name, file_key)
    tsql_query = build_tsql_from_tags(bucket_name, file_key)
    print("in ValidateHeaders tsql_query = ", tsql_query) #for troubleshooting
    db_headers = get_headers_from_db(tsql_query)

    if not csv_headers or not db_headers:
        return {"status": "error", "message": "Failed to retrieve headers"}

    comparison_results = compare_headers(csv_headers, db_headers)

    # Check if any record in comparison_results contains False
    if any(not record[3] for record in comparison_results):
        print("Discrepancy found in header validation. Generating validation file.")
        parent_tags = get_tags_from_file(bucket_name, file_key)
        tagsforvalidationfile = parent_tags.copy()
        print(f"In Validate_Headers Errors and Warnings tag value for file {file_key} are: {parent_tags.get('Errors and Warnings')}")
        if parent_tags.get('Errors and Warnings'):
            parent_tags["Errors and Warnings"] = f"{parent_tags.get('Errors and Warnings')} - Valid Headers: Fail"
            add_tags_to_s3_object(bucket_name, file_key, parent_tags)
        else:
            parent_tags["Errors and Warnings"] = "Valid Headers: Fail"
            add_tags_to_s3_object(bucket_name, file_key, parent_tags)

        #Get only the parent file name without the folder and subfolders.
        parent_file_name = file_key.split('/')[-1]
        
        #Update the tagsforvalidationfile to include the parent file name and change Category to "File Name Validation".
        tagsforvalidationfile["Parent File Name"] = parent_file_name
        tagsforvalidationfile["File Category"] = 'Header Validation'
        tagsforvalidationfile.pop('File Name')
        print(f"Tags after updating Header Validation {parent_tags}") #for troubleshooting

        # Get the file_key last modified date and time and apply formatting.
        response = s3.head_object(Bucket=bucket_name, Key=file_key)
        last_modified = response["LastModified"]  
        last_modified_formatted = last_modified.strftime("%m_%d_%Y %I_%M_%p").lower()  # Format
        
        output_file_key = f"InitialUploadErrors/{last_modified_formatted} {parent_file_name}/{parent_file_name} (Header Validation).xlsx"
        print(f"Tags to add to header validation file are: {tagsforvalidationfile}") #For troubleshooting
        generate_header_validation_file(tagsforvalidationfile, output_file_key, comparison_results)

        # Get user email and send notification
        #user_email = get_user_email_from_s3(bucket_name, file_key)
        #send_email(user_email, bucket_name, output_file_key)

        return {"status": "success", "message": f"Comparison file generated at {output_file_key}"} #requested production access and others.
