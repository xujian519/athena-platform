// Package main - LLM独立HTTP服务
package main

import (
	"context"
	"encoding/json"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	llm "github.com/athena-workspace/gateway-unified/services/llm"
)

func main() {
	log.SetFlags(log.LstdFlags | log.Lshortfile)
	log.Println("=== DeepSeek LLM服务启动 ===")

	// 从环境变量获取API密钥
	apiKey := os.Getenv("DEEPSEEK_API_KEY")
	if apiKey == "" {
		log.Fatal("错误: 未设置DEEPSEEK_API_KEY环境变量")
	}

	log.Printf("API密钥: %s...", apiKey[:7])

	// 初始化LLM智能路由器
	router := llm.NewSmartRouter()
	log.Printf("智能路由器初始化成功，模型数量: %d", len(router.ListModels()))

	// 创建HTTP路由器
	mux := http.NewServeMux()

	// 健康检查
	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]interface{}{
			"status":     "healthy",
			"service":    "llm-service",
			"provider":   "deepseek",
			"models":     []string{"deepseek-chat", "deepseek-reasoner"},
			"version":    "1.0.0-deepseek",
		})
	})

	// 聊天接口
	mux.HandleFunc("/api/v1/chat", handleChat)
	mux.HandleFunc("/api/v1/batch-chat", handleBatchChat)

	// 统计接口
	mux.HandleFunc("/api/v1/stats", handleStats)
	mux.HandleFunc("/api/v1/stats/router", handleRouterStats)
	mux.HandleFunc("/api/v1/stats/cache", handleCacheStats)

	port := "8022"
	server := &http.Server{
		Addr:    ":" + port,
		Handler: mux,
	}

	// 启动服务
	go func() {
		log.Printf("🚀 LLM服务启动成功 http://0.0.0.0:%s\n", port)
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("服务启动失败: %v", err)
		}
	}()

	// 优雅关闭
	sigchan := make(chan os.Signal, 1)
	signal.Notify(sigchan, syscall.SIGINT, syscall.SIGTERM)
	<-sigchan
	log.Println("收到关闭信号，正在优雅关闭...")

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	server.Shutdown(ctx)

	log.Println("=== LLM服务已停止 ===")
}

func handleChat(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")

	var req struct {
		Messages []struct {
			Role    string `json:"role"`
			Content string `json:"content"`
		} `json:"messages"`
		Model string `json:"model"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(map[string]string{
			"error": "请求格式错误",
		})
		return
	}

	// TODO: 调用LLM服务
	json.NewEncoder(w).Encode(map[string]interface{}{
		"status":     "ok",
		"service":    "llm-service",
		"provider":   "deepseek",
		"message":    "DeepSeek LLM服务运行中",
		"model":      req.Model,
	})
}

func handleBatchChat(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")

	// TODO: 实现批量处理
	json.NewEncoder(w).Encode(map[string]string{
		"status":  "ok",
		"message": "批量聊天功能开发中",
	})
}

func handleStats(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")

	// TODO: 返回真实统计
	json.NewEncoder(w).Encode(map[string]interface{}{
		"status":  "ok",
		"service":  "llm-service",
		"provider":  "deepseek",
		"models": []string{"deepseek-chat", "deepseek-reasoner"},
	})
}

func handleRouterStats(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")

	// TODO: 返回路由统计
	json.NewEncoder(w).Encode(map[string]interface{}{
		"economy_count":  0,
		"balanced_count": 0,
		"premium_count": 0,
		"total_requests": 0,
	})
}

func handleCacheStats(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")

	// TODO: 返回缓存统计
	json.NewEncoder(w).Encode(map[string]interface{}{
		"hits": 0,
		"misses": 0,
		"hit_rate": 0.0,
	})
}
