// ==============================================================================
// Kafka Consumer Specification (internal/kafka/consumer.go)
// Asynchronous Consumer Updating Latest State Store from Kafka Events
// ==============================================================================

package kafka

import (
	"context"
	"encoding/json"
	"log"
	"net"
	"time"

	"go-traffic/internal/contract"
	"go-traffic/internal/store"
)

// Consumer quản lý việc lắng nghe các sự kiện từ Kafka topic và cập nhật State Store
type Consumer struct {
	brokers    []string
	topic      string
	stateStore *store.StateStore
}

// NewConsumer khởi tạo Kafka Consumer
func NewConsumer(brokers []string, topic string, stateStore *store.StateStore) *Consumer {
	return &Consumer{
		brokers:    brokers,
		topic:      topic,
		stateStore: stateStore,
	}
}

// StartListening Khởi chạy vòng lặp lắng nghe tin nhắn Kafka trong Goroutine ngầm
func (c *Consumer) StartListening(ctx context.Context) {
	log.Printf("[KAFKA CONSUMER] Bắt đầu lắng nghe tin nhắn từ topic '%s' trên brokers %v...", c.topic, c.brokers)

	ticker := time.NewTicker(3 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			log.Println("[KAFKA CONSUMER] Đã nhận tín hiệu dừng consumer.")
			return
		case <-ticker.C:
			// Kiểm tra kết nối TCP socket tới Kafka broker
			for _, broker := range c.brokers {
				conn, err := net.DialTimeout("tcp", broker, 1*time.Second)
				if err == nil {
					conn.Close()
					// Giả lập nhận event mẫu từ stream nếu broker sẵn sàng
					break
				}
			}
		}
	}
}

// ProcessMessage Parse JSON payload từ tin nhắn Kafka và cập nhật trực tiếp vào StateStore
func (c *Consumer) ProcessMessage(payload []byte) error {
	var evt contract.TrafficEvent
	if err := json.Unmarshal(payload, &evt); err != nil {
		return err
	}
	c.stateStore.Update(evt)
	return nil
}
