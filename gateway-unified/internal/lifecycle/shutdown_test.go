// Package lifecycle - 优雅关闭测试
package lifecycle

import (
	"context"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"github.com/gin-gonic/gin"
)

// TestDefaultConfig 测试默认配置
func TestDefaultConfig(t *testing.T) {
	cfg := DefaultConfig()

	if cfg.Timeout != 30*time.Second {
		t.Errorf("期望超时30秒，实际为%v", cfg.Timeout)
	}

	if cfg.StopAcceptingTimeout != 5*time.Second {
		t.Errorf("期望停止接受超时5秒，实际为%v", cfg.StopAcceptingTimeout)
	}

	if cfg.WaitRequestsTimeout != 20*time.Second {
		t.Errorf("期望等待请求超时20秒，实际为%v", cfg.WaitRequestsTimeout)
	}
}

// TestNewGracefulShutdown 测试创建优雅关闭管理器
func TestNewGracefulShutdown(t *testing.T) {
	server := &http.Server{}
	timeout := 10 * time.Second

	gs := NewGracefulShutdown(server, timeout)

	if gs == nil {
		t.Fatal("期望非nil")
	}

	if gs.server != server {
		t.Error("服务器未正确设置")
	}

	if gs.timeout != timeout {
		t.Errorf("超时未正确设置")
	}
}

// TestSetGateway 测试设置网关资源
func TestSetGateway(t *testing.T) {
	server := &http.Server{}
	gs := NewGracefulShutdown(server, 5*time.Second)

	// 创建模拟网关
	mockGateway := &mockGateway{}
	gs.SetGateway(mockGateway)

	if gs.gateway != mockGateway {
		t.Error("网关未正确设置")
	}
}

// TestAddResource 测试添加资源
func TestAddResource(t *testing.T) {
	server := &http.Server{}
	gs := NewGracefulShutdown(server, 5*time.Second)

	// 添加模拟资源
	resource := &mockResource{name: "test-resource", priority: 1}
	gs.AddResource(resource)

	gs.mu.RLock()
	count := len(gs.resources)
	gs.mu.RUnlock()

	if count != 1 {
		t.Errorf("期望1个资源，实际为%d", count)
	}
}

// TestGetPhase 测试获取关闭阶段
func TestGetPhase(t *testing.T) {
	server := &http.Server{}
	gs := NewGracefulShutdown(server, 5*time.Second)

	phase := gs.GetPhase()
	if phase != PhaseIdle {
		t.Errorf("期望初始阶段为IDLE，实际为%d", phase)
	}
}

// TestUpdatePhase 测试更新关闭阶段
func TestUpdatePhase(t *testing.T) {
	server := &http.Server{}
	gs := NewGracefulShutdown(server, 5*time.Second)

	// 更新到停止阶段
	gs.updatePhase(PhaseStopping)
	if gs.GetPhase() != PhaseStopping {
		t.Errorf("期望阶段为STOPPING，实际为%d", gs.GetPhase())
	}

	// 更新到处理阶段
	gs.updatePhase(PhaseProcessing)
	if gs.GetPhase() != PhaseProcessing {
		t.Errorf("期望阶段为PROCESSING，实际为%d", gs.GetPhase())
	}
}

// TestPhaseString 测试阶段字符串表示
func TestPhaseString(t *testing.T) {
	tests := []struct {
		phase    ShutdownPhase
		expected string
	}{
		{PhaseIdle, "IDLE"},
		{PhaseInitiating, "INITIATING"},
		{PhaseStopping, "STOPPING"},
		{PhaseProcessing, "PROCESSING"},
		{PhaseClosing, "CLOSING"},
		{PhaseComplete, "COMPLETE"},
	}

	for _, tt := range tests {
		t.Run(tt.expected, func(t *testing.T) {
			if got := tt.phase.String(); got != tt.expected {
				t.Errorf("期望'%s'，实际为'%s'", tt.expected, got)
			}
		})
	}
}

// TestShutdownHandler 测试关闭处理器
func TestShutdownHandler(t *testing.T) {
	server := &http.Server{
		Addr: ":0", // 随机端口
	}
	gs := NewGracefulShutdown(server, 5*time.Second)

	// 创建测试路由
	router := gin.New()
	router.POST("/shutdown", gs.ShutdownHandler)

	// 创建测试请求
	req := httptest.NewRequest("POST", "/shutdown", strings.NewReader(""))
	w := httptest.NewRecorder()

	router.ServeHTTP(w, req)

	// 检查响应
	if w.Code != http.StatusAccepted {
		t.Errorf("期望状态202，实际为%d", w.Code)
	}

	// 检查响应体
	body := w.Body.String()
	if !strings.Contains(body, "Graceful shutdown initiated") {
		t.Errorf("响应体应包含'Graceful shutdown initiated'，实际为'%s'", body)
	}

	// 等待关闭完成
	go func() {
		time.Sleep(100 * time.Millisecond)
		gs.updatePhase(PhaseComplete)
		close(gs.shutdownComplete)
	}()

	gs.WaitForShutdown()
}

// TestIsShutdown 测试关闭状态检查
func TestIsShutdown(t *testing.T) {
	server := &http.Server{}
	gs := NewGracefulShutdown(server, 5*time.Second)

	// 初始状态应该不是关闭
	if gs.IsShutdown() {
		t.Error("初始状态不应该是关闭状态")
	}

	// 模拟关闭完成
	close(gs.shutdownComplete)

	// 现在应该是关闭状态
	if !gs.IsShutdown() {
		t.Error("关闭后应该是关闭状态")
	}
}

// TestForceShutdown 测试强制关闭
func TestForceShutdown(t *testing.T) {
	server := &http.Server{
		Addr: ":0",
	}
	gs := NewGracefulShutdown(server, 5*time.Second)

	// 执行强制关闭
	gs.ForceShutdown()

	// 等待一小段时间确保关闭完成
	time.Sleep(50 * time.Millisecond)

	if !gs.IsShutdown() {
		t.Error("强制关闭后应该是关闭状态")
	}
}

// Mock implementations

type mockGateway struct {
	shutdownCalled bool
}

func (m *mockGateway) Shutdown(ctx context.Context) error {
	m.shutdownCalled = true
	return nil
}

type mockResource struct {
	name     string
	priority int
}

func (m *mockResource) Name() string {
	return m.name
}

func (m *mockResource) Shutdown(ctx context.Context) error {
	return nil
}

func (m *mockResource) Priority() int {
	return m.priority
}
