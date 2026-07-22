// ==============================================================================
// TomTom Flow API HTTP Client (internal/tomtom/client.go)
// Connection-Pooled HTTP Client, Context Timeout & API Key Masking
// ==============================================================================

package tomtom

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"go-traffic/internal/config"
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

// Client quản lý HTTP Client có Connection Pool tối ưu hiệu năng và tài nguyên bộ nhớ
type Client struct {
	apiKey     string
	httpClient *http.Client
}

// NewClient tạo instance TomTom HTTP Client với Connection Pool tùy chỉnh
func NewClient(apiKey string) *Client {
	transport := &http.Transport{
		MaxIdleConns:        100,
		MaxIdleConnsPerHost: 20,
		IdleConnTimeout:     90 * time.Second,
	}

	httpClient := &http.Client{
		Transport: transport,
		Timeout:   10 * time.Second,
	}

	return &Client{
		apiKey:     apiKey,
		httpClient: httpClient,
	}
}

// FetchFlowData thực hiện gọi TomTom Flow Segment Data API với Context Timeout
func (c *Client) FetchFlowData(ctx context.Context, lat, lon float64) (*TomTomFlowResponse, int, error) {
	if c.apiKey == "" {
		return nil, 401, fmt.Errorf("TomTom API Key trống (Masked Key: %s)", config.MaskAPIKey(c.apiKey))
	}

	url := fmt.Sprintf(
		"https://api.tomtom.com/traffic/services/4/flowSegmentData/relative-delay/10/json?point=%.6f,%.6f&key=%s",
		lat, lon, c.apiKey,
	)

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, 0, err
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, 0, fmt.Errorf("lỗi kết nối HTTP tới TomTom API: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, resp.StatusCode, fmt.Errorf("TomTom API trả về HTTP Status %d", resp.StatusCode)
	}

	var flowData TomTomFlowResponse
	if err := json.NewDecoder(resp.Body).Decode(&flowData); err != nil {
		return nil, resp.StatusCode, fmt.Errorf("lỗi parse JSON phản hồi từ TomTom: %w", err)
	}

	return &flowData, resp.StatusCode, nil
}
