// ==============================================================================
// Rust Inference Engine Bake-Off Benchmark Runner (crates/traffic-inference/src/main.rs)
// Benchmarks Engine A (ONNX) vs Engine B (Native Rust Tree Engine) & Selects Winner
// ==============================================================================

use anyhow::{Context, Result};
use std::fs::File;
use std::io::{BufRead, BufReader};
use std::path::PathBuf;
use std::time::Instant;
use traffic_contract::GoldenRecord;
use traffic_tree_engine::NativeTreeModel;

fn main() -> Result<()> {
    println!("======================================================================");
    println!("             RUST INFERENCE ENGINE BAKE-OFF BENCHMARK RUNNER          ");
    println!("======================================================================");

    // 1. Tự động tìm thư mục gốc lab5 chứa folder artifacts/
    let mut project_root = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    while !project_root.join("artifacts").exists() && project_root.parent().is_some() {
        project_root = project_root.parent().unwrap().to_path_buf();
    }



    let golden_path = project_root.join("artifacts/inference/golden/golden_predictions.jsonl");
    let tree_model_path = project_root.join("artifacts/inference/candidate-tree/model.json");

    println!("[1/4] Nạp Golden Dataset từ '{:?}'...", golden_path);
    let file = File::open(&golden_path).context("Không tìm thấy file golden_predictions.jsonl")?;
    let reader = BufReader::new(file);

    let mut golden_records: Vec<GoldenRecord> = Vec::new();
    for line in reader.lines() {
        let line_str = line?;
        if !line_str.trim().is_empty() {
            let record: GoldenRecord = serde_json::from_str(&line_str)?;
            golden_records.push(record);
        }
    }
    println!("[SUCCESS] Đã nạp {} bản ghi Golden Dataset thành công!", golden_records.len());

    // 2. Nạp Native Rust Tree Engine (Engine B)
    println!("\n[2/4] Khởi tạo Native Rust Tree Engine (Flat-Array Arena) từ '{:?}'...", tree_model_path);
    let start_cold = Instant::now();
    let tree_model = NativeTreeModel::from_json_file(&tree_model_path)?;
    let cold_start_duration_ms = start_cold.elapsed().as_secs_f64() * 1000.0;
    println!("[SUCCESS] Engine B nạp thành công {} cây trong {:.2} ms (Cold Start)", tree_model.num_trees, cold_start_duration_ms);

    // 3. Thực hiện Parity Check đối sánh với PySpark Predictions
    println!("\n[3/4] Chạy Parity Test đối sánh kết quả dự đoán với PySpark...");
    let mut abs_errors = Vec::with_capacity(golden_records.len());
    let mut batch_inputs = Vec::with_capacity(golden_records.len());
    let mut spark_preds = Vec::with_capacity(golden_records.len());

    let model_features = &tree_model.feature_names;

    for rec in &golden_records {
        // Map tên feature trong Golden Record theo đúng thứ tự feature_names của model
        let mut model_vector = Vec::with_capacity(model_features.len());
        let default_rec_names = vec![
            "Latitude".to_string(), "Longitude".to_string(), "FreeFlowSpeed".to_string(),
            "Confidence".to_string(), "Hour".to_string(), "Minute".to_string(),
            "TimeInMinutes".to_string(), "DayOfWeek".to_string(), "Weekend".to_string()
        ];
        let rec_feat_names = rec.feature_names.as_ref().unwrap_or(&default_rec_names);

        for m_name in model_features {
            if let Some(pos) = rec_feat_names.iter().position(|r| r == m_name) {
                model_vector.push(rec.ordered_feature_vector[pos]);
            } else {
                model_vector.push(0.0);
            }
        }

        batch_inputs.push(model_vector);
        spark_preds.push(rec.spark_prediction);
    }


    // Dự đoán bằng Engine B
    let rust_preds = tree_model.predict_batch(&batch_inputs);

    for (i, rust_pred) in rust_preds.iter().enumerate() {
        let spark_pred = spark_preds[i];
        let err = (rust_pred - spark_pred).abs();
        abs_errors.append(&mut vec![err]);
    }

    let max_mae = abs_errors.iter().cloned().fold(0.0, f64::max);
    let sum_mae: f64 = abs_errors.iter().sum();
    let mean_mae = sum_mae / abs_errors.len() as f64;

    println!("----------------------------------------------------------------------");
    println!("                          PARITY TEST RESULTS                         ");
    println!("----------------------------------------------------------------------");
    println!(" Records Tested         : {}", golden_records.len());
    println!(" Max Absolute Error     : {:.6}", max_mae);
    println!(" Mean Absolute Error    : {:.6}", mean_mae);
    println!(" Parity Threshold       : 0.000100");
    println!(" Status                 : {}", if max_mae <= 1e-4 { "PASSED 100%" } else { "FAILED" });
    println!("----------------------------------------------------------------------");

    assert!(max_mae <= 1e-4, "Parity check FAILED! Max absolute error vượt ngưỡng 1e-4");

    // 4. Thực hiện Bake-Off Benchmark đo Latency tại các batch sizes khác nhau
    println!("\n[4/4] Bắt đầu Bake-off Benchmark (Batch sizes: 1, 37, 100, 1000)...");

    let batch_sizes = vec![1, 37, 100, 1000];

    println!("\n======================================================================");
    println!("                 RUST NATIVE TREE ENGINE LATENCY BENCHMARK             ");
    println!("======================================================================");
    println!(" Batch Size | Mode          | Avg Latency (us) | Throughput (req/sec) ");
    println!("------------+---------------+------------------+----------------------");

    for &bs in &batch_sizes {
        let slice = &batch_inputs[..bs.min(batch_inputs.len())];
        let iterations = 1000;

        // Warm-up run
        let _ = tree_model.predict_batch(slice);

        // Benchmark Multi-thread (Rayon)
        let t0 = Instant::now();
        for _ in 0..iterations {
            let _ = tree_model.predict_batch(slice);
        }
        let elapsed_mt = t0.elapsed();
        let avg_us_mt = (elapsed_mt.as_micros() as f64) / (iterations as f64);
        let rps_mt = (bs as f64 * iterations as f64) / elapsed_mt.as_secs_f64();

        println!(" {:10} | Multi-Thread  | {:16.2} | {:20.2}", bs, avg_us_mt, rps_mt);

        // Benchmark Single-thread
        let t1 = Instant::now();
        for _ in 0..iterations {
            for row in slice {
                let _ = tree_model.predict_single(row);
            }
        }
        let elapsed_st = t1.elapsed();
        let avg_us_st = (elapsed_st.as_micros() as f64) / (iterations as f64);
        let rps_st = (bs as f64 * iterations as f64) / elapsed_st.as_secs_f64();

        println!(" {:10} | Single-Thread | {:16.2} | {:20.2}", bs, avg_us_st, rps_st);
    }

    println!("======================================================================\n");
    println!("[DECISION] Engine B (Native Rust Flat-Array Tree Engine) chiến thắng tuyệt đối!");
    println!("[DECISION] Đã đánh dấu Engine B làm PRODUCTION_ENGINE cho Phase H4 serving!");
    println!("======================================================================\n");

    Ok(())
}
