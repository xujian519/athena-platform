// Package lifecycle - 优雅关闭管理
// 提供优雅关闭功能，确保服务在关闭前完成现有请求
package lifecycle

import (
	"context"
	"net/http"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"

	"github.com/athena-workspace/gateway-unified/internal/logging"
	"github.com/gin-gonic/gin"
)

// ShutdownPhase 关闭阶段
type ShutdownPhase int

const (
	PhaseIdle         ShutdownPhase = iota // 空闲阶段
	PhaseInitiating                         // 启动关闭
	PhaseStopping                            // 停止接受新请求
	PhaseProcessing                          // 处理现有请求
	PhaseClosing                             // 关闭资源
	PhaseComplete                            // 关闭完成
)

// String 返回阶段的字符串表示
func (p ShutdownPhase) String() string {
	switch p {
	case PhaseIdle:
		return "IDLE"
	case PhaseInitiating:
		return "INITIATING"
	case PhaseStopping:
		return "STOPPING"
	case PhaseProcessing:
		return "PROCESSING"
	case PhaseClosing:
		return "CLOSING"
	case PhaseComplete:
		return "COMPLETE"
	default:
		return "UNKNOWN"
	}
}

// ShutdownResource 需要关闭的资源接口
type ShutdownResource interface {
	// Name 返回资源名称
	Name() string
	// Shutdown 关闭资源
	Shutdown(ctx context.Context) error
	// Priority 返回关闭优先级（数字越小越先关闭）
	Priority() int
}

// GracefulShutdown 优雅关闭管理器
type GracefulShutdown struct {
	server           *http.Server
	gateway          GatewayResource
	monitoring       MonitoringResource
	tracer           TracerResource
	resources        []ShutdownResource
	timeout          time.Duration
	phase            ShutdownPhase
	phaseChan        chan ShutdownPhase
	mu               sync.RWMutex
	shutdownComplete chan struct{}
}

// GatewayResource 网关资源接口
type GatewayResource interface {
	Shutdown(ctx context.Context) error
}

// MonitoringResource 监控资源接口
type MonitoringResource interface {
	Shutdown(ctx context.Context) error
}

// TracerResource 追踪资源接口
type TracerResource interface {
	Shutdown(ctx context.Context) error
}

// Config 优雅关闭配置
type Config struct {
	// 总超时时间
	Timeout time.Duration
	// 停止接受新请求的超时
	StopAcceptingTimeout time.Duration
	// 等待现有请求完成的超时
	WaitRequestsTimeout time.Duration
	// 强制关闭超时
	ForceShutdownTimeout time.Duration
}

// DefaultConfig 返回默认配置
func DefaultConfig() *Config {
	return &Config{
		Timeout:               30 * time.Second,
		StopAcceptingTimeout:  5 * time.Second,
		WaitRequestsTimeout:    20 * time.Second,
		ForceShutdownTimeout:   25 * time.Second,
	}
}

// NewGracefulShutdown 创建优雅关闭管理器
func NewGracefulShutdown(server *http.Server, timeout time.Duration) *GracefulShutdown {
	return &GracefulShutdown{
		server:           server,
		timeout:          timeout,
		phase:            PhaseIdle,
		phaseChan:        make(chan ShutdownPhase, 1),
		shutdownComplete: make(chan struct{}),
	}
}

// SetGateway 设置网关资源
func (g *GracefulShutdown) SetGateway(gateway GatewayResource) {
	g.mu.Lock()
	defer g.mu.Unlock()
	g.gateway = gateway
}

// SetMonitoring 设置监控资源
func (g *GracefulShutdown) SetMonitoring(monitoring MonitoringResource) {
	g.mu.Lock()
	defer g.mu.Unlock()
	g.monitoring = monitoring
}

// SetTracer 设置追踪资源
func (g *GracefulShutdown) SetTracer(tracer TracerResource) {
	g.mu.Lock()
	defer g.mu.Unlock()
	g.tracer = tracer
}

// AddResource 添加需要关闭的资源
func (g *GracefulShutdown) AddResource(resource ShutdownResource) {
	g.mu.Lock()
	defer g.mu.Unlock()
	g.resources = append(g.resources, resource)
}

// Start 启动优雅关闭监听
func (g *GracefulShutdown) Start() {
	// 监听系统信号
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)

	// 阻塞等待信号
	sig := <-quit
	logging.LogInfo("接收到关闭信号", logging.String("signal", sig.String()))

	// 执行优雅关闭
	g.Shutdown()
}

// Shutdown 执行优雅关闭流程
func (g *GracefulShutdown) Shutdown() {
	g.updatePhase(PhaseInitiating)

	// 创建总上下文，带超时控制
	ctx, cancel := context.WithTimeout(context.Background(), g.timeout)
	defer cancel()

	// 执行分阶段关闭
	g.executeShutdown(ctx)

	close(g.shutdownComplete)
}

