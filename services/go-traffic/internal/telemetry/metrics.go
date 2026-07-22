// ==============================================================================
// Go Prometheus Metrics Manager (services/go-traffic/internal/telemetry/metrics.go)
// Khởi tạo Registry và phơi bày toàn bộ counters, gauges, histograms cho Prometheus Scraper
// ==============================================================================

package telemetry

import (
	"net/http"
	"sync"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

var (
	once sync.Once

	// --- Collector Metrics ---
	TomTomRequestsTotal = prometheus.NewCounter(prometheus.CounterOpts{
		Name: "tomtom_requests_total",
		Help: "Tổng số HTTP request đã gửi tới TomTom Traffic API",
	})

	TomTomErrorsTotal = prometheus.NewCounter(prometheus.CounterOpts{
		Name: "tomtom_errors_total",
		Help: "Tổng số HTTP lỗi khi gọi TomTom Traffic API",
	})

	TomTomRateLimitTotal = prometheus.NewCounter(prometheus.CounterOpts{
		Name: "tomtom_rate_limit_total",
		Help: "Tổng số lần bị TomTom API rate limit (429)",
	})

	CollectorBatchesTotal = prometheus.NewCounter(prometheus.CounterOpts{
		Name: "collector_batches_total",
		Help: "Tổng số batch thu thập dữ liệu đã hoàn thành",
	})

	CollectorEventsTotal = prometheus.NewCounter(prometheus.CounterOpts{
		Name: "collector_events_total",
		Help: "Tổng số sự kiện giao thông đã thu thập thành công",
	})

	KafkaProduceErrorsTotal = prometheus.NewCounter(prometheus.CounterOpts{
		Name: "kafka_produce_errors_total",
		Help: "Tổng số lỗi khi gửi message tới Kafka topic",
	})

	// --- Generic Traffic Provider Metrics (HERE, TomTom, etc.) ---
	ProviderRequestsTotal = prometheus.NewCounterVec(prometheus.CounterOpts{
		Name: "traffic_provider_requests_total",
		Help: "Tổng số HTTP request đã gửi tới traffic provider",
	}, []string{"provider"})

	ProviderErrorsTotal = prometheus.NewCounterVec(prometheus.CounterOpts{
		Name: "traffic_provider_errors_total",
		Help: "Tổng số HTTP lỗi khi gọi traffic provider",
	}, []string{"provider"})

	ProviderRequestDurationSeconds = prometheus.NewHistogramVec(prometheus.HistogramOpts{
		Name:    "traffic_provider_request_duration_seconds",
		Help:    "Thời gian phản hồi HTTP request từ provider (giây)",
		Buckets: prometheus.DefBuckets,
	}, []string{"provider"})

	ProviderItemsTotal = prometheus.NewCounterVec(prometheus.CounterOpts{
		Name: "traffic_provider_items_total",
		Help: "Tổng số flow items nhận được từ provider",
	}, []string{"provider"})

	ProviderRateLimitedTotal = prometheus.NewCounterVec(prometheus.CounterOpts{
		Name: "traffic_provider_rate_limited_total",
		Help: "Tổng số lần bị provider rate limit (HTTP 429)",
	}, []string{"provider"})

	// --- Coverage Cell Overdue Metrics (Phase R5) ---
	CellOverdueTotal = prometheus.NewCounterVec(prometheus.CounterOpts{
		Name: "coverage_cell_overdue_total",
		Help: "Tổng số lần ô lưới (cell) bị trễ thời điểm polling theo lịch",
	}, []string{"cell_id"})

	CellOverdueSeconds = prometheus.NewGaugeVec(prometheus.GaugeOpts{
		Name: "coverage_cell_overdue_seconds",
		Help: "Số giây bị trễ polling của ô lưới (cell)",
	}, []string{"cell_id"})

	// --- Live API Metrics ---
	LiveCacheAgeSeconds = prometheus.NewGauge(prometheus.GaugeOpts{
		Name: "live_cache_age_seconds",
		Help: "Số giây tính từ lần cập nhật dữ liệu giao thông gần nhất (Data Freshness)",
	})
)

// RegisterMetrics khởi tạo và đăng ký tất cả các Prometheus metrics vào default registry.
func RegisterMetrics() {
	once.Do(func() {
		prometheus.MustRegister(
			TomTomRequestsTotal,
			TomTomErrorsTotal,
			TomTomRateLimitTotal,
			CollectorBatchesTotal,
			CollectorEventsTotal,
			KafkaProduceErrorsTotal,
			ProviderRequestsTotal,
			ProviderErrorsTotal,
			ProviderRequestDurationSeconds,
			ProviderItemsTotal,
			ProviderRateLimitedTotal,
			CellOverdueTotal,
			CellOverdueSeconds,
			LiveCacheAgeSeconds,
		)
	})
}

// NewMetricsHandler trả về HTTP handler cho Prometheus Scraper (GET /metrics).
func NewMetricsHandler() http.Handler {
	return promhttp.Handler()
}
