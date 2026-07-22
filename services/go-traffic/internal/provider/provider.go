// ==============================================================================
// Traffic Provider Interface (internal/provider/provider.go)
// Phase HERE-1 — Provider Abstraction Layer
// Định nghĩa TrafficProvider interface và các type vùng địa lý truy vấn.
// Mọi provider (TomTom, HERE, Offline) phải implement interface này.
// Business logic KHÔNG được kiểm tra provider name trực tiếp (if provider == "here").
// ==============================================================================

package provider

import "context"

// TrafficProvider là interface chung cho mọi traffic data provider.
// Mỗi provider (TomTom, HERE, Offline) phải implement đầy đủ interface này.
type TrafficProvider interface {
	// Name trả về tên định danh của provider (dùng cho log, metric, không dùng cho if/switch).
	Name() string

	// HealthCheck kiểm tra kết nối tới provider.
	// Trả lỗi nếu provider không sẵn sàng.
	HealthCheck(ctx context.Context) error

	// FetchFlow lấy dữ liệu flow giao thông cho 1 vùng địa lý.
	// Trả về danh sách FlowObservation đã normalize về contract nội bộ.
	FetchFlow(ctx context.Context, area QueryArea) ([]FlowObservation, error)

	// FetchIncidents lấy danh sách sự cố giao thông trong vùng.
	// Trả về danh sách TrafficIncident đã normalize.
	FetchIncidents(ctx context.Context, area QueryArea) ([]TrafficIncident, error)
}

// QueryArea là interface định nghĩa vùng địa lý truy vấn.
// Mỗi loại vùng (BoundingBox, Circle, Corridor) tự biết cách
// serialize thành query string cho từng provider.
type QueryArea interface {
	// ToHEREFilter trả về chuỗi filter phù hợp với HERE Traffic API v7.
	ToHEREFilter() string

	// ToTomTomPoint trả về tọa độ trung tâm dùng cho TomTom Flow Segment API.
	// TomTom API cũ dùng điểm đơn thay vì bbox.
	ToTomTomPoint() (lat, lon float64)
}
