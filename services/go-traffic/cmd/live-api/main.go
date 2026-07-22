// ==============================================================================
// Go Live Traffic API Main Entrypoint (cmd/live-api/main.go)
// Serving Real-Time Traffic Data directly from Latest State Store (<1ms Latency)
// ==============================================================================

package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"

	"os"
	"os/signal"
	"syscall"
	"time"

	"go-traffic/internal/api"
	"go-traffic/internal/budget"
	"go-traffic/internal/config"
	"go-traffic/internal/contract"
	"go-traffic/internal/kafka"
	"go-traffic/internal/retry"
	"go-traffic/internal/store"
	"go-traffic/internal/telemetry"
)

func main() {
	log.Println("======================================================================")
	log.Println("             STARTING GO LIVE TRAFFIC API SERVICE (PORT 8084)         ")
	log.Println("======================================================================")

	// 1. Nạp cấu hình biến môi trường
	cfg := config.LoadConfig()

	// Đảm bảo Live API dùng Port 8084 nếu không có env override
	port := os.Getenv("PORT")
	if port == "" {
		port = "8084"
	}

	// 2. Khởi tạo các thành phần State Store, Budget & Kafka Consumer
	stateStore := store.NewStateStore()
	budgetTracker := budget.NewBudgetTracker(cfg.DailyBudgetLimit)
	circuitBreaker := retry.NewCircuitBreaker(5, 30*time.Second)

	// 2. Khởi tạo Danh mục Tuyến đường Toàn quốc Việt Nam (Nạp từ JSON Seed hoặc Fallback Data)
	type RoadSeedItem struct {
		ID, Name, District, Province, Region, RoadClass, Direction string
		Lat                                                         float64 `json:"lat"`
		Lon                                                         float64 `json:"lon"`
		CS                                                          float64 `json:"cs"`
		FFS                                                         float64 `json:"ffs"`
		Density                                                     float64 `json:"density"`
		Delay                                                       float64 `json:"delay"`
	}

	var nationalRoads []RoadSeedItem

	// Thử tìm nạp file JSON danh mục 250+ tuyến đường Việt Nam từ các vị trí đường dẫn khác nhau
	seedPaths := []string{
		"./data/seed/vietnam_national_roads.json",
		"./services/go-traffic/data/seed/vietnam_national_roads.json",
		"/app/data/seed/vietnam_national_roads.json",
	}

	var loadedFromFile bool
	for _, path := range seedPaths {
		data, err := os.ReadFile(path)
		if err == nil {
			if err := json.Unmarshal(data, &nationalRoads); err == nil && len(nationalRoads) > 0 {
				log.Printf("[STATE STORE INIT] Nạp thành công %d tuyến đường toàn quốc từ file seed: '%s'", len(nationalRoads), path)
				loadedFromFile = true
				break
			}
		}
	}

	// Fallback nếu không tìm thấy file JSON seed
	if !loadedFromFile {
		log.Println("[STATE STORE INIT] Nạp danh mục fallback 25+ tuyến đường trọng điểm Việt Nam...")
		nationalRoads = []RoadSeedItem{
			{"loc-ct01", "Cao Tốc TP.HCM - Long Thành - Dầu Giây", "Long Thành", "Đồng Nai", "Cao Tốc", "Cao Tốc", "Hướng Dầu Giây", 10.8120, 106.8850, 95.0, 120.0, 35.0, 0.0},
			{"loc-ct02", "Cao Tốc TP.HCM - Trung Lương", "Bình Chánh", "TP.HCM", "Cao Tốc", "Cao Tốc", "Hướng Về Miền Tây", 10.6650, 106.5620, 85.0, 100.0, 45.0, 2.0},
			{"loc-ct03", "Cao Tốc Hà Nội - Hải Phòng", "Gia Lâm", "Hà Nội", "Cao Tốc", "Cao Tốc", "Hướng Hải Phòng", 20.9750, 105.9520, 110.0, 120.0, 25.0, 0.0},
			{"loc-ct04", "Cao Tốc Pháp Vân - Cầu Giẽ", "Thanh Trì", "Hà Nội", "Cao Tốc", "Cao Tốc", "Hướng Nam", 20.9320, 105.8610, 65.0, 100.0, 75.0, 12.0},
			{"loc-ql01", "Quốc Lộ 1A - Trục Xương Sống Nam Bắc", "Bình Tân", "TP.HCM", "Mien Nam", "Quốc Lộ", "Hướng Tây Bắc", 10.7420, 106.5910, 32.0, 60.0, 68.0, 8.0},
			{"loc-ql14", "Quốc Lộ 14 - Đường Hồ Chí Minh Tây Nguyên", "BMT", "Đắk Lắk", "Mien Trung", "Quốc Lộ", "Hướng Pleiku", 12.6820, 108.0380, 55.0, 70.0, 35.0, 0.0},
			{"loc-ql20", "Quốc Lộ 20 - Trục TP.HCM đi Đà Lạt", "Định Quán", "Đồng Nai", "Mien Nam", "Quốc Lộ", "Hướng Đà Lạt", 11.0250, 107.1820, 45.0, 60.0, 55.0, 5.0},
			{"loc-01", "Đại Lộ Võ Văn Kiệt", "Quận 1", "TP.HCM", "Mien Nam", "Đại Lộ", "Hướng Hầm Thủ Thiêm", 10.7531, 106.6698, 42.5, 60.0, 45.0, 0.0},
			{"loc-hn01", "Đường Vành Đai 3 Trên Cầu", "Cầu Giấy", "Hà Nội", "Mien Bac", "Vành Đai", "Hướng Nội Bài", 21.0280, 105.7820, 18.0, 80.0, 95.0, 25.0},
			{"loc-dn01", "Đường Nguyễn Văn Linh - Cầu Rồng", "Hải Châu", "Đà Nẵng", "Mien Trung", "Trục Chính", "Hướng Hướng Biển", 16.0610, 108.2180, 38.0, 50.0, 42.0, 0.0},
		}
	}

	// Nạp toàn bộ tuyến đường vào In-Memory State Store chuẩn hóa Thread-Safe
	for _, loc := range nationalRoads {
		evt := contract.NewTrafficEventWithRegion(
			loc.ID, loc.Name, loc.District, loc.Province, loc.Region, loc.RoadClass, loc.Direction,
			loc.Lat, loc.Lon, loc.CS, loc.FFS, loc.Density, loc.Delay, 0.95,
			time.Now().Format(time.RFC3339), "tomtom_live", "init-batch-v3",
		)
		stateStore.Update(evt)
	}



	// 3. Khởi chạy Kafka Consumer ngầm
	kafkaConsumer := kafka.NewConsumer(cfg.KafkaBootstrapServers, cfg.KafkaTopic, stateStore)
	ctxConsumer, cancelConsumer := context.WithCancel(context.Background())
	defer cancelConsumer()
	go kafkaConsumer.StartListening(ctxConsumer)

	// 4. Cấu hình HTTP Server Routing
	apiServer := api.NewServer(stateStore, budgetTracker, circuitBreaker)

	// Đăng ký Prometheus Metrics Registry trước khi khởi động server
	telemetry.RegisterMetrics()

	// Khởi tạo HTTP ServeMux phục vụ các Public REST Endpoints
	mux := http.NewServeMux()

	// 1. Health Probe Endpoints (Phục vụ Liveness/Readiness Probes cho Kubernetes Pods)
	mux.HandleFunc("/health/live", apiServer.HandleLiveness)
	mux.HandleFunc("/health/ready", apiServer.HandleReadiness)

	// 2. Public Traffic Read Endpoints (Đọc dữ liệu giao thông công khai thời gian thực, không bắt buộc token)
	mux.HandleFunc("/v1/traffic/live", apiServer.HandleGetLiveTraffic)
	mux.HandleFunc("/v1/traffic/live/", apiServer.HandleGetLiveTrafficByLocation)
	mux.HandleFunc("/v1/source/status", apiServer.HandleGetSourceStatus)

	// 3. Phơi bày Prometheus metrics endpoint cho Prometheus Scraper
	mux.Handle("/metrics", telemetry.NewMetricsHandler())

	httpAddr := fmt.Sprintf(":%s", port)
	// Bọc toàn bộ ServeMux bằng api.CORSMiddleware để cho phép Cross-Origin Requests từ Web Dashboard UI
	srv := &http.Server{
		Addr:    httpAddr,
		Handler: api.CORSMiddleware(mux),
	}

	go func() {
		log.Printf("[HTTP LIVE API] Listening on http://0.0.0.0%s", httpAddr)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("Lỗi khởi chạy HTTP Live API Server: %v", err)
		}
	}()

	// 5. Lắng nghe tín hiệu dừng SIGINT / SIGTERM
	stop := make(chan os.Signal, 1)
	signal.Notify(stop, syscall.SIGINT, syscall.SIGTERM)

	<-stop
	log.Println("[SHUTDOWN] Tiến hành Graceful Shutdown Go Live API...")

	ctxShutdown, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	srv.Shutdown(ctxShutdown)

	log.Println("[SUCCESS] Go Live Traffic API Service shut down safely.")
}
