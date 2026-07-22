Đúng rồi. Dưới đây là một **đặc tả end-to-end hoàn chỉnh**, có thể copy nguyên khối đưa cho Gemini/Codex để nó triển khai từng phase.

Lab yêu cầu pipeline chính:

```text
TomTom API
→ dữ liệu CSV
→ HDFS
→ Spark ETL
→ Spark MLlib GBTRegressor
→ lưu model
→ Streamlit + Folium
```

Đây cũng là luồng được mô tả trong tài liệu Lab 5. 

---

# Prompt tổng thể đưa cho Gemini

```text
Bạn là Senior Data Engineer và Machine Learning Engineer.

Hãy xây dựng hoàn chỉnh project Lab 5: Hệ thống phân tích và dự đoán
lưu lượng giao thông đô thị.

Mục tiêu cuối cùng:
- Thu thập dữ liệu giao thông từ TomTom API hoặc dùng dữ liệu CSV có sẵn.
- Lưu dữ liệu thô vào HDFS.
- Xử lý dữ liệu bằng Apache Spark.
- Feature engineering dữ liệu thời gian và vị trí.
- Huấn luyện GBTRegressor bằng Spark MLlib.
- Đánh giá model bằng RMSE, MAE và R².
- Lưu model.
- Dùng model để dự đoán tốc độ giao thông.
- Hiển thị kết quả trên Streamlit và Folium.
- Toàn bộ hệ thống phải có thể chạy bằng Docker Compose trên laptop.
- Không hard-code API key, đường dẫn hoặc thông tin cấu hình.
- Code phải có logging, validation và xử lý lỗi.
- Mỗi phase phải có README hoặc hướng dẫn chạy.
- Không viết toàn bộ trong một file.
- Phân chia module rõ ràng theo cấu trúc bên dưới.
```

---

# Cấu trúc project cần tạo

```text
traffic-prediction-lab5/
│
├── docker-compose.yml
├── Dockerfile
├── .dockerignore
├── .gitignore
├── .env.example
├── requirements.txt
├── Makefile
├── README.md
│
├── config/
│   ├── application.yaml
│   ├── spark-defaults.conf
│   └── log_config.yaml
│
├── data/
│   ├── locations/
│   │   └── data_converted.csv
│   ├── seed/
│   │   └── *.csv
│   ├── output/
│   └── samples/
│
├── src/
│   ├── __init__.py
│   │
│   ├── common/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── logging_utils.py
│   │   ├── schemas.py
│   │   └── spark_session.py
│   │
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── tomtom_client.py
│   │   ├── crawl_traffic.py
│   │   ├── seed_loader.py
│   │   └── upload_to_hdfs.py
│   │
│   ├── processing/
│   │   ├── __init__.py
│   │   ├── validate_raw_data.py
│   │   ├── process_spark.py
│   │   └── data_quality_report.py
│   │
│   ├── training/
│   │   ├── __init__.py
│   │   ├── train_gbt.py
│   │   ├── evaluate_model.py
│   │   ├── hyperparameter_tuning.py
│   │   └── model_metadata.py
│   │
│   ├── prediction/
│   │   ├── __init__.py
│   │   ├── feature_builder.py
│   │   ├── predictor.py
│   │   └── batch_predict.py
│   │
│   └── dashboard/
│       ├── __init__.py
│       ├── app.py
│       ├── map_builder.py
│       └── dashboard_service.py
│
├── scripts/
│   ├── wait_for_hdfs.sh
│   ├── init_hdfs.sh
│   ├── upload_seed_data.sh
│   ├── run_ingestion.sh
│   ├── run_processing.sh
│   ├── run_training.sh
│   ├── run_prediction.sh
│   ├── run_pipeline.sh
│   └── clean_project.sh
│
├── tests/
│   ├── unit/
│   │   ├── test_config.py
│   │   ├── test_tomtom_client.py
│   │   ├── test_feature_builder.py
│   │   └── test_data_validation.py
│   │
│   ├── integration/
│   │   ├── test_hdfs_connection.py
│   │   ├── test_spark_processing.py
│   │   └── test_model_prediction.py
│   │
│   └── fixtures/
│       └── sample_traffic.csv
│
├── artifacts/
│   ├── models/
│   ├── metrics/
│   ├── predictions/
│   └── reports/
│
└── docs/
    ├── architecture.md
    ├── data_dictionary.md
    ├── api_ingestion.md
    ├── model_report.md
    └── demo_guide.md
```

