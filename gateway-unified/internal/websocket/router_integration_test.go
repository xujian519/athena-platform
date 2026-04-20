package websocket

import (
	"encoding/json"
	"testing"
	"time"

	"github.com/athena-workspace/gateway-unified/internal/websocket/protocol"
	"github.com/fasthttp/websocket"
)

// TestRouterMessageForwarding 测试路由器消息转发
func TestRouterMessageForwarding(t *testing.T) {
	// 创建会话管理器
	sessionConfig := &session.ManagerConfig{
		HeartbeatInterval: 30 * time.Second,
		SessionTimeout:    600 * time.Second,
	}
	sessionMgr := session.NewManager(sessionConfig)

	// 创建路由器
	router := router.NewRouter(sessionMgr)

	// 创建测试会话
	conn1, _ := websocket.NewClient(
		websocket.Config{
			HandshakeTimeout: 10 * time.Second,
		},
		nil,
	)
	sess1, _ := sessionMgr.CreateSession(conn1, "client_1", "test", "127.0.0.1", nil)

	conn2, _ := websocket.NewClient(
		websocket.Config{
			HandshakeTimeout: 10 * time.Second,
		},
		nil,
	)
	sess2, _ := sessionMgr.CreateSession(conn2, "client_2", "test", "127.0.0.1", nil)

	// 创建测试消息
	msg := protocol.NewMessage(protocol.MessageTypeNotify, sess1.ID, map[string]interface{}{
		"type":    "test",
		"message": "Hello from client 1",
	})

	// 测试转发
	err := router.ForwardMessage(&msg.Message, sess2.ID)
	if err != nil {
		t.Errorf("转发消息失败: %v", err)
	}

	// 验证统计信息
	stats := router.GetStats()
	forwarded, ok := stats["messages_forwarded"].(int64)
	if !ok || forwarded != 1 {
		t.Errorf("转发计数不正确: %v", forwarded)
	}

	t.Log("✅ 消息转发测试通过")
}

// TestRouterBroadcastToAll 测试广播到所有会话
func TestRouterBroadcastToAll(t *testing.T) {
	// 创建会话管理器
	sessionConfig := &session.ManagerConfig{
		HeartbeatInterval: 30 * time.Second,
		SessionTimeout:    600 * time.Second,
	}
	sessionMgr := session.NewManager(sessionConfig)

	// 创建路由器
	router := router.NewRouter(sessionMgr)

	// 创建多个测试会话
	for i := 1; i <= 3; i++ {
		conn, _ := websocket.NewClient(
			websocket.Config{
				HandshakeTimeout: 10 * time.Second,
			},
			nil,
		)
		sessionMgr.CreateSession(conn, "client_"+string(rune(i)), "test", "127.0.0.1", nil)
	}

	// 创建广播消息
	msg := protocol.NewMessage(protocol.MessageTypeNotify, "sender_session", map[string]interface{}{
		"type":    "broadcast",
		"message": "Hello everyone",
	})

	// 测试广播
	err := router.BroadcastToAll(&msg.Message, true)
	if err != nil {
		t.Errorf("广播消息失败: %v", err)
	}

	// 验证统计信息
	stats := router.GetStats()
	broadcast, ok := stats["messages_broadcast"].(int64)
	if !ok || broadcast != 3 {
		t.Errorf("广播计数不正确: %v", broadcast)
	}

	t.Log("✅ 广播到所有会话测试通过")
}

// TestRouterBroadcastToAgentType 测试按Agent类型广播
func TestRouterBroadcastToAgentType(t *testing.T) {
	// 创建会话管理器
	sessionConfig := &session.ManagerConfig{
		HeartbeatInterval: 30 * time.Second,
		SessionTimeout:    600 * time.Second,
	}
	sessionMgr := session.NewManager(sessionConfig)

	// 创建路由器
	router := router.NewRouter(sessionMgr)

	// 创建不同类型的测试会话
	for _, agentType := range []protocol.AgentType{
		protocol.AgentTypeXiaona,
		protocol.AgentTypeXiaonuo,
		protocol.AgentTypeYunxi,
	} {
		conn, _ := websocket.NewClient(
			websocket.Config{
				HandshakeTimeout: 10 * time.Second,
			},
			nil,
		)
		sess, _ := sessionMgr.CreateSession(conn, "client_"+string(agentType), "test", "127.0.0.1", nil)
		sess.Metadata["agent_type"] = string(agentType)
	}

	// 创建广播消息
	msg := protocol.NewMessage(protocol.MessageTypeNotify, "sender_session", map[string]interface{}{
		"type":    "broadcast",
		"message": "Hello xiaona agents",
	})

	// 测试按类型广播
	err := router.BroadcastToAgentType(&msg.Message, protocol.AgentTypeXiaona)
	if err != nil {
		t.Errorf("按类型广播失败: %v", err)
	}

	// 验证只广播给指定类型
	stats := router.GetStats()
	broadcast, ok := stats["messages_broadcast"].(int64)
	if !ok || broadcast != 1 {
		t.Errorf("按类型广播计数不正确: %v", broadcast)
	}

	t.Log("✅ 按Agent类型广播测试通过")
}

