// ==============================================================================
// Provider Types (internal/provider/types.go)
// Phase HERE-1 — QueryArea implementations, FlowObservation, TrafficIncident
// Tất cả provider normalize output về các struct này trước khi trả ra ngoài.
// ==============================================================================

package provider

import "fmt"

// ─────────────────────────────────────────────
// QueryArea implementations
// ─────────────────────────────────────────────

// BoundingBox định nghĩa vùng hình chữ nhật theo tọa độ địa lý.
// Dùng khi truy vấn toàn bộ khu vực (HERE bbox query).
type BoundingBox struct {
	South float64 // vĩ độ min
	West  float64 // kinh độ min
	North float64 // vĩ độ max
	East  float64 // kinh độ max
}

// ToHEREFilter trả HERE Traffic API v7 bbox filter string.
// Format: bbox={west},{south},{east},{north}
func (b BoundingBox) ToHEREFilter() string {
	return fmt.Sprintf("bbox=%f,%f,%f,%f", b.West, b.South, b.East, b.North)
}

// ToTomTomPoint trả điểm trung tâm của bbox dùng cho TomTom Flow API.
func (b BoundingBox) ToTomTomPoint() (lat, lon float64) {
	return (b.South + b.North) / 2.0, (b.West + b.East) / 2.0
}

// Circle định nghĩa vùng hình tròn theo tâm và bán kính.
type Circle struct {
	Latitude  float64 // vĩ độ tâm
	Longitude float64 // kinh độ tâm
	RadiusM   int     // bán kính tính bằng mét
}

// ToHEREFilter trả HERE Traffic API v7 circle filter string.
// Format: circle={lat},{lon};r={radius}
func (c Circle) ToHEREFilter() string {
	return fmt.Sprintf("circle=%f,%f;r=%d", c.Latitude, c.Longitude, c.RadiusM)
}

// ToTomTomPoint trả tâm circle — đây là điểm duy nhất TomTom Point API nhận.
func (c Circle) ToTomTomPoint() (lat, lon float64) {
	return c.Latitude, c.Longitude
}

// Coordinate là 1 cặp tọa độ địa lý.
type Coordinate struct {
	Latitude  float64
	Longitude float64
}

// Corridor định nghĩa vùng hành lang dọc theo tuyến đường.
type Corridor struct {
	Points  []Coordinate // danh sách điểm tạo thành tuyến đường
	RadiusM int          // bán kính hành lang tính bằng mét
}

// ToHEREFilter trả HERE Traffic API v7 corridor filter.
// Format: corridor={lat1},{lon1},{lat2},{lon2},...;r={radius}
func (c Corridor) ToHEREFilter() string {
	if len(c.Points) == 0 {
		return ""
	}
	coords := ""
	for i, p := range c.Points {
		if i > 0 {
			coords += ","
		}
		coords += fmt.Sprintf("%f,%f", p.Latitude, p.Longitude)
	}
	return fmt.Sprintf("corridor=%s;r=%d", coords, c.RadiusM)
}

// ToTomTomPoint trả điểm đầu tiên của corridor cho TomTom Point API.
func (c Corridor) ToTomTomPoint() (lat, lon float64) {
	if len(c.Points) == 0 {
		return 0, 0
	}
	mid := c.Points[len(c.Points)/2]
	return mid.Latitude, mid.Longitude
}

// ─────────────────────────────────────────────
// Provider output types — chuẩn hóa nội bộ
// ─────────────────────────────────────────────

// FlowObservation là quan sát tốc độ giao thông từ bất kỳ provider nào,
// đã được normalize về contract nội bộ. Không chứa field provider-specific.
type FlowObservation struct {
	// Metadata provider — bắt buộc ghi đầy đủ để traceback
	Provider              string  `json:"provider"`               // "here" | "tomtom" | "offline"
	ProviderRequestID     string  `json:"provider_request_id"`    // request ID từ response header
	ProviderSegmentID     string  `json:"provider_segment_id"`    // segment/link ID của provider
	ProviderObservedAt    string  `json:"provider_observed_at"`   // timestamp theo provider
	ProviderSchemaVersion string  `json:"provider_schema_version"` // phiên bản schema provider

	// Vị trí đo
	Latitude  float64 `json:"latitude"`
	Longitude float64 `json:"longitude"`

	// Dữ liệu giao thông đã normalize
	CurrentSpeedKPH       float64 `json:"current_speed_kph"`
	FreeFlowSpeedKPH      float64 `json:"free_flow_speed_kph"`
	JamFactor             float64 `json:"jam_factor"`      // 0–10, -1 nếu provider không cung cấp
	Confidence            float64 `json:"confidence"`      // 0–1
	RoadClosed            bool    `json:"road_closed"`
	TravelTimeSeconds     float64 `json:"travel_time_seconds"`
	FreeFlowTravelSeconds float64 `json:"free_flow_travel_time_seconds"`

	// Internal matching — điền ở bước sau (HERE-4)
	SegmentID    string  `json:"segment_id,omitempty"`    // internal road catalog ID
	MatchScore   float64 `json:"match_score,omitempty"`   // 0–1
	FallbackUsed bool    `json:"fallback_used"`
	FallbackReason string `json:"fallback_reason,omitempty"`
}

// TrafficIncident là sự cố giao thông từ bất kỳ provider nào, đã normalize.
type TrafficIncident struct {
	Provider          string  `json:"provider"`
	ProviderRequestID string  `json:"provider_request_id"`
	ProviderIncidentID string `json:"provider_incident_id"`
	IncidentType      string  `json:"incident_type"` // "accident" | "construction" | "closure" | ...
	Severity          int     `json:"severity"`      // 0–4
	Latitude          float64 `json:"latitude"`
	Longitude         float64 `json:"longitude"`
	Description       string  `json:"description"`
	StartAt           string  `json:"start_at"`
	EndAt             string  `json:"end_at,omitempty"`
}