---

# Phase 0 — Khởi tạo project và chuẩn hóa cấu hình

## Mục tiêu

Tạo bộ khung project, quản lý cấu hình tập trung và loại bỏ toàn bộ hard-code.

## Task

* Tạo cấu trúc thư mục.
* Tạo virtual environment hoặc Docker image.
* Tạo `requirements.txt`.
* Tạo `.env.example`.
* Tạo file YAML cấu hình.
* Viết module đọc biến môi trường.
* Thiết lập logging.
* Tạo `.gitignore`.
* Tạo README hướng dẫn ban đầu.

## File cần viết

### `.env.example`

```env
TOMTOM_API_KEY=
INGESTION_MODE=seed

HDFS_URI=hdfs://namenode:9000
HDFS_RAW_PATH=/traffic_project/raw
HDFS_PROCESSED_PATH=/traffic_project/processed
HDFS_MODEL_PATH=/traffic_project/models/gbt
HDFS_PREDICTION_PATH=/traffic_project/predictions

CRAWL_INTERVAL_SECONDS=120
MAX_RETRIES=5
RETRY_DELAY_SECONDS=10

SPARK_MASTER=spark://spark-master:7077
SPARK_APP_NAME=traffic-prediction

MODEL_MAX_ITER=100
MODEL_MAX_DEPTH=5
MODEL_SEED=42
```

### `requirements.txt`

Chứa tối thiểu:

```text
pyspark
streamlit
pandas
numpy
requests
folium
streamlit-folium
pyyaml
python-dotenv
scikit-learn
pytest
```

Phải pin phiên bản, không sử dụng `latest`.

### `config/application.yaml`

```yaml
project:
  name: traffic-prediction-lab5

ingestion:
  mode: seed
  interval_seconds: 120
  max_retries: 5

data:
  locations_file: data/locations/data_converted.csv
  seed_folder: data/seed

model:
  target: CurrentSpeed
  features:
    - Latitude
    - Longitude
    - TimeInMinutes
    - DayOfWeek
    - Weekend
```

### Module chung

```text
src/common/config.py
src/common/logging_utils.py
src/common/schemas.py
src/common/spark_session.py
```

## Kết quả cần đạt

```bash
python -c "from src.common.config import settings; print(settings)"
```

chạy thành công và đọc được `.env`.

## Acceptance criteria

* Không còn API key trong source code.
* Không hard-code `localhost:9000`.
* Không hard-code đường dẫn model.
* Mọi module dùng chung một đối tượng cấu hình.
* Logging có timestamp, level và tên module.

---

# Phase 1 — Dựng hạ tầng Docker, Hadoop và Spark

## Mục tiêu

Có một môi trường local end-to-end gồm:

```text
HDFS NameNode
HDFS DataNode
Spark Master
Spark Worker
Streamlit
```

## Task

* Viết `docker-compose.yml`.
* Tạo network chung.
* Tạo persistent volumes cho NameNode và DataNode.
* Dựng Spark master và ít nhất một Spark worker.
* Dựng container ứng dụng Python/Streamlit.
* Thêm health check.
* Thêm script chờ HDFS sẵn sàng.
* Tự động tạo thư mục HDFS ban đầu.

## File cần viết

```text
docker-compose.yml
Dockerfile
.dockerignore
config/spark-defaults.conf
scripts/wait_for_hdfs.sh
scripts/init_hdfs.sh
```

## Các service trong `docker-compose.yml`

```text
namenode
datanode
spark-master
spark-worker
hdfs-init
streamlit
```

Có thể thêm các profile tùy chọn:

```text
crawler
spark-job
```

## Các thư mục HDFS cần tạo

```text
/traffic_project/raw
/traffic_project/processed
/traffic_project/models
/traffic_project/predictions
/traffic_project/metrics
```

## Lệnh cần hỗ trợ

```bash
docker compose up -d
docker compose ps
docker compose logs namenode
docker compose logs spark-master
```

## Kết quả cần đạt

