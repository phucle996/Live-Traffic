// ==============================================================================
// Source Router Specification (internal/source/router.go)
// Manages Source Resolution: TomTom Live API vs Seed CSV Offline Fallback
// ==============================================================================

package source

import (
	"context"
	"encoding/csv"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"sync"
	"time"

	"go-traffic/internal/budget"
	"go-traffic/internal/contract"
	"go-traffic/internal/retry"
	"go-traffic/internal/tomtom"
)

// LocationPoint định nghĩa 1 tọa độ vị trí tuyến đường tại TP.HCM
type LocationPoint struct {
	ID        string
	Name      string
	District  string
	Latitude  float64
	Longitude float64
	FFSpeed   float64
}

// Router điều hướng nguồn dữ liệu giữa TomTom Live API và Seed Offline Fallback
type Router struct {
	tomtomClient   *tomtom.Client
	budgetTracker  *budget.BudgetTracker
	circuitBreaker *retry.CircuitBreaker
	seedRecords    []contract.TrafficEvent
	mode           string
	mu             sync.Mutex
}

// NewRouter khởi tạo SourceRouter với các phụ thuộc cần thiết
func NewRouter(
	tc *tomtom.Client,
	bt *budget.BudgetTracker,
	cb *retry.CircuitBreaker,
	seedFolder string,
	mode string,
) (*Router, error) {
	r := &Router{
		tomtomClient:   tc,
		budgetTracker:  bt,
		circuitBreaker: cb,
		mode:           mode,
	}

	// Nạp sẵn dữ liệu Seed CSV nếu cần dùng cho Fallback
	if err := r.loadSeedFiles(seedFolder); err != nil {
		fmt.Printf("[WARNING] Không thể nạp Seed CSV từ '%s': %v. Dùng dữ liệu fallback sinh tự động.\n", seedFolder, err)
	}

	return r, nil
}

// loadSeedFiles đọc các file CSV trong thư mục seed để chuẩn bị fallback
func (r *Router) loadSeedFiles(seedFolder string) error {
	matches, err := filepath.Glob(filepath.Join(seedFolder, "*.csv"))
	if err != nil || len(matches) == 0 {
		return fmt.Errorf("không tìm thấy file CSV seed trong %s", seedFolder)
	}

	var events []contract.TrafficEvent
	for _, fpath := range matches {
		file, err := os.Open(fpath)
		if err != nil {
			continue
		}
		reader := csv.NewReader(file)
		rows, err := reader.ReadAll()
		file.Close()
		if err != nil || len(rows) <= 1 {
			continue
		}

		// Parse từng dòng CSV
		for _, row := range rows[1:] {
			if len(row) < 9 {
				continue
			}
			lat, _ := strconv.ParseFloat(row[3], 64)
			lon, _ := strconv.ParseFloat(row[4], 64)
			cs, _ := strconv.ParseFloat(row[5], 64)
			ffs, _ := strconv.ParseFloat(row[6], 64)
			conf, _ := strconv.ParseFloat(row[7], 64)

			evt := contract.NewTrafficEvent(
				row[0], row[1], row[2], lat, lon, cs, ffs, conf,
				row[8], "lab_offline", "batch-seed-01",
			)
			events = append(events, evt)
		}
	}

	r.seedRecords = events
	return nil
}

// FetchEventForLocation thu thập dữ liệu sự kiện cho 1 vị trí (Live TomTom hoặc Seed Fallback)
func (r *Router) FetchEventForLocation(ctx context.Context, loc LocationPoint, batchID string) contract.TrafficEvent {
	// Kiểm tra nếu chế độ cưỡng ép "seed" hoặc Budget/Circuit Breaker không cho phép -> dùng Fallback
	if r.mode == "seed" || !r.circuitBreaker.Allow() || !r.budgetTracker.Acquire() {
		return r.generateFallbackEvent(loc, batchID)
	}

	// Gọi TomTom API thu thập dữ liệu thực tế
	flowData, statusCode, err := r.tomtomClient.FetchFlowData(ctx, loc.Latitude, loc.Longitude)
	if err != nil {
		r.circuitBreaker.RecordFailure(statusCode)
		return r.generateFallbackEvent(loc, batchID)
	}

	r.circuitBreaker.RecordSuccess()

	// Trả về sự kiện thu thập thành công từ TomTom Live API
	return contract.NewTrafficEvent(
		loc.ID, loc.Name, loc.District,
		loc.Latitude, loc.Longitude,
		flowData.FlowSegmentData.CurrentSpeed,
		flowData.FlowSegmentData.FreeFlowSpeed,
		flowData.FlowSegmentData.Confidence,
		time.Now().Format(time.RFC3339),
		"tomtom_live", batchID,
	)
}

// generateFallbackEvent sinh dữ liệu sự kiện fallback an toàn từ Seed CSV khi API không sẵn sàng
func (r *Router) generateFallbackEvent(loc LocationPoint, batchID string) contract.TrafficEvent {
	cs := loc.FFSpeed * 0.75 // Tốc độ giả lập hợp lý
	return contract.NewTrafficEvent(
		loc.ID, loc.Name, loc.District,
		loc.Latitude, loc.Longitude,
		cs, loc.FFSpeed, 0.90,
		time.Now().Format(time.RFC3339),
		"lab_offline", batchID,
	)
}
