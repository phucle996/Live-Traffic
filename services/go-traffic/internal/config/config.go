// ==============================================================================
// Configuration Specification (internal/config/config.go)
// Manages Environment Variables, TomTom API Keys, Budget Limits & Kafka Brokers
// ==============================================================================

package config

import (
	"os"
	"strconv"
	"strings"
)

// Config chứa toàn bộ cấu hình hoạt động của Go Collector Microservice
type Config struct {
	TrafficProvider         string
	TrafficFallbackProvider string
	TrafficProviderMode     string
	TomTomAPIKey            string
	HEREAPIKey              string
	KafkaBootstrapServers   []string
	KafkaTopic              string
	DailyBudgetLimit        int64
	PerBatchLimit           int
	WorkerPoolSize          int
	SeedFolderPath          string
	IngestionMode           string
	HTTPPort                string
}

// LoadConfig nạp cấu hình từ biến môi trường với các giá trị mặc định an toàn
func LoadConfig() *Config {
	provider := os.Getenv("TRAFFIC_PROVIDER")
	if provider == "" {
		provider = "tomtom"
	}

	fallbackProvider := os.Getenv("TRAFFIC_FALLBACK_PROVIDER")
	if fallbackProvider == "" {
		fallbackProvider = "offline"
	}

	providerMode := os.Getenv("TRAFFIC_PROVIDER_MODE")
	if providerMode == "" {
		providerMode = "primary_fallback"
	}

	apiKey := os.Getenv("TOMTOM_API_KEY")
	hereKey := os.Getenv("HERE_API_KEY")

	kafkaServersStr := os.Getenv("KAFKA_BOOTSTRAP_SERVERS")
	if kafkaServersStr == "" {
		kafkaServersStr = "localhost:9092,kafka:9092"
	}
	kafkaServers := strings.Split(kafkaServersStr, ",")

	topic := os.Getenv("KAFKA_TOPIC")
	if topic == "" {
		topic = "traffic_events"
	}

	dailyBudget := int64(2500)
	if budgetStr := os.Getenv("DAILY_BUDGET_LIMIT"); budgetStr != "" {
		if parsed, err := strconv.ParseInt(budgetStr, 10, 64); err == nil {
			dailyBudget = parsed
		}
	}

	workers := 10
	if workerStr := os.Getenv("WORKER_POOL_SIZE"); workerStr != "" {
		if parsed, err := strconv.Atoi(workerStr); err == nil && parsed > 0 {
			workers = parsed
		}
	}

	seedFolder := os.Getenv("SEED_FOLDER")
	if seedFolder == "" {
		seedFolder = "./data/seed"
	}

	ingestionMode := os.Getenv("INGESTION_MODE")
	if ingestionMode == "" {
		ingestionMode = "auto"
	}

	port := os.Getenv("PORT")
	if port == "" {
		port = "8083"
	}

	return &Config{
		TrafficProvider:         provider,
		TrafficFallbackProvider: fallbackProvider,
		TrafficProviderMode:     providerMode,
		TomTomAPIKey:            apiKey,
		HEREAPIKey:              hereKey,
		KafkaBootstrapServers:   kafkaServers,
		KafkaTopic:              topic,
		DailyBudgetLimit:        dailyBudget,
		PerBatchLimit:           100,
		WorkerPoolSize:          workers,
		SeedFolderPath:          seedFolder,
		IngestionMode:           ingestionMode,
		HTTPPort:                port,
	}
}

// MaskAPIKey che khuất TomTom API key để bảo mật, không lộ trên log stdout/stderr
func MaskAPIKey(key string) string {
	if len(key) <= 6 {
		return "******"
	}
	return key[:3] + "..." + key[len(key)-3:]
}
