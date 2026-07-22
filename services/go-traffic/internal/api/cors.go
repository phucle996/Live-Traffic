// ==============================================================================
// CORS Middleware Module (services/go-traffic/internal/api/cors.go)
// Cross-Origin Resource Sharing (CORS) Handling cho Public REST Microservices
// ==============================================================================

package api

import (
	"net/http"
)

// CORSMiddleware cấu hình các HTTP response header cho phép Cross-Origin requests từ Web Dashboard (Port 3000, 8501, vv)
func CORSMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Thiết lập header Access-Control-Allow-Origin cho phép mọi Web Client kết nối API công khai
		w.Header().Set("Access-Control-Allow-Origin", "*")
		// Phê duyệt các HTTP Methods phổ biến
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		// Phê duyệt các Request Headers cơ bản cho ứng dụng công khai
		w.Header().Set("Access-Control-Allow-Headers", "Authorization, Content-Type, Accept, X-Requested-With")

		// Nếu là OPTIONS request (Preflight inspection từ Web Browser), trả về 200 OK ngay lập tức
		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusOK)
			return
		}

		// Chuyển giao request xử lý cho handler tiếp theo trong chuỗi HTTP pipeline
		next.ServeHTTP(w, r)
	})
}
