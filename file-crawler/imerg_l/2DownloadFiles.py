import os
import sys
import time
import re
import requests
import zipfile
from io import BytesIO
from requests.auth import HTTPBasicAuth
from concurrent.futures import ThreadPoolExecutor, as_completed

# FTP Authentication
FTP_USER = 'tungba100302@gmail.com'
FTP_PASSWORD = 'tungba100302@gmail.com'

def download_and_extract_liquid_tif(url, output_folder, max_retries=3):
    """
    Downloads a file from the given URL. If it's a .zip file, extracts only the 'liquid.tif' file.
    """
    attempt = 0
    while attempt < max_retries:
        try:
            # Extract date from URL to create the file name
            date_match = re.search(r'\.(\d{8})\.V\d{2}', url)
            if date_match:
                date_str = date_match.group(1)
                file_name = f"imerg_l_{date_str}.tif"
            else:
                print(f"Cannot find date format in URL: {url}")
                return
            
            file_path = os.path.join(output_folder, file_name)

            # Send HTTP GET request to download the file
            response = requests.get(url, stream=True, auth=HTTPBasicAuth(FTP_USER, FTP_PASSWORD))
            response.raise_for_status()  # Raise an error for bad HTTP status

            # Check if the file is a ZIP file
            if 'zip' in response.headers.get('Content-Type', '').lower():
                # Read the zip file content
                with zipfile.ZipFile(BytesIO(response.content)) as zip_file:
                    # Check if 'liquid.tif' exists in the zip
                    liquid_file_name = next((name for name in zip_file.namelist() if 'liquid.tif' in name), None)
                    if liquid_file_name:
                        # Extract and save 'liquid.tif'
                        with zip_file.open(liquid_file_name) as liquid_file, open(file_path, 'wb') as f:
                            f.write(liquid_file.read())
                        print(f"Downloaded and extracted: {file_name}")
                    else:
                        print(f"'liquid.tif' not found in {url}")
            else:
                print(f"File at {url} is not a ZIP file. Skipping.")
            return  # Exit the function on success
            
        except Exception as e:
            attempt += 1
            print(f"Failed to download {url} - Retry {attempt}/{max_retries} - Error: {e}")
            if attempt == max_retries:
                print(f"Skipping file: {file_name}")
            else:
                time.sleep(2)  # Wait before retrying

def download_files_from_txt(txt_file, month=None):
    """
    Reads a .txt file and downloads URLs based on the specified month (if any).
    """
    # Extract year from the file name (file format is {year}.txt)
    year = os.path.splitext(os.path.basename(txt_file))[0]
    
    # Create the output folder with format "files/{year}"
    output_folder = os.path.join("files", year)
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Read the list of URLs from the .txt file
    with open(txt_file, 'r') as f:
        urls = f.read().splitlines()
    
    # Filter URLs by month if specified
    if month:
        urls = [url for url in urls if f'/{year}/{month:02d}/' in url]
    
    # List of URLs to download (excluding files that already exist)
    urls_to_download = []
    for url in urls:
        # Extract date to create file name
        date_match = re.search(r'\.(\d{8})\.V\d{2}', url)
        if date_match:
            date_str = date_match.group(1)
            file_name = f"imerg_l_{date_str}.tif"
        else:
            print(f"Cannot find date format in URL: {url}")
            continue
        
        file_path = os.path.join(output_folder, file_name)
        
        # Check if the file already exists, skip if it does
        if not os.path.exists(file_path):
            urls_to_download.append(url)
        else:
            print(f"File already exists, skipping: {file_name}")
    
    # Use ThreadPoolExecutor to download files in parallel
    with ThreadPoolExecutor(max_workers=6) as executor:
        future_to_url = {executor.submit(download_and_extract_liquid_tif, url, output_folder): url for url in urls_to_download}
        
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                future.result()  # Raise any exceptions that occurred
            except Exception as exc:
                print(f"URL {url} generated an exception: {exc}")

if __name__ == "__main__":
    # Check if parameters are passed from the command line
    if len(sys.argv) < 2:
        print("Please provide a year as an argument, e.g., python script.py 2024 [month]")
        sys.exit(1)
    
    year = sys.argv[1]
    month = int(sys.argv[2]) if len(sys.argv) > 2 else None  # Get the month if provided

    # Validate month
    if month and (month < 1 or month > 12):
        print("Invalid month. Please enter a month between 1 and 12.")
        sys.exit(1)
    
    # Create the path to the .txt file for the given year
    txt_file = os.path.join("urls", f"{year}.txt")
    
    if not os.path.exists(txt_file):
        print(f"File {txt_file} does not exist.")
        sys.exit(1)

    # Call the function to download files from the URL list in the .txt file
    download_files_from_txt(txt_file, month)
