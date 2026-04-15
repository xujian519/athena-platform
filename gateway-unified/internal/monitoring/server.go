package monitoring

import (
	"github.com/athena-workspace/gateway-unified/internal/config"
	"github.com/athena-workspace/gateway-unified/internal/logging"
)

// Server 监控服务器
type Server struct {
	config config.MonitoringConfig
}

// NewServer 创建监控服务器
func NewServer(cfg config.MonitoringConfig) *Server {
	return &Server{
		config: cfg,
	}
}

// Start 启动监控服务器
func (s *Server) Start() error {
	logging.LogInfo("监控服务器启动",
		logging.String("port", string(rune(s.config.Port))),
	)
	// TODO: 实现Prometheus metrics端点
	return nil
}

// Stop 停止监控服务器
func (s *Server) Stop() error {
	logging.LogInfo("监控服务器停止")
	return nil
}
