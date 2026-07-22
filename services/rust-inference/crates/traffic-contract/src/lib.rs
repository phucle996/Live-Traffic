// ==============================================================================
// Traffic Contract Shared Types Library (crates/traffic-contract/src/lib.rs)
// Defines Single Source of Truth Rust Structs & Serde Serialization Standards
// ==============================================================================

use serde::{Deserialize, Serialize};

/// Struct đại diện cho 1 sự kiện giao thông (Traffic Event)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TrafficEvent {
    pub event_id: String,
    pub event_time: String,
    pub ingested_at: String,
    pub location_id: String,
    pub location_name: String,
    pub district: String,
    pub latitude: f64,
    pub longitude: f64,
    pub current_speed: f64,
    pub free_flow_speed: f64,
    pub confidence: f64,
    pub source: String,
    pub batch_id: String,
    pub schema_version: String,
}

/// Struct đại diện cho yêu cầu dự đoán HTTP REST API (Prediction Request)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PredictionRequest {
    pub street_name: String,
    pub hour: u32,
    pub is_weekend: bool,
}

/// Struct đại diện cho kết quả trả về của HTTP REST API (Prediction Response)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PredictionResponse {
    pub street_name: String,
    pub hour: u32,
    pub is_weekend: bool,
    pub predicted_speed_kmh: f64,
    pub congestion_level: String,
    pub model_version: String,
    pub data_source: String,
    pub prediction_time: String,
}

/// Struct đại diện cho 1 bản ghi trong Golden Parity Dataset (JSONL)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GoldenRecord {
    pub sample_id: u64,
    pub input_business_fields: InputBusinessFields,
    pub ordered_feature_vector: Vec<f64>,
    pub feature_names: Option<Vec<String>>,
    pub spark_prediction: f64,
    pub model_checksum: String,
}

/// Thông tin nghiệp vụ trong Golden Record
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InputBusinessFields {
    pub street_name: String,
    pub district: String,
    pub prediction_time: String,
}

/// Struct đại diện cho Feature Contract SOT JSON (`contracts/feature_contract.json`)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FeatureContractSpec {
    pub contract_name: String,
    pub version: String,
    pub feature_order: Vec<String>,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_traffic_event_serialization() {
        // Kiểm tra tính hợp lệ của việc Serialize / Deserialize TrafficEvent
        let event = TrafficEvent {
            event_id: "test-123".to_string(),
            event_time: "2026-07-21T20:30:00Z".to_string(),
            ingested_at: "2026-07-21T20:30:01Z".to_string(),
            location_id: "loc-1".to_string(),
            location_name: "Nam Kỳ Khởi Nghĩa".to_string(),
            district: "Quận 3".to_string(),
            latitude: 10.778,
            longitude: 106.695,
            current_speed: 25.0,
            free_flow_speed: 45.0,
            confidence: 0.95,
            source: "tomtom_live".to_string(),
            batch_id: "batch-1".to_string(),
            schema_version: "v1.0.0".to_string(),
        };

        let json = serde_json::to_string(&event).unwrap();
        assert!(json.contains("Nam Kỳ Khởi Nghĩa"));

        let deserialized: TrafficEvent = serde_json::from_str(&json).unwrap();
        assert_eq!(deserialized.current_speed, 25.0);
    }
}
