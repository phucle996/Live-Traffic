// ==============================================================================
// HERE Mapper Specification (internal/provider/here/mapper.go)
// Phase HERE-2 — Map HERE FlowResponse to Standardized FlowObservation Contract
// ==============================================================================

package here

import (
	"fmt"
	"time"

	"go-traffic/internal/provider"
)

// MapToObservations chuyển đổi FlowResponse từ HERE API thành danh sách provider.FlowObservation đã chuẩn hóa
func MapToObservations(resp *FlowResponse, requestID string, defaultObservedAt string) []provider.FlowObservation {
	if resp == nil || len(resp.Results) == 0 {
		return []provider.FlowObservation{}
	}

	if defaultObservedAt == "" {
		defaultObservedAt = time.Now().UTC().Format(time.RFC3339)
	}

	observations := make([]provider.FlowObservation, 0, len(resp.Results))

	for idx, res := range resp.Results {
		// Trích xuất điểm tọa độ đầu tiên của đoạn đường nếu có
		var lat, lon float64
		if len(res.Location.Shape.Links) > 0 && len(res.Location.Shape.Links[0].Points) > 0 {
			firstPoint := res.Location.Shape.Links[0].Points[0]
			lat = firstPoint.Lat
			lon = firstPoint.Lng
		}

		// Tạo segment ID của provider
		providerSegID := fmt.Sprintf("here_seg_%d_%.4f_%.4f", idx, lat, lon)
		if res.Location.Description != "" {
			providerSegID = fmt.Sprintf("here_%s", res.Location.Description)
		}

		// Tính toán Travel Time xấp xỉ từ chiều dài và vận tốc nếu chưa có
		var travelTimeSec, freeFlowTravelSec float64
		if res.Location.Length > 0 && res.CurrentFlow.Speed > 0 {
			travelTimeSec = (res.Location.Length / 1000.0) / res.CurrentFlow.Speed * 3600.0
		}
		if res.Location.Length > 0 && res.CurrentFlow.FreeFlow > 0 {
			freeFlowTravelSec = (res.Location.Length / 1000.0) / res.CurrentFlow.FreeFlow * 3600.0
		}

		obs := provider.FlowObservation{
			Provider:              "here",
			ProviderRequestID:     requestID,
			ProviderSegmentID:     providerSegID,
			ProviderObservedAt:    defaultObservedAt,
			ProviderSchemaVersion: "v7",

			Latitude:  lat,
			Longitude: lon,

			CurrentSpeedKPH:       res.CurrentFlow.Speed,
			FreeFlowSpeedKPH:      res.CurrentFlow.FreeFlow,
			JamFactor:             res.CurrentFlow.JamFactor,
			Confidence:            res.CurrentFlow.Confidence,
			RoadClosed:            res.CurrentFlow.RoadClosed,
			TravelTimeSeconds:     travelTimeSec,
			FreeFlowTravelSeconds: freeFlowTravelSec,
		}

		observations = append(observations, obs)
	}

	return observations
}
