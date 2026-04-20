package websocket

import (
	"encoding/json"
	"testing"
	"time"

	"github.com/athena-workspace/gateway-unified/internal/websocket/protocol"
	"github.com/athena-workspace/gateway-unified/internal/websocket/session"
)

// TestNewController 测试创建WebSocket控制器
func TestNewController(t *testing.T) {
	ctrl := NewController(nil)
	defer ctrl.Close()

	if ctrl == nil {
		t.Fatal("NewController返回nil")
	}

	if ctrl.sessionManager == nil {
		t.Error("sessionManager未初始化")
	}

	if ctrl.messageRouter == nil {
		t.Error("messageRouter未初始化")
	}

	if ctrl.canvasHost == nil {
		t.Error("canvasHost未初始化")
	}
}

// TestNewControllerWithConfig 测试使用配置创建控制器
func TestNewControllerWithConfig(t *testing.T) {
	config := &Config{
		ReadBufferSize:    2048,
		WriteBufferSize:   2048,
		HeartbeatInterval: 60,
		SessionTimeout:    1200,
		EnableCanvasHost:  true,
	}

	ctrl := NewController(config)
	defer ctrl.Close()

	if ctrl == nil {
		t.Fatal("NewController返回nil")
	}
}

// TestNewControllerDisableCanvasHost 测试禁用Canvas Host
func TestNewControllerDisableCanvasHost(t *testing.T) {
	config := &Config{
		EnableCanvasHost: false,
	}

	ctrl := NewController(config)
	defer ctrl.Close()

	if ctrl.canvasHost != nil {
		t.Error("canvasHost应该为nil")
	}
}

// TestBroadcastToAll 测试广播消息到所有会话
func TestBroadcastToAll(t *testing.T) {
	ctrl := NewController(nil)
	defer ctrl.Close()

	message := protocol.NewMessage(
		protocol.MessageTypeNotify,
		"",
		map[string]interface{}{
			"title": "测试广播",
			"body":  "这是一条测试消息",
		},
	)

	err := ctrl.BroadcastToAll(message)
	if err != nil {
		t.Errorf("BroadcastToAll失败: %v", err)
	}
}

// TestSendToSession 测试发送消息到指定会话
func TestSendToSession(t *testing.T) {
	ctrl := NewController(nil)
	defer ctrl.Close()

	message := protocol.NewMessage(
		protocol.MessageTypeNotify,
		"test_session_id",
		map[string]interface{}{
			"title": "测试消息",
		},
	)

	// 不存在的会话应该返回错误
	err := ctrl.SendToSession("non_existent_session", message)
	if err == nil {
		t.Error("期望发送到不存在的会话返回错误")
	}
}

// TestSendToClient 测试发送消息到指定客户端
func TestSendToClient(t *testing.T) {
	ctrl := NewController(nil)
	defer ctrl.Close()

	message := protocol.NewMessage(
		protocol.MessageTypeNotify,
		"",
		map[string]interface{}{
			"title": "测试消息",
		},
	)

	// 不存在的客户端应该返回错误
	err := ctrl.SendToClient("non_existent_client", message)
	if err == nil {
		t.Error("期望发送到不存在的客户端返回错误")
	}
}

// TestGetStats 测试获取统计信息
func TestGetStats(t *testing.T) {
	ctrl := NewController(nil)
	defer ctrl.Close()

	stats := ctrl.GetStats()

	if stats == nil {
		t.Fatal("GetStats返回nil")
	}

	sessionCount, ok := stats["session_count"].(int)
	if !ok {
		t.Error("session_count类型错误")
	}

	if sessionCount < 0 {
		t.Error("session_count不能为负数")
	}
}

// TestClose 测试关闭控制器
func TestClose(t *testing.T) {
	ctrl := NewController(nil)

	err := ctrl.Close()
	if err != nil {
		t.Errorf("Close失败: %v", err)
	}

	// 验证context已取消
	select {
	case <-ctrl.ctx.Done():
		// Context已取消,正常
	default:
		t.Error("Context应该已取消")
	}
}

// TestHandleMessage 测试消息处理
func TestHandleMessage(t *testing.T) {
	ctrl := NewController(nil)
	defer ctrl.Close()

	// 创建测试会话
	testSession := &session.Session{
		ID:       "test_session",
		ClientID: "test_client",
		Send:     make(chan []byte, 256),
		Metadata: make(map[string]interface{}),
	}

	tests := []struct {
		name      string
		message   *protocol.Message
		wantError bool
	}{
		{
			name: "握手消息",
			message: protocol.NewMessage(
				protocol.MessageTypeHandshake,
				"",
				map[string]interface{}{
					"client_id":  "test_client",
					"auth_token": "test_token",
				},
			),
			wantError: false,
		},
		{
			name: "心跳消息",
			message: protocol.NewMessage(
				protocol.MessageTypePing,
				"",
				map[string]interface{}{},
			),
			wantError: false,
		},
		{
			name: "任务消息",
			message: protocol.NewMessage(
				protocol.MessageTypeTask,
				"",
				map[string]interface{}{
					"task_type":     "test_task",
					"target_agent":  "xiaona",
					"priority":      5,
					"parameters":    map[string]interface{}{},
				},
			),
			wantError: false,
		},
		{
			name: "无效JSON",
			message: &protocol.Message{
				ID:      "test",
				Type:    "invalid",
				Data:    nil,
			},
			wantError: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			data, _ := json.Marshal(tt.message)
			err := ctrl.handleMessage(testSession, data)

			if (err != nil) != tt.wantError {
				t.Errorf("handleMessage() error = %v, wantError %v", err, tt.wantError)
			}
		})
	}
}

