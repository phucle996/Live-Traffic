// ==============================================================================
// Grid Planner Specification (internal/coverage/planner.go)
// Phase R5 — Area Scheduler, Quota Degradation Policy & Cell Overdue Metrics
// ==============================================================================

package coverage

import (
	"context"
	"fmt"
	"log"
	"time"

	"go-traffic/internal/budget"
	"go-traffic/internal/provider"
	"go-traffic/internal/retry"
	"go-traffic/internal/telemetry"
)

// PlannerConfig chứa cấu hình cho GridPlanner
type PlannerConfig struct {
	WorkerID        string
	StepDeg         float64
	GeoJSONPath     string
	GridYAMLPath    string
	PollingYAMLPath string
}

// GridPlanner chịu trách nhiệm lập kế hoạch crawl traffic theo ô lưới
type GridPlanner struct {
	boundary      *CityBoundary
	cells         []Cell
	priorityZones []ZonePriorityConfig
	leaseManager  *LeaseManager
	workerID      string
}

// NewGridPlanner khởi tạo GridPlanner với ranh giới thành phố và các ô lưới
func NewGridPlanner(cfg PlannerConfig) *GridPlanner {
	boundary, err := LoadBoundaryFromGeoJSON(cfg.GeoJSONPath)
	if err != nil {
		boundary = DefaultHCMBoundary()
	}

	cells := GenerateGrid(boundary, cfg.StepDeg)
	pz := GetBuiltinPriorityZones()

	workerID := cfg.WorkerID
	if workerID == "" {
		workerID = "collector-worker-local"
	}

	planner := &GridPlanner{
		boundary:      boundary,
		cells:         cells,
		priorityZones: pz,
		leaseManager:  NewLeaseManager(),
		workerID:      workerID,
	}

	// Đánh giá Priority & PollingInterval ban đầu cho tất cả các cell
	planner.RefreshPriorities(time.Now())
	return planner
}

// RefreshPriorities cập nhật lại priority và polling interval cho tất cả các cell theo thời gian thực
func (gp *GridPlanner) RefreshPriorities(now time.Time) {
	for i := range gp.cells {
		EnrichCellPriority(&gp.cells[i], gp.priorityZones, now)
	}
}

// GetSchedulableCells trả về danh sách các Cell đủ điều kiện để crawl ở thời điểm hiện tại:
// 1. Quá hạn PollingInterval (kèm ghi nhận Cell Overdue Prometheus Metrics)
// 2. Lấy thành công khóa Lease Lock (chưa bị worker khác khóa)
// 3. Quota Degradation Check (>80% quota daily limit -> bỏ cell Priority 3, gấp đôi interval Priority 2)
// 4. Provider Circuit Breaker đang ngắt -> KHÔNG crawl
// 5. Hết Daily Budget -> KHÔNG crawl, dừng có kiểm soát (không crash)
func (gp *GridPlanner) GetSchedulableCells(
	ctx context.Context,
	cb *retry.CircuitBreaker,
	bt *budget.BudgetTracker,
	now time.Time,
) ([]Cell, error) {

	// 1. Kiểm tra Circuit Breaker trước khi lên kế hoạch
	if cb != nil && !cb.Allow() {
		return nil, fmt.Errorf("Provider Circuit Breaker đang OPEN - Hủy lịch crawl cell")
	}

	// Cập nhật lại Priority theo thời gian thực (Giờ cao điểm)
	gp.RefreshPriorities(now)

	// 2. Tỷ lệ Budget đã sử dụng (Quota Ratio)
	quotaRatio := 0.0
	if bt != nil {
		used, maxLimit := bt.GetStats()
		if maxLimit > 0 {
			quotaRatio = float64(used) / float64(maxLimit)
		}
	}

	var schedulable []Cell

	for i, cell := range gp.cells {
		// 3. Graceful Quota Degradation Policy khi gần hết quota (> 80% daily budget)
		effectiveInterval := cell.PollingInterval
		if quotaRatio >= 0.80 {
			if cell.Priority >= 3 {
				// Bỏ qua các cell ưu tiên thấp (Priority 3) để tiết kiệm budget cho zone trọng điểm
				continue
			}
			if cell.Priority == 2 {
				// Gấp đôi khoảng thời gian polling cho Priority 2
				effectiveInterval = cell.PollingInterval * 2
			}
		}

		// 4. Kiểm tra xem cell đã quá hạn polling chưa
		if !cell.LastPolledAt.IsZero() {
			elapsed := now.Sub(cell.LastPolledAt)
			if elapsed < effectiveInterval {
				continue
			}

			// Ghi nhận Cell Overdue metrics nếu trễ > 60 giây so với lịch
			if overdue := elapsed - effectiveInterval; overdue > 60*time.Second {
				telemetry.CellOverdueTotal.WithLabelValues(cell.CellID).Inc()
				telemetry.CellOverdueSeconds.WithLabelValues(cell.CellID).Set(overdue.Seconds())
				log.Printf("[COVERAGE WARN] Cell %s (%s) bị trễ polling %v", cell.CellID, cell.Name, overdue)
			}
		}

		// 5. Kiểm tra Daily Budget cạn hoàn toàn
		if bt != nil && !bt.CanAcquire() {
			log.Printf("[COVERAGE WARN] Daily Budget Limit reached — Dừng lên lịch cell dừng có kiểm soát")
			return schedulable, nil
		}

		// 6. Cố gắng lấy khóa Lease Lock cho Cell
		leaseTTL := effectiveInterval / 2
		if leaseTTL < 1*time.Minute {
			leaseTTL = 1 * time.Minute
		}

		if gp.leaseManager.AcquireLease(cell.CellID, gp.workerID, leaseTTL) {
			// Cập nhật thời điểm vừa lên lịch
			gp.cells[i].LastPolledAt = now
			schedulable = append(schedulable, gp.cells[i])
		}
	}

	return schedulable, nil
}

// ReleaseCellLease giải phóng khóa lease sau khi worker hoàn thành crawl cell
func (gp *GridPlanner) ReleaseCellLease(cellID string) {
	gp.leaseManager.ReleaseLease(cellID, gp.workerID)
}

// GetAllCells trả về toàn bộ danh sách Cell để theo dõi / thống kê
func (gp *GridPlanner) GetAllCells() []Cell {
	return gp.cells
}

// MapCellToQueryArea chuyển đổi Cell sang provider.QueryArea (BoundingBox)
func MapCellToQueryArea(cell Cell) provider.QueryArea {
	return cell.BBox
}
