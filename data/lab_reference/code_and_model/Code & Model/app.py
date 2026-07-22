import streamlit as st
import pandas as pd
import numpy as np
import joblib
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
from datetime import datetime, timedelta

# =========================================================
# 1. CẤU HÌNH & HÀM HỖ TRỢ
# =========================================================
st.set_page_config(page_title="Hệ thống Giám sát Giao thông TP.HCM", layout="wide", page_icon="🚦")

# CSS tùy chỉnh để làm đẹp giao diện
st.markdown("""
    <style>
    .metric-card {background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b;}
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def load_model_and_data():
    """Load model và dữ liệu địa điểm một lần duy nhất"""
    try:
        # Load Model
        model = joblib.load('xgboost_model.pkl')
        
        # Load Data và xử lý cột tọa độ
        df_loc = pd.read_csv('data_converted.csv')
        
        # Tách cột "Latitude,Longitude" thành 2 cột riêng
        if "Latitude,Longitude" in df_loc.columns:
            # Xóa các ký tự thừa như ngoặc kép nếu có
            df_loc["Latitude,Longitude"] = df_loc["Latitude,Longitude"].astype(str).str.replace('"', '')
            df_loc[['Latitude', 'Longitude']] = df_loc['Latitude,Longitude'].str.split(',', expand=True).astype(float)
        
        return model, df_loc
    except Exception as e:
        st.error(f"Lỗi khi load dữ liệu: {e}")
        return None, None

model, df_locations = load_model_and_data()

def prepare_input(lat, lon, query_time, free_flow_speed=40):
    # Feature Engineering giống hệt lúc train
    hour = query_time.hour
    minute = query_time.minute
    time_in_minutes = hour * 60 + minute
    day_of_week = query_time.weekday()
    weekend = 1 if day_of_week >= 5 else 0
    
    # Tạo DataFrame 1 dòng
    input_data = pd.DataFrame([{
        'Latitude': lat,
        'Longitude': lon,
        'FreeFlowSpeed': free_flow_speed,
        'TimeInMinutes': time_in_minutes,
        'DayOfWeek': day_of_week,
        'Weekend': weekend
    }])
    
    # Đảm bảo thứ tự cột (quan trọng với XGBoost)
    cols = ['Latitude', 'Longitude', 'FreeFlowSpeed', 'TimeInMinutes', 'DayOfWeek', 'Weekend']
    return input_data[cols]

def get_status_color(speed, free_flow=40):
    # Quy định màu sắc dựa trên tốc độ
    ratio = speed / free_flow
    if ratio < 0.4: return "red", "Tắc nghẽn nghiêm trọng"
    if ratio < 0.7: return "orange", "Đông xe"
    return "green", "Thông thoáng"

# =========================================================
# 2. GIAO DIỆN SIDEBAR
# =========================================================
st.sidebar.title("Bảng Điều Khiển")

# Chọn thời gian giả lập
input_date = st.sidebar.date_input("Ngày quan sát", datetime.now())
input_time = st.sidebar.time_input("Giờ quan sát", datetime.now())
current_time = datetime.combine(input_date, input_time)

st.sidebar.markdown("---")
st.sidebar.info(f"Thời gian hệ thống: **{current_time.strftime('%H:%M %d/%m/%Y')}**")

# Tùy chọn địa điểm 
selected_location_name = st.sidebar.selectbox(
    "Chọn nhanh địa điểm:", 
    ["Chọn trên bản đồ"] + list(df_locations['Location/Street'].unique())
)

# =========================================================
# 3. TÍNH TOÁN DỮ LIỆU TOÀN THÀNH PHỐ (BATCH PREDICTION)
# =========================================================
# Để vẽ Heatmap và Marker màu, ta cần dự đoán tốc độ cho TẤT CẢ các điểm trong file CSV tại thời điểm này
if model and df_locations is not None:
    # Tạo input cho toàn bộ điểm cùng lúc (nhanh hơn loop)
    batch_input = df_locations.copy()
    batch_input['FreeFlowSpeed'] = 40
    batch_input['TimeInMinutes'] = current_time.hour * 60 + current_time.minute
    batch_input['DayOfWeek'] = current_time.weekday()
    batch_input['Weekend'] = 1 if current_time.weekday() >= 5 else 0
    
    # Dự đoán
    # Lưu ý: Cần filter đúng cột để đưa vào model
    predict_cols = ['Latitude', 'Longitude', 'FreeFlowSpeed', 'TimeInMinutes', 'DayOfWeek', 'Weekend']
    
    try:
        df_locations['PredictedSpeed'] = model.predict(batch_input[predict_cols])
    except Exception as e:
        st.warning("Model có vẻ yêu cầu các feature khác. Đang dùng tốc độ ngẫu nhiên để demo giao diện.")
        df_locations['PredictedSpeed'] = np.random.randint(10, 50, size=len(df_locations))

# =========================================================
# 4. HIỂN THỊ BẢN ĐỒ CHÍNH
# =========================================================
col_map, col_info = st.columns([2, 1])

with col_map:
    st.subheader("BẢN ĐỒ GIAO THÔNG TP.HCM")
    
    # Tìm tọa độ trung tâm (Lấy trung bình các điểm)
    center_lat = df_locations['Latitude'].mean()
    center_lon = df_locations['Longitude'].mean()
    
    m = folium.Map(location=[center_lat, center_lon], zoom_start=13, tiles="CartoDB positron")
    
    # A. VẼ HEATMAP (Mức độ thông thoáng)
    if True:
        # Heatmap cần dữ liệu dạng [Lat, Lon, Weight]. 
        # Weight ở đây là mức độ Tắc nghẽn (1 - Speed/MaxSpeed). Tắc càng nặng (Speed thấp) -> Màu càng đậm.
        heat_data = []
        for _, row in df_locations.iterrows():
            congestion_weight = 1 - (row['PredictedSpeed'] / 40) # Giả sử max speed là 40
            congestion_weight = max(0, min(1, congestion_weight)) # Kẹp giá trị 0-1
            heat_data.append([row['Latitude'], row['Longitude'], congestion_weight])
            
        HeatMap(heat_data, radius=15, blur=20, gradient={0.2: "blue", 0.5: "lime", 0.9: "red"}).add_to(m)

    # B. VẼ MARKER CÁC ĐIỂM
    # Nếu người dùng chọn từ Sidebar, ta sẽ highlight điểm đó
    selected_row = None
    if selected_location_name != "Chọn trên bản đồ":
        selected_row = df_locations[df_locations['Location/Street'] == selected_location_name].iloc[0]

    for _, row in df_locations.iterrows():
        color, status = get_status_color(row['PredictedSpeed'])
        
        # Nếu điểm này đang được chọn -> Icon to hơn, màu khác
        icon_type = "info-sign"
        if selected_row is not None and row['No'] == selected_row['No']:
            color = "blue" # Highlight màu xanh dương
            icon_type = "star"
            
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            popup=f"<b>{row['Location/Street']}</b><br>Speed: {row['PredictedSpeed']:.1f} km/h",
            tooltip=f"{row['Location/Street']} ({status})",
            icon=folium.Icon(color=color, icon=icon_type)
        ).add_to(m)

    # Hiển thị Map
    # returned_objects=["last_clicked"] để bắt sự kiện click
    map_output = st_folium(m, width="100%", height=600, returned_objects=["last_clicked"])

# =========================================================
# 5. HIỂN THỊ CHI TIẾT & BÁO CÁO (KHI CHỌN ĐỊA ĐIỂM)
# =========================================================
with col_info:
    st.subheader("Thông tin chi tiết")
    
    # Xác định địa điểm đang được chọn (Ưu tiên Click trên Map -> Sau đó đến Selectbox)
    current_location = None
    
    # Case 1: Click trên Map
    if map_output['last_clicked']:
        click_lat = map_output['last_clicked']['lat']
        click_lon = map_output['last_clicked']['lng']
        # Tìm điểm gần nhất trong CSV với tọa độ click
        # (Tính khoảng cách Euclid đơn giản)
        df_locations['dist'] = ((df_locations['Latitude'] - click_lat)**2 + (df_locations['Longitude'] - click_lon)**2)**0.5
        closest_point = df_locations.sort_values('dist').iloc[0]
        
        # Nếu click đủ gần (sai số < 0.005 độ ~ 500m) thì mới nhận
        if closest_point['dist'] < 0.005:
            current_location = closest_point
            
    # Case 2: Chọn từ Sidebar (nếu chưa click map)
    if current_location is None and selected_row is not None:
        current_location = selected_row

    # --- HIỂN THỊ DỮ LIỆU ---
    if current_location is not None:
        st.markdown(f"### {current_location['Location/Street']}")
        st.caption(f"Quận: {current_location['District']}")
        
        # 1. TỐC ĐỘ HIỆN TẠI
        cur_speed = current_location['PredictedSpeed']
        color_code, status_text = get_status_color(cur_speed)
        
        col_metric1, col_metric2 = st.columns(2)
        col_metric1.metric("Tốc độ dự đoán", f"{cur_speed:.1f} km/h")
        col_metric2.metric("Trạng thái", status_text, delta_color="off")
        
    else:
        st.info("👈 Hãy chọn một địa điểm trên bản đồ hoặc danh sách bên trái để xem chi tiết.")
        
        # Hiển thị bảng dữ liệu tóm tắt nếu chưa chọn gì
        st.markdown("#### Danh sách các điểm giám sát")
        st.dataframe(df_locations[['Location/Street', 'District', 'PredictedSpeed']].sort_values('PredictedSpeed'), height=300)