// ==============================================================================
// Provider Router Unit Tests (internal/provider/router_test.go)
// Phase HERE-1 — Test điều hướng Primary + Fallback với Fake Provider (Không dùng Internet)
// ==============================================================================

package provider

import (
	"context"
	"fmt"
	"testing"
)

// FakeProvider mock lại TrafficProvider cho unit testing
type FakeProvider struct {
	name      string
	shouldErr bool
	mockFlows []FlowObservation
}

func (f *FakeProvider) Name() string {
	return f.name
}

func (f *FakeProvider) HealthCheck(ctx context.Context) error {
	if f.shouldErr {
		return fmt.Errorf("fake provider %s is unhealthy", f.name)
	}
	return nil
}

func (f *FakeProvider) FetchFlow(ctx context.Context, area QueryArea) ([]FlowObservation, error) {
	if f.shouldErr {
		return nil, fmt.Errorf("fake provider %s error", f.name)
	}
	return f.mockFlows, nil
}

func (f *FakeProvider) FetchIncidents(ctx context.Context, area QueryArea) ([]TrafficIncident, error) {
	return []TrafficIncident{}, nil
}

func TestRouter_PrimarySuccess(t *testing.T) {
	reg := NewRegistry()

	primaryFake := &FakeProvider{
		name: "here",
		mockFlows: []FlowObservation{
			{
				Provider:           "here",
				ProviderSegmentID:  "seg-101",
				CurrentSpeedKPH:    45.0,
				FreeFlowSpeedKPH:   60.0,
				Confidence:         0.95,
				Latitude:           10.77,
				Longitude:          106.69,
			},
		},
	}
	reg.Register(primaryFake)

	fallbackFake := &FakeProvider{
		name: "tomtom",
		mockFlows: []FlowObservation{
			{
				Provider:           "tomtom",
				ProviderSegmentID:  "seg-fb",
				CurrentSpeedKPH:    30.0,
				FreeFlowSpeedKPH:   60.0,
			},
		},
	}
	reg.Register(fallbackFake)

	cfg := RouterConfig{
		PrimaryProvider:  "here",
		FallbackProvider: "tomtom",
		Mode:             "primary_fallback",
	}

	r := NewRouter(reg, cfg)
	bbox := BoundingBox{South: 10.70, West: 106.60, North: 10.80, East: 106.70}

	events, err := r.FetchTrafficEvents(context.Background(), bbox, "batch-001", nil)
	if err != nil {
		t.Fatalf("kỳ vọng thành công từ Primary, nhận được lỗi: %v", err)
	}

	if len(events) != 1 {
		t.Fatalf("kỳ vọng 1 event, nhận được %d", len(events))
	}

	if events[0].Source != "here" {
		t.Errorf("kỳ vọng Source = 'here', nhận được '%s'", events[0].Source)
	}

	if events[0].CurrentSpeed != 45.0 {
		t.Errorf("kỳ vọng CurrentSpeed = 45.0, nhận được %f", events[0].CurrentSpeed)
	}
}

func TestRouter_FallbackToSecondaryWhenPrimaryFails(t *testing.T) {
	reg := NewRegistry()

	// Primary bị lỗi
	primaryFake := &FakeProvider{
		name:      "here",
		shouldErr: true,
	}
	reg.Register(primaryFake)

	// Fallback hoạt động tốt
	fallbackFake := &FakeProvider{
		name: "tomtom",
		mockFlows: []FlowObservation{
			{
				Provider:           "tomtom",
				ProviderSegmentID:  "seg-fb-01",
				CurrentSpeedKPH:    32.0,
				FreeFlowSpeedKPH:   50.0,
				Confidence:         0.88,
				Latitude:           10.80,
				Longitude:          106.71,
			},
		},
	}
	reg.Register(fallbackFake)

	cfg := RouterConfig{
		PrimaryProvider:  "here",
		FallbackProvider: "tomtom",
		Mode:             "primary_fallback",
	}

	r := NewRouter(reg, cfg)
	bbox := BoundingBox{South: 10.70, West: 106.60, North: 10.80, East: 106.70}

	events, err := r.FetchTrafficEvents(context.Background(), bbox, "batch-002", nil)
	if err != nil {
		t.Fatalf("kỳ vọng Fallback thành công, nhận lỗi: %v", err)
	}

	if len(events) != 1 {
		t.Fatalf("kỳ vọng 1 event từ Fallback, nhận được %d", len(events))
	}

	if events[0].Source != "tomtom" {
		t.Errorf("kỳ vọng Source = 'tomtom' (fallback), nhận được '%s'", events[0].Source)
	}
}
