import streamlit as st
import pandas as pd
import numpy as np
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
from datetime import datetime, timedelta
from pyspark.sql import SparkSession
from pyspark.ml import PipelineModel

# CẤU HÌNH & HÀM HỖ TRỢ
st.set_page_config(page_title="Hệ thống Giám sát Giao thông (Spark Engine)", layout="wide", page_icon="🚦")

st.markdown("""
    <style>
    .metric-card {background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b;}
    </style>
    """, unsafe_allow_html=True)

# KHỞI TẠO SPARK SESSION & LOAD MODEL
@st.cache_resource
def init_spark_and_model():
    """
    Khởi tạo SparkSession và Load Model từ thư mục.
    Dùng cache_resource để không phải khởi động lại Spark mỗi lần click.
    """
    try:
        # Khởi tạo Spark Session (Chạy local)
        spark = SparkSession.builder \
            .appName("Streamlit_Traffic_App") \
            .master("local[*]") \
            .config("spark.ui.showConsoleProgress", "false") \
            .getOrCreate()
        
        # Load Model từ thư mục 'train_model_spark'
        # Lưu ý: 'train_model_spark' là tên thư mục bạn đã upload
        model_path = "/traffic_project/train_model_spark" 
        model = PipelineModel.load(model_path)
        
        # Load Data địa điểm
        df_loc = pd.read_csv('data_converted.csv')
        
        # Xử lý tọa độ từ file csv
        if "Latitude,Longitude" in df_loc.columns:
            df_loc["Latitude,Longitude"] = df_loc["Latitude,Longitude"].astype(str).str.replace('"', '')
            df_loc[['Latitude', 'Longitude']] = df_loc['Latitude,Longitude'].str.split(',', expand=True).astype(float)
            
        return spark, model, df_loc
        
    except Exception as e:
        st.error(f"Lỗi khởi tạo Spark hoặc Load Model: {e}")
        return None, None, None

# Gọi hàm khởi tạo
spark, model, df_locations = init_spark_and_model()

def prepare_input(lat, lon, query_time, free_flow_speed=40):
    # Chuẩn bị dữ liệu đầu vào (Pandas DataFrame)
    hour = query_time.hour
    minute = query_time.minute
    time_in_minutes = hour * 60 + minute
    day_of_week = query_time.weekday()
    weekend = 1 if day_of_week >= 5 else 0
    
    # Tạo DataFrame Pandas
    input_data = pd.DataFrame([{
        'Latitude': float(lat),
        'Longitude': float(lon),
        'FreeFlowSpeed': float(free_flow_speed), 
        'TimeInMinutes': int(time_in_minutes),
        'DayOfWeek': int(day_of_week),
        'Weekend': int(weekend),
        
        # Spark Model yêu cầu các cột này phải tồn tại (dù pipeline có thể tự tạo lại)
        'Hour': int(hour),
        'Minute': int(minute)
    }])
    
    return input_data

def predict_with_spark(input_pandas_df):
    """Hàm trung gian: Pandas -> Spark -> Predict -> Kết quả"""
    if spark is None or model is None:
        return 0.0
    
    # Chuyển Pandas DF -> Spark DF
    spark_df = spark.createDataFrame(input_pandas_df)
    
    # Dự đoán (Transform)
    predictions = model.transform(spark_df)
    
    # Lấy kết quả về (Collect)
    # Model Spark trả về cột 'prediction'
    result = predictions.select("prediction").collect()[0]["prediction"]
    return float(result)

def get_status_color(speed, free_flow=40):
    ratio = speed / free_flow
    if ratio < 0.4: return "red", "Tắc nghẽn nghiêm trọng"
    if ratio < 0.7: return "orange", "Đông xe"
    return "green", "Thông thoáng"

# GIAO DIỆN SIDEBAR
st.sidebar.title("Bảng Điều Khiển")

input_date = st.sidebar.date_input("Ngày quan sát", datetime.now())
input_time = st.sidebar.time_input("Giờ quan sát", datetime.now())
current_time = datetime.combine(input_date, input_time)

st.sidebar.markdown("---")
st.sidebar.info(f"Thời gian: **{current_time.strftime('%H:%M %d/%m/%Y')}**")
st.sidebar.caption("Engine: Apache Spark MLlib")

selected_location_name = st.sidebar.selectbox(
    "Chọn nhanh địa điểm:", 
    ["Chọn trên bản đồ"] + list(df_locations['Location/Street'].unique()) if df_locations is not None else []
)

