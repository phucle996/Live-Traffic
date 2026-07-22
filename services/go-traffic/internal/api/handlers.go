// ==============================================================================
// Live Traffic HTTP API Handlers (internal/api/handlers.go)
// Serving Real-Time Traffic Data directly from Latest State Store with ETag & Freshness
// ==============================================================================

package api

import (
	"encoding/json"
	"net/http"
	"strings"

	"go-traffic/internal/budget"
	"go-traffic/internal/retry"
	"go-traffic/internal/store"
)

// Server đại diện cho HTTP Live API Server
type Server struct {
	stateStore     *store.StateStore
	budgetTracker  *budget.BudgetTracker
	circuitBreaker *retry.CircuitBreaker
}

// NewServer khởi tạo Server HTTP Handlers
func NewServer(st *store.StateStore, bt *budget.BudgetTracker, cb *retry.CircuitBreaker) *Server {
	return &Server{
		stateStore:     st,
		budgetTracker:  bt,
		circuitBreaker: cb,
	}
}

// HandleLiveness Liveness Probe GET /health/live
func (s *Server) HandleLiveness(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{
		"service": "go-live-traffic-api",
		"status":  "UP",
	})
}

// HandleReadiness Readiness Probe GET /health/ready
func (s *Server) HandleReadiness(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]interface{}{
		"service": "go-live-traffic-api",
		"status":  "READY",
		"ready":   true,
	})
}

// HandleGetLiveTraffic GET /v1/traffic/live (Trả về trạng thái tất cả vị trí từ StateStore)
func (s *Server) HandleGetLiveTraffic(w http.ResponseWriter, r *http.Request) {
	etag := s.stateStore.ComputeETag()

	// Kiểm tra Conditional GET (If-None-Match header)
	if match := r.Header.Get("If-None-Match"); match != "" && match == etag {
		w.WriteHeader(http.StatusNotModified) // 304 Not Modified
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Cache-Control", "public, max-age=15")
	w.Header().Set("ETag", etag)
	w.WriteHeader(http.StatusOK)

	records := s.stateStore.GetAll()
	json.NewEncoder(w).Encode(map[string]interface{}{
		"count":         len(records),
		"traffic_data":  records,
		"served_from":   "latest_state_store",
		"cache_control": "15_seconds",
	})
}

// HandleGetLiveTrafficByLocation GET /v1/traffic/live/{location_id} (Trả về 1 vị trí)
func (s *Server) HandleGetLiveTrafficByLocation(w http.ResponseWriter, r *http.Request) {
	// Parse location_id từ URL path
	path := strings.TrimPrefix(r.URL.Path, "/v1/traffic/live/")
	locationID := strings.TrimSpace(path)

	if locationID == "" {
		s.HandleGetLiveTraffic(w, r)
		return
	}

	rec, exists := s.stateStore.GetByLocationID(locationID)
	if !exists {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusNotFound)
		json.NewEncoder(w).Encode(map[string]string{
			"error":       "Location ID không tồn tại",
			"location_id": locationID,
		})
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Cache-Control", "public, max-age=15")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(rec)
}

// HandleGetSourceStatus GET /v1/source/status (Báo cáo trạng thái nguồn dữ liệu & Data Freshness)
func (s *Server) HandleGetSourceStatus(w http.ResponseWriter, r *http.Request) {
	records := s.stateStore.GetAll()

	tomtomCount := 0
	offlineCount := 0
	maxAge := int64(0)

	for _, rec := range records {
		if rec.Source == "tomtom_live" {
			tomtomCount++
		} else {
			offlineCount++
		}
		if rec.DataAgeSeconds > maxAge {
			maxAge = rec.DataAgeSeconds
		}
	}

	activeMode := "tomtom_live"
	if offlineCount > 0 && tomtomCount == 0 {
		activeMode = "lab_offline_fallback"
	} else if offlineCount > 0 && tomtomCount > 0 {
		activeMode = "hybrid"
	}

	used, limit := s.budgetTracker.GetStats()

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]interface{}{
		"active_source_mode":   activeMode,
		"total_locations":     len(records),
		"tomtom_live_count":   tomtomCount,
		"offline_seed_count":  offlineCount,
		"max_data_age_seconds": maxAge,
		"daily_budget_used":   used,
		"daily_budget_limit":  limit,
	})
}
