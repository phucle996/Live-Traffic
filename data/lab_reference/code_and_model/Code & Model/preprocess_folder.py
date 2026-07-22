import pandas as pd
import numpy as np
import os
import glob
import warnings

# Tắt các cảnh báo không cần thiết
warnings.filterwarnings('ignore')

# CẤU HÌNH
INPUT_FOLDER = 'data'           # Thư mục chứa file gốc
OUTPUT_FOLDER = 'preprocess data' # Thư mục chứa file sau xử lý
os.makedirs(OUTPUT_FOLDER, exist_ok=True) # Tự tạo thư mục output nếu chưa có

def process_single_file(input_path, output_path, filename):
    """Hàm xử lý logic cho 1 file duy nhất"""
    try:
        # Đọc dữ liệu
        df = pd.read_csv(input_path)
        original_len = len(df)
        
        # Xóa hàng trùng lặp
        df.drop_duplicates(inplace=True)
        
        # Lọc Confidence >= 0.9
        # Kiểm tra cả viết hoa và thường cho chắc chắn
        if 'Confidence' in df.columns:
            df = df[df['Confidence'] >= 0.9]
        elif 'confidence' in df.columns:
            df = df[df['confidence'] >= 0.9]
            
        # Chuyển đổi thời gian & Tạo đặc trưng
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        df['Hour'] = df['Timestamp'].dt.hour
        df['Minute'] = df['Timestamp'].dt.minute
        df['DayOfWeek'] = df['Timestamp'].dt.dayofweek
        df['Weekend'] = df['DayOfWeek'].apply(lambda x: 1 if x >= 5 else 0)
        
        # Thêm cột Tỷ lệ lưu thông (Congestion Ratio)
        # Sử dụng numpy where để xử lý nhanh và tránh chia cho 0
        df['CongestionRatio'] = np.where(
            df['FreeFlowSpeed'] > 0,
            df['CurrentSpeed'] / df['FreeFlowSpeed'],
            0.0
        )
        df['CongestionRatio'] = df['CongestionRatio'].round(4)
        
        # Bỏ các cột không cần thiết (Giữ lại GPS: Latitude, Longitude)
        cols_to_drop = ['Location/Street', 'District', 'Timestamp']
        # Chỉ drop những cột thực sự tồn tại
        existing_cols_to_drop = [c for c in cols_to_drop if c in df.columns]
        df.drop(columns=existing_cols_to_drop, inplace=True)
        
        # Lưu file
        df.to_csv(output_path, index=False)
        
        print(f"✔ Đã xử lý: {filename}")
        print(f"   - Giảm từ {original_len} dòng xuống {len(df)} dòng")
        
    except Exception as e:
        print(f"✘ Lỗi khi xử lý file {filename}: {e}")

def main():
    # Lấy danh sách tất cả file .csv trong thư mục data
    search_path = os.path.join(INPUT_FOLDER, "*.csv")
    csv_files = glob.glob(search_path)
    
    if not csv_files:
        print(f"Không tìm thấy file .csv nào trong thư mục '{INPUT_FOLDER}'")
        return

    print(f"Tìm thấy {len(csv_files)} file csv. Bắt đầu xử lý...\n" + "-"*30)
    
    for file_path in csv_files:
        # Lấy tên file gốc (ví dụ: data.csv)
        filename = os.path.basename(file_path)
        
        # Tạo tên file mới (ví dụ: preprocess_data.csv)
        new_filename = f"preprocess_{filename}"
        output_path = os.path.join(OUTPUT_FOLDER, new_filename)
        
        process_single_file(file_path, output_path, filename)
        
    print("-" * 30)
    print(f"Kiểm tra thư mục '{OUTPUT_FOLDER}' để lấy file kết quả.")

if __name__ == "__main__":
    main()