# TÍNH TOÁN DỮ LIỆU (BATCH PREDICTION QUA SPARK)
if spark and model and df_locations is not None:
    # Chuẩn bị dữ liệu Batch cho toàn bộ điểm trên bản đồ
    batch_pdf = df_locations.copy()
    batch_pdf['FreeFlowSpeed'] = 40.0
    batch_pdf['Hour'] = int(current_time.hour)
    batch_pdf['Minute'] = int(current_time.minute)
    batch_pdf['TimeInMinutes'] = int(current_time.hour * 60 + current_time.minute)
    batch_pdf['DayOfWeek'] = int(current_time.weekday())
    batch_pdf['Weekend'] = 1 if current_time.weekday() >= 5 else 0
    
    # Đảm bảo kiểu dữ liệu đúng chuẩn Spark yêu cầu (Double/Int)
    batch_pdf['Latitude'] = batch_pdf['Latitude'].astype(float)
    batch_pdf['Longitude'] = batch_pdf['Longitude'].astype(float)
    
    # Chuyển sang Spark DataFrame
    batch_sdf = spark.createDataFrame(batch_pdf)
    
    # Dự đoán hàng loạt (Nhanh hơn dự đoán từng dòng)
    pred_sdf = model.transform(batch_sdf)
    
    # Lấy kết quả về lại Pandas để hiển thị
    # Chỉ lấy cột 'prediction' và gán ngược lại
    results = pred_sdf.select("prediction").toPandas()
    df_locations['PredictedSpeed'] = results['prediction']

# HIỂN THỊ BẢN ĐỒ
col_map, col_info = st.columns([2, 1])

with col_map:
    st.subheader("BẢN ĐỒ GIAO THÔNG")
    
    if df_locations is not None:
        center_lat = df_locations['Latitude'].mean()
        center_lon = df_locations['Longitude'].mean()
        m = folium.Map(location=[center_lat, center_lon], zoom_start=13, tiles="CartoDB positron")
        
        # VẼ HEATMAP
        if True:
            heat_data = []
            for _, row in df_locations.iterrows():
                congestion_weight = 1 - (row['PredictedSpeed'] / 60)
                congestion_weight = max(0, min(1, congestion_weight))
                heat_data.append([row['Latitude'], row['Longitude'], congestion_weight])
            HeatMap(heat_data, radius=15, blur=20, gradient={0.2: 'blue', 0.5: 'lime', 0.9: 'red'}).add_to(m)

        # VẼ MARKER
        selected_row = None
        if selected_location_name != "Chọn trên bản đồ":
            selected_row = df_locations[df_locations['Location/Street'] == selected_location_name].iloc[0]

        for _, row in df_locations.iterrows():
            color, status = get_status_color(row['PredictedSpeed'])
            icon_type = "info-sign"
            if selected_row is not None and row['No'] == selected_row['No']:
                color = "blue"
                icon_type = "star"
                
            folium.Marker(
                location=[row['Latitude'], row['Longitude']],
                popup=f"<b>{row['Location/Street']}</b><br>Speed: {row['PredictedSpeed']:.1f} km/h",
                tooltip=f"{row['Location/Street']}",
                icon=folium.Icon(color=color, icon=icon_type)
            ).add_to(m)

        map_output = st_folium(m, width="100%", height=600, returned_objects=["last_clicked"])
    else:
        st.error("Không có dữ liệu địa điểm.")

# CHI TIẾT & DỰ BÁO TƯƠNG LAI
with col_info:
    st.subheader("Chi tiết Dự báo")
    
    current_location = None
    if df_locations is not None:
        # Case 1: Click Map
        if map_output['last_clicked']:
            click_lat = map_output['last_clicked']['lat']
            click_lon = map_output['last_clicked']['lng']
            df_locations['dist'] = ((df_locations['Latitude'] - click_lat)**2 + (df_locations['Longitude'] - click_lon)**2)**0.5
            closest = df_locations.sort_values('dist').iloc[0]
            if closest['dist'] < 0.005:
                current_location = closest
                
        # Case 2: Sidebar
        if current_location is None and selected_row is not None:
            current_location = selected_row

    if current_location is not None:
        st.markdown(f"### 📍 {current_location['Location/Street']}")
        st.caption(f"Quận: {current_location['District']}")
        
        # TỐC ĐỘ HIỆN TẠI
        cur_speed = current_location['PredictedSpeed']
        _, status_text = get_status_color(cur_speed)
        
        c1, c2 = st.columns(2)
        c1.metric("Tốc độ", f"{cur_speed:.1f} km/h")
        c2.metric("Trạng thái", status_text)
                
    else:
        st.info("Hãy chọn một địa điểm để xem chi tiết.")