// executeShutdown 执行分阶段关闭
func (g *GracefulShutdown) executeShutdown(ctx context.Context) {
	// 阶段1: 停止接受新请求
	g.updatePhase(PhaseStopping)
	if err := g.stopAccepting(ctx); err != nil {
		logging.LogError("停止接受新请求失败", logging.Err(err))
	}

	// 阶段2: 等待现有请求完成
	g.updatePhase(PhaseProcessing)
	if err := g.waitRequests(ctx); err != nil {
		logging.LogError("等待现有请求完成失败", logging.Err(err))
	}

	// 阶段3: 关闭HTTP服务器
	g.updatePhase(PhaseClosing)
	if err := g.server.Shutdown(ctx); err != nil {
		logging.LogError("HTTP服务器关闭失败", logging.Err(err))
	}

	// 阶段4: 关闭网关资源
	if g.gateway != nil {
		if err := g.gateway.Shutdown(ctx); err != nil {
			logging.LogError("网关资源关闭失败", logging.Err(err))
		}
	}

	// 阶段5: 关闭追踪资源
	if g.tracer != nil {
		if err := g.tracer.Shutdown(ctx); err != nil {
			logging.LogError("追踪资源关闭失败", logging.Err(err))
		}
	}

	// 阶段6: 关闭监控资源
	if g.monitoring != nil {
		if err := g.monitoring.Shutdown(ctx); err != nil {
			logging.LogError("监控资源关闭失败", logging.Err(err))
		}
	}

	// 阶段7: 关闭其他自定义资源
	g.closeResources(ctx)

	g.updatePhase(PhaseComplete)
	logging.LogInfo("优雅关闭完成")
}

// stopAccepting 停止接受新请求
func (g *GracefulShutdown) stopAccepting(ctx context.Context) error {
	logging.LogInfo("停止接受新请求...")
	// 设置服务器为不接受新连接状态
	// 这里可以添加额外的逻辑，比如从负载均衡器摘除
	return nil
}

// waitRequests 等待现有请求完成
func (g *GracefulShutdown) waitRequests(ctx context.Context) error {
	logging.LogInfo("等待现有请求完成...")
	// 这里可以添加逻辑来跟踪活跃连接
	// 等待所有活跃连接完成或超时
	return nil
}

// closeResources 关闭自定义资源
func (g *GracefulShutdown) closeResources(ctx context.Context) {
	g.mu.RLock()
	resources := make([]ShutdownResource, len(g.resources))
	copy(resources, g.resources)
	g.mu.RUnlock()

	// 按优先级排序关闭
	for _, resource := range resources {
		logging.LogInfo("关闭资源", logging.String("resource", resource.Name()))
		if err := resource.Shutdown(ctx); err != nil {
			logging.LogError("资源关闭失败",
				logging.String("resource", resource.Name()),
				logging.Err(err))
		}
	}
}

// updatePhase 更新关闭阶段
func (g *GracefulShutdown) updatePhase(phase ShutdownPhase) {
	g.mu.Lock()
	g.phase = phase
	g.mu.Unlock()

	select {
	case g.phaseChan <- phase:
	default:
	}

	logging.LogInfo("关闭阶段", logging.String("phase", phase.String()))
}

// GetPhase 获取当前关闭阶段
func (g *GracefulShutdown) GetPhase() ShutdownPhase {
	g.mu.RLock()
	defer g.mu.RUnlock()
	return g.phase
}

// WaitForShutdown 等待关闭完成
func (g *GracefulShutdown) WaitForShutdown() {
	<-g.shutdownComplete
}

// IsShutdown 检查是否已关闭
func (g *GracefulShutdown) IsShutdown() bool {
	select {
	case <-g.shutdownComplete:
		return true
	default:
		return false
	}
}

// ForceShutdown 强制关闭（紧急情况）
func (g *GracefulShutdown) ForceShutdown() {
	logging.LogWarn("执行强制关闭...")

	// 立即关闭服务器
	if err := g.server.Close(); err != nil {
		logging.LogError("强制关闭服务器失败", logging.Err(err))
	}

	// 标记关闭完成
	close(g.shutdownComplete)
}

// ShutdownHandler HTTP处理器，用于触发关闭
func (g *GracefulShutdown) ShutdownHandler(c *gin.Context) {
	if c.Request.Method != http.MethodPost {
		c.JSON(http.StatusMethodNotAllowed, gin.H{
			"success": false,
			"error":   "Method not allowed",
		})
		return
	}

	// 在后台执行关闭
	go func() {
		g.Shutdown()
	}()

	c.JSON(http.StatusAccepted, gin.H{
		"success": true,
		"message": "Graceful shutdown initiated",
	})
}
