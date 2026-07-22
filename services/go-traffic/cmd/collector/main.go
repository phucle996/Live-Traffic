// ==============================================================================
// Go TomTom Collector Main Entrypoint (cmd/collector/main.go)
// High-Performance Cloud-Native Traffic Data Collector Microservice
// ==============================================================================

package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"go-traffic/internal/budget"
	"go-traffic/internal/collector"
	"go-traffic/internal/config"
	"go-traffic/internal/health"
	"go-traffic/internal/kafka"
	"go-traffic/internal/retry"
	"go-traffic/internal/source"
	"go-traffic/internal/telemetry"
	"go-traffic/internal/tomtom"
)

func main() {
	log.Println("======================================================================")
	log.Println("             STARTING GO TOMTOM TRAFFIC COLLECTOR SERVICE             ")
	log.Println("======================================================================")

	// 1. Nạp cấu hình từ biến môi trường
	cfg := config.LoadConfig()
	log.Printf("[CONFIG] Ingestion Mode: %s | Workers: %d | Budget Limit: %d reqs/day",
		cfg.IngestionMode, cfg.WorkerPoolSize, cfg.DailyBudgetLimit)
	log.Printf("[CONFIG] TomTom Key: %s | Kafka Brokers: %v | Topic: %s",
		config.MaskAPIKey(cfg.TomTomAPIKey), cfg.KafkaBootstrapServers, cfg.KafkaTopic)

	// 2. Khởi tạo các thành phần cốt lõi
	budgetTracker := budget.NewBudgetTracker(cfg.DailyBudgetLimit)
	circuitBreaker := retry.NewCircuitBreaker(5, 30*time.Second)
	tomtomClient := tomtom.NewClient(cfg.TomTomAPIKey)

	sourceRouter, err := source.NewRouter(
		tomtomClient, budgetTracker, circuitBreaker,
		cfg.SeedFolderPath, cfg.IngestionMode,
	)
	if err != nil {
		log.Printf("[WARNING] Lỗi khởi tạo SourceRouter: %v", err)
	}

	kafkaProducer := kafka.NewProducer(cfg.KafkaBootstrapServers, cfg.KafkaTopic)
	workerEngine := collector.NewEngine(sourceRouter, cfg.WorkerPoolSize)
	healthServer := health.NewServer(budgetTracker, kafkaProducer)

	// 3. Khởi chạy HTTP Health Probe Server trong Goroutine riêng
	// Đăng ký Prometheus Metrics Registry trước khi khởi động server
	telemetry.RegisterMetrics()

	mux := http.NewServeMux()
	mux.HandleFunc("/health/live", healthServer.HandleLiveness)
	mux.HandleFunc("/health/ready", healthServer.HandleReadiness)
	mux.HandleFunc("/v1/status", healthServer.HandleStatus)
	// Phơi bày Prometheus metrics endpoint cho Prometheus Scraper
	mux.Handle("/metrics", telemetry.NewMetricsHandler())

	httpAddr := fmt.Sprintf(":%s", cfg.HTTPPort)
	srv := &http.Server{
		Addr:    httpAddr,
		Handler: mux,
	}

	go func() {
		log.Printf("[HTTP SERVER] Listening for health probes on http://0.0.0.0%s", httpAddr)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("Lỗi khởi chạy HTTP Health Server: %v", err)
		}
	}()

	// 4. Danh sách các tuyến đường tọa độ mẫu tại TP.HCM
	locations := []source.LocationPoint{
		{ID: "loc-01", Name: "Nam Kỳ Khởi Nghĩa", District: "Quận 3", Latitude: 10.7781, Longitude: 106.6952, FFSpeed: 45.0},
		{ID: "loc-02", Name: "Điện Biên Phủ", District: "Bình Thạnh", Latitude: 10.7983, Longitude: 106.7115, FFSpeed: 50.0},
		{ID: "loc-03", Name: "Võ Thị Sáu", District: "Quận 3", Latitude: 10.7852, Longitude: 106.6908, FFSpeed: 40.0},
		{ID: "loc-04", Name: "Nguyễn Thị Minh Khai", District: "Quận 1", Latitude: 10.7745, Longitude: 106.6931, FFSpeed: 45.0},
		{ID: "loc-05", Name: "Cách Mạng Tháng 8", District: "Quận 10", Latitude: 10.7798, Longitude: 106.6784, FFSpeed: 40.0},
		{ID: "loc-06", Name: "Xa Lộ Hà Nội", District: "TP. Thủ Đức", Latitude: 10.8450, Longitude: 106.7700, FFSpeed: 60.0},
		{ID: "loc-07", Name: "Phạm Văn Đồng", District: "Gò Vấp", Latitude: 10.8220, Longitude: 106.6870, FFSpeed: 60.0},
		{ID: "loc-08", Name: "Nguyễn Văn Linh", District: "Quận 7", Latitude: 10.7290, Longitude: 106.7150, FFSpeed: 55.0},
	}

	// 5. Khởi chạy Polling Crawling Engine (Chu kỳ 30s)
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	// Crawl lượt đầu tiên ngay khi startup
	go func() {
		ctx := context.Background()
		log.Printf("[INGESTION RUN] Starting initial crawling for %d HCMC locations...", len(locations))
		events := workerEngine.CrawlLocations(ctx, locations)
		success, fail := kafkaProducer.PublishBatch(events)
		log.Printf("[INGESTION COMPLETE] Initial run complete! Kafka Ack Success: %d, Fail/DLQ: %d", success, fail)
	}()

	// 6. Lắng nghe tín hiệu dừng SIGINT / SIGTERM cho Graceful Shutdown
	stop := make(chan os.Signal, 1)
	signal.Notify(stop, syscall.SIGINT, syscall.SIGTERM)

	select {
	case sig := <-stop:
		log.Printf("[SHUTDOWN] Nhận tín hiệu os.Signal '%v'. Tiến hành Graceful Shutdown...", sig)
	}

	// Đóng HTTP Server an toàn
	ctxShutdown, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := srv.Shutdown(ctxShutdown); err != nil {
		log.Printf("[WARNING] Lỗi khi shutdown HTTP server: %v", err)
	}

	log.Println("[SUCCESS] Go TomTom Traffic Collector Service shut down safely.")
}
