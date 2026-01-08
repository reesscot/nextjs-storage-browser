import boto3
import pandas as pd
import pyodbc
import io
import json

def LoadFile(bucket_name, file_key):
    # Initialize S3 client
    s3_client = boto3.client('s3')

    try:
        # Download the file from S3
        response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        file_content = response['Body'].read().decode('utf-8')
        
        # Load the CSV content into a DataFrame
        data = pd.read_csv(io.StringIO(file_content), dtype={
            "NAME1_AS_SUPPLIER_NAME": "string",
            "NAME1_AC_ALTERNATE_NAME": "string",
            "DH_ECON_SCTR_SUPPLIER_TYPE": "string",
            "BLANK_AS_DUNS_NUMBER": "string",
            "BLANK_AS_SIC": "string",
            "VENDOR_ID_AS_TAXPAYER_ID": "string",
            "DH_ECON_SCTR_21_AS_FEDERAL_REPORTABLE": "string",
            "BLANK_FEDERAL_INCOME_TAX_TYPE": "string",
            "BLANK_TAX_REPORTING_NAME": "string",
            "Y_AS_USE_WITHHOLDING_TAX": "string",
            "PR_AS_WITHHOLDING_TAX_GROUP": "string",
            "VENDOR_ID": "string",
            "VENDOR_CLASS": "string",
            "VENDOR_STATUS": "string",
            "LAST_PO_DT": "string",
            "LAST_VCHR_DT": "string",
            "LAST_CNTR_DT": "string",
            "LAST_PYMN_DT": "string",
            "LAST_EDIT_DT": "string",
            "LAST_INVC_DT": "string",
            "LAST_PO_BU": "string",
            "LAST_VCHR_BU": "string",
            "LAST_PYMN_BU": "string",
            "LAST_CNTR_BU": "string",
            "LAST_INVC_BU": "string"
        })

        # Replace NaN values in the DataFrame
        data = data.fillna("")
    
    except s3_client.exceptions.NoSuchKey as e:
        print(f"Error: The file with key '{file_key}' does not exist in the bucket '{bucket_name}'.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

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
    
    # Connect to SQL Server
    cnxn = pyodbc.connect(connection_string)
    cursor = cnxn.cursor()

    # Insert each row from the DataFrame into the database table
    for index, row in data.iterrows():
        cursor.execute("""
            INSERT INTO SCM_SUPPLIER_MOCK7_PRIFAS
            (Supplier_Name, ALTERNATE_NAME, Supplier_Type, DUNS_NUMBER, SIC, TAXPAYER_ID, FEDERAL_REPORTABLE, FEDERAL_INCOME_TAX_TYPE, TAX_REPORTING_NAME, USE_WITHHOLDING_TAX, PR_AS_WITHHOLDING_TAX_GROUP, Supplier_ID, VENDOR_CLASS, VENDOR_STATUS, LAST_PO_DT, LAST_VCHR_DT, LAST_CNTR_DT, LAST_PYMN_DT, LAST_EDIT_DT, LAST_INVC_DT, LAST_PO_BU, LAST_VCHR_BU, LAST_PYMN_BU, LAST_CNTR_BU, LAST_INVC_BU)  
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            row.NAME1_AS_SUPPLIER_NAME, row.NAME1_AC_ALTERNATE_NAME, row.DH_ECON_SCTR_SUPPLIER_TYPE,
            row.BLANK_AS_DUNS_NUMBER, row.BLANK_AS_SIC, row.VENDOR_ID_AS_TAXPAYER_ID,
            row.DH_ECON_SCTR_21_AS_FEDERAL_REPORTABLE, row.BLANK_FEDERAL_INCOME_TAX_TYPE,
            row.BLANK_TAX_REPORTING_NAME, row.Y_AS_USE_WITHHOLDING_TAX, row.PR_AS_WITHHOLDING_TAX_GROUP,
            row.VENDOR_ID, row.VENDOR_CLASS, row.VENDOR_STATUS, row.LAST_PO_DT, row.LAST_VCHR_DT, row.LAST_CNTR_DT,
            row.LAST_PYMN_DT, row.LAST_EDIT_DT, row.LAST_INVC_DT, row.LAST_PO_BU, row.LAST_VCHR_BU, 
            row.LAST_PYMN_BU, row.LAST_CNTR_BU, row.LAST_INVC_BU
        )

    # Commit and close the connection
    cnxn.commit()
    cursor.close()
    cnxn.close()
    print("File successfully imported to SCM_SUPPLIER_MOCK7_PRIFAS")