```bash
docker compose exec namenode hdfs dfs -ls /traffic_project
```

phải hiển thị các thư mục đã tạo.

## Acceptance criteria

* NameNode có trạng thái healthy.
* DataNode kết nối được NameNode.
* Spark Worker kết nối được Spark Master.
* Container ứng dụng phân giải được hostname `namenode`.
* Dữ liệu không mất sau khi restart container.
* Không dùng IP container cố định.

---

# Phase 2 — Định nghĩa schema và data contract

## Mục tiêu

Chuẩn hóa định dạng dữ liệu đầu vào và tránh lỗi schema giữa crawler, Spark, model và dashboard.

## Schema dữ liệu thô

```text
Timestamp        timestamp/string
Location/Street string
District        string
Latitude        double
Longitude       double
CurrentSpeed    double
FreeFlowSpeed   double
Confidence      double
```

## Task

* Viết schema Spark rõ ràng.
* Không dựa hoàn toàn vào `inferSchema`.
* Viết hàm kiểm tra cột bắt buộc.
* Kiểm tra latitude, longitude.
* Kiểm tra tốc độ không âm.
* Kiểm tra `Confidence` trong khoảng hợp lệ.
* Xác định chuẩn duy nhất cho `DayOfWeek`.

## Quy ước bắt buộc

Sử dụng chuẩn Python:

```text
Monday = 0
Tuesday = 1
...
Sunday = 6
```

Cuối tuần:

```text
Weekend = 1 khi DayOfWeek thuộc [5, 6]
```

Spark `dayofweek()` không được sử dụng trực tiếp mà không chuyển đổi, vì Spark trả:

```text
Sunday = 1
...
Saturday = 7
```

Công thức chuyển đổi Spark sang chuẩn Python:

```python
python_day_of_week = (spark_day_of_week + 5) % 7
```

## File cần viết

```text
src/common/schemas.py
src/processing/validate_raw_data.py
docs/data_dictionary.md
tests/unit/test_data_validation.py
```

## Kết quả cần đạt

Một hàm:

```python
validate_traffic_dataframe(df)
```

trả về:

```text
valid_dataframe
invalid_dataframe
validation_statistics
```

## Acceptance criteria

* Thiếu cột bắt buộc phải báo lỗi rõ ràng.
* Không silently bỏ qua dữ liệu lỗi.
* Dữ liệu lỗi được ghi ra khu vực quarantine hoặc báo cáo.
* Quy ước `DayOfWeek` giống nhau ở ETL, training và prediction.

---

# Phase 3 — Data ingestion từ TomTom hoặc seed CSV

## Mục tiêu

Hệ thống chạy được trong hai chế độ:

```text
INGESTION_MODE=api
INGESTION_MODE=seed
```

Điều này bảo đảm vẫn demo được khi API hết hạn hoặc mất mạng.

## Task chế độ API

* Đọc danh sách vị trí từ `data_converted.csv`.
* Gọi TomTom Flow Segment API.
* Thêm timeout.
* Retry lỗi mạng.
* Không retry vô hạn với lỗi authentication.
* Ghi log status code.
* Không ghi đè dữ liệu cũ.
* Mỗi lần crawl tạo hoặc append file theo ngày.
* Có thể chạy một lần hoặc chạy daemon.

## Task chế độ seed

* Đọc toàn bộ CSV có sẵn trong `data/seed`.
* Validate schema.
* Upload lên HDFS.
* Không yêu cầu TomTom API key.

## File cần viết

```text
src/ingestion/tomtom_client.py
src/ingestion/crawl_traffic.py
src/ingestion/seed_loader.py
src/ingestion/upload_to_hdfs.py
scripts/run_ingestion.sh
scripts/upload_seed_data.sh
tests/unit/test_tomtom_client.py
```

## Thiết kế `tomtom_client.py`

```python
class TomTomTrafficClient:
    def get_flow_segment(self, latitude: float, longitude: float) -> dict:
        ...
```

Không để logic HTTP lẫn với logic ghi CSV.

## Đường dẫn raw trên HDFS

Nên partition theo ngày:

```text
/traffic_project/raw/date=2026-07-21/traffic_data.csv
```

## Kết quả cần đạt

