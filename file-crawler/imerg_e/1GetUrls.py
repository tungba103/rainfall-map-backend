import requests
from bs4 import BeautifulSoup
import argparse
import os

def get_file_urls(year, month):
    # Thông tin xác thực
    username = 'tungba100302@gmail.com'
    password = 'tungba100302@gmail.com'
    
    # URL gốc với định dạng tháng hai chữ số
    base_url = f'https://jsimpsonhttps.pps.eosdis.nasa.gov/imerg/gis/early/{year}/{month:02d}/'
    
    # Gửi yêu cầu HTTP GET với thông tin xác thực
    response = requests.get(base_url, auth=(username, password))
    
    # Kiểm tra nếu yêu cầu không thành công
    if response.status_code != 200:
        print(f"Không thể truy cập URL: {base_url}")
        return []
    
    # Phân tích HTML
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Tìm tất cả các thẻ <a> và lấy giá trị href
    file_urls = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        # Lọc các URL có đuôi ".1day.tif" và chứa "0150"
        if href.endswith('.1day.tif') and '0150' in href:
            # Tạo URL đầy đủ
            full_url = base_url + href
            file_urls.append(full_url)
    
    return file_urls

def main():
    # Sử dụng argparse để nhận tham số year từ dòng lệnh
    parser = argparse.ArgumentParser(description='Lấy danh sách file URLs cho một năm cụ thể.')
    parser.add_argument('year', type=int, help='Năm cần lấy dữ liệu')

    args = parser.parse_args()
    year = args.year

    # Đường dẫn tệp đầu ra
    output_dir = "urls"
    output_file = os.path.join(output_dir, f"{year}.txt")

    # Tạo thư mục nếu chưa tồn tại
    os.makedirs(output_dir, exist_ok=True)

    # Mở tệp để ghi kết quả
    with open(output_file, 'w') as file:
        # Lặp qua các tháng từ 01 đến 12
        for month in range(1, 13):
            print(f"Đang xử lý: Năm {year}, Tháng {month:02d}")
            # Lấy danh sách các URL cho từng tháng trong năm
            urls = get_file_urls(year, month)
            # Ghi các URL vào tệp
            for url in urls:
                file.write(url + '\n')

    print(f'Danh sách URL đã được lưu vào {output_file}')

if __name__ == "__main__":
    main()
