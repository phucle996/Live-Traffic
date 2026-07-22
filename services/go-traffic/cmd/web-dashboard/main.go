// ==============================================================================
// Go Static Web Dashboard Server Entrypoint (cmd/web-dashboard/main.go)
// Serving Production Single Page Application (SPA) Web Frontend on Port 8501
// ==============================================================================

package main

import (
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"path/filepath"
	"syscall"
)

func main() {
	log.Println("======================================================================")
	log.Println("        STARTING GO PRODUCTION WEB DASHBOARD SERVER (PORT 8501)       ")
	log.Println("======================================================================")

	port := os.Getenv("PORT")
	if port == "" {
		port = "8501"
	}

	// Xác định đường dẫn thư mục tĩnh static web assets
	execDir, err := os.Getwd()
	if err != nil {
		execDir = "."
	}
	webDir := filepath.Join(execDir, "web")
	if _, err := os.Stat(webDir); os.IsNotExist(err) {
		webDir = "./services/go-traffic/web"
	}

	log.Printf("[STATIC SERVER] Serving static assets from path: '%s'", webDir)

	// Cấu hình HTTP Static File Server Router
	fs := http.FileServer(http.Dir(webDir))
	mux := http.NewServeMux()

	mux.Handle("/", fs)
	mux.HandleFunc("/health/live", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		fmt.Fprintf(w, `{"service":"go-web-dashboard","status":"UP"}`)
	})
	mux.HandleFunc("/health/ready", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		fmt.Fprintf(w, `{"service":"go-web-dashboard","status":"READY","ready":true}`)
	})

	httpAddr := fmt.Sprintf(":%s", port)
	srv := &http.Server{
		Addr:    httpAddr,
		Handler: mux,
	}

	go func() {
		log.Printf("[HTTP WEB DASHBOARD] Listening on http://0.0.0.0%s", httpAddr)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("Lỗi server Web Dashboard: %v", err)
		}
	}()

	// Lắng nghe tín hiệu dừng SIGINT / SIGTERM
	stop := make(chan os.Signal, 1)
	signal.Notify(stop, syscall.SIGINT, syscall.SIGTERM)

	<-stop
	log.Println("[SHUTDOWN] Shutting down Go Web Dashboard Server...")
}
