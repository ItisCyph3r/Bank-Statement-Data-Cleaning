import os
import glob
import pdfplumber
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

pdf_folder = os.getenv('PDF_FOLDER')  
output_file = os.getenv('OUTPUT_FILE')  
pdf_password = os.getenv('PDF_PASSWORD')


def process_pdf(pdf_path, pdf_password=None):
    data = []
    
    with pdfplumber.open(pdf_path, password=pdf_password) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                data.extend(table)

    if not data:
        print(f"No data extracted from {pdf_path}")
        return None

    
    df = pd.DataFrame(data)

    df.columns = df.iloc[0]
    df = df[1:]  
    df = df.iloc[:, 1:]  

    df = df.rename(columns={df.columns[-1]: 'None'})  

    
    extra_columns = [col for col in df.columns if 'None' in col or 'Unnamed' in col]
    if extra_columns:
        df['Remarks'] = df['Remarks'].fillna('') + ' ' + df[extra_columns[0]].fillna('')
        df['Remarks'] = df['Remarks'].str.strip()
        df = df.drop(columns=extra_columns)

    
    normalized_columns = [col.strip().lower() for col in df.columns]

    # Remove duplicate headers
    def is_duplicate_header(row):
        return [str(x).strip().lower() for x in row] == normalized_columns
    df = df[~df.apply(is_duplicate_header, axis=1)]

    
    df = df.reset_index(drop=True)

    
    for col in ['Credits', 'Debits']:
        if col in df.columns:
            df[col] = df[col].str.replace(r'[^0-9.,]', '', regex=True)
            df[col] = df[col].str.replace(',', '')
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df

# 🔹 Process and Merge All PDFs
all_data = []
pdf_files = glob.glob(os.path.join(pdf_folder, '*.pdf'))

for pdf_file in pdf_files:
    df = process_pdf(pdf_file, pdf_password=pdf_password)  
    
    if df is not None:
        all_data.append(df)

# Merge and Save
if all_data:
    final_df = pd.concat(all_data, ignore_index=True)
    final_df.to_csv(output_file, index=False)
    print(f"All PDFs processed! Final file: {output_file}")
else:
    print("No valid data found in PDFs!")
