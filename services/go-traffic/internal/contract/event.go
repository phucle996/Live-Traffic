// ==============================================================================
// Traffic Event Contract Specification (internal/contract/event.go)
// Single Source of Truth Struct & Deterministic EventID Hash Generator (SHA-256)
// ==============================================================================

package contract

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"time"
)

// TrafficEvent đại diện cho 1 sự kiện giao thông chuẩn được đẩy vào Kafka topic
type TrafficEvent struct {
	EventID        string  `json:"event_id"`
	EventTime      string  `json:"event_time"`
	IngestedAt     string  `json:"ingested_at"`
	LocationID     string  `json:"location_id"`
	LocationName   string  `json:"location_name"`
	District       string  `json:"district"`
	Province       string  `json:"province"`        // Tỉnh/Thành phố (VD: TP.HCM, Hà Nội, Đà Nẵng)
	Region         string  `json:"region"`          // Vùng miền (VD: Mien Nam, Mien Trung, Mien Bac, Cao Toc)
	RoadClass      string  `json:"road_class"`      // Loại đường (VD: Cao tốc, Quốc lộ, Trục đô thị)
	Direction      string  `json:"direction"`       // Hướng di chuyển (VD: Hướng trung tâm, Hướng ngoại thành)
	Latitude       float64 `json:"latitude"`
	Longitude      float64 `json:"longitude"`
	CurrentSpeed   float64 `json:"current_speed"`
	FreeFlowSpeed  float64 `json:"free_flow_speed"`
	DensityPercent float64 `json:"density_percent"` // Mật độ lưu thông (%)
	DelayMinutes   float64 `json:"delay_minutes"`   // Thời gian trễ dự kiến (+X phút)
	Confidence     float64 `json:"confidence"`
	Source         string  `json:"source"`
	BatchID        string  `json:"batch_id"`
	SchemaVersion  string  `json:"schema_version"`
}

// GenerateDeterministicEventID sinh UUID/SHA-256 duy nhất dựa trên (locationID + timestamp) để chống trùng lặp dữ liệu trên Kafka
func GenerateDeterministicEventID(locationID string, timestamp string) string {
	raw := fmt.Sprintf("%s:%s", locationID, timestamp)
	hash := sha256.Sum256([]byte(raw))
	return hex.EncodeToString(hash[:16]) // Lấy 32 ký tự hex làm EventID
}

// NewTrafficEvent tạo sự kiện giao thông mới với EventID chuẩn hóa
func NewTrafficEvent(
	locID, locName, district string,
	lat, lon, currentSpeed, freeFlowSpeed, confidence float64,
	eventTimeStr, source, batchID string,
) TrafficEvent {
	return NewTrafficEventWithRegion(
		locID, locName, district, "TP.HCM", "Mien Nam", "Trục chính", "Hai chiều",
		lat, lon, currentSpeed, freeFlowSpeed, 50.0, 0.0, confidence,
		eventTimeStr, source, batchID,
	)
}

// NewTrafficEventWithRegion khởi tạo TrafficEvent mở rộng với đầy đủ thông số vùng miền và độ chi tiết cao
func NewTrafficEventWithRegion(
	locID, locName, district, province, region, roadClass, direction string,
	lat, lon, currentSpeed, freeFlowSpeed, densityPercent, delayMinutes, confidence float64,
	eventTimeStr, source, batchID string,
) TrafficEvent {
	// 1. Kiểm tra và gán timestamp mặc định nếu trống
	if eventTimeStr == "" {
		eventTimeStr = time.Now().Format(time.RFC3339)
	}

	// 2. Sinh EventID chống trùng lặp dữ liệu trên Kafka Broker
	eventID := GenerateDeterministicEventID(locID, eventTimeStr)

	// 3. Khởi tạo đối tượng TrafficEvent chuẩn hóa schema
	return TrafficEvent{
		EventID:        eventID,
		EventTime:      eventTimeStr,
		IngestedAt:     time.Now().Format(time.RFC3339),
		LocationID:     locID,
		LocationName:   locName,
		District:       district,
		Province:       province,
		Region:         region,
		RoadClass:      roadClass,
		Direction:      direction,
		Latitude:       lat,
		Longitude:      lon,
		CurrentSpeed:   currentSpeed,
		FreeFlowSpeed:  freeFlowSpeed,
		DensityPercent: densityPercent,
		DelayMinutes:   delayMinutes,
		Confidence:     confidence,
		Source:         source,
		BatchID:        batchID,
		SchemaVersion:  "v2.0.0",
	}
}

