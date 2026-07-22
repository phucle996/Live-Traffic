// ==============================================================================
// HERE Decoder Specification (internal/provider/here/decoder.go)
// Phase HERE-2 — Safe JSON Decoder & Validation
// ==============================================================================

package here

import (
	"encoding/json"
	"fmt"
	"io"
)

// DecodeFlowResponse giải mã an toàn JSON response từ HTTP Body
func DecodeFlowResponse(r io.Reader) (*FlowResponse, error) {
	var resp FlowResponse
	decoder := json.NewDecoder(r)

	if err := decoder.Decode(&resp); err != nil {
		return nil, fmt.Errorf("lỗi parse JSON từ HERE API: %w", err)
	}

	return &resp, nil
}