```bash
docker compose exec namenode \
  hdfs dfs -ls -R /traffic_project/raw
```

phải nhìn thấy dữ liệu theo ngày.

## Acceptance criteria

* Chạy seed mode không cần Internet.
* API key chỉ lấy từ environment.
* Chạy lại không xóa dữ liệu cũ.
* Không tạo file rỗng nếu API thất bại.
* Có log số địa điểm thành công/thất bại.
* Có timeout và retry hữu hạn.

---

# Phase 4 — Xử lý dữ liệu bằng Spark ETL

## Mục tiêu

Spark đọc raw CSV từ HDFS, làm sạch và tạo feature cho machine learning.

## Task

* Đọc dữ liệu raw từ HDFS.
* Áp dụng schema.
* Xóa duplicate.
* Parse `Timestamp`.
* Cast numeric columns.
* Lọc `Confidence >= 0.9`.
* Loại dữ liệu không hợp lệ.
* Tạo feature thời gian.
* Tính `CongestionRatio`.
* Ghi dữ liệu đã xử lý về HDFS.
* Sinh báo cáo chất lượng dữ liệu.

## Feature cần tạo

```text
Hour
Minute
TimeInMinutes
DayOfWeek
Weekend
CongestionRatio
```

Công thức:

```python
TimeInMinutes = Hour * 60 + Minute
CongestionRatio = CurrentSpeed / FreeFlowSpeed
```

Không chia khi `FreeFlowSpeed <= 0`.

## File cần viết

```text
src/processing/process_spark.py
src/processing/data_quality_report.py
scripts/run_processing.sh
tests/integration/test_spark_processing.py
```

## Đường dẫn output

```text
/traffic_project/processed
```

Nên ghi dạng Parquet:

```text
/traffic_project/processed/date=YYYY-MM-DD/
```

CSV chỉ nên dùng để export hoặc demo, không phải định dạng chính.

## Kết quả cần đạt

Spark job hiển thị:

```text
Raw rows
Duplicate rows removed
Invalid rows
Rows after confidence filter
Processed rows
Output path
```

## Acceptance criteria

* Output có đủ feature bắt buộc.
* Không còn null trong feature và target.
* Không còn `CurrentSpeed < 0`.
* Không còn `FreeFlowSpeed <= 0`.
* `DayOfWeek` nằm trong khoảng 0–6.
* `Weekend` chỉ nhận 0 hoặc 1.
* Dữ liệu được lưu Parquet trên HDFS.

---

# Phase 5 — Phân tích dữ liệu khám phá

## Mục tiêu

Tạo báo cáo thống kê phục vụ thuyết trình và kiểm tra dữ liệu trước khi train.

## Task

* Thống kê tổng số bản ghi.
* Tốc độ trung bình, nhỏ nhất, lớn nhất.
* Phân bố `Confidence`.
* Tốc độ theo giờ.
* Tốc độ theo ngày trong tuần.
* Phân tích giờ cao điểm.
* Phân tích vị trí thường xuyên ùn tắc.
* Thống kê `CongestionRatio`.

## File cần viết

```text
src/processing/data_quality_report.py
src/processing/exploratory_analysis.py
artifacts/reports/
docs/eda_report.md
```

Có thể tạo thêm:

```text
artifacts/reports/speed_by_hour.csv
artifacts/reports/congestion_by_location.csv
artifacts/reports/data_quality.json
```

## Kết quả cần đạt

Báo cáo cho biết:

```text
Giờ có tốc độ thấp nhất
Giờ có tốc độ cao nhất
Các vị trí thường xuyên tắc
Tỷ lệ dữ liệu bị loại
```

## Acceptance criteria

* Báo cáo sinh tự động từ processed data.
* Không dùng số liệu viết cứng.
* Có thể chạy lại khi dữ liệu thay đổi.

---

# Phase 6 — Huấn luyện Spark MLlib GBTRegressor

## Mục tiêu

Huấn luyện model dự đoán `CurrentSpeed`.

## Input features

```text
Latitude
Longitude
TimeInMinutes
DayOfWeek
Weekend
```

Có thể thêm `FreeFlowSpeed`, nhưng phải thống nhất giữa training và prediction.

## Target

```text
CurrentSpeed
```

## Task

