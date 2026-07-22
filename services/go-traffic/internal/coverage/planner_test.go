// ==============================================================================
// Planner Unit Tests Specification (internal/coverage/planner_test.go)
// Phase HERE-3 — Test Grid Generator, Priority Calculation, Lease Lock & Scheduler
// ==============================================================================

package coverage

import (
	"context"
	"testing"
	"time"

	"go-traffic/internal/budget"
	"go-traffic/internal/provider"
)

// TestGenerateGrid_Count verifies grid cells are properly partitioned across city bounds
func TestGenerateGrid_Count(t *testing.T) {
	boundary := DefaultHCMBoundary()
	stepDeg := 0.05 // 0.05 deg grid step

	cells := GenerateGrid(boundary, stepDeg)
	if len(cells) == 0 {
		t.Fatalf("Grid generator không được trả danh sách rỗng")
	}

	for _, cell := range cells {
		if cell.CellID == "" {
			t.Errorf("CellID không được rỗng")
		}
		if cell.BBox.South >= cell.BBox.North || cell.BBox.West >= cell.BBox.East {
			t.Errorf("Cell BBox %s không hợp lệ: %+v", cell.CellID, cell.BBox)
		}
	}
}

// TestPriority_Enrichment verifies priority 1 is assigned to central zones
func TestPriority_Enrichment(t *testing.T) {
	cell := Cell{
		CellID:   "test_q1",
		Priority: 3,
		BBox: provider.BoundingBox{
			South: 10.770,
			West:  106.700,
			North: 10.780,
			East:  106.710,
		},
	}

	pz := GetBuiltinPriorityZones()
	now := time.Date(2026, 7, 22, 8, 0, 0, 0, time.UTC) // 8:00 AM weekday -> Peak Hour

	EnrichCellPriority(&cell, pz, now)

	if cell.Priority != 1 {
		t.Errorf("Kỳ vọng Priority = 1 cho cell trung tâm Q1, nhận được: %d", cell.Priority)
	}

	// Interval phải ngắn hơn (cao điểm)
	if cell.PollingInterval >= 3*time.Minute {
		t.Errorf("Kỳ vọng PollingInterval ngắn hơn 3 phút trong giờ cao điểm, nhận được: %v", cell.PollingInterval)
	}
}

// TestLeaseManager_AcquireAndRelease verifies atomic lease locking with TTL
func TestLeaseManager_AcquireAndRelease(t *testing.T) {
	lm := NewLeaseManager()
	cellID := "cell_1076_10669"
	worker1 := "worker-01"
	worker2 := "worker-02"
	ttl := 100 * time.Millisecond

	// Worker 1 lấy khóa
	if !lm.AcquireLease(cellID, worker1, ttl) {
		t.Fatalf("Worker 1 phải lấy được lease")
	}

	// Worker 2 thử lấy khóa trong khi khóa còn hạn -> Từ chối
	if lm.AcquireLease(cellID, worker2, ttl) {
		t.Fatalf("Worker 2 không được phép lấy lease khi Worker 1 đang giữ khóa")
	}

	// Chờ lease quá hạn TTL
	time.Sleep(120 * time.Millisecond)

	// Worker 2 thử lại sau khi hết TTL -> Thành công
	if !lm.AcquireLease(cellID, worker2, ttl) {
		t.Fatalf("Worker 2 phải lấy được lease sau khi TTL quá hạn")
	}
}

// TestGridPlanner_GetSchedulableCells verifies schedulable cells filter
func TestGridPlanner_GetSchedulableCells(t *testing.T) {
	planner := NewGridPlanner(PlannerConfig{
		WorkerID: "test-worker",
		StepDeg:  0.1, // Ma trận nhỏ để test nhanh
	})

	now := time.Now()
	cells, err := planner.GetSchedulableCells(context.Background(), nil, nil, now)
	if err != nil {
		t.Fatalf("GetSchedulableCells không được trả lỗi: %v", err)
	}

	if len(cells) == 0 {
		t.Fatalf("Kỳ vọng ít nhất 1 cell đủ điều kiện crawl lần đầu")
	}

	// Lần gọi thứ 2 ngay lập tức -> Không cell nào được lên lịch vì chưa quá hạn polling
	cells2, err2 := planner.GetSchedulableCells(context.Background(), nil, nil, now)
	if err2 != nil {
		t.Fatalf("GetSchedulableCells lần 2 không được trả lỗi: %v", err2)
	}

	if len(cells2) != 0 {
		t.Errorf("Kỳ vọng 0 cell khi gọi dồn dập ngay lập tức, nhận được: %d", len(cells2))
	}
}

// TestScheduler_BatchIDGeneration verifies deterministic batch ID generation
func TestScheduler_BatchIDGeneration(t *testing.T) {
	now := time.Date(2026, 7, 22, 12, 0, 0, 0, time.UTC)
	batchID1 := GenerateBatchID("cell_01", now)
	batchID2 := GenerateBatchID("cell_01", now)

	if batchID1 != batchID2 {
		t.Errorf("Batch ID phải mang tính xác định cho cùng cellID và timestamp: %s vs %s", batchID1, batchID2)
	}
}

// TestGridPlanner_QuotaDegradation verifies Priority 3 cells are dropped when budget ratio > 80%
func TestGridPlanner_QuotaDegradation(t *testing.T) {
	planner := NewGridPlanner(PlannerConfig{
		WorkerID: "test-worker-degrade",
		StepDeg:  0.1,
	})

	bt := budget.NewBudgetTracker(10)
	// Giả lập sử dụng 9/10 requests (90% quota ratio > 80%)
	for i := 0; i < 9; i++ {
		bt.Acquire()
	}

	now := time.Now()
	schedulable, err := planner.GetSchedulableCells(context.Background(), nil, bt, now)
	if err != nil {
		t.Fatalf("Planner không được trả lỗi khi quotaratio > 80%%: %v", err)
	}

	// Đảm bảo không có cell nào có Priority 3 được xếp lịch khi quota > 80%
	for _, cell := range schedulable {
		if cell.Priority >= 3 {
			t.Errorf("Kỳ vọng Cell Priority 3 bị bỏ qua khi quota > 80%%, nhưng cell %s (%d) lại được xếp lịch", cell.CellID, cell.Priority)
		}
	}
}
