// ==============================================================================
// HERE Response Schema Specification (internal/provider/here/response.go)
// Phase HERE-2 — Mapping JSON Struct cho HERE Traffic API v7 Flow Response
// ==============================================================================

package here

// FlowResponse đại diện cho JSON payload gốc trả về từ HERE Traffic API v7
type FlowResponse struct {
	Results []FlowResult `json:"results"`
}

// FlowResult chứa thông tin location và tình trạng giao thông thời gian thực
type FlowResult struct {
	Location    FlowLocation `json:"location"`
	CurrentFlow FlowMetrics  `json:"currentFlow"`
}

// FlowLocation chứa thông tin vị trí, chiều dài và hình học đoạn đường (shape geometry)
type FlowLocation struct {
	Description string    `json:"description,omitempty"`
	Length      float64   `json:"length,omitempty"` // Chiều dài đoạn đường tính bằng mét
	Shape       FlowShape `json:"shape,omitempty"`
}

// FlowShape chứa danh sách liên kết hình học các điểm tọa độ
type FlowShape struct {
	Links []FlowLink `json:"links,omitempty"`
}

// FlowLink chứa danh sách các điểm tọa độ [lat, lon]
type FlowLink struct {
	Points []Point `json:"points,omitempty"`
}

// Point đại diện cho 1 điểm tọa độ địa lý trong GeoJSON
type Point struct {
	Lat float64 `json:"lat"`
	Lng float64 `json:"lng"`
}

// FlowMetrics chứa các chỉ số giao thông quan trọng (vận tốc, chỉ số ùn tắc jamFactor, độ tin cậy)
type FlowMetrics struct {
	Speed          float64 `json:"speed"`          // Vận tốc thực tế hiện tại (km/h)
	FreeFlow       float64 `json:"freeFlow"`       // Vận tốc tự do lý tưởng (km/h)
	JamFactor      float64 `json:"jamFactor"`      // Chỉ số ùn tắc từ 0.0 (thông thoáng) đến 10.0 (tắc nghẽn hoàn toàn)
	Confidence     float64 `json:"confidence"`     // Độ tin cậy dữ liệu từ 0.0 đến 1.0
	RoadClosed     bool    `json:"roadClosed"`     // Cờ báo đoạn đường đang bị phong tỏa/đóng
	Traversability string  `json:"traversability"` // "open" | "closed"
}