// TestWebSocketControllerStats 测试控制器统计
func TestWebSocketControllerStats(t *testing.T) {
	config := &Config{
		ReadBufferSize:    1024,
		WriteBufferSize:   1024,
		HeartbeatInterval: 30,
		SessionTimeout:    600,
		EnableCanvasHost:  false,
	}

	ctrl := NewController(config)

	// 获取统计信息
	stats := ctrl.GetStats()

	// 验证统计字段
	if _, ok := stats["session_count"]; !ok {
		t.Error("统计信息应该包含session_count")
	}

	if _, ok := stats["router_stats"]; !ok {
		t.Error("统计信息应该包含router_stats")
	}

	routerStats, ok := stats["router_stats"].(map[string]interface{})
	if !ok {
		t.Fatal("router_stats应该是map类型")
	}

	if _, ok := routerStats["messages_routed"]; !ok {
		t.Error("路由器统计应该包含messages_routed")
	}

	if _, ok := routerStats["messages_broadcast"]; !ok {
		t.Error("路由器统计应该包含messages_broadcast")
	}

	if _, ok := routerStats["messages_forwarded"]; !ok {
		t.Error("路由器统计应该包含messages_forwarded")
	}

	t.Log("✅ 控制器统计测试通过")
}

// TestMessageProtocolCompatibility 测试消息协议兼容性
func TestMessageProtocolCompatibility(t *testing.T) {
	// 创建Go消息
	goMsg := protocol.Message{
		ID:        "test_msg_123",
		Type:      protocol.MessageTypeTask,
		Timestamp: time.Now().UnixNano(),
		SessionID: "test_session",
		Data: map[string]interface{}{
			"task_type":     "patent_analysis",
			"target_agent":  "xiaona",
			"priority":      5,
			"parameters":    map[string]interface{}{
				"patent_id": "CN123456789A",
			},
		},
	}

	// 序列化为JSON
	jsonData, err := json.Marshal(goMsg)
	if err != nil {
		t.Fatalf("序列化失败: %v", err)
	}

	// 反序列化
	var decodedMsg protocol.Message
	err = json.Unmarshal(jsonData, &decodedMsg)
	if err != nil {
		t.Fatalf("反序列化失败: %v", err)
	}

	// 验证字段
	if decodedMsg.ID != goMsg.ID {
		t.Errorf("ID不匹配: %s != %s", decodedMsg.ID, goMsg.ID)
	}

	if decodedMsg.Type != goMsg.Type {
		t.Errorf("Type不匹配: %s != %s", decodedMsg.Type, goMsg.Type)
	}

	if decodedMsg.SessionID != goMsg.SessionID {
		t.Errorf("SessionID不匹配: %s != %s", decodedMsg.SessionID, goMsg.SessionID)
	}

	t.Log("✅ 消息协议兼容性测试通过")
}

// BenchmarkMessageRouting 性能基准测试
func BenchmarkMessageRouting(b *testing.B) {
	sessionConfig := &session.ManagerConfig{
		HeartbeatInterval: 30 * time.Second,
		SessionTimeout:    600 * time.Second,
	}
	sessionMgr := session.NewManager(sessionConfig)
	router := router.NewRouter(sessionMgr)

	// 创建测试会话
	conn, _ := websocket.NewClient(
		websocket.Config{
			HandshakeTimeout: 10 * time.Second,
		},
		nil,
	)
	sess, _ := sessionMgr.CreateSession(conn, "bench_client", "test", "127.0.0.1", nil)

	msg := protocol.NewMessage(protocol.MessageTypePing, sess.ID, map[string]interface{}{
		"timestamp": time.Now().UnixNano(),
	})

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		router.Route(&msg, sess)
	}
}

// BenchmarkMessageBroadcast 性能基准测试
func BenchmarkMessageBroadcast(b *testing.B) {
	sessionConfig := &session.ManagerConfig{
		HeartbeatInterval: 30 * time.Second,
		SessionTimeout:    600 * time.Second,
	}
	sessionMgr := session.NewManager(sessionConfig)
	router := router.NewRouter(sessionMgr)

	// 创建100个测试会话
	for i := 0; i < 100; i++ {
		conn, _ := websocket.NewClient(
			websocket.Config{
				HandshakeTimeout: 10 * time.Second,
			},
			nil,
		)
		sessionMgr.CreateSession(conn, "client_"+string(rune(i)), "test", "127.0.0.1", nil)
	}

	msg := protocol.NewMessage(protocol.MessageTypeNotify, "sender", map[string]interface{}{
		"type": "broadcast",
	})

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		router.BroadcastToAll(&msg.Message, true)
	}
}
