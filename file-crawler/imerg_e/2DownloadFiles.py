import os
import sys
import time
import re
import requests
from requests.auth import HTTPBasicAuth
from concurrent.futures import ThreadPoolExecutor, as_completed

# Thông tin đăng nhập FTP
FTP_USER = 'tungba100302@gmail.com'
FTP_PASSWORD = 'tungba100302@gmail.com'

def download_file(url, output_folder, max_retries=3):
    """
    Hàm để tải file từ url và lưu vào thư mục output_folder với tên đã định dạng, có cơ chế retry.
    """
    attempt = 0
    while attempt < max_retries:
        try:
            # Trích xuất thông tin ngày từ tên file trong URL
            date_match = re.search(r'\.(\d{8})-S\d{6}', url)
            if date_match:
                date_str = date_match.group(1)
                file_name = f"imerg_e_{date_str}.tif"
            else:
                print(f"Không tìm thấy định dạng ngày trong URL: {url}")
                return
            
            file_path = os.path.join(output_folder, file_name)
            
            # Gửi yêu cầu HTTP GET để tải file với Basic Authentication
            response = requests.get(url, stream=True, auth=HTTPBasicAuth(FTP_USER, FTP_PASSWORD))
            response.raise_for_status()  # Kiểm tra lỗi HTTP
            
            # Ghi nội dung của file vào output folder
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            print(f"Tải thành công: {file_name}")
            return  # Thành công thì thoát hàm
            
        except Exception as e:
            attempt += 1
            print(f"Không thể tải {url} - Thử lại lần {attempt}/{max_retries} - Lỗi: {e}")
            if attempt == max_retries:
                print(f"Bỏ qua file: {file_name}")
            else:
                time.sleep(2)  # Nghỉ trước khi thử lại

def download_files_from_txt(txt_file, month=None):
    """
    Hàm để đọc file txt và tải các URL theo tháng (nếu có).
    """
    # Lấy năm từ tên file (file có format {year}.txt)
    year = os.path.splitext(os.path.basename(txt_file))[0]
    
    # Tạo thư mục lưu trữ theo format "files/{year}"
    output_folder = os.path.join("files", year)
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Đọc danh sách URL từ file txt
    with open(txt_file, 'r') as f:
        urls = f.read().splitlines()
    
    # Lọc các URL theo tháng (nếu có)
    if month:
        urls = [url for url in urls if f'/{year}/{month:02d}/' in url]
    
    # Danh sách các URL cần tải (loại bỏ những file đã tồn tại)
    urls_to_download = []
    for url in urls:
        # Trích xuất thông tin ngày từ tên file trong URL
        date_match = re.search(r'\.(\d{8})-S\d{6}', url)
        if date_match:
            date_str = date_match.group(1)
            file_name = f"imerg_e_{date_str}.tif"
        else:
            print(f"Không tìm thấy định dạng ngày trong URL: {url}")
            continue
        
        file_path = os.path.join(output_folder, file_name)
        
        # Kiểm tra nếu file đã tồn tại thì bỏ qua URL này
        if not os.path.exists(file_path):
            urls_to_download.append(url)
        else:
            print(f"File đã tồn tại, bỏ qua: {file_name}")
    
    # Sử dụng ThreadPoolExecutor để tải các file song song
    with ThreadPoolExecutor(max_workers=6) as executor:  # Giảm max_workers để giảm tải cho server
        future_to_url = {executor.submit(download_file, url, output_folder): url for url in urls_to_download}
        
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                future.result()  # Lấy kết quả, ném lỗi nếu có
            except Exception as exc:
                print(f"URL {url} sinh lỗi: {exc}")

if __name__ == "__main__":
    # Kiểm tra nếu tham số được truyền từ dòng lệnh
    if len(sys.argv) < 2:
        print("Vui lòng truyền năm dưới dạng tham số, ví dụ: python script.py 2024 [month]")
        sys.exit(1)
    
    year = sys.argv[1]
    month = int(sys.argv[2]) if len(sys.argv) > 2 else None  # Lấy tháng nếu có

    # Kiểm tra tính hợp lệ của tháng
    if month and (month < 1 or month > 12):
        print("Tháng không hợp lệ. Vui lòng nhập tháng từ 1 đến 12.")
        sys.exit(1)
    
    # Tạo đường dẫn đến file txt theo năm
    txt_file = os.path.join("urls", f"{year}.txt")
    
    if not os.path.exists(txt_file):
        print(f"File {txt_file} không tồn tại.")
        sys.exit(1)

    # Gọi hàm để tải file từ danh sách URL trong file txt
    download_files_from_txt(txt_file, month)
