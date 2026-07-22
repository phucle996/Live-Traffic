// ==============================================================================
// Health & Status Probe Handlers (internal/health/health.go)
// Liveness & Readiness Probes for Kubernetes / Cloud-Native Orchestration
// ==============================================================================

package health

import (
	"encoding/json"
	"net/http"

	"go-traffic/internal/budget"
	"go-traffic/internal/kafka"
)

// Server quản lý các HTTP healthcheck probe endpoints
type Server struct {
	budgetTracker *budget.BudgetTracker
	producer      *kafka.Producer
}

// NewServer khởi tạo Server health probes
func NewServer(bt *budget.BudgetTracker, kp *kafka.Producer) *Server {
	return &Server{
		budgetTracker: bt,
		producer:      kp,
	}
}

// HandleLiveness Liveness Probe (Trả về 200 OK nếu process đang sống)
func (s *Server) HandleLiveness(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{
		"status":  "UP",
		"service": "go-traffic-collector",
	})
}

// HandleReadiness Readiness Probe (Trả về 200 OK khi dịch vụ đã sẵn sàng)
func (s *Server) HandleReadiness(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]interface{}{
		"status": "READY",
		"ready":  true,
	})
}

// HandleStatus Trả về thống kê hạn ngạch Budget sử dụng và Dead Letter Queue
func (s *Server) HandleStatus(w http.ResponseWriter, r *http.Request) {
	used, limit := s.budgetTracker.GetStats()
	dlqCount := s.producer.GetDLQStats()

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]interface{}{
		"service":             "go-traffic-collector",
		"daily_budget_used":   used,
		"daily_budget_limit":  limit,
		"dead_letter_count":   dlqCount,
		"status":              "ACTIVE",
	})
}
