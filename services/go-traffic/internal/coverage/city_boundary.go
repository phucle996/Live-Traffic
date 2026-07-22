// ==============================================================================
// City Boundary Specification (internal/coverage/city_boundary.go)
// Phase HERE-3 — Quản lý ranh giới địa lý TP.HCM và lọc BoundingBox hợp lệ
// ==============================================================================

package coverage

import (
	"encoding/json"
	"fmt"
	"os"

	"go-traffic/internal/provider"
)

// CityBoundary chứa thông tin ranh giới thành phố và BoundingBox tổng thể
type CityBoundary struct {
	Name    string
	MinLat  float64
	MaxLat  float64
	MinLon  float64
	MaxLon  float64
}

// DefaultHCMBoundary trả về BoundingBox bao phủ toàn bộ TP.HCM làm giá trị mặc định an toàn
func DefaultHCMBoundary() *CityBoundary {
	return &CityBoundary{
		Name:   "Ho Chi Minh City",
		MinLat: 10.3800,
		MaxLat: 11.1600,
		MinLon: 106.3500,
		MaxLon: 107.0300,
	}
}

// LoadBoundaryFromGeoJSON nạp GeoJSON ranh giới thành phố từ file
func LoadBoundaryFromGeoJSON(filepath string) (*CityBoundary, error) {
	data, err := os.ReadFile(filepath)
	if err != nil {
		return DefaultHCMBoundary(), fmt.Errorf("không đọc được file GeoJSON %s, dùng mặc định: %w", filepath, err)
	}

	var geojson struct {
		Features []struct {
			Geometry struct {
				Coordinates [][][]float64 `json:"coordinates"`
			} `json:"geometry"`
		} `json:"features"`
	}

	if err := json.Unmarshal(data, &geojson); err != nil {
		return DefaultHCMBoundary(), fmt.Errorf("không parse được GeoJSON, dùng mặc định: %w", err)
	}

	// Nếu tìm thấy tọa độ polygon trong GeoJSON
	if len(geojson.Features) > 0 && len(geojson.Features[0].Geometry.Coordinates) > 0 {
		coords := geojson.Features[0].Geometry.Coordinates[0]
		if len(coords) > 0 {
			minLon, maxLon := coords[0][0], coords[0][0]
			minLat, maxLat := coords[0][1], coords[0][1]

			for _, pt := range coords {
				if pt[0] < minLon {
					minLon = pt[0]
				}
				if pt[0] > maxLon {
					maxLon = pt[0]
				}
				if pt[1] < minLat {
					minLat = pt[1]
				}
				if pt[1] > maxLat {
					maxLat = pt[1]
				}
			}

			return &CityBoundary{
				Name:   "Ho Chi Minh City GeoJSON",
				MinLat: minLat,
				MaxLat: maxLat,
				MinLon: minLon,
				MaxLon: maxLon,
			}, nil
		}
	}

	return DefaultHCMBoundary(), nil
}

// ContainsPoint kiểm tra 1 tọa độ (lat, lon) có nằm trong ranh giới thành phố không
func (cb *CityBoundary) ContainsPoint(lat, lon float64) bool {
	return lat >= cb.MinLat && lat <= cb.MaxLat && lon >= cb.MinLon && lon <= cb.MaxLon
}

// IntersectsBBox kiểm tra 1 BoundingBox của cell có giao với ranh giới thành phố không
func (cb *CityBoundary) IntersectsBBox(bbox provider.BoundingBox) bool {
	// Cell hoàn toàn nằm bên ngoài ranh giới
	if bbox.North < cb.MinLat || bbox.South > cb.MaxLat || bbox.East < cb.MinLon || bbox.West > cb.MaxLon {
		return false
	}
	return true
}
