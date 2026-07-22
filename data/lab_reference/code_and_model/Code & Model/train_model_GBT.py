from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.regression import GBTRegressor
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml import Pipeline

# KHOI TAO SPARK
spark = SparkSession.builder \
    .appName("Traffic_Model_Training") \
    .getOrCreate()

# Duong dan file CSV ban vua tao ra tren HDFS
DATA_PATH = "hdfs://localhost:9000/traffic_project/processed_data_spark/*.csv" 
MODEL_OUTPUT = "hdfs://localhost:9000/traffic_project/train_model_spark"

# LOAD DU LIEU
print("Dang doc du lieu huan luyen...")
df = spark.read.csv(DATA_PATH, header=True, inferSchema=True)

# Dam bao cac cot la so (ep kieu cho chac chan)
df = df.withColumn("Latitude", col("Latitude").cast("double")) \
       .withColumn("Longitude", col("Longitude").cast("double")) \
       .withColumn("Hour", col("Hour").cast("int")) \
       .withColumn("Minute", col("Minute").cast("int")) \
       .withColumn("DayOfWeek", col("DayOfWeek").cast("int")) \
       .withColumn("Weekend", col("Weekend").cast("int")) \
       .withColumn("CurrentSpeed", col("CurrentSpeed").cast("double"))

# Tao them feature TimeInMinutes (neu chua co trong file csv output)
df = df.withColumn("TimeInMinutes", col("Hour") * 60 + col("Minute"))

# Xoa dong thieu du lieu
df = df.dropna()

# CHUAN BI FEATURES
# Spark can gom cac cot input thanh 1 cot Vector ten la "features"
feature_cols = ['Latitude', 'Longitude', 'TimeInMinutes', 'DayOfWeek', 'Weekend']

assembler = VectorAssembler(
    inputCols=feature_cols,
    outputCol="features"
)

# CHIA TAP TRAIN/TEST
# Chia 80% de hoc, 20% de thi
train_data, test_data = df.randomSplit([0.8, 0.2], seed=42)

print(f"So luong mau Train: {train_data.count():,}")
print(f"So luong mau Test: {test_data.count():,}")

# DINH NGHIA MO HINH (GBT Regressor)
gbt = GBTRegressor(
    featuresCol="features",
    labelCol="CurrentSpeed", # Cot can du doan
    maxIter=100,             # So luong cay (giong n_estimators)
    maxDepth=5,              # Do sau cay
    seed=42
)

# Tao Pipeline (Quy trinh khep kin: Gop Features -> Train Model)
pipeline = Pipeline(stages=[assembler, gbt])

# HUAN LUYEN
print("Bat dau huan luyen mo hinh")
model = pipeline.fit(train_data)

# DANH GIA
print("Dang danh gia tren tap Test")
predictions = model.transform(test_data)

# Hien thi vai ket qua du doan so voi thuc te
predictions.select("CurrentSpeed", "prediction").show(5)

# Tinh sai so RMSE (Root Mean Squared Error)
evaluator = RegressionEvaluator(
    labelCol="CurrentSpeed", 
    predictionCol="prediction", 
    metricName="rmse"
)
rmse = evaluator.evaluate(predictions)
print(f"Sai so trung binh (RMSE): {rmse:.2f} km/h")

# LUU MO HINH
print(f"--> Dang luu mo hinh vao HDFS: {MODEL_OUTPUT}")
# Spark luu model duoi dang Folder, khong phai file .pkl
model.write().overwrite().save(MODEL_OUTPUT)

print("Hoan tat!")
spark.stop()