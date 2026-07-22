// ==============================================================================
// Grid Cell Generator Specification (internal/coverage/grid.go)
// Phase HERE-3 — Chia lưới thành phố thành các Cell ổn định kèm định danh CellID duy nhất
// ==============================================================================

package coverage

import (
	"fmt"
	"time"

	"go-traffic/internal/provider"
)

// Cell đại diện cho 1 ô lưới phân vùng địa lý để crawl traffic data theo khu vực
type Cell struct {
	CellID          string               `json:"cell_id"`          // Mã ô lưới ổn định e.g. "cell_1076_10669"
	Name            string               `json:"name"`             // Tên mô tả ô lưới
	BBox            provider.BoundingBox `json:"bbox"`             // BoundingBox góc nam, tây, bắc, đông
	Priority        int                  `json:"priority"`         // Mức ưu tiên (1: Cao, 2: Trung bình, 3: Thấp)
	RoadCount       int                  `json:"road_count"`       // Ước tính số tuyến đường trong cell
	RoadLengthM     float64              `json:"road_length_m"`    // Ước tính tổng chiều dài đường (mét)
	PollingInterval time.Duration        `json:"polling_interval"` // Khoảng thời gian thu thập lại dữ liệu
	LastPolledAt    time.Time            `json:"last_polled_at"`   // Thời điểm thu thập gần nhất
}

// GenerateGridGenerator chia ranh giới city thành ma trận ô lưới theo bước lưới stepDeg (độ)
func GenerateGrid(boundary *CityBoundary, stepDeg float64) []Cell {
	if stepDeg <= 0 {
		stepDeg = 0.03 // Mặc định ~3.3km mỗi cạnh ô
	}

	var cells []Cell
	col := 0

	for lat := boundary.MinLat; lat < boundary.MaxLat; lat += stepDeg {
		row := 0
		for lon := boundary.MinLon; lon < boundary.MaxLon; lon += stepDeg {
			north := lat + stepDeg
			if north > boundary.MaxLat {
				north = boundary.MaxLat
			}

			east := lon + stepDeg
			if east > boundary.MaxLon {
				east = boundary.MaxLon
			}

			bbox := provider.BoundingBox{
				South: lat,
				West:  lon,
				North: north,
				East:  east,
			}

			// Tạo CellID ổn định từ tọa độ góc nam-tây
			cellID := fmt.Sprintf("cell_%04d_%04d", int(lat*100), int(lon*100))
			cellName := fmt.Sprintf("Grid Cell (%d,%d)", col, row)

			// Mặc định gán Priority 3, sẽ được tinh chỉnh bởi priority.go
			cell := Cell{
				CellID:          cellID,
				Name:            cellName,
				BBox:            bbox,
				Priority:        3,
				RoadCount:       10,
				RoadLengthM:     3000.0,
				PollingInterval: 15 * time.Minute,
			}

			cells = append(cells, cell)
			row++
		}
		col++
	}

	return cells
}
