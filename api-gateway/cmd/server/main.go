package main

import (
	"flag"
	"fmt"
	"os"

	"athena-gateway/internal/config"
	"athena-gateway/internal/logging"
	"athena-gateway/pkg/server"
	"go.uber.org/zap"
)

const (
	Version = "1.0.0"
	AppName = "Athena API Gateway"
)

func main() {
	// 解析命令行参数
	configPath := flag.String("config", "", "配置文件路径")
	version := flag.Bool("version", false, "显示版本信息")
	flag.Parse()

	// 显示版本信息
	if *version {
		fmt.Printf("%s v%s\n", AppName, Version)
		os.Exit(0)
	}

	// 打印启动信息
	fmt.Printf("🌸 启动 %s v%s\n", AppName, Version)

	// 加载配置
	cfg, err := config.LoadConfig(*configPath)
	if err != nil {
		fmt.Printf("❌ 配置加载失败: %v\n", err)
		os.Exit(1)
	}

	// 初始化日志系统
	if err := logging.InitLogger(); err != nil {
		fmt.Printf("❌ 日志系统初始化失败: %v\n", err)
		os.Exit(1)
	}

	// 记录启动日志
	logging.LogInfo("正在启动API网关",
		zap.String("version", Version),
		zap.String("config_path", *configPath),
		zap.String("server_addr", cfg.GetServerAddr()),
	)

	// 创建HTTP服务器
	srv, err := server.NewServer(Version)
	if err != nil {
		logging.LogError(err, "创建HTTP服务器失败")
		os.Exit(1)
	}

	// 运行服务器
	if err := srv.Run(); err != nil {
		logging.LogError(err, "服务器运行失败")
		os.Exit(1)
	}
}
