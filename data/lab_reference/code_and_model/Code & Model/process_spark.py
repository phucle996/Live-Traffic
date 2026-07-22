from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_timestamp, hour, minute, dayofweek, when, round, lit

# KHỞI TẠO SPARK SESSION
spark = SparkSession.builder \
    .appName("Traffic_Data_Preprocessing") \
    .getOrCreate()

# Cấu hình đường dẫn HDFS
HADOOP_URI = "hdfs://localhost:9000" 
INPUT_PATH = f"{HADOOP_URI}/traffic_project/data/*.csv" 
OUTPUT_PATH = f"{HADOOP_URI}/traffic_project/processed_data_spark"

# ĐỌC DỮ LIỆU TỪ HADOOP (HDFS)
print(f"--> Đang đọc dữ liệu từ: {INPUT_PATH}")
df = spark.read.csv(INPUT_PATH, header=True, inferSchema=True)

original_count = df.count()
print(f"Tổng số dòng ban đầu: {original_count:,}")

# XỬ LÝ DỮ LIỆU

# Xóa hàng trùng lặp
df = df.dropDuplicates()

# Lọc Confidence >= 0.9
# Kiểm tra xem cột viết hoa hay thường để lọc
if "Confidence" in df.columns:
    df = df.filter(col("Confidence") >= 0.9)
elif "confidence" in df.columns:
    df = df.filter(col("confidence") >= 0.9)

# Chuyển đổi thời gian (Timestamp)
df = df.withColumn("Timestamp", to_timestamp(col("Timestamp")))

# Tạo cột Hour, Minute, DayOfWeek
df = df.withColumn("Hour", hour(col("Timestamp")))
df = df.withColumn("Minute", minute(col("Timestamp")))
df = df.withColumn("DayOfWeek", dayofweek(col("Timestamp")))

# Weekend (Điều chỉnh logic theo chuẩn Spark)
# Cuối tuần là Thứ 7 (7) hoặc Chủ Nhật (1)
df = df.withColumn("Weekend", 
                   when(col("DayOfWeek").isin([1, 7]), 1)
                   .otherwise(0))

# Tính CongestionRatio (Tỷ lệ lưu thông)
df = df.withColumn("CongestionRatio", 
                   when(col("FreeFlowSpeed") > 0, col("CurrentSpeed") / col("FreeFlowSpeed"))
                   .otherwise(0.0))

# Làm tròn 4 chữ số thập phân
df = df.withColumn("CongestionRatio", round(col("CongestionRatio"), 4))

# Loại bỏ cột thừa
# Chỉ giữ lại các cột cần thiết cho Model hoặc Visual
cols_to_drop = ['Location/Street', 'District', 'Timestamp', 'date']
# Dùng *cols_to_drop để unpack list thành các tham số rời
df_clean = df.drop(*cols_to_drop)

# Gộp tất cả dữ liệu thành 1 file duy nhất
df_single_file = df_clean.coalesce(1)

# LƯU KẾT QUẢ VỀ HADOOP (HDFS)
print(f"Đang lưu kết quả vào: {OUTPUT_PATH}")

df_single_file.write \
    .mode("overwrite") \
    .option("header", "true") \
    .csv(OUTPUT_PATH)

print("Xử lý hoàn tất! Kiểm tra HDFS để xem kết quả.")
spark.stop()