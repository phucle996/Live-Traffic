// ==============================================================================
// Circuit Breaker Unit Tests (internal/retry/circuit_breaker_test.go)
// Verifies Circuit Breaker State Transition & 401/403 Non-Retry Logic
// ==============================================================================

package retry

import (
	"testing"
	"time"
)

func TestCircuitBreakerStateTransition(t *testing.T) {
	cb := NewCircuitBreaker(2, 100*time.Millisecond) // Ngắt sau 2 lần thất bại

	if !cb.Allow() {
		t.Errorf("Ban đầu Circuit Breaker phải ở trạng thái CLOSED!")
	}

	// Ghi nhận 2 lần thất bại
	cb.RecordFailure(500)
	cb.RecordFailure(502)

	// Lần 3 phải bị chặn do Circuit Breaker đã sang StateOpen
	if cb.Allow() {
		t.Errorf("Circuit Breaker phải ngắt kết nối (OPEN) sau 2 lần thất bại!")
	}

	// Lỗi 401/403 không được tính làm tăng cờ ngắt kết nối của Circuit Breaker
	cb2 := NewCircuitBreaker(2, 100*time.Millisecond)
	cb2.RecordFailure(401)
	cb2.RecordFailure(403)
	if !cb2.Allow() {
		t.Errorf("Lỗi 401/403 không được làm ngắt Circuit Breaker!")
	}
}

func TestIsRetryableError(t *testing.T) {
	if IsRetryableError(401) {
		t.Errorf("Lỗi 401 không được retry!")
	}
	if IsRetryableError(403) {
		t.Errorf("Lỗi 403 không được retry!")
	}
	if !IsRetryableError(429) {
		t.Errorf("Lỗi 429 Rate Limit phải được retry!")
	}
	if !IsRetryableError(500) {
		t.Errorf("Lỗi 500 Server Error phải được retry!")
	}
}
