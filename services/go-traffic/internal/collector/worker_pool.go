// ==============================================================================
// Bounded Worker Pool Crawling Engine (internal/collector/worker_pool.go)
// Fan-Out Concurrent Location Fetcher without Goroutine Leaks
// ==============================================================================

package collector

import (
	"context"
	"fmt"
	"sync"
	"time"

	"go-traffic/internal/contract"
	"go-traffic/internal/source"
)

// Engine quản lý Bounded Worker Pool để thu thập dữ liệu giao thông cho danh sách các vị trí
type Engine struct {
	router     *source.Router
	numWorkers int
}

// NewEngine khởi tạo Engine với số lượng Worker cố định
func NewEngine(router *source.Router, numWorkers int) *Engine {
	if numWorkers <= 0 {
		numWorkers = 5
	}
	return &Engine{
		router:     router,
		numWorkers: numWorkers,
	}
}

// CrawlLocations Thực thi thu thập dữ liệu giao thông song song bằng Worker Pool
func (e *Engine) CrawlLocations(ctx context.Context, locations []source.LocationPoint) []contract.TrafficEvent {
	batchID := fmt.Sprintf("batch-%d", time.Now().Unix())
	numJobs := len(locations)

	jobs := make(chan source.LocationPoint, numJobs)
	results := make(chan contract.TrafficEvent, numJobs)

	var wg sync.WaitGroup

	// Khởi tạo cố định N Worker Goroutines (Bounded Worker Pool)
	for w := 1; w <= e.numWorkers; w++ {
		wg.Add(1)
		go func(workerID int) {
			defer wg.Done()
			for loc := range jobs {
				evt := e.router.FetchEventForLocation(ctx, loc, batchID)
				results <- evt
			}
		}(w)
	}

	// Đẩy các công việc thu thập vào channel jobs
	for _, loc := range locations {
		jobs <- loc
	}
	close(jobs)

	// Đợi tất cả workers hoàn thành công việc
	wg.Wait()
	close(results)

	// Gom kết quả sự kiện trả về
	var events []contract.TrafficEvent
	for evt := range results {
		events = append(events, evt)
	}

	return events
}
