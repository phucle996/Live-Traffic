// ==============================================================================
// Provider Registry (internal/provider/registry.go)
// Phase HERE-1 — Đăng ký và lookup provider theo tên.
// Dùng để provider router không hard-code tên provider.
// ==============================================================================

package provider

import (
	"fmt"
	"sync"
)

// Registry lưu trữ danh sách provider đã đăng ký, thread-safe.
type Registry struct {
	mu        sync.RWMutex
	providers map[string]TrafficProvider
}

// NewRegistry tạo Registry mới rỗng.
func NewRegistry() *Registry {
	return &Registry{
		providers: make(map[string]TrafficProvider),
	}
}

// Register đăng ký 1 provider vào registry theo tên.
// Nếu tên đã tồn tại, provider mới sẽ ghi đè.
func (r *Registry) Register(p TrafficProvider) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.providers[p.Name()] = p
}

// Get trả về provider theo tên. Trả lỗi nếu không tìm thấy.
func (r *Registry) Get(name string) (TrafficProvider, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	p, ok := r.providers[name]
	if !ok {
		return nil, fmt.Errorf("provider %q chưa được đăng ký trong registry", name)
	}
	return p, nil
}

// List trả về danh sách tên provider đã đăng ký.
func (r *Registry) List() []string {
	r.mu.RLock()
	defer r.mu.RUnlock()

	names := make([]string, 0, len(r.providers))
	for name := range r.providers {
		names = append(names, name)
	}
	return names
}
