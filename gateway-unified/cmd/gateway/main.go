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

	"github.com/athena-workspace/gateway-unified/internal/config"
	"github.com/athena-workspace/gateway-unified/internal/gateway"
	"github.com/athena-workspace/gateway-unified/internal/logging"
	"github.com/athena-workspace/gateway-unified/internal/monitoring"
	"github.com/athena-workspace/gateway-unified/internal/router"
	"github.com/athena-workspace/gateway-unified/internal/tailscale"
)

// 版本信息
const (
	Version   = "1.0.0"
	BuildTime = "2026-02-20"
	GitCommit = "unified-v1.0.0"
)

func main() {
	// 打印启动信息
	fmt.Printf("🌸 Athena Gateway Unified v%s\n", Version)
	fmt.Printf("🕐 构建时间: %s\n", BuildTime)
	fmt.Printf("📦 Git提交: %s\n\n", GitCommit)

	// 加载配置
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("❌ 加载配置失败: %v", err)
	}

	// 初始化日志系统
	if err := logging.Init(&cfg.Logging); err != nil {
		log.Fatalf("❌ 初始化日志失败: %v", err)
	}
	defer logging.Sync()

	logging.LogInfo("启动Athena Gateway",
		logging.String("version", Version),
		logging.String("build_time", BuildTime),
		logging.String("git_commit", GitCommit),
	)

	// 创建网关实例
	gw, err := gateway.NewGateway(cfg)
	if err != nil {
		logging.LogFatal("创建网关失败", logging.Err(err))
	}

	// 设置路由
	if err := router.SetupRoutes(gw.GetRouter(), cfg); err != nil {
		logging.LogFatal("设置路由失败", logging.Err(err))
	}

	// 启动监控服务（如果启用）
	if cfg.Monitoring.Enabled {
		monitoringServer := monitoring.NewServer(cfg.Monitoring)
		go func() {
			if err := monitoringServer.Start(); err != nil {
				logging.LogError("监控服务启动失败", logging.Err(err))
			}
		}()
	}

	// 初始化Tailscale管理器
	var tsManager *tailscale.Manager
	if cfg.IsTailscaleEnabled() {
		tsManager = tailscale.NewManager(&cfg.Tailscale, cfg.Server.Port)

		// 检查Tailscale是否可用
		if !tsManager.IsAvailable() {
			logging.LogFatal("Tailscale模式已启用但CLI未安装",
				logging.String("mode", cfg.Tailscale.Mode),
			)
		}

		// 打印Tailscale配置信息
		tsManager.PrintInfo()

		// Funnel模式需要认证
		if cfg.IsTailscaleFunnel() && !cfg.IsAuthRequired() {
			logging.LogFatal("Funnel模式需要配置认证",
				logging.String("hint", "请设置 GATEWAY_AUTH_PASSWORD 或在配置文件中配置 auth.password"),
			)
		}

		// 配置Tailscale
		if err := tsManager.Setup(); err != nil {
			logging.LogFatal("Tailscale配置失败", logging.Err(err))
		}

		logging.LogInfo("Tailscale配置完成",
			logging.String("mode", cfg.Tailscale.Mode),
		)
	}

	// 创建HTTP服务器
	server := &http.Server{
		Addr:         fmt.Sprintf(":%d", cfg.Server.Port),
		Handler:      gw.GetRouter(),
		ReadTimeout:  time.Duration(cfg.Server.ReadTimeout) * time.Second,
		WriteTimeout:  time.Duration(cfg.Server.WriteTimeout) * time.Second,
		IdleTimeout:  time.Duration(cfg.Server.IdleTimeout) * time.Second,
	}

	// 启动服务器
	go func() {
		logging.LogInfo("HTTP服务器启动",
			logging.String("addr", server.Addr),
			logging.Bool("production", cfg.Server.Production),
			logging.Bool("tls", cfg.TLS.Enabled),
		)

		var err error
		if cfg.TLS.Enabled {
			// TLS模式
			if cfg.TLS.CertFile == "" || cfg.TLS.KeyFile == "" {
				logging.LogFatal("TLS已启用但未指定证书文件或密钥文件",
					logging.String("cert_file", cfg.TLS.CertFile),
					logging.String("key_file", cfg.TLS.KeyFile),
				)
			}
			err = server.ListenAndServeTLS(cfg.TLS.CertFile, cfg.TLS.KeyFile)
		} else {
			// HTTP模式
			err = server.ListenAndServe()
		}

		if err != nil && err != http.ErrServerClosed {
			logging.LogFatal("服务器启动失败", logging.Err(err))
		}
	}()

	// 等待中断信号
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM, syscall.SIGQUIT)
	sig := <-quit

	logging.LogInfo("收到关闭信号",
		logging.String("signal", sig.String()),
	)

	logging.LogInfo("开始优雅关闭服务器...")

	// 设置关闭超时 - 分阶段关闭
	// 第一阶段: 停止接受新请求 (5秒)
	ctx1, cancel1 := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel1()

	logging.LogInfo("第一阶段: 停止接受新请求...")
	if err := server.Shutdown(ctx1); err != nil {
		if err == context.DeadlineExceeded {
			logging.LogWarn("第一阶段超时，强制关闭")
		} else {
			logging.LogError("服务器关闭失败", logging.Err(err))
		}
	} else {
		logging.LogInfo("第一阶段完成: 所有请求已处理完毕")
	}

	// 第二阶段: 关闭网关资源 (10秒)
	logging.LogInfo("第二阶段: 关闭网关资源...")
	ctx2, cancel2 := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel2()

	done := make(chan error, 1)
	go func() {
		done <- gw.Close()
	}()

	select {
	case err := <-done:
		if err != nil {
			logging.LogError("网关关闭失败", logging.Err(err))
		} else {
			logging.LogInfo("第二阶段完成: 网关资源已释放")
		}
	case <-ctx2.Done():
		logging.LogWarn("第二阶段超时")
	}

	// 第三阶段: 重置Tailscale配置
	if tsManager != nil && cfg.Tailscale.ResetOnExit {
		logging.LogInfo("第三阶段: 重置Tailscale配置...")
		if err := tsManager.Reset(); err != nil {
			logging.LogError("Tailscale重置失败", logging.Err(err))
		} else {
			logging.LogInfo("第三阶段完成: Tailscale配置已重置")
		}
	}

	logging.LogInfo("Athena Gateway已关闭")
}
