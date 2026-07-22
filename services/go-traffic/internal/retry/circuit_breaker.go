// ==============================================================================
// Circuit Breaker & Retry Mechanism (internal/retry/circuit_breaker.go)
// Exponential Backoff with Jitter, Skipping 401/403 Non-Retryable Errors
// ==============================================================================

package retry

import (
	"errors"
	"math"
	"math/rand"
	"sync"
	"time"
)

// Trạng thái Circuit Breaker
type State int

const (
	StateClosed State = iota
	StateHalfOpen
	StateOpen
)

// ErrCircuitOpen trả về khi Circuit Breaker đang ngắt kết nối
var ErrCircuitOpen = errors.New("circuit breaker is OPEN - skipping request to protect upstream")

// CircuitBreaker bảo vệ hệ thống khỏi việc gọi dồn dập vào upstream khi gặp sự cố diện rộng
type CircuitBreaker struct {
	maxFailures  int
	resetTimeout time.Duration

	failures int
	state    State
	lastFail time.Time
	mu       sync.Mutex
}

// NewCircuitBreaker khởi tạo CircuitBreaker mới
func NewCircuitBreaker(maxFailures int, resetTimeout time.Duration) *CircuitBreaker {
	return &CircuitBreaker{
		maxFailures:  maxFailures,
		resetTimeout: resetTimeout,
		state:        StateClosed,
	}
}

// Allow kiểm tra xem request có được phép gửi đi hay không
func (cb *CircuitBreaker) Allow() bool {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	if cb.state == StateOpen {
		if time.Since(cb.lastFail) > cb.resetTimeout {
			cb.state = StateHalfOpen
			return true
		}
		return false
	}
	return true
}

// RecordSuccess ghi nhận request thành công và chuyển trạng thái về StateClosed
func (cb *CircuitBreaker) RecordSuccess() {
	cb.mu.Lock()
	defer cb.mu.Unlock()
	cb.failures = 0
	cb.state = StateClosed
}

// RecordFailure ghi nhận request thất bại và chuyển sang StateOpen nếu vượt quá maxFailures
func (cb *CircuitBreaker) RecordFailure(statusCode int) {
	// Không tính các lỗi authentication 401/403 vào Circuit Breaker ngắt kết nối
	if statusCode == 401 || statusCode == 403 {
		return
	}

	cb.mu.Lock()
	defer cb.mu.Unlock()

	cb.failures++
	cb.lastFail = time.Now()

	if cb.failures >= cb.maxFailures {
		cb.state = StateOpen
	}
}

// IsRetryableError kiểm tra xem lỗi HTTP Status Code có đáng để retry hay không (Bỏ qua 401/403)
func IsRetryableError(statusCode int) bool {
	if statusCode == 401 || statusCode == 403 {
		return false // Không retry lỗi sai API Key / hết hạn quyền
	}
	if statusCode == 429 || statusCode >= 500 {
		return true // Retry cho lỗi Rate limit hoặc Server Error
	}
	return false
}

// CalculateBackoff Jitter tính toán thời gian chờ tăng dần exponential backoff có ngẫu nhiên jitter
func CalculateBackoff(attempt int, baseDelay time.Duration) time.Duration {
	temp := math.Pow(2, float64(attempt)) * float64(baseDelay)
	jitter := rand.Float64() * temp * 0.5
	return time.Duration(temp + jitter)
}