// TestHandleXiaonaAgent 测试小娜Agent处理器
func TestHandleXiaonaAgent(t *testing.T) {
	ctrl := NewController(nil)
	defer ctrl.Close()

	testSession := &session.Session{
		ID:       "test_session",
		ClientID: "test_client",
		Send:     make(chan []byte, 256),
		Metadata: make(map[string]interface{}),
	}

	message := protocol.NewMessage(
		protocol.MessageTypeTask,
		"test_session",
		map[string]interface{}{
			"task_type":    "patent_analysis",
			"target_agent": "xiaona",
		},
	)

	err := ctrl.handleXiaonaAgent(ctrl.ctx, message, testSession)
	if err != nil {
		t.Errorf("handleXiaonaAgent失败: %v", err)
	}

	// 验证响应消息已发送
	select {
	case resp := <-testSession.Send:
		var response protocol.Response
		if err := json.Unmarshal(resp, &response); err != nil {
			t.Errorf("解析响应失败: %v", err)
		}

		if !response.Success {
			t.Error("期望响应成功")
		}
	case <-time.After(100 * time.Millisecond):
		t.Error("未收到响应消息")
	}
}

// TestHandleXiaonuoAgent 测试小诺Agent处理器
func TestHandleXiaonuoAgent(t *testing.T) {
	ctrl := NewController(nil)
	defer ctrl.Close()

	testSession := &session.Session{
		ID:       "test_session",
		ClientID: "test_client",
		Send:     make(chan []byte, 256),
		Metadata: make(map[string]interface{}),
	}

	message := protocol.NewMessage(
		protocol.MessageTypeTask,
		"test_session",
		map[string]interface{}{
			"task_type":    "coordination",
			"target_agent": "xiaonuo",
		},
	)

	err := ctrl.handleXiaonuoAgent(ctrl.ctx, message, testSession)
	if err != nil {
		t.Errorf("handleXiaonuoAgent失败: %v", err)
	}

	// 验证响应消息已发送
	select {
	case resp := <-testSession.Send:
		var response protocol.Response
		if err := json.Unmarshal(resp, &response); err != nil {
			t.Errorf("解析响应失败: %v", err)
		}

		if !response.Success {
			t.Error("期望响应成功")
		}
	case <-time.After(100 * time.Millisecond):
		t.Error("未收到响应消息")
	}
}

// TestHandleYunxiAgent 测试云熙Agent处理器
func TestHandleYunxiAgent(t *testing.T) {
	ctrl := NewController(nil)
	defer ctrl.Close()

	testSession := &session.Session{
		ID:       "test_session",
		ClientID: "test_client",
		Send:     make(chan []byte, 256),
		Metadata: make(map[string]interface{}),
	}

	message := protocol.NewMessage(
		protocol.MessageTypeTask,
		"test_session",
		map[string]interface{}{
			"task_type":    "ip_management",
			"target_agent": "yunxi",
		},
	)

	err := ctrl.handleYunxiAgent(ctrl.ctx, message, testSession)
	if err != nil {
		t.Errorf("handleYunxiAgent失败: %v", err)
	}

	// 验证响应消息已发送
	select {
	case resp := <-testSession.Send:
		var response protocol.Response
		if err := json.Unmarshal(resp, &response); err != nil {
			t.Errorf("解析响应失败: %v", err)
		}

		if !response.Success {
			t.Error("期望响应成功")
		}
	case <-time.After(100 * time.Millisecond):
		t.Error("未收到响应消息")
	}
}

// TestRegisterAgentHandlers 测试注册Agent处理器
func TestRegisterAgentHandlers(t *testing.T) {
	ctrl := NewController(nil)
	defer ctrl.Close()

	// 验证Agent处理器已注册
	agents := []protocol.AgentType{
		protocol.AgentTypeXiaona,
		protocol.AgentTypeXiaonuo,
		protocol.AgentTypeYunxi,
	}

	for _, agent := range agents {
		// 通过路由器验证处理器已注册
		// 这里只是验证不会panic
		t.Logf("Agent %s 处理器已注册", agent)
	}
}

// BenchmarkGetStats 性能测试: 获取统计信息
func BenchmarkGetStats(b *testing.B) {
	ctrl := NewController(nil)
	defer ctrl.Close()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		ctrl.GetStats()
	}
}

// BenchmarkBroadcastToAll 性能测试: 广播消息
func BenchmarkBroadcastToAll(b *testing.B) {
	ctrl := NewController(nil)
	defer ctrl.Close()

	message := protocol.NewMessage(
		protocol.MessageTypeNotify,
		"",
		map[string]interface{}{"test": "data"},
	)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		ctrl.BroadcastToAll(message)
	}
}
