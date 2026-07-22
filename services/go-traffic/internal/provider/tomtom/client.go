// ==============================================================================
// TomTom Provider Implementation (internal/provider/tomtom/client.go)
// Phase HERE-1 — Di chuyển và bọc TomTom Client để tuân thủ TrafficProvider interface
// ==============================================================================

package tomtom

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"go-traffic/internal/config"
	"go-traffic/internal/provider"
)

// TomTomFlowResponse đại diện cho cấu trúc JSON phản hồi từ TomTom Traffic Flow API
type TomTomFlowResponse struct {
	FlowSegmentData struct {
		CurrentSpeed   float64 `json:"currentSpeed"`
		FreeFlowSpeed  float64 `json:"freeFlowSpeed"`
		Confidence     float64 `json:"confidence"`
		CurrentTravel  float64 `json:"currentTravelTime"`
		FreeFlowTravel float64 `json:"freeFlowTravelTime"`
	} `json:"flowSegmentData"`
}

// Provider quản lý kết nối HTTP và implement TrafficProvider interface cho TomTom
type Provider struct {
	apiKey     string
	httpClient *http.Client
}

// NewProvider khởi tạo TomTom Provider với HTTP Client connection pool
func NewProvider(apiKey string) *Provider {
	// Cấu hình Connection Pool cho HTTP Transport
	transport := &http.Transport{
		MaxIdleConns:        100,
		MaxIdleConnsPerHost: 20,
		IdleConnTimeout:     90 * time.Second,
	}

	httpClient := &http.Client{
		Transport: transport,
		Timeout:   10 * time.Second,
	}

	return &Provider{
		apiKey:     apiKey,
		httpClient: httpClient,
	}
}

// Name trả về định danh của provider
func (p *Provider) Name() string {
	return "tomtom"
}

// HealthCheck kiểm tra sự sẵn sàng của API key
func (p *Provider) HealthCheck(ctx context.Context) error {
	if p.apiKey == "" {
		return fmt.Errorf("TomTom API Key bị trống (Masked Key: %s)", config.MaskAPIKey(p.apiKey))
	}
	return nil
}

// FetchFlow thu thập dữ liệu flow giao thông và normalize về provider.FlowObservation
func (p *Provider) FetchFlow(ctx context.Context, area provider.QueryArea) ([]provider.FlowObservation, error) {
	if p.apiKey == "" {
		return nil, fmt.Errorf("TomTom API Key trống")
	}

	// Tách tọa độ điểm từ QueryArea
	lat, lon := area.ToTomTomPoint()

	url := fmt.Sprintf(
		"https://api.tomtom.com/traffic/services/4/flowSegmentData/relative-delay/10/json?point=%.6f,%.6f&key=%s",
		lat, lon, p.apiKey,
	)

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, fmt.Errorf("lỗi khởi tạo request TomTom: %w", err)
	}

	resp, err := p.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("lỗi kết nối HTTP tới TomTom API: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("TomTom API trả về HTTP status %d", resp.StatusCode)
	}

	var flowData TomTomFlowResponse
	if err := json.NewDecoder(resp.Body).Decode(&flowData); err != nil {
		return nil, fmt.Errorf("lỗi decode JSON từ TomTom: %w", err)
	}

	// Trích xuất request ID nếu có từ header
	reqID := resp.Header.Get("Tracking-ID")
	if reqID == "" {
		reqID = resp.Header.Get("X-Request-ID")
	}

	// Biến đổi phản hồi thành FlowObservation đã chuẩn hóa
	obs := provider.FlowObservation{
		Provider:              p.Name(),
		ProviderRequestID:     reqID,
		ProviderSegmentID:     fmt.Sprintf("tomtom_pt_%.4f_%.4f", lat, lon),
		ProviderObservedAt:    time.Now().UTC().Format(time.RFC3339),
		ProviderSchemaVersion: "v4",
		Latitude:              lat,
		Longitude:             lon,
		CurrentSpeedKPH:       flowData.FlowSegmentData.CurrentSpeed,
		FreeFlowSpeedKPH:      flowData.FlowSegmentData.FreeFlowSpeed,
		JamFactor:             -1, // TomTom Point API không trả jam factor chuẩn 0-10
		Confidence:            flowData.FlowSegmentData.Confidence,
		RoadClosed:            false,
		TravelTimeSeconds:     flowData.FlowSegmentData.CurrentTravel,
		FreeFlowTravelSeconds: flowData.FlowSegmentData.FreeFlowTravel,
	}

	return []provider.FlowObservation{obs}, nil
}

// FetchIncidents trả danh sách sự cố (TomTom Flow Segment API không hỗ trợ trực tiếp incidents)
func (p *Provider) FetchIncidents(ctx context.Context, area provider.QueryArea) ([]provider.TrafficIncident, error) {
	// Trả về slice rỗng vì Flow Segment API không kèm dữ liệu incident
	return []provider.TrafficIncident{}, nil
}
