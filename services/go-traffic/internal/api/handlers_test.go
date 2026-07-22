// ==============================================================================
// Live API Handlers Unit Tests (internal/api/handlers_test.go)
// Verifies GET /v1/traffic/live, ETag 304 Not Modified, and Source Status
// ==============================================================================

package api

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"go-traffic/internal/budget"
	"go-traffic/internal/contract"
	"go-traffic/internal/retry"
	"go-traffic/internal/store"
)

func TestLiveAPIEndpoints(t *testing.T) {
	st := store.NewStateStore()
	bt := budget.NewBudgetTracker(2500)
	cb := retry.NewCircuitBreaker(5, 30)

	srv := NewServer(st, bt, cb)

	// Thêm 1 bản ghi mẫu vào StateStore
	evt := contract.NewTrafficEvent(
		"loc-01", "Nam Kỳ Khởi Nghĩa", "Quận 3",
		10.7781, 106.6952, 25.0, 45.0, 0.95,
		"2026-07-21T20:30:00Z", "tomtom_live", "batch-1",
	)
	st.Update(evt)

	// Test GET /health/live
	reqLive := httptest.NewRequest(http.MethodGet, "/health/live", nil)
	wLive := httptest.NewRecorder()
	srv.HandleLiveness(wLive, reqLive)
	if wLive.Code != http.StatusOK {
		t.Errorf("HandleLiveness trả về code %d, mong đợi 200", wLive.Code)
	}

	// Test GET /v1/traffic/live
	reqData := httptest.NewRequest(http.MethodGet, "/v1/traffic/live", nil)
	wData := httptest.NewRecorder()
	srv.HandleGetLiveTraffic(wData, reqData)

	if wData.Code != http.StatusOK {
		t.Errorf("HandleGetLiveTraffic trả về code %d, mong đợi 200", wData.Code)
	}

	etag := wData.Header().Get("ETag")
	if len(etag) == 0 {
		t.Errorf("Header ETag phải tồn tại!")
	}

	// Test Conditional GET (304 Not Modified)
	reqConditional := httptest.NewRequest(http.MethodGet, "/v1/traffic/live", nil)
	reqConditional.Header.Set("If-None-Match", etag)
	wConditional := httptest.NewRecorder()
	srv.HandleGetLiveTraffic(wConditional, reqConditional)

	if wConditional.Code != http.StatusNotModified {
		t.Errorf("Conditional GET phải trả về 304 Not Modified. Thu được: %d", wConditional.Code)
	}

	// Test GET /v1/source/status
	reqStatus := httptest.NewRequest(http.MethodGet, "/v1/source/status", nil)
	wStatus := httptest.NewRecorder()
	srv.HandleGetSourceStatus(wStatus, reqStatus)

	if wStatus.Code != http.StatusOK {
		t.Errorf("HandleGetSourceStatus trả về code %d, mong đợi 200", wStatus.Code)
	}

	var statusResp map[string]interface{}
	json.NewDecoder(wStatus.Body).Decode(&statusResp)
	if statusResp["active_source_mode"] != "tomtom_live" {
		t.Errorf("active_source_mode phải là tomtom_live!")
	}
}
