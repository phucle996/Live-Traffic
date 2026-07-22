// ==============================================================================
// State Store Unit Tests (internal/store/state_store_test.go)
// Verifies Concurrent Read/Write Locks, Data Freshness & ETag Calculation
// ==============================================================================

package store

import (
	"fmt"
	"sync"
	"testing"
	"time"

	"go-traffic/internal/contract"
)

func TestStateStoreUpdateAndGet(t *testing.T) {
	st := NewStateStore()

	evt := contract.NewTrafficEvent(
		"loc-01", "Nam Kỳ Khởi Nghĩa", "Quận 3",
		10.7781, 106.6952, 20.0, 45.0, 0.95,
		time.Now().Format(time.RFC3339), "tomtom_live", "batch-1",
	)

	st.Update(evt)

	rec, exists := st.GetByLocationID("loc-01")
	if !exists {
		t.Fatalf("Không tìm thấy location loc-01 trong StateStore!")
	}

	if rec.LocationName != "Nam Kỳ Khởi Nghĩa" {
		t.Errorf("LocationName không khớp: %s", rec.LocationName)
	}
	if rec.Source != "tomtom_live" {
		t.Errorf("Source không khớp: %s", rec.Source)
	}

	etag := st.ComputeETag()
	if len(etag) == 0 {
		t.Errorf("ETag không được để trống!")
	}
}

func TestStateStoreConcurrentAccess(t *testing.T) {
	st := NewStateStore()
	var wg sync.WaitGroup

	// Chạy 50 Goroutines đồng thời ghi và đọc để kiểm tra chống Race Condition
	for i := 0; i < 50; i++ {
		wg.Add(2)
		locID := fmt.Sprintf("loc-%d", i%5)

		// Goroutine ghi
		go func(id string) {
			defer wg.Done()
			evt := contract.NewTrafficEvent(
				id, "Tuyến Đường Mẫu", "Quận 1",
				10.77, 106.69, 30.0, 50.0, 0.9,
				time.Now().Format(time.RFC3339), "tomtom_live", "batch-test",
			)
			st.Update(evt)
		}(locID)

		// Goroutine đọc
		go func(id string) {
			defer wg.Done()
			st.GetByLocationID(id)
			st.GetAll()
			st.ComputeETag()
		}(locID)
	}

	wg.Wait()

	all := st.GetAll()
	if len(all) == 0 {
		t.Errorf("GetAll phải trả về dữ liệu sau khi ghi đồng thời!")
	}
}
