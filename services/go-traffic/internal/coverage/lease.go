// ==============================================================================
// Lease Manager Specification (internal/coverage/lease.go)
// Phase HERE-3 — Distributed / In-Memory Cell Lease Lock với TTL
// Tránh 2 collector replicas gọi trùng cell trong cùng một mốc thời gian
// ==============================================================================

package coverage

import (
	"sync"
	"time"
)

// LeaseRecord thông tin lock lease của 1 cell
type LeaseRecord struct {
	CellID    string    `json:"cell_id"`
	WorkerID  string    `json:"worker_id"`
	Acquired  time.Time `json:"acquired_at"`
	ExpiresAt time.Time `json:"expires_at"`
}

// LeaseManager quản lý lock lease cho các cell (thread-safe)
type LeaseManager struct {
	leases map[string]LeaseRecord
	mu     sync.Mutex
}

// NewLeaseManager khởi tạo LeaseManager
func NewLeaseManager() *LeaseManager {
	return &LeaseManager{
		leases: make(map[string]LeaseRecord),
	}
}

// AcquireLease cố gắng lấy khóa lease cho cellID trong thời gian ttl.
// Trả về true nếu lấy khóa thành công, false nếu cellID đang bị khóa bởi worker khác.
func (lm *LeaseManager) AcquireLease(cellID string, workerID string, ttl time.Duration) bool {
	lm.mu.Lock()
	defer lm.mu.Unlock()

	now := time.Now()

	// Kiểm tra xem khóa hiện tại còn hạn không
	if existing, exists := lm.leases[cellID]; exists {
		if now.Before(existing.ExpiresAt) {
			// Khóa vẫn đang thuộc worker khác và chưa hết hạn -> Từ chối
			return false
		}
	}

	// Cấp khóa lease mới
	lm.leases[cellID] = LeaseRecord{
		CellID:    cellID,
		WorkerID:  workerID,
		Acquired:  now,
		ExpiresAt: now.Add(ttl),
	}

	return true
}

// ReleaseLease chủ động giải phóng khóa lease cho cellID
func (lm *LeaseManager) ReleaseLease(cellID string, workerID string) {
	lm.mu.Lock()
	defer lm.mu.Unlock()

	if existing, exists := lm.leases[cellID]; exists {
		if existing.WorkerID == workerID {
			delete(lm.leases, cellID)
		}
	}
}

// CleanupExpiredLeases tự động dọn dẹp các lease quá hạn
func (lm *LeaseManager) CleanupExpiredLeases() {
	lm.mu.Lock()
	defer lm.mu.Unlock()

	now := time.Now()
	for cellID, lease := range lm.leases {
		if now.After(lease.ExpiresAt) {
			delete(lm.leases, cellID)
		}
	}
}
