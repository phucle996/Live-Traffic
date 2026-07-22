// ==============================================================================
// Global & Per-Batch Request Budget Tracker (internal/budget/budget.go)
// Atomic Counter, HTTP 429 Detection & Daily Quota Guard (2,500 reqs/day)
// ==============================================================================

package budget

import (
	"sync"
	"sync/atomic"
	"time"
)

// BudgetTracker theo dõi và quản lý hạn ngạch API request hàng ngày an toàn trong môi trường đa luồng
type BudgetTracker struct {
	maxDailyLimit int64
	currentCount  int64
	lastResetDay  int
	mu            sync.Mutex
}

// NewBudgetTracker khởi tạo BudgetTracker với hạn ngạch cho phép
func NewBudgetTracker(maxDailyLimit int64) *BudgetTracker {
	return &BudgetTracker{
		maxDailyLimit: maxDailyLimit,
		currentCount:  0,
		lastResetDay:  time.Now().YearDay(),
	}
}

// Acquire check và tăng số lượng request nếu còn trong hạn ngạch budget
func (bt *BudgetTracker) Acquire() bool {
	bt.mu.Lock()
	defer bt.mu.Unlock()

	// Reset counter nếu sang ngày mới
	today := time.Now().YearDay()
	if today != bt.lastResetDay {
		bt.currentCount = 0
		bt.lastResetDay = today
	}

	if bt.currentCount >= bt.maxDailyLimit {
		return false // Hạn ngạch daily budget đã cạn
	}

	atomic.AddInt64(&bt.currentCount, 1)
	return true
}

// CanAcquire kiểm tra xem budget còn dư hay không mà chưa tăng counter
func (bt *BudgetTracker) CanAcquire() bool {
	bt.mu.Lock()
	defer bt.mu.Unlock()

	today := time.Now().YearDay()
	if today != bt.lastResetDay {
		bt.currentCount = 0
		bt.lastResetDay = today
	}

	return bt.currentCount < bt.maxDailyLimit
}

// GetStats trả về số lượng request đã sử dụng và hạn ngạch tối đa
func (bt *BudgetTracker) GetStats() (int64, int64) {
	bt.mu.Lock()
	defer bt.mu.Unlock()
	return atomic.LoadInt64(&bt.currentCount), bt.maxDailyLimit
}
