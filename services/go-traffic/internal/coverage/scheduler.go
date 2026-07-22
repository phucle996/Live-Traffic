// ==============================================================================
// Scheduler Specification (internal/coverage/scheduler.go)
// Phase HERE-3 — Emitting CrawlTask với BatchID, CellID, ScheduledAt, StartedAt, FinishedAt
// ==============================================================================

package coverage

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"time"
)

// CrawlTask chứa thông tin lịch crawl cho 1 cell cụ thể
type CrawlTask struct {
	BatchID     string    `json:"batch_id"`     // Định danh đợt crawl
	CellID      string    `json:"cell_id"`      // Định danh ô lưới
	Cell        Cell      `json:"cell"`         // Thông tin chi tiết cell
	ScheduledAt time.Time `json:"scheduled_at"` // Thời điểm lên lịch
	StartedAt   time.Time `json:"started_at"`   // Thời điểm bắt đầu gọi API
	FinishedAt  time.Time `json:"finished_at"`  // Thời điểm hoàn thành
	Success     bool      `json:"success"`      // Trạng thái thu thập thành công
	ItemCount   int       `json:"item_count"`   // Số lượng flow items thu được
	ErrorMessage string   `json:"error_message,omitempty"`
}

// GenerateBatchID tạo định danh duy nhất cho 1 đợt batch crawl
func GenerateBatchID(cellID string, t time.Time) string {
	raw := fmt.Sprintf("batch:%s:%d", cellID, t.Unix())
	hash := sha256.Sum256([]byte(raw))
	return fmt.Sprintf("batch_%s", hex.EncodeToString(hash[:8]))
}

// NewCrawlTask tạo CrawlTask mới cho ô lưới
func NewCrawlTask(cell Cell, scheduledAt time.Time) CrawlTask {
	return CrawlTask{
		BatchID:     GenerateBatchID(cell.CellID, scheduledAt),
		CellID:      cell.CellID,
		Cell:        cell,
		ScheduledAt: scheduledAt,
	}
}
