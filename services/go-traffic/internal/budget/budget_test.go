// ==============================================================================
// Budget Tracker Unit Tests (internal/budget/budget_test.go)
// Verifies Daily Budget Counter & Rate Limit Guard Behavior
// ==============================================================================

package budget

import (
	"testing"
)

func TestBudgetTrackerAcquire(t *testing.T) {
	bt := NewBudgetTracker(3) // Hạn ngạch 3 requests

	if !bt.Acquire() {
		t.Errorf("Request 1 phải được cho phép!")
	}
	if !bt.Acquire() {
		t.Errorf("Request 2 phải được cho phép!")
	}
	if !bt.Acquire() {
		t.Errorf("Request 3 phải được cho phép!")
	}

	// Request thứ 4 phải bị từ chối do chạm hạn ngạch (Limit = 3)
	if bt.Acquire() {
		t.Errorf("Request 4 phải bị từ chối do cạn hạn ngạch daily budget!")
	}

	used, limit := bt.GetStats()
	if used != 3 || limit != 3 {
		t.Errorf("Stats không khớp: used=%d, limit=%d", used, limit)
	}
}
