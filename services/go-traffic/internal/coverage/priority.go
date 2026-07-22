// ==============================================================================
// Priority Policy Specification (internal/coverage/priority.go)
// Phase HERE-3 — Đánh giá mức độ ưu tiên Priority (1-3) & Khoảng thời gian Polling
// Ưu tiên trung tâm, nút giao lớn và tăng tần suất thu thập trong giờ cao điểm
// ==============================================================================

package coverage

import (
	"time"

	"go-traffic/internal/provider"
)

// ZonePriorityConfig định nghĩa cấu hình ưu tiên cho các zone đặc biệt
type ZonePriorityConfig struct {
	ID       string
	Name     string
	Priority int
	BBox     provider.BoundingBox
}

// GetBuiltinPriorityZones trả về danh sách các zone trọng điểm mặc định tại TP.HCM
func GetBuiltinPriorityZones() []ZonePriorityConfig {
	return []ZonePriorityConfig{
		{
			ID:       "cell_q1_center",
			Name:     "Quận 1 — Trung tâm",
			Priority: 1,
			BBox:     provider.BoundingBox{South: 10.7600, West: 106.6920, North: 10.7900, East: 106.7100},
		},
		{
			ID:       "cell_binh_thanh",
			Name:     "Bình Thạnh — Hàng Xanh",
			Priority: 1,
			BBox:     provider.BoundingBox{South: 10.7950, West: 106.7000, North: 10.8200, East: 106.7300},
		},
		{
			ID:       "cell_tan_son_nhat",
			Name:     "Sân bay Tân Sơn Nhất",
			Priority: 1,
			BBox:     provider.BoundingBox{South: 10.8000, West: 106.6550, North: 10.8300, East: 106.6850},
		},
		{
			ID:       "cell_thu_duc",
			Name:     "TP. Thủ Đức — Xa lộ Hà Nội",
			Priority: 2,
			BBox:     provider.BoundingBox{South: 10.8450, West: 106.7700, North: 10.8900, East: 106.8200},
		},
	}
}

// IsPeakHour kiểm tra xem thời điểm hiện tại có thuộc khung giờ cao điểm TP.HCM hay không
// Cao điểm sáng: 07:00 – 09:00 (Thứ 2 đến Thứ 6)
// Cao điểm chiều: 16:00 – 19:00 (Thứ 2 đến Thứ 6)
func IsPeakHour(t time.Time) bool {
	// Kiểm tra cuối tuần (Thứ 7 = 6, Chủ nhật = 0)
	if t.Weekday() == time.Saturday || t.Weekday() == time.Sunday {
		return false
	}

	hour := t.Hour()
	// Cao điểm sáng 7h-9h hoặc chiều 16h-19h
	return (hour >= 7 && hour < 9) || (hour >= 16 && hour < 19)
}

// CalculatePollingInterval tính toán polling interval linh hoạt dựa trên priority và giờ cao điểm
func CalculatePollingInterval(priority int, isPeak bool) time.Duration {
	baseInterval := 15 * time.Minute

	switch priority {
	case 1:
		baseInterval = 3 * time.Minute // Priority 1: mỗi 3 phút
	case 2:
		baseInterval = 7 * time.Minute // Priority 2: mỗi 7 phút
	case 3:
		baseInterval = 15 * time.Minute // Priority 3: mỗi 15 phút
	}

	// Nếu đang là giờ cao điểm -> tăng tần suất thu thập thêm 30% (rút ngắn interval)
	if isPeak {
		baseInterval = time.Duration(float64(baseInterval) * 0.7)
	}

	return baseInterval
}

// EnrichCellPriority cập nhật Priority & PollingInterval cho 1 Cell dựa trên các zone trọng điểm
func EnrichCellPriority(cell *Cell, priorityZones []ZonePriorityConfig, now time.Time) {
	isPeak := IsPeakHour(now)

	// Kiểm tra xem cell có giao với zone trọng điểm nào không
	for _, pz := range priorityZones {
		// Nếu BoundingBox cell giao với zone ưu tiên -> cập nhật priority cao hơn
		if cell.BBox.South <= pz.BBox.North && cell.BBox.North >= pz.BBox.South &&
			cell.BBox.West <= pz.BBox.East && cell.BBox.East >= pz.BBox.West {
			if pz.Priority < cell.Priority {
				cell.Priority = pz.Priority
				cell.Name = pz.Name
			}
		}
	}

	// Cập nhật PollingInterval chuẩn cho cell
	cell.PollingInterval = CalculatePollingInterval(cell.Priority, isPeak)
}
