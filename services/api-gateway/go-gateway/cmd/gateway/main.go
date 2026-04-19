package main

import (
	"context"
	"flag"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"athena-gateway/internal/config"
	"athena-gateway/internal/gateway"
	"athena-gateway/internal/middleware"
	"athena-gateway/internal/monitoring"
	"athena-gateway/pkg/logger"

	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
)

// 版本信息
const (
	Version   = "1.0.0"
	BuildTime = "2024-01-01"
	GitCommit = "unknown"
)

func main() {
	// 解析命令行参数
	configFile := flag.String("config", "config/config.yaml", "配置文件路径")
	version := flag.Bool("version", false, "显示版本信息")
	flag.Parse()

	// 显示版本信息
	if *version {
		fmt.Printf("Athena API Gateway\nVersion: %s\nBuild: %s\nCommit: %s\n", Version, BuildTime, GitCommit)
		return
	}

	// 初始化日志
	logger.InitLogger()
	defer logger.Sync()

	zap.L().Info("启动Athena API网关",
		zap.String("version", Version),
		zap.String("build_time", BuildTime),
		zap.String("git_commit", GitCommit),
	)

	// 加载配置
	cfg, err := config.LoadConfig(*configFile)
	if err != nil {
		log.Fatalf("加载配置失败: %v", err)
	}

	zap.L().Info("配置加载完成", zap.Any("config", cfg))

	// 设置Gin模式
	if cfg.Server.Mode == "release" {
		gin.SetMode(gin.ReleaseMode)
	} else {
		gin.SetMode(gin.DebugMode)
	}

	// 创建网关实例
	gw, err := gateway.NewGateway(cfg)
	if err != nil {
		zap.L().Fatal("创建网关失败", zap.Error(err))
	}

	// 创建HTTP服务器
	server := &http.Server{
		Addr:         fmt.Sprintf(":%d", cfg.Server.Port),
		Handler:      gw.Router(),
		ReadTimeout:  time.Duration(cfg.Server.ReadTimeout) * time.Second,
		WriteTimeout: time.Duration(cfg.Server.WriteTimeout) * time.Second,
		IdleTimeout:  time.Duration(cfg.Server.IdleTimeout) * time.Second,
	}

	// 启动监控服务
	monitoringServer := monitoring.NewMonitoringServer(cfg.Monitoring)
	go func() {
		if err := monitoringServer.Start(); err != nil {
			zap.L().Error("监控服务启动失败", zap.Error(err))
		}
	}()

	// 启动服务器
	go func() {
		zap.L().Info("HTTP服务器启动",
			zap.String("addr", server.Addr),
			zap.String("mode", cfg.Server.Mode),
		)

		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			zap.L().Fatal("服务器启动失败", zap.Error(err))
		}
	}()

	// 等待中断信号
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	zap.L().Info("开始优雅关闭服务器...")

	// 设置关闭超时
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	// 关闭HTTP服务器
	if err := server.Shutdown(ctx); err != nil {
		zap.L().Error("服务器关闭失败", zap.Error(err))
	}

	// 关闭网关资源
	if err := gw.Close(); err != nil {
		zap.L().Error("网关资源关闭失败", zap.Error(err))
	}

	// 关闭监控服务
	if err := monitoringServer.Shutdown(ctx); err != nil {
		zap.L().Error("监控服务关闭失败", zap.Error(err))
	}

	zap.L().Info("服务器已优雅关闭")
}
