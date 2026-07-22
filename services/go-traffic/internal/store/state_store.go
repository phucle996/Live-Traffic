// ==============================================================================
// Latest State Store Specification (internal/store/state_store.go)
// Thread-Safe In-Memory / Redis Cache Store Guarding Against Race Conditions
// ==============================================================================

package store

import (
	"crypto/sha256"
	"encoding/hex"
	"sort"
	"sync"
	"time"

	"go-traffic/internal/contract"
)

// LiveStateRecord biểu diễn trạng thái giao thông mới nhất của 1 tuyến đường được lưu trữ trong State Store
type LiveStateRecord struct {
	LocationID     string  `json:"location_id"`
	LocationName   string  `json:"location_name"`
	District       string  `json:"district"`
	Latitude       float64 `json:"latitude"`
	Longitude      float64 `json:"longitude"`
	CurrentSpeed   float64 `json:"current_speed"`
	FreeFlowSpeed  float64 `json:"free_flow_speed"`
	Confidence     float64 `json:"confidence"`
	Source         string  `json:"source"`
	ObservedAt     string  `json:"observed_at"`
	DataAgeSeconds int64   `json:"data_age_seconds"`
}

// StateStore quản lý kho lưu trữ trạng thái giao thông thời gian thực an toàn với RWMutex
type StateStore struct {
	records map[string]LiveStateRecord
	mu      sync.RWMutex
}

// NewStateStore khởi tạo StateStore mới
func NewStateStore() *StateStore {
	return &StateStore{
		records: make(map[string]LiveStateRecord),
	}
}

// Update Cập nhật hoặc chèn trạng thái mới nhất cho 1 location (Thread-Safe Write Lock)
func (s *StateStore) Update(evt contract.TrafficEvent) {
	s.mu.Lock()
	defer s.mu.Unlock()

	obsTime, err := time.Parse(time.RFC3339, evt.EventTime)
	if err != nil {
		obsTime = time.Now()
	}

	age := int64(time.Since(obsTime).Seconds())
	if age < 0 {
		age = 0
	}

	s.records[evt.LocationID] = LiveStateRecord{
		LocationID:     evt.LocationID,
		LocationName:   evt.LocationName,
		District:       evt.District,
		Latitude:       evt.Latitude,
		Longitude:      evt.Longitude,
		CurrentSpeed:   evt.CurrentSpeed,
		FreeFlowSpeed:  evt.FreeFlowSpeed,
		Confidence:     evt.Confidence,
		Source:         evt.Source,
		ObservedAt:     evt.EventTime,
		DataAgeSeconds: age,
	}
}

// GetAll Trả về danh sách trạng thái của tất cả các vị trí tuyến đường (Thread-Safe Read Lock)
func (s *StateStore) GetAll() []LiveStateRecord {
	s.mu.RLock()
	defer s.mu.RUnlock()

	now := time.Now()
	list := make([]LiveStateRecord, 0, len(s.records))

	for _, rec := range s.records {
		obsTime, err := time.Parse(time.RFC3339, rec.ObservedAt)
		if err == nil {
			rec.DataAgeSeconds = int64(now.Sub(obsTime).Seconds())
			if rec.DataAgeSeconds < 0 {
				rec.DataAgeSeconds = 0
			}
		}
		list = append(list, rec)
	}

	// Sắp xếp danh sách theo LocationID để phản hồi tính ETag nhất quán
	sort.Slice(list, func(i, j int) bool {
		return list[i].LocationID < list[j].LocationID
	})

	return list
}

// GetByLocationID Trả về trạng thái của 1 location cụ thể
func (s *StateStore) GetByLocationID(locationID string) (LiveStateRecord, bool) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	rec, exists := s.records[locationID]
	if !exists {
		return LiveStateRecord{}, false
	}

	obsTime, err := time.Parse(time.RFC3339, rec.ObservedAt)
	if err == nil {
		rec.DataAgeSeconds = int64(time.Since(obsTime).Seconds())
		if rec.DataAgeSeconds < 0 {
			rec.DataAgeSeconds = 0
		}
	}
	return rec, true
}

// ComputeETag Tính toán mã ETag SHA-256 snapshot dữ liệu dựa trên LocationID + ObservedAt + Source
func (s *StateStore) ComputeETag() string {
	records := s.GetAll()
	var raw string
	for _, r := range records {
		raw += r.LocationID + ":" + r.ObservedAt + ":" + r.Source + ";"
	}
	hash := sha256.Sum256([]byte(raw))
	return "\"" + hex.EncodeToString(hash[:16]) + "\""
}
