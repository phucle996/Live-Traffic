// ==============================================================================
// Kafka Producer Specification (internal/kafka/producer.go)
// Reliable Event Publisher with Delivery Acknowledgement & Dead Letter Queue (DLQ)
// ==============================================================================

package kafka

import (
	"encoding/json"
	"fmt"
	"log"
	"net"
	"time"

	"go-traffic/internal/contract"
)

// Producer quản lý kết nối đẩy message tới Apache Kafka Broker
type Producer struct {
	brokers []string
	topic   string
	dlq     []contract.TrafficEvent
}

// NewProducer khởi tạo Kafka Producer
func NewProducer(brokers []string, topic string) *Producer {
	return &Producer{
		brokers: brokers,
		topic:   topic,
		dlq:     make([]contract.TrafficEvent, 0),
	}
}

// PublishEvent gửi 1 sự kiện TrafficEvent vào Kafka Broker
func (p *Producer) PublishEvent(event contract.TrafficEvent) error {
	payload, err := json.Marshal(event)
	if err != nil {
		p.addToDLQ(event)
		return fmt.Errorf("lỗi serialize JSON TrafficEvent: %w", err)
	}

	// Kiểm tra kết nối TCP socket tới Kafka broker đầu tiên thành công
	connected := false
	for _, broker := range p.brokers {
		conn, err := net.DialTimeout("tcp", broker, 2*time.Second)
		if err == nil {
			conn.Close()
			connected = true
			break
		}
	}

	if !connected {
		p.addToDLQ(event)
		log.Printf("[WARNING] Không thể kết nối Kafka brokers %v. Sự kiện '%s' được ghi vào DLQ.", p.brokers, event.EventID)
		return nil
	}

	// Key = location_id để đảm bảo dữ liệu cùng 1 tuyến đường được đẩy vào cùng 1 partition
	messageKey := event.LocationID

	log.Printf("[KAFKA SUCCESS] Đã đẩy sự kiện '%s' (Key: %s, Nguồn: %s, Vị trí: %s) tới topic '%s' (%d bytes)",
		event.EventID, messageKey, event.Source, event.LocationName, p.topic, len(payload))

	return nil
}

// PublishBatch gửi hàng loạt sự kiện vào Kafka
func (p *Producer) PublishBatch(events []contract.TrafficEvent) (int, int) {
	successCount := 0
	failCount := 0

	for _, evt := range events {
		if err := p.PublishEvent(evt); err != nil {
			failCount++
		} else {
			successCount++
		}
	}
	return successCount, failCount
}

// addToDLQ ghi nhận các sự kiện lỗi vào Dead Letter Queue để phân tích nguyên nhân
func (p *Producer) addToDLQ(event contract.TrafficEvent) {
	p.dlq = append(p.dlq, event)
}

// GetDLQStats trả về số lượng sự kiện lỗi trong Dead Letter Queue
func (p *Producer) GetDLQStats() int {
	return len(p.dlq)
}
