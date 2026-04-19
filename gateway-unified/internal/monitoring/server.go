package monitoring

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"github.com/athena-workspace/gateway-unified/internal/config"
	"github.com/athena-workspace/gateway-unified/internal/logging"
	"github.com/athena-workspace/gateway-unified/internal/metrics"
)

// Server 监控服务器
type Server struct {
	config      config.MonitoringConfig
	httpServer  *http.Server
	promMetrics *metrics.PrometheusMetrics
}

// NewServer 创建监控服务器
func NewServer(cfg config.MonitoringConfig) *Server {
	return &Server{
		config:      cfg,
		promMetrics: metrics.NewPrometheusMetrics(),
	}
}

// Start 启动监控服务器
func (s *Server) Start() error {
	// 启动Prometheus指标收集
	s.promMetrics.Start()

	// 创建HTTP服务器
	mux := http.NewServeMux()

	// 注册Prometheus metrics端点
	metricsPath := s.config.Path
	if metricsPath == "" {
		metricsPath = "/metrics"
	}
	mux.Handle(metricsPath, s.promMetrics.Handler())

	// 健康检查端点
	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("OK"))
	})

	// 创建HTTP服务器
	s.httpServer = &http.Server{
		Addr:         fmt.Sprintf(":%d", s.config.Port),
		Handler:      mux,
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 10 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	logging.LogInfo("监控服务器启动",
		logging.String("port", fmt.Sprintf("%d", s.config.Port)),
		logging.String("metrics_path", metricsPath),
	)

	// 启动HTTP服务器（非阻塞）
	go func() {
		if err := s.httpServer.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			logging.LogError("监控服务器运行失败", logging.Err(err))
		}
	}()

	return nil
}

// Stop 停止监控服务器
func (s *Server) Stop() error {
	logging.LogInfo("监控服务器停止")

	// 停止Prometheus指标收集
	s.promMetrics.Stop()

	// 优雅关闭HTTP服务器
	if s.httpServer != nil {
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		if err := s.httpServer.Shutdown(ctx); err != nil {
			logging.LogError("监控服务器关闭失败", logging.Err(err))
			return err
		}
	}

	return nil
}