* Đọc processed Parquet từ HDFS.
* Chia train/test.
* Dùng `VectorAssembler`.
* Dùng `GBTRegressor`.
* Tạo Spark Pipeline.
* Train model.
* Đánh giá model.
* Lưu model.
* Lưu metadata.
* Lưu metrics JSON.
* Lưu sample prediction.

## File cần viết

```text
src/training/train_gbt.py
src/training/evaluate_model.py
src/training/model_metadata.py
src/training/hyperparameter_tuning.py
scripts/run_training.sh
tests/integration/test_model_prediction.py
```

## Metrics bắt buộc

```text
RMSE
MAE
R²
```

Không gọi R² là “accuracy”.

## Model output

```text
/traffic_project/models/gbt/version=YYYYMMDD_HHMMSS/
```

Metadata:

```json
{
  "model_type": "GBTRegressor",
  "target": "CurrentSpeed",
  "features": [
    "Latitude",
    "Longitude",
    "TimeInMinutes",
    "DayOfWeek",
    "Weekend"
  ],
  "rmse": 0,
  "mae": 0,
  "r2": 0,
  "training_rows": 0,
  "spark_version": "",
  "created_at": ""
}
```

## Kết quả cần đạt

```bash
docker compose run --rm spark-job \
  spark-submit src/training/train_gbt.py
```

hoặc một lệnh tương đương.

## Acceptance criteria

* Train/test split có seed cố định.
* Pipeline bao gồm VectorAssembler và GBT.
* Model load lại được sau khi lưu.
* Prediction không âm; có thể clamp về 0.
* Metrics được lưu thành file JSON.
* Feature order được lưu trong metadata.
* Model và dashboard dùng cùng feature definition.

---

# Phase 7 — Batch prediction và lớp serving

## Mục tiêu

Tách logic dự đoán khỏi giao diện Streamlit.

Dashboard không được tự xây feature theo một cách khác với training.

## Task

* Viết `feature_builder.py`.
* Load model một lần.
* Tạo batch input cho toàn bộ địa điểm.
* Dự đoán tốc độ cho thời gian người dùng chọn.
* Tính trạng thái ùn tắc.
* Ghi prediction ra HDFS hoặc local artifacts.
* Kiểm tra input trước khi predict.

## File cần viết

```text
src/prediction/feature_builder.py
src/prediction/predictor.py
src/prediction/batch_predict.py
scripts/run_prediction.sh
tests/unit/test_feature_builder.py
```

## Interface mong muốn

```python
class TrafficPredictor:
    def predict_locations(
        self,
        locations_df,
        prediction_time
    ):
        ...
```

## Trạng thái giao thông

```text
ratio < 0.4           → Tắc nghẽn nghiêm trọng
0.4 <= ratio < 0.7    → Đông xe
ratio >= 0.7          → Thông thoáng
```

Trong đó:

```text
ratio = PredictedSpeed / FreeFlowSpeed
```

Không mặc định toàn bộ đường đều có `FreeFlowSpeed = 40` nếu có thể lấy từ dữ liệu lịch sử.

## Output

```text
Location/Street
District
Latitude
Longitude
PredictionTime
PredictedSpeed
FreeFlowSpeed
CongestionRatio
TrafficStatus
```

## Kết quả cần đạt

```bash
python -m src.prediction.batch_predict \
  --datetime "2026-07-21 17:30:00"
```

tạo được file prediction.

## Acceptance criteria

* Không duplicate logic feature giữa app và training.
* Batch prediction hoạt động cho nhiều địa điểm.
* Không gọi Spark `collect()` từng dòng.
* Không thay prediction lỗi bằng số random.
* Khi model lỗi phải hiển thị lỗi thật.

---

# Phase 8 — Dashboard Streamlit và Folium

## Mục tiêu

Hiển thị bản đồ giao thông và thông tin dự đoán.

## Task

* Load model qua lớp `TrafficPredictor`.
* Cho chọn ngày và giờ.
* Cho chọn địa điểm.
* Batch predict tất cả địa điểm.
* Vẽ marker.
* Vẽ heatmap.
* Hiển thị speed và traffic status.
* Hiển thị metrics của model.
* Hiển thị trạng thái kết nối Spark/HDFS.
* Cache SparkSession và model.

