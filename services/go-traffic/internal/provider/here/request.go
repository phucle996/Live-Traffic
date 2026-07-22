// ==============================================================================
// HERE Request Builder Specification (internal/provider/here/request.go)
// Phase HERE-2 — Safe Request Construction & API Key Redaction
// ==============================================================================

package here

import (
	"fmt"

	"go-traffic/internal/config"
	"go-traffic/internal/provider"
)

// BuildFlowURL tạo URL gọi endpoint v7 /flow với QueryArea và API key
func BuildFlowURL(baseURL string, apiKey string, area provider.QueryArea) (string, string, error) {
	if apiKey == "" {
		return "", "", fmt.Errorf("API key bị trống")
	}

	if baseURL == "" {
		baseURL = "https://data.traffic.hereapi.com/traffic/6.3/flow.json"
	}

	filter := area.ToHEREFilter()
	if filter == "" {
		return "", "", fmt.Errorf("QueryArea không hợp lệ hoặc rỗng")
	}

	// URL hoàn chỉnh với API Key thực tế (dùng khi gửi HTTP Request)
	fullURL := fmt.Sprintf("%s?%s&apiKey=%s&units=metric", baseURL, filter, apiKey)

	// URL che giấu API Key (dùng cho Logging & Tracing)
	maskedURL := fmt.Sprintf("%s?%s&apiKey=%s&units=metric", baseURL, filter, config.MaskAPIKey(apiKey))

	return fullURL, maskedURL, nil
}
