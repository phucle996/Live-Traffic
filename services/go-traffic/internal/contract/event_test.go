// ==============================================================================
// Contract Unit Tests (internal/contract/event_test.go)
// Verifies TrafficEvent Schema & Deterministic EventID Hash Generation
// ==============================================================================

package contract

import (
	"testing"
)

func TestDeterministicEventID(t *testing.T) {
	// Kiểm tra xem cùng locationID và timestamp có cho ra EventID giống nhau không
	locID := "loc-01"
	ts := "2026-07-21T20:30:00Z"

	id1 := GenerateDeterministicEventID(locID, ts)
	id2 := GenerateDeterministicEventID(locID, ts)

	if id1 != id2 {
		t.Fatalf("EventID phải mang tính deterministic hoàn toàn. Thu được: id1=%s, id2=%s", id1, id2)
	}

	// Đảm bảo khác timestamp thì cho ra EventID khác nhau
	id3 := GenerateDeterministicEventID(locID, "2026-07-21T20:30:01Z")
	if id1 == id3 {
		t.Fatalf("Khác timestamp phải sinh ra EventID khác nhau!")
	}
}

func TestNewTrafficEventCreation(t *testing.T) {
	evt := NewTrafficEvent(
		"loc-01", "Nam Kỳ Khởi Nghĩa", "Quận 3",
		10.7781, 106.6952, 25.0, 45.0, 0.95,
		"2026-07-21T20:30:00Z", "tomtom_live", "batch-01",
	)

	if evt.LocationID != "loc-01" {
		t.Errorf("LocationID không khớp: %s", evt.LocationID)
	}
	if evt.CurrentSpeed != 25.0 {
		t.Errorf("CurrentSpeed không khớp: %f", evt.CurrentSpeed)
	}
	if len(evt.EventID) == 0 {
		t.Errorf("EventID không được để trống!")
	}
}