## File cần viết

```text
src/dashboard/app.py
src/dashboard/map_builder.py
src/dashboard/dashboard_service.py
```

## Giao diện cần có

Sidebar:

```text
Ngày dự đoán
Giờ dự đoán
Chọn địa điểm
Nút Predict
Thông tin model version
```

Khu vực chính:

```text
Bản đồ Folium
Heatmap
Marker xanh/cam/đỏ
Bảng địa điểm
Tốc độ dự đoán
Trạng thái giao thông
```

## Kết quả cần đạt

```bash
streamlit run src/dashboard/app.py
```

hoặc:

```bash
docker compose up streamlit
```

Truy cập:

```text
http://localhost:8501
```

## Acceptance criteria

* Không tạo SparkSession lại sau mỗi click.
* Model chỉ load một lần.
* App không crash khi chưa có model.
* App không dùng số random thay cho prediction.
* Click marker hiển thị đúng địa điểm.
* Heatmap có trọng số giới hạn từ 0 đến 1.
* App dùng đúng `DayOfWeek` như training.

---

# Phase 9 — Orchestration pipeline end-to-end

## Mục tiêu

Chạy toàn bộ project bằng một lệnh.

## Pipeline

```text
Initialize HDFS
→ Upload seed data hoặc crawl API
→ Spark ETL
→ Train model
→ Evaluate model
→ Batch prediction smoke test
→ Start dashboard
```

## File cần viết

```text
scripts/run_pipeline.sh
Makefile
```

## Makefile mong muốn

```makefile
up:
	docker compose up -d

down:
	docker compose down

init:
	bash scripts/init_hdfs.sh

ingest:
	bash scripts/run_ingestion.sh

process:
	bash scripts/run_processing.sh

train:
	bash scripts/run_training.sh

predict:
	bash scripts/run_prediction.sh

dashboard:
	docker compose up -d streamlit

pipeline:
	bash scripts/run_pipeline.sh

test:
	pytest -v

clean:
	bash scripts/clean_project.sh
```

## Lệnh cuối cùng

```bash
cp .env.example .env
make up
make pipeline
make dashboard
```

## Kết quả cần đạt

Sau khi chạy pipeline:

```text
HDFS có raw data
HDFS có processed data
HDFS có model
Có file metrics
Có file sample predictions
Dashboard hoạt động
```

## Acceptance criteria

* Script dừng ngay nếu một phase thất bại.
* Mỗi phase log rõ thời gian bắt đầu và kết thúc.
* Có thể chạy lại pipeline.
* Chạy lại không làm hỏng dữ liệu cũ.
* Không phụ thuộc thao tác thủ công trong container.

---

# Phase 10 — Testing và data quality

## Mục tiêu

Bảo đảm pipeline không chỉ “chạy được” mà còn cho kết quả đúng.

## Unit test

```text
Config loading
API response parsing
Timestamp feature extraction
DayOfWeek conversion
Weekend conversion
Congestion ratio
Input validation
Traffic status mapping
```

## Integration test

```text
Kết nối HDFS
Spark đọc CSV
Spark ghi Parquet
Train model với sample data
Save/load model
Batch prediction
```

## File cần viết

```text
tests/unit/test_config.py
tests/unit/test_tomtom_client.py
tests/unit/test_feature_builder.py
tests/unit/test_data_validation.py
tests/integration/test_hdfs_connection.py
tests/integration/test_spark_processing.py
tests/integration/test_model_prediction.py
```

## Kết quả cần đạt

```bash
pytest -v
```

Tất cả test pass.

## Acceptance criteria

* Có fixture dữ liệu nhỏ.
* Test không gọi TomTom API thật.
* HTTP được mock.
* Test model dùng dataset nhỏ để chạy nhanh.
* Có test bảo đảm Spark và Python dùng cùng `DayOfWeek`.

---

# Phase 11 — Tài liệu, báo cáo và demo

## Mục tiêu

Có đủ tài liệu để nộp và thuyết trình.

## File cần viết

```text
README.md
docs/architecture.md
docs/data_dictionary.md
docs/api_ingestion.md
docs/model_report.md
docs/demo_guide.md
```

## `README.md` phải có

