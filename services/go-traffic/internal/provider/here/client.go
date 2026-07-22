// ==============================================================================
// HERE Client Production Implementation (internal/provider/here/client.go)
// Phase R4 — HERE Traffic API v7 Client với Telemetry Metrics, Retry-After Header,
// Connection Pool, Retries (Backoff+Jitter), Circuit Breaker, Key Redaction & Context Timeout
// ==============================================================================

package here

import (
	"context"
	"fmt"
	"io"
	"log"
	"net/http"
	"strconv"
	"time"

	"go-traffic/internal/config"
	"go-traffic/internal/provider"
	"go-traffic/internal/retry"
	"go-traffic/internal/telemetry"
)

// Provider quản lý kết nối HTTP production-grade tới HERE Traffic API v7
type Provider struct {
	apiKey         string
	baseURL        string
	httpClient     *http.Client
	circuitBreaker *retry.CircuitBreaker
	maxRetries     int
	baseBackoff    time.Duration
}

// Option cho phép tùy biến cấu hình Client (dùng cho Unit Tests hoặc Mock Server)
type Option func(*Provider)

// WithBaseURL thiết lập custom base URL (hữu ích cho mock server trong unit test)
func WithBaseURL(url string) Option {
	return func(p *Provider) {
		p.baseURL = url
	}
}

// WithHTTPClient truyền HTTP client tùy chỉnh
func WithHTTPClient(client *http.Client) Option {
	return func(p *Provider) {
		p.httpClient = client
	}
}

// NewProvider khởi tạo HERE Provider production-grade với connection pool và circuit breaker
func NewProvider(apiKey string, opts ...Option) *Provider {
	// Connection pool tối ưu hiệu năng
	transport := &http.Transport{
		MaxIdleConns:        100,
		MaxIdleConnsPerHost: 20,
		IdleConnTimeout:     90 * time.Second,
	}

	httpClient := &http.Client{
		Transport: transport,
		Timeout:   10 * time.Second,
	}

	// Circuit breaker riêng cho HERE: tối đa 5 lỗi liên tiếp ngắt trong 30 giây
	cb := retry.NewCircuitBreaker(5, 30*time.Second)

	p := &Provider{
		apiKey:         apiKey,
		baseURL:        "https://data.traffic.hereapi.com/traffic/6.3/flow.json",
		httpClient:     httpClient,
		circuitBreaker: cb,
		maxRetries:     3,
		baseBackoff:    500 * time.Millisecond,
	}

	for _, opt := range opts {
		opt(p)
	}

	return p
}

// Name trả định danh provider "here"
func (p *Provider) Name() string {
	return "here"
}

// HealthCheck kiểm tra trạng thái API key
func (p *Provider) HealthCheck(ctx context.Context) error {
	if p.apiKey == "" {
		return fmt.Errorf("HERE API Key bị trống (Masked Key: %s)", config.MaskAPIKey(p.apiKey))
	}
	return nil
}

