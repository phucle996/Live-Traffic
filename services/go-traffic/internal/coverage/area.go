// ==============================================================================
// Coverage Area Specification (internal/coverage/area.go)
// Phase R5 — Định nghĩa Area interface & BoundingBox helpers cho Grid Cells
// ==============================================================================

package coverage

import (
	"fmt"

	"go-traffic/internal/provider"
)

// CellArea định nghĩa 1 khu vực cell dạng BoundingBox
type CellArea struct {
	CellID string
	BBox   provider.BoundingBox
}

// ToHEREFilter chuyển đổi sang HERE v7 BoundingBox filter query string
func (ca CellArea) ToHEREFilter() string {
	return ca.BBox.ToHEREFilter()
}

// ToTomTomPoint chuyển đổi sang điểm trung tâm cho TomTom Point API
func (ca CellArea) ToTomTomPoint() (lat, lon float64) {
	return ca.BBox.ToTomTomPoint()
}

// String trả về biểu diễn dạng text của CellArea
func (ca CellArea) String() string {
	return fmt.Sprintf("CellArea[%s: S=%.4f W=%.4f N=%.4f E=%.4f]", ca.CellID, ca.BBox.South, ca.BBox.West, ca.BBox.North, ca.BBox.East)
}