* Tổng quan project.
* Architecture diagram.
* Yêu cầu hệ thống.
* Cách cấu hình `.env`.
* Cách chạy Docker.
* Cách chạy từng phase.
* Cách chạy toàn pipeline.
* Cách mở Streamlit.
* Cách xử lý lỗi thường gặp.

## `architecture.md`

Mô tả:

```text
TomTom API / Seed Data
          ↓
     Ingestion
          ↓
        HDFS Raw
          ↓
       Spark ETL
          ↓
    HDFS Processed
          ↓
 Spark MLlib Training
          ↓
       GBT Model
          ↓
   Batch Prediction
          ↓
 Streamlit + Folium
```

## `model_report.md`

Phải bao gồm:

```text
Số lượng mẫu
Feature sử dụng
Train/test ratio
GBT parameters
RMSE
MAE
R²
Ví dụ prediction
Hạn chế của model
```

## `demo_guide.md`

Kịch bản demo:

```text
1. Mở HDFS UI.
2. Cho xem raw CSV.
3. Chạy Spark ETL.
4. Cho xem processed Parquet.
5. Train GBT.
6. Cho xem RMSE, MAE, R².
7. Mở Streamlit.
8. Chọn giờ cao điểm.
9. Cho xem marker và heatmap.
10. Giải thích ưu điểm và hạn chế.
```

## Kết quả cần đạt

Người khác clone project và chạy được chỉ bằng README.

---

# Các yêu cầu kỹ thuật Gemini bắt buộc phải tuân thủ

Đưa thêm đoạn này vào cuối prompt:

```text
Yêu cầu bắt buộc:

1. Không hard-code TomTom API key.
2. Không lưu API key vào Git.
3. Không dùng random prediction khi model lỗi.
4. Không để logic feature engineering bị lặp lại giữa training và dashboard.
5. Phải thống nhất DayOfWeek:
   Monday=0 và Sunday=6.
6. Phải dùng Spark MLlib GBTRegressor cho model chính.
7. HDFS là nơi lưu raw và processed data.
8. Dữ liệu processed ưu tiên Parquet.
9. Mọi đường dẫn phải lấy từ config.
10. Dùng logging thay cho print ở code production.
11. Tất cả script phải có hàm main().
12. File Python phải chạy được bằng python -m.
13. Phải xử lý empty dataframe.
14. Phải validate schema trước khi xử lý.
15. Không được collect toàn bộ dữ liệu lớn về driver.
16. Dashboard chỉ collect kết quả của số lượng điểm địa lý nhỏ.
17. Model metadata phải chứa feature list và metrics.
18. Phải có seed mode để chạy mà không cần TomTom API.
19. Phải có unit test và integration test.
20. Phải có một lệnh chạy toàn pipeline.
```

---

# Cách yêu cầu Gemini làm theo từng bước

Không nên yêu cầu Gemini viết toàn bộ project trong một lần. Gửi lần lượt:

## Prompt đầu tiên

```text
Hãy thực hiện Phase 0 của đặc tả.

Yêu cầu:
- Tạo cấu trúc project.
- Viết .env.example.
- Viết requirements.txt.
- Viết config/application.yaml.
- Viết src/common/config.py.
- Viết src/common/logging_utils.py.
- Viết src/common/schemas.py.
- Viết README ban đầu.

Trả về:
1. Cây thư mục.
2. Nội dung đầy đủ từng file.
3. Lệnh kiểm tra.
4. Không làm các phase tiếp theo.
```

## Sau khi Phase 0 chạy được

```text
Phase 0 đã hoàn thành.

Hãy thực hiện Phase 1 theo đặc tả.
Viết đầy đủ:
- docker-compose.yml
- Dockerfile
- spark-defaults.conf
- wait_for_hdfs.sh
- init_hdfs.sh

Yêu cầu:
- HDFS NameNode và DataNode.
- Spark Master và Worker.
- Persistent volumes.
- Health checks.
- Không dùng latest tag.
- Cho tôi lệnh kiểm tra từng service.
- Không làm Phase 2.
```

Tiếp tục cùng cách đó cho từng phase. Cách này giúp dễ kiểm tra lỗi và tránh Gemini thay đổi những phần đã chạy ổn.
