package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/athena-workspace/core/gateway/internal/config"
	"github.com/athena-workspace/core/gateway/internal/handler"
	"github.com/athena-workspace/core/gateway/internal/middleware"
	"github.com/athena-workspace/core/gateway/internal/monitoring"
	"github.com/athena-workspace/core/gateway/internal/router"
	"github.com/athena-workspace/core/gateway/pkg/logger"
	"github.com/athena-workspace/core/gateway/pkg/tracing"
	"github.com/gin-gonic/gin"
)

// @title Athena API Gateway
// @version 1.0
// @description Athena工作平台的统一API网关
// @termsOfService http://swagger.io/terms/

// @contact.name API Support
// @contact.url http://www.swagger.io/support
// @contact.email support@swagger.io

// @license.name MIT
// @license.url https://opensource.org/licenses/MIT

// @host localhost:8080
// @BasePath /api/v1
func main() {
	// 加载配置
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("Failed to load config: %v", err)
	}

	// 初始化日志
	logger.Init(cfg.Logging)

	// 初始化追踪
	tracerConfig := tracing.Config{
		ServiceName:    cfg.Monitoring.Tracing.ServiceName,
		ServiceVersion: "1.0.0",
		Environment:    cfg.Environment,
		Enabled:        cfg.Monitoring.Tracing.Enabled,
		Jaeger: tracing.JaegerConfig{
			Endpoint: cfg.Monitoring.Tracing.Jaeger.Endpoint,
			Insecure: cfg.Monitoring.Tracing.Jaeger.Insecure,
		},
		Sampling: tracing.SamplingConfig{
			Type:  cfg.Monitoring.Tracing.Sampling.Type,
			Param: cfg.Monitoring.Tracing.Sampling.Param,
		},
		BatchTimeout:       5 * time.Second,
		ExportTimeout:      30 * time.Second,
		MaxExportBatchSize: 512,
	}

	tracer, err := tracing.NewTracer(tracerConfig)
	if err != nil {
		logger.Fatal("Failed to initialize tracer: %v", err)
	}
	defer func() {
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		if err := tracer.Shutdown(ctx); err != nil {
			logger.Error("Failed to shutdown tracer: %v", err)
		}
	}()

	// 设置Gin模式
	if cfg.Environment == "production" {
		gin.SetMode(gin.ReleaseMode)
	}

	// 创建Gin引擎
	engine := gin.New()

	// 设置中间件
	setupMiddleware(engine, cfg)

	// 设置路由
	setupRoutes(engine, cfg)

	// 创建HTTP服务器
	server := &http.Server{
		Addr:           fmt.Sprintf("%s:%d", cfg.Server.Host, cfg.Server.Port),
		Handler:        engine,
		ReadTimeout:    cfg.Server.ReadTimeout,
		WriteTimeout:   cfg.Server.WriteTimeout,
		MaxHeaderBytes: cfg.Server.MaxHeaderBytes,
	}

	// 启动服务器
	go func() {
		logger.Info("Starting gateway server on %s:%d", cfg.Server.Host, cfg.Server.Port)
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			logger.Fatal("Failed to start server: %v", err)
		}
	}()

	// 等待中断信号优雅关闭服务器
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit
	logger.Info("Shutting down server...")

	// 设置5秒超时关闭
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := server.Shutdown(ctx); err != nil {
		logger.Fatal("Server forced to shutdown: %v", err)
	}

	logger.Info("Server exited")
}

// setupMiddleware 设置中间件
func setupMiddleware(engine *gin.Engine, cfg *config.Config) {
	// 恢复中间件
	engine.Use(gin.Recovery())

	// 日志中间件
	engine.Use(middleware.Logger(cfg.Logging))

	// 追踪中间件
	if cfg.Monitoring.Tracing.Enabled {
		engine.Use(middleware.TracingMiddleware(cfg.Monitoring.Tracing.ServiceName))
		engine.Use(middleware.TracingHeadersMiddleware())
	}

	// 指标中间件
	if cfg.Monitoring.Prometheus.Enabled {
		engine.Use(middleware.MetricsMiddleware())
	}

	// CORS中间件
	if cfg.Security.CORS.Enabled {
		engine.Use(middleware.CORS(cfg.Security.CORS))
	}

	// 限流中间件
	if cfg.Limiter.Enabled {
		engine.Use(middleware.RateLimiter(cfg.Limiter))
	}

	// 安全头中间件
	engine.Use(middleware.SecurityHeaders())

	// 监控中间件（保持兼容性）
	if cfg.Monitoring.Prometheus.Enabled {
		engine.Use(middleware.Metrics())
	}
}

// setupRoutes 设置路由
func setupRoutes(engine *gin.Engine, cfg *config.Config) {
	// 初始化监控
	monitoring.Init(cfg.Monitoring)

	// 创建处理器
	healthHandler := handler.NewHealthHandler()
	metricsHandler := handler.NewMetricsHandler()

	// 健康检查路由
	engine.GET("/health", healthHandler.Check)
	engine.GET("/ready", healthHandler.Ready)

	// 指标路由
	if cfg.Monitoring.Prometheus.Enabled {
		engine.GET(cfg.Monitoring.Prometheus.Path, metricsHandler.Prometheus)
	}

	// 创建路由器
	gatewayRouter := router.NewRouter(cfg)
	gatewayRouter.SetupRoutes(engine)
}
