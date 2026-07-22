// ==============================================================================
// HERE Provider Errors Specification (internal/provider/here/errors.go)
// Phase HERE-2 — Custom Errors & Retryability Checks cho HERE Traffic API v7
// ==============================================================================

package here

import (
	"fmt"

	"go-traffic/internal/config"
)

// ProviderError đại diện cho lỗi trả về từ HERE Traffic API kèm theo StatusCode
type ProviderError struct {
	StatusCode int
	Message    string
	RawBody    string
}

func (e *ProviderError) Error() string {
	return fmt.Sprintf("HERE API Error (HTTP %d): %s", e.StatusCode, e.Message)
}

// IsRetryable kiểm tra xem lỗi này có đáng để retry hay không
// KHÔNG retry các lỗi Authentication (401, 403) hoặc Client Request Error (400)
func (e *ProviderError) IsRetryable() bool {
	if e.StatusCode == 401 || e.StatusCode == 403 || e.StatusCode == 400 {
		return false
	}
	// Retry với Rate Limit (429) hoặc lỗi Server (500, 502, 503, 504)
	if e.StatusCode == 429 || e.StatusCode >= 500 {
		return true
	}
	return false
}

// MaskKeyError tạo lỗi bảo mật không làm lộ API key trong log stdout/stderr
func MaskKeyError(key string, err error) error {
	masked := config.MaskAPIKey(key)
	return fmt.Errorf("HERE API Key [%s]: %w", masked, err)
}
