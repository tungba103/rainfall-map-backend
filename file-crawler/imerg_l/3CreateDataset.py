import os
import sys
from datetime import datetime
import uuid  # Thêm thư viện uuid

def create_yaml_file(year, file_name, output_folder="data"):
    """
    Tạo file YAML cho một file TIFF cụ thể với định dạng tên và nội dung yêu cầu, nếu chưa tồn tại.
    """
    # Tạo thư mục lưu trữ theo format "data/{year}" nếu chưa tồn tại
    output_path = os.path.join(output_folder, year)
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # Đường dẫn file YAML cần tạo
    yaml_file_path = os.path.join(output_path, f"{file_name}.dataset.yaml")
    
    # Kiểm tra nếu file đã tồn tại thì bỏ qua
    if os.path.exists(yaml_file_path):
        print(f"File {yaml_file_path} đã tồn tại, bỏ qua.")
        return

    # Lấy ngày tháng từ tên file, định dạng YYYYMMDD
    date_str = file_name.split('_')[-1]  # Lấy phần YYYYMMDD từ tên file
    date_obj = datetime.strptime(date_str, "%Y%m%d")
    datetime_str = date_obj.strftime("%Y-%m-%dT00:00:00Z")

    # Tạo UUID ngẫu nhiên cho id
    unique_id = str(uuid.uuid4())

    # Định nghĩa nội dung YAML dưới dạng chuỗi
    yaml_content = f"""$schema: https://schemas.opendatacube.org/dataset
id: {unique_id}
product: 
  name: imerg_l_10KM_daily
crs: "EPSG:4326"
grids:
  default:
    shape: [1800, 3600] 
    transform: [0.1, 0.0, -180.0, 0.0, -0.1, 90.0, 0.0, 0.0, 1.0]
properties:
  datetime: "{datetime_str}"
measurements:
  Precipitation:
    path: /STORAGE/DATA/DATA_10KM_daily/imerg_l/{year}/{file_name}.tif
"""

    # Ghi nội dung vào file YAML
    with open(yaml_file_path, 'w') as yaml_file:
        yaml_file.write(yaml_content)
    print(f"Đã tạo file: {yaml_file_path}")

def generate_yaml_files(year=None, files_folder="files", output_folder="dataset"):
    """
    Duyệt qua các file TIFF và tạo file YAML tương ứng.
    """
    # Nếu có năm, chỉ lấy file từ thư mục files/{year}
    if year:
        tiff_folder = os.path.join(files_folder, year)
        if not os.path.exists(tiff_folder):
            print(f"Thư mục {tiff_folder} không tồn tại.")
            return
        tiff_files = [f for f in os.listdir(tiff_folder) if f.endswith('.tif')]
        tiff_files = [(year, f) for f in tiff_files]  # Đưa về định dạng (year, file) cho đồng nhất
    else:
        # Không có năm, lấy tất cả các file TIFF từ thư mục files/{year}/*
        tiff_files = []
        for root, dirs, files in os.walk(files_folder):
            for file in files:
                if file.endswith('.tif'):
                    # Lấy năm từ cấu trúc thư mục của file
                    year = os.path.basename(root)
                    tiff_files.append((year, file))

    # Tạo file YAML cho từng file TIFF
    for year, file in tiff_files:
        file_name = os.path.splitext(file)[0]  # Loại bỏ phần mở rộng .tif
        create_yaml_file(year, file_name, output_folder)

if __name__ == "__main__":
    # Nhận tham số năm nếu có từ dòng lệnh
    year = sys.argv[1] if len(sys.argv) > 1 else None

    # Gọi hàm để tạo file YAML
    generate_yaml_files(year)
