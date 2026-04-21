package main

import (
	"context"
	"fmt"
	"log"
	"net"
	"net/http"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"

	"github.com/athena-workspace/gateway-unified/internal/config"
	"github.com/athena-workspace/gateway-unified/internal/discovery"
	"github.com/athena-workspace/gateway-unified/internal/gateway"
	grpcserver "github.com/athena-workspace/gateway-unified/internal/grpc"
	"github.com/athena-workspace/gateway-unified/internal/logging"
	"github.com/athena-workspace/gateway-unified/internal/monitoring"
	"github.com/athena-workspace/gateway-unified/internal/router"
	"github.com/athena-workspace/gateway-unified/internal/tailscale"
	"github.com/athena-workspace/gateway-unified/internal/websocket"

	"google.golang.org/grpc"
	pb "github.com/athena-workspace/gateway-unified/proto"
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

	// 初始化OpenTelemetry（如果启用监控）
	if cfg.Monitoring.Enabled {
		tracer, err := monitoring.InitOpenTelemetry(cfg.Monitoring)
		if err != nil {
			logging.LogWarn("OpenTelemetry初始化失败，将不启用链路追踪", logging.Err(err))
		} else {
			logging.LogInfo("OpenTelemetry链路追踪已启用")
			_ = tracer // 记录tracer供后续使用
		}
	}

	logging.LogInfo("启动Athena Gateway",
		logging.String("version", Version),
		logging.String("build_time", BuildTime),
		logging.String("git_commit", GitCommit),
	)

	// generateServiceID 生成服务实例ID
	// 创建网关实例
	gw, err := gateway.NewGateway(cfg)
	if err != nil {
		logging.LogFatal("创建网关失败", logging.Err(err))
	}

	// 声明gRPC服务器变量（可能在下面创建）
	var grpcServer *grpc.Server

	// 加载版本配置
	versionLoader := config.NewVersionLoader()
	versionConfigPath := "config/versions.yaml"
	if err := versionLoader.LoadFromFile(versionConfigPath); err != nil {
		logging.LogWarn("版本配置加载失败，使用默认配置", logging.Err(err))
	} else {
		// 应用版本配置到中间件
		versionLoader.ApplyTo(gw.GetVersionConfig())
		logging.LogInfo("版本配置加载完成",
			logging.String("default_version", gw.GetVersionConfig().GetDefaultVersion()),
			logging.Int("total_versions", len(gw.GetVersionConfig().ListVersions())),
		)
	}

	// 加载路由配置
	routesLoader := config.NewRoutesLoader()
	routesConfigPath := "config/routes.yaml"
	if err := routesLoader.LoadFromFile(routesConfigPath); err != nil {
		logging.LogWarn("路由配置加载失败，使用默认配置", logging.Err(err))
	} else {
		// 验证路由配置
		if err := routesLoader.Validate(); err != nil {
			logging.LogWarn("路由配置验证失败", logging.Err(err))
		}

		// 批量创建路由
		routeManager := gw.GetRouteManager()
		validator := gateway.NewRouteValidator()
		loadedCount := 0

		for _, cfgRoute := range routesLoader.GetRoutes() {
			// 转换为gateway.RouteRule
			route := &gateway.RouteRule{
				ID:            cfgRoute.ID,
				Path:          cfgRoute.Path,
				TargetService: cfgRoute.TargetService,
				Methods:       cfgRoute.Methods,
				StripPrefix:   cfgRoute.StripPrefix,
				Timeout:       cfgRoute.Timeout,
				Retries:       cfgRoute.Retries,
				AuthRequired:  cfgRoute.AuthRequired,
				Priority:      cfgRoute.Priority,
				Weight:        cfgRoute.Weight,
				Enabled:       cfgRoute.Enabled,
				Metadata:      cfgRoute.Metadata,
			}

			// 验证路由
			if err := validator.Validate(route); err != nil {
				logging.LogWarn("路由验证失败，跳过",
					logging.String("id", route.ID),
					logging.String("path", route.Path),
					logging.Err(err),
				)
				continue
			}

			// 检查路由冲突
			existingRoutes := routeManager.GetAll()
			if err := validator.ValidateConflict(route, existingRoutes); err != nil {
				logging.LogWarn("路由冲突检测失败，跳过",
					logging.String("id", route.ID),
					logging.String("path", route.Path),
					logging.Err(err),
				)
				continue
			}

			// 创建路由
			routeManager.Create(route)

			loadedCount++
			logging.LogInfo("路由已加载",
				logging.String("id", route.ID),
				logging.String("path", route.Path),
				logging.String("target", route.TargetService),
				logging.Int("priority", route.Priority),
			)
		}

		logging.LogInfo("路由配置加载完成",
			logging.Int("total", len(routesLoader.GetRoutes())),
			logging.Int("loaded", loadedCount),
		)
	}

	// 加载服务实例配置
	servicesConfigPath := "config/services.yaml"
	if servicesConfig, err := config.LoadServiceInstances(servicesConfigPath); err == nil {
		registry := gw.GetRegistry()
		registeredCount := 0

		for i, svc := range servicesConfig.Services {
			instance := &gateway.ServiceInstance{
				ID:          gateway.GenerateServiceID(svc.Name, svc.Host, svc.Port, i),
				ServiceName: svc.Name,
				Host:        svc.Host,
				Port:        svc.Port,
				Status:      "UP",
				Weight:      1,
				Metadata:    svc.Metadata,
			}
			registry.Register(instance)
			registeredCount++
			logging.LogInfo("服务实例已注册",
				logging.String("service", svc.Name),
				logging.String("host", svc.Host),
				logging.Int("port", svc.Port),
			)
		}

		logging.LogInfo("服务实例注册完成",
			logging.Int("total", len(servicesConfig.Services)),
			logging.Int("registered", registeredCount),
		)
	} else {
		logging.LogWarn("服务实例配置加载失败", logging.Err(err))
	}

	// 创建WebSocket控制器
	wsController := websocket.NewController(websocket.DefaultConfig())
	logging.LogInfo("WebSocket控制器已创建")

	// 创建WebSocket Hub（用于新的控制平面）
	wsHub := websocket.NewHub()
	go wsHub.Run()
	logging.LogInfo("WebSocket Hub已启动")

	// 创建gRPC服务器（如果启用）
	if cfg.IsGRPCEnabled() {
		grpcPort := cfg.GRPC.Port
		if grpcPort == 0 {
			grpcPort = 50051 // 默认gRPC端口
		}

		grpcServer = grpc.NewServer()
		agentServer := grpcserver.NewAgentServer()
		pb.RegisterAgentServiceServer(grpcServer, agentServer)

		// 启动gRPC服务器
		go func() {
			grpcAddr := fmt.Sprintf(":%d", grpcPort)
			lis, err := net.Listen("tcp", grpcAddr)
			if err != nil {
				logging.LogFatal("gRPC监听失败", logging.Err(err))
			}

			logging.LogInfo("gRPC服务器启动",
				logging.String("addr", grpcAddr),
			)

			if err := grpcServer.Serve(lis); err != nil {
				logging.LogError("gRPC服务器错误", logging.Err(err))
			}
		}()
		logging.LogInfo("gRPC服务器已创建")
	} else {
		logging.LogInfo("gRPC服务器未启用")
	}

	// 创建服务发现适配器
	discoveryConfig := &discovery.ServiceDiscoveryConfig{
		ConfigPath:     "config/service_discovery.json",
		ScanInterval:   30 * time.Second,
		AutoRegister:   true,
		HealthCheck:    true,
		HealthEndpoint: "/health",
	}

	// 使用适配器包装Gateway的ServiceRegistry，避免循环导入
	registryAdapter := discovery.NewGatewayRegistryAdapter(gw.GetRegistry())
	discoveryAdapter := discovery.NewAdapter(discoveryConfig, registryAdapter)
	if err := discoveryAdapter.Start(); err != nil {
		logging.LogWarn("启动服务发现失败，将不启用自动服务发现", logging.Err(err))
	} else {
		logging.LogInfo("服务发现适配器已启动",
			logging.String("config_path", discoveryConfig.ConfigPath),
			logging.String("scan_interval", discoveryConfig.ScanInterval.String()),
		)
		defer discoveryAdapter.Close()
	}

	// 设置路由
	if err := router.SetupRoutes(gw.GetRouter(), cfg, wsController, wsHub); err != nil {
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

	var wg sync.WaitGroup
	resourceCount := 2

	done := make(chan error, 3)

	wg.Add(2)
	go func() {
		defer wg.Done()
		done <- gw.Close()
	}()
	go func() {
		defer wg.Done()
		done <- wsController.Close()
	}()

	// 只有gRPC服务器存在时才关闭
	if grpcServer != nil {
		resourceCount = 3
		wg.Add(1)
		go func() {
			defer wg.Done()
			// 优雅关闭gRPC服务器
			grpcServer.GracefulStop()
			logging.LogInfo("gRPC服务器已关闭")
			done <- nil
		}()
	}

	// 等待所有资源关闭
	for i := 0; i < resourceCount; i++ {
		select {
		case err := <-done:
			if err != nil {
				logging.LogError("资源关闭失败", logging.Err(err))
			}
		case <-ctx2.Done():
			logging.LogWarn("第二阶段超时")
			break
		}
	}

	if grpcServer != nil {
		logging.LogInfo("第二阶段完成: 网关、WebSocket和gRPC资源已释放")
	} else {
		logging.LogInfo("第二阶段完成: 网关和WebSocket资源已释放")
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

	// 关闭OpenTelemetry
	if cfg.Monitoring.Enabled {
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		if err := monitoring.ShutdownOpenTelemetry(ctx); err != nil {
			logging.LogError("OpenTelemetry关闭失败", logging.Err(err))
		}
	}
}
