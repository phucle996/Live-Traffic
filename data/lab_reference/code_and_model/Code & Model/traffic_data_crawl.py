import requests
import pandas as pd
import time
from datetime import datetime

# TomTom API key
API_KEY = "iphqzsxmWMoyRioFGtCGljBQ0v1OE0KZ"
#API_KEY = "RzHUrgUWabD9tBzYZmGfJWzenuKfpfBp"
#API_KEY = "zpdSSDZClZiF0dMGzqzthUuod8ELsiph"

# File CSV chứa dữ liệu vị trí
input_file = "data_converted.csv"
output_file = "traffic_data_from_traffic.csv"

# Đọc danh sách địa điểm
df = pd.read_csv(input_file)

# Chuẩn bị file lưu kết quả
columns = ["Timestamp", "Location/Street", "District", "Latitude", "Longitude", "CurrentSpeed", "FreeFlowSpeed", "Confidence"]
result_df = pd.DataFrame(columns=columns)
result_df.to_csv(output_file, index=False, encoding='utf-8-sig')

# CAU HINH THU LAI (RETRY)
MAX_RETRIES = 5 # So lan thu lai toi da neu gap loi mang
RETRY_DELAY = 10 # So giay cho giua moi lan thu lai

def get_tomtom_data(lat, lon):
    url = "https://api.tomtom.com/traffic/services/4/flowSegmentData/relative/10/json"
    params = {"point": f"{lat},{lon}", "key": API_KEY}
    
    # LOGIC THU LAI
    for attempt in range(MAX_RETRIES):
        try:
            res = requests.get(url, params=params, timeout=10)

            # API tra ve thanh cong
            if res.status_code == 200:
                data = res.json()
                flow = data.get("flowSegmentData", {})
                return {
                    "currentSpeed": flow.get("currentSpeed"),
                    "freeFlowSpeed": flow.get("freeFlowSpeed"),
                    "confidence": flow.get("confidence")
                }
            
            # API tra ve loi
            # Neu la loi phia TomTom hoac Key thi khong can thu lai
            elif res.status_code != 200:
                print(f"Loi API {res.status_code} tai ({lat}, {lon}) - {res.text}. Se KHONG thu lai.")
                return None # Bo qua, khong thu lai

        # Gap loi ket noi mang
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            print(f"LOI MANG: {e}. Dang cho {RETRY_DELAY} giay de thu lai... (Lan {attempt + 1}/{MAX_RETRIES})")
            if attempt < MAX_RETRIES - 1: # Neu chua phai lan cuoi
                time.sleep(RETRY_DELAY) # Cho truoc khi thu lai
            else:
                print(f"Da thu lai {MAX_RETRIES} lan cho ({lat}, {lon}) nhung van loi.")
        
        # Gap loi code khac
        except Exception as e:
            print(f"Lỗi bat ngo (Exception): {e}. Se KHONG thu lai.")
            return None # Bo qua, khong thu lai

    # Neu vong 'for' chay het ma van khong thanh cong (do loi mang)
    return None

while True:
    print(f"Bắt đầu lấy dữ liệu lúc {datetime.now().strftime('%H:%M:%S')}")

    all_data = []
    for _, row in df.iterrows():
        lat, lon = row["Latitude,Longitude"].split(",")
        lat, lon = lat.strip(), lon.strip()

        info = get_tomtom_data(lat, lon)
        if info:
            all_data.append({
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Location/Street": row["Location/Street"],
                "District": row["District"],
                "Latitude": lat,
                "Longitude": lon,
                "CurrentSpeed": info["currentSpeed"],
                "FreeFlowSpeed": info["freeFlowSpeed"],
                "Confidence": info["confidence"]
            })

    if all_data:
        pd.DataFrame(all_data).to_csv(output_file, mode='a', header=False, index=False, encoding='utf-8-sig')
        print(f"Lưu {len(all_data)} dòng vào {output_file}")

    print("Chờ 2 phút trước lần tiếp theo...\n")
    time.sleep(120)  # 2 phút