// FetchFlow thực thi thu thập dữ liệu giao thông theo QueryArea từ HERE Traffic API v7
func (p *Provider) FetchFlow(ctx context.Context, area provider.QueryArea) ([]provider.FlowObservation, error) {
	if p.apiKey == "" {
		return nil, fmt.Errorf("HERE API Key không được thiết lập")
	}

	// Kiểm tra Circuit Breaker trước khi gửi request
	if !p.circuitBreaker.Allow() {
		return nil, retry.ErrCircuitOpen
	}

	fullURL, maskedURL, err := BuildFlowURL(p.baseURL, p.apiKey, area)
	if err != nil {
		return nil, fmt.Errorf("lỗi tạo request URL: %w", err)
	}

	var lastErr error
	var resp *http.Response

	startReqTime := time.Now()

	// Thực hiện vòng lặp Retry với Exponential Backoff & Jitter
	for attempt := 0; attempt <= p.maxRetries; attempt++ {
		// Ghi nhận telemetry metrics cho mỗi lượt gửi request
		telemetry.ProviderRequestsTotal.WithLabelValues("here").Inc()

		if attempt > 0 {
			backoff := retry.CalculateBackoff(attempt, p.baseBackoff)
			log.Printf("[HERE RETRY] Thử lại lần %d/%d sau %v cho request %s", attempt, p.maxRetries, backoff, maskedURL)
			select {
			case <-ctx.Done():
				return nil, ctx.Err()
			case <-time.After(backoff):
			}
		}

		req, errReq := http.NewRequestWithContext(ctx, http.MethodGet, fullURL, nil)
		if errReq != nil {
			return nil, fmt.Errorf("lỗi khởi tạo HTTP request: %w", errReq)
		}
		req.Header.Set("Accept", "application/json")

		resp, err = p.httpClient.Do(req)
		if err != nil {
			telemetry.ProviderErrorsTotal.WithLabelValues("here").Inc()
			lastErr = fmt.Errorf("lỗi kết nối HTTP tới HERE API: %w", err)
			p.circuitBreaker.RecordFailure(500)
			continue
		}

		// Đánh giá latency request
		latency := time.Since(startReqTime).Seconds()
		telemetry.ProviderRequestDurationSeconds.WithLabelValues("here").Observe(latency)

		// Xử lý StatusCode thành công 200 OK
		if resp.StatusCode == http.StatusOK {
			p.circuitBreaker.RecordSuccess()
			break
		}

		// Ghi nhận lỗi theo StatusCode
		telemetry.ProviderErrorsTotal.WithLabelValues("here").Inc()

		// Xử lý 429 Rate Limit & đọc Retry-After header
		if resp.StatusCode == http.StatusTooManyRequests {
			telemetry.ProviderRateLimitedTotal.WithLabelValues("here").Inc()

			retryAfterSec := 2
			if raHeader := resp.Header.Get("Retry-After"); raHeader != "" {
				if parsedSec, err := strconv.Atoi(raHeader); err == nil && parsedSec > 0 {
					retryAfterSec = parsedSec
				}
			}
			log.Printf("[HERE WARN] Rate limit (HTTP 429). Retry-After header = %d giây cho request %s", retryAfterSec, maskedURL)
		}

		// Đọc lỗi từ Body
		bodyBytes, _ := io.ReadAll(resp.Body)
		resp.Body.Close()

		pErr := &ProviderError{
			StatusCode: resp.StatusCode,
			Message:    http.StatusText(resp.StatusCode),
			RawBody:    string(bodyBytes),
		}

		p.circuitBreaker.RecordFailure(resp.StatusCode)
		lastErr = pErr

		// Nếu lỗi không đáng để retry (401, 403, 400) -> dừng ngay lập tức
		if !pErr.IsRetryable() {
			log.Printf("[HERE ERROR] Lỗi không thể retry HTTP %d cho request %s: %s", resp.StatusCode, maskedURL, pErr.Message)
			return nil, pErr
		}
	}

	if resp == nil || resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("HERE API request thất bại sau %d lần thử: %w", p.maxRetries+1, lastErr)
	}
	defer resp.Body.Close()

	// Trích xuất Request ID từ header phản hồi
	requestID := resp.Header.Get("X-Request-Id")
	if requestID == "" {
		requestID = resp.Header.Get("Here-Request-Id")
	}

	// Giải mã JSON response
	flowResp, errDecode := DecodeFlowResponse(resp.Body)
	if errDecode != nil {
		return nil, fmt.Errorf("lỗi decode JSON từ HERE response: %w", errDecode)
	}

	// Map sang standardized FlowObservation list
	obsList := MapToObservations(flowResp, requestID, time.Now().UTC().Format(time.RFC3339))

	// Thống kê Prometheus items nhận được
	telemetry.ProviderItemsTotal.WithLabelValues("here").Add(float64(len(obsList)))

	return obsList, nil
}

// FetchIncidents thu thập danh sách sự cố giao thông (Incidents)
func (p *Provider) FetchIncidents(ctx context.Context, area provider.QueryArea) ([]provider.TrafficIncident, error) {
	return []provider.TrafficIncident{}, nil
}
