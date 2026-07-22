import pandas as pd
import glob
import xgboost as xgb
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

# CẤU HÌNH (BẠN CHỈ CẦN CHỈNH SỬA PHẦN NÀY)
DATA_FOLDER = './preprocess data/*.csv' 
MODEL_FILE = 'xgboost_model.pkl'

# LOAD VÀ GỘP DỮ LIỆU TỪ NHIỀU FILE
print(f"--> Đang quét dữ liệu từ: {DATA_FOLDER}")
all_files = glob.glob(DATA_FOLDER)

if not all_files:
    print("LỖI: Không tìm thấy file .csv nào! Vui lòng kiểm tra lại đường dẫn.")
    exit()

# Đọc và gộp data (Sử dụng list comprehension để tối ưu tốc độ)
df_list = []
for filename in all_files:
    try:
        # Đọc file, bỏ qua lỗi nếu file hỏng nhẹ
        df_temp = pd.read_csv(filename)
        df_list.append(df_temp)
    except Exception as e:
        print(f"Bỏ qua file lỗi: {filename} ({e})")

if not df_list:
    print("Không đọc được dữ liệu nào.")
    exit()

df = pd.concat(df_list, axis=0, ignore_index=True)
print(f"\nTổng cộng: {len(df):,} dòng dữ liệu.")

# TIỀN XỬ LÝ (PRE-PROCESSING)
print("--> Đang xử lý dữ liệu...")

# Tạo đặc trưng thời gian (TimeInMinutes)
if 'Hour' not in df.columns or 'Minute' not in df.columns:
    if 'Timestamp' in df.columns:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        df['Hour'] = df['Timestamp'].dt.hour
        df['Minute'] = df['Timestamp'].dt.minute
    else:
        print("Lỗi: Dữ liệu thiếu cột thời gian (Timestamp hoặc Hour/Minute).")
        exit()

df['TimeInMinutes'] = df['Hour'] * 60 + df['Minute']

# Kiểm tra target 'CongestionRatio'
if 'CongestionRatio' not in df.columns:
    print("Cảnh báo: Không thấy cột 'CongestionRatio'. Đang tự tính toán...")
    df['CongestionRatio'] = df['CurrentSpeed'] / (df['FreeFlowSpeed'] + 0.001)

# Lọc dữ liệu sạch
# Features: Vị trí + Đặc điểm đường + Thời gian
features = ['Latitude', 'Longitude', 'FreeFlowSpeed', 'TimeInMinutes', 'DayOfWeek', 'Weekend']
target = 'CurrentSpeed'

df_clean = df.dropna(subset=features + [target])

X = df_clean[features]
y = df_clean[target]

# HUẤN LUYỆN MÔ HÌNH (TRAINING)
print(f"--> Bắt đầu huấn luyện XGBoost với target là '{target}'...")

# Chia tập train/test (90% Train, 10% Test để đánh giá)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, random_state=42)

# Khởi tạo mô hình XGBoost Regressor
model = xgb.XGBRegressor(
    objective='reg:squarederror',
    n_estimators=500,
    learning_rate=0.05,
    max_depth=9,
    subsample=0.7,
    colsample_bytree=0.7,
    n_jobs=-1,      # Sử dụng 100% CPU
    random_state=42,
    tree_method='hist' # Dùng GPU
)

model.fit(X_train, y_train)

# ĐÁNH GIÁ VÀ LƯU (SAVE)
# Đánh giá sơ bộ
y_pred = model.predict(X_test)
r2 = r2_score(y_test, y_pred)
mae = mean_absolute_error(y_test, y_pred)

print("\n" + "="*30)
print("KẾT QUẢ HUẤN LUYỆN:")
print(f" - R2 Score (Độ chính xác): {r2:.4f}")
print(f" - MAE (Sai số trung bình): {mae:.4f}")
print("="*30)

# Lưu model
print(f"\n--> Đang lưu mô hình vào file: {MODEL_FILE}")
joblib.dump(model, MODEL_FILE)

print("Chương trình kết thúc.")