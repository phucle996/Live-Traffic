// ==============================================================================
// Provider Router (internal/provider/router.go)
// Phase HERE-1 — Điều phối Primary & Fallback Provider thông qua TrafficProvider interface.
// Không chứa logic rẽ nhánh cứng (if provider == "here") trong code nghiệp vụ.
// ==============================================================================

package provider

import (
	"context"
	"fmt"
	"log"
	"sync"
	"time"

	"go-traffic/internal/contract"
)

// RouterConfig chứa tham số điều khiển router nguồn dữ liệu
type RouterConfig struct {
	PrimaryProvider  string // e.g. "here", "tomtom", "offline"
	FallbackProvider string // e.g. "tomtom", "offline"
	Mode             string // "primary_fallback" | "single" | "auto"
}

// Router quản lý các provider và thực hiện chuyển đổi tự động khi Primary gặp sự cố
type Router struct {
	registry *Registry
	cfg      RouterConfig
	mu       sync.RWMutex
}

// NewRouter khởi tạo Router từ Registry và RouterConfig
func NewRouter(registry *Registry, cfg RouterConfig) *Router {
	// Gán mặc định nếu không truyền mode
	if cfg.Mode == "" {
		cfg.Mode = "primary_fallback"
	}
	if cfg.PrimaryProvider == "" {
		cfg.PrimaryProvider = "tomtom"
	}
	if cfg.FallbackProvider == "" {
		cfg.FallbackProvider = "offline"
	}

	return &Router{
		registry: registry,
		cfg:      cfg,
	}
}

// FetchTrafficEvents thu thập dữ liệu giao thông cho 1 QueryArea và trả về TrafficEvent slice đã normalize cho Kafka contract
func (r *Router) FetchTrafficEvents(ctx context.Context, area QueryArea, batchID string, locationMeta map[string]string) ([]contract.TrafficEvent, error) {
	r.mu.RLock()
	primaryName := r.cfg.PrimaryProvider
	fallbackName := r.cfg.FallbackProvider
	mode := r.cfg.Mode
	r.mu.RUnlock()

	// 1. Lấy Primary Provider từ Registry
	primary, err := r.registry.Get(primaryName)
	if err == nil {
		// Thử thu thập dữ liệu từ Primary Provider
		obsList, errFetch := primary.FetchFlow(ctx, area)
		if errFetch == nil && len(obsList) > 0 {
			// Thu thập thành công từ Primary -> chuyển đổi sang contract.TrafficEvent
			return r.mapToTrafficEvents(obsList, batchID, locationMeta), nil
		}

		log.Printf("[ROUTER WARN] Primary provider '%s' thất bại: %v. Kiểm tra chuyển đổi sang Fallback...", primaryName, errFetch)
	} else {
		log.Printf("[ROUTER WARN] Không tìm thấy Primary provider '%s': %v", primaryName, err)
	}

	// Nếu cấu hình chỉ chạy "single" mode -> dừng lại không chuyển sang fallback
	if mode == "single" {
		return nil, fmt.Errorf("Primary provider '%s' thất bại và mode được đặt là 'single'", primaryName)
	}

	// 2. Chuyển sang Fallback Provider
	fallback, errFb := r.registry.Get(fallbackName)
	if errFb != nil {
		return nil, fmt.Errorf("cả Primary ('%s') và Fallback ('%s') đều không khả dụng: %w", primaryName, fallbackName, errFb)
	}

	log.Printf("[ROUTER INFO] Đang sử dụng Fallback provider '%s'", fallbackName)
	obsList, errFbFetch := fallback.FetchFlow(ctx, area)
	if errFbFetch != nil {
		return nil, fmt.Errorf("Fallback provider '%s' cũng gặp lỗi: %w", fallbackName, errFbFetch)
	}

	// Đánh dấu fallback_used = true trong mọi record
	for i := range obsList {
		obsList[i].FallbackUsed = true
		obsList[i].FallbackReason = fmt.Sprintf("Primary '%s' failed", primaryName)
	}

	return r.mapToTrafficEvents(obsList, batchID, locationMeta), nil
}

// mapToTrafficEvents chuyển đổi danh sách FlowObservation sang contract.TrafficEvent của hệ thống
func (r *Router) mapToTrafficEvents(obsList []FlowObservation, batchID string, locationMeta map[string]string) []contract.TrafficEvent {
	events := make([]contract.TrafficEvent, 0, len(obsList))

	for _, obs := range obsList {
		locID := locationMeta["id"]
		if locID == "" {
			locID = obs.ProviderSegmentID
		}
		locName := locationMeta["name"]
		if locName == "" {
			locName = fmt.Sprintf("Segment %.4f,%.4f", obs.Latitude, obs.Longitude)
		}
		district := locationMeta["district"]
		if district == "" {
			district = "Unknown District"
		}

		eventTime := obs.ProviderObservedAt
		if eventTime == "" {
			eventTime = time.Now().UTC().Format(time.RFC3339)
		}

		evt := contract.NewTrafficEvent(
			locID, locName, district,
			obs.Latitude, obs.Longitude,
			obs.CurrentSpeedKPH, obs.FreeFlowSpeedKPH,
			obs.Confidence,
			eventTime,
			obs.Provider,
			batchID,
		)

		events = append(events, evt)
	}

	return events
}
