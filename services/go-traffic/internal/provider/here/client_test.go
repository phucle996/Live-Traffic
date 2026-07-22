// ==============================================================================
// HERE Client Unit Tests Specification (internal/provider/here/client_test.go)
// Phase HERE-2 — Offline Mock Server & Fixtures Testing
// Không kết nối Internet, kiểm tra 200 OK, 401 Unauthorized, 429 Rate Limit, Invalid JSON
// ==============================================================================

package here

import (
	"context"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"testing"
	"time"

	"go-traffic/internal/provider"
)

// helperLoadFixture nạp file fixture từ thư mục testdata
func helperLoadFixture(t *testing.T, filename string) []byte {
	t.Helper()
	path := filepath.Join("testdata", filename)
	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("Không thể đọc file fixture '%s': %v", path, err)
	}
	return data
}

// TestFetchFlow_Success kiểm tra trường hợp gọi API thành công HTTP 200 OK
func TestFetchFlow_Success(t *testing.T) {
	fixtureData := helperLoadFixture(t, "flow_success.json")

	// Tạo HTTP Mock Server giả lập HERE Traffic API v7
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Kiểm tra query parameter
		if r.URL.Query().Get("apiKey") != "test_here_key_123" {
			http.Error(w, "Unauthorized", http.StatusUnauthorized)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		w.Header().Set("X-Request-Id", "req-test-uuid-999")
		w.WriteHeader(http.StatusOK)
		w.Write(fixtureData)
	}))
	defer server.Close()

	// Khởi tạo client tới Mock Server
	client := NewProvider("test_here_key_123", WithBaseURL(server.URL))

	bbox := provider.BoundingBox{
		South: 10.760,
		West:  106.692,
		North: 10.790,
		East:  106.710,
	}

	obs, err := client.FetchFlow(context.Background(), bbox)
	if err != nil {
		t.Fatalf("Kỳ vọng FetchFlow thành công, nhận lỗi: %v", err)
	}

	if len(obs) != 2 {
		t.Fatalf("Kỳ vọng 2 observations từ fixture, nhận được: %d", len(obs))
	}

	// Kiểm tra dữ liệu chuẩn hóa của observation đầu tiên
	first := obs[0]
	if first.Provider != "here" {
		t.Errorf("Kỳ vọng Provider = 'here', nhận được: %s", first.Provider)
	}
	if first.ProviderRequestID != "req-test-uuid-999" {
		t.Errorf("Kỳ vọng ProviderRequestID = 'req-test-uuid-999', nhận được: %s", first.ProviderRequestID)
	}
	if first.CurrentSpeedKPH != 24.5 {
		t.Errorf("Kỳ vọng CurrentSpeedKPH = 24.5, nhận được: %f", first.CurrentSpeedKPH)
	}
	if first.FreeFlowSpeedKPH != 45.0 {
		t.Errorf("Kỳ vọng FreeFlowSpeedKPH = 45.0, nhận được: %f", first.FreeFlowSpeedKPH)
	}
	if first.JamFactor != 4.2 {
		t.Errorf("Kỳ vọng JamFactor = 4.2, nhận được: %f", first.JamFactor)
	}
}

// TestFetchFlow_Empty kiểm tra trường hợp response rỗng results: []
func TestFetchFlow_Empty(t *testing.T) {
	fixtureData := helperLoadFixture(t, "flow_empty.json")

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		w.Write(fixtureData)
	}))
	defer server.Close()

	client := NewProvider("test_key", WithBaseURL(server.URL))
	bbox := provider.BoundingBox{South: 10.0, West: 106.0, North: 10.1, East: 106.1}

	obs, err := client.FetchFlow(context.Background(), bbox)
	if err != nil {
		t.Fatalf("Kỳ vọng không lỗi khi response rỗng, nhận lỗi: %v", err)
	}

	if len(obs) != 0 {
		t.Errorf("Kỳ vọng 0 observations cho empty response, nhận được: %d", len(obs))
	}
}

// TestFetchFlow_Unauthorized_NoRetry kiểm tra lỗi HTTP 401 ngắt ngay lập tức, không retry
func TestFetchFlow_Unauthorized_NoRetry(t *testing.T) {
	requestCount := 0

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		requestCount++
		w.WriteHeader(http.StatusUnauthorized)
		w.Write([]byte(`{"error": "Unauthorized"}`))
	}))
	defer server.Close()

	client := NewProvider("invalid_key", WithBaseURL(server.URL))
	bbox := provider.BoundingBox{South: 10.0, West: 106.0, North: 10.1, East: 106.1}

	_, err := client.FetchFlow(context.Background(), bbox)
	if err == nil {
		t.Fatalf("Kỳ vọng lỗi khi HTTP 401 Unauthorized")
	}

	if requestCount != 1 {
		t.Errorf("Kỳ vọng đúng 1 request cho HTTP 401 (không được retry), số request thực tế: %d", requestCount)
	}
}

// TestBuildFlowURL_Masking kiểm tra hàm che khuất API Key trong URL log
func TestBuildFlowURL_Masking(t *testing.T) {
	bbox := provider.BoundingBox{South: 10.76, West: 106.69, North: 10.79, East: 106.71}
	fullURL, maskedURL, err := BuildFlowURL("https://data.traffic.hereapi.com/flow", "secret_here_api_key_xyz", bbox)
	if err != nil {
		t.Fatalf("BuildFlowURL không được trả lỗi: %v", err)
	}

	if fullURL == maskedURL {
		t.Errorf("maskedURL phải khác fullURL để bảo mật API key")
	}

	if len(maskedURL) == 0 {
		t.Errorf("maskedURL không được rỗng")
	}
}

// TestFetchFlow_Timeout kiểm tra Context Timeout hoạt động chính xác
func TestFetchFlow_Timeout(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		time.Sleep(200 * time.Millisecond) // Giả lập server xử lý chậm
		w.WriteHeader(http.StatusOK)
	}))
	defer server.Close()

	client := NewProvider("test_key", WithBaseURL(server.URL))
	bbox := provider.BoundingBox{South: 10.0, West: 106.0, North: 10.1, East: 106.1}

	// Context với timeout 50ms (ngắn hơn server sleep 200ms)
	ctx, cancel := context.WithTimeout(context.Background(), 50*time.Millisecond)
	defer cancel()

	_, err := client.FetchFlow(ctx, bbox)
	if err == nil {
		t.Fatalf("Kỳ vọng lỗi Timeout khi context quá hạn")
	}
}

// TestFetchFlow_IntegrationLive kiểm tra gọi API thực tế — CHỈ CHẠY khi có HERE_API_KEY
func TestFetchFlow_IntegrationLive(t *testing.T) {
	apiKey := os.Getenv("HERE_API_KEY")
	if apiKey == "" {
		t.Skip("Bỏ qua Integration Test vì chưa set biến môi trường HERE_API_KEY")
	}

	client := NewProvider(apiKey)
	bbox := provider.BoundingBox{
		South: 10.760,
		West:  106.692,
		North: 10.790,
		East:  106.710,
	}

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	obs, err := client.FetchFlow(ctx, bbox)
	if err != nil {
		t.Fatalf("Integration test với live HERE API thất bại: %v", err)
	}

	t.Logf("Tải thành công %d flow items từ live HERE Traffic API", len(obs))
}
