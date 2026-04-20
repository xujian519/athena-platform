package router

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"
	"sync/atomic"
	"time"

	"github.com/athena-workspace/gateway-unified/internal/logging"
	"github.com/athena-workspace/gateway-unified/internal/websocket/protocol"
	"github.com/athena-workspace/gateway-unified/internal/websocket/session"
)

// HandlerFunc 消息处理函数
type HandlerFunc func(ctx context.Context, msg *protocol.Message, sess *session.Session) error

// Router 消息路由器
type Router struct {
	handlers      map[protocol.MessageType]HandlerFunc
	agentHandlers map[protocol.AgentType]HandlerFunc
	mu            sync.RWMutex
	ctx           context.Context
	cancel        context.CancelFunc

	// 新增：会话管理器引用（用于消息转发）
	sessionManager *session.Manager

	// 新增：消息统计
	messagesRouted atomic.Int64
	messagesBroadcast atomic.Int64
	messagesForwarded atomic.Int64
}

// NewRouter 创建消息路由器
func NewRouter(sessionMgr *session.Manager) *Router {
	ctx, cancel := context.WithCancel(context.Background())

	router := &Router{
		handlers:        make(map[protocol.MessageType]HandlerFunc),
		agentHandlers:   make(map[protocol.AgentType]HandlerFunc),
		ctx:             ctx,
		cancel:          cancel,
		sessionManager:  sessionMgr,
	}

	// 注册默认处理器
	router.registerDefaultHandlers()

	return router
}

// SetSessionManager 设置会话管理器
func (r *Router) SetSessionManager(manager *session.Manager) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.sessionManager = manager
}

// registerDefaultHandlers 注册默认处理器
func (r *Router) registerDefaultHandlers() {
	// 握手处理器
	r.RegisterHandler(protocol.MessageTypeHandshake, r.handleHandshake)

	// 任务处理器
	r.RegisterHandler(protocol.MessageTypeTask, r.handleTask)

	// 查询处理器
	r.RegisterHandler(protocol.MessageTypeQuery, r.handleQuery)

	// 取消处理器
	r.RegisterHandler(protocol.MessageTypeCancel, r.handleCancel)

	// Ping处理器
	r.RegisterHandler(protocol.MessageTypePing, r.handlePing)
}

// RegisterHandler 注册消息处理器
func (r *Router) RegisterHandler(msgType protocol.MessageType, handler HandlerFunc) {
	r.mu.Lock()
	defer r.mu.Unlock()

	r.handlers[msgType] = handler
}

// RegisterAgentHandler 注册Agent处理器
func (r *Router) RegisterAgentHandler(agentType protocol.AgentType, handler HandlerFunc) {
	r.mu.Lock()
	defer r.mu.Unlock()

	r.agentHandlers[agentType] = handler
}

// Route 路由消息
func (r *Router) Route(msg *protocol.Message, sess *session.Session) error {
	// 检查会话是否有效
	if sess == nil || sess.IsClosed() {
		return fmt.Errorf("无效的会话")
	}

	// 更新会话活跃时间
	sess.UpdateLastActive()

	// DEBUG: 打印收到的消息
	fmt.Printf("[DEBUG] 收到消息: ID=%s, Type=%s, SessionID=%s\n", msg.ID, msg.Type, sess.ID)

	// 查找处理器
	r.mu.RLock()
	handler, exists := r.handlers[msg.Type]
	r.mu.RUnlock()

	if !exists {
		err := r.sendError(sess, msg, "UNKNOWN_MESSAGE_TYPE", fmt.Sprintf("未知的消息类型: %s", msg.Type))
		if err != nil {
			return err
		}
		return fmt.Errorf("未知的消息类型: %s", msg.Type)
	}

	// DEBUG: 打印找到处理器
	fmt.Printf("[DEBUG] 找到处理器: %s\n", msg.Type)

	// 执行处理器
	if err := handler(r.ctx, msg, sess); err != nil {
		return r.sendError(sess, msg, "HANDLER_ERROR", err.Error())
	}

	return nil
}

// RouteToAgent 路由到指定Agent
func (r *Router) RouteToAgent(agentType protocol.AgentType, msg *protocol.Message, sess *session.Session) error {
	r.mu.RLock()
	handler, exists := r.agentHandlers[agentType]
	r.mu.RUnlock()

	if !exists {
		return fmt.Errorf("未找到Agent处理器: %s", agentType)
	}

	return handler(r.ctx, msg, sess)
}

// Close 关闭路由器
func (r *Router) Close() {
	r.cancel()
}

// ==================== 新增：消息转发和广播功能 ====================

// ForwardMessage 转发消息到另一个会话
func (r *Router) ForwardMessage(originalMsg *protocol.Message, targetSessionID string) error {
	if r.sessionManager == nil {
		return fmt.Errorf("会话管理器未设置")
	}

	// 获取目标会话
	targetSess, exists := r.sessionManager.GetSession(targetSessionID)
	if !exists {
		return fmt.Errorf("目标会话不存在: %s", targetSessionID)
	}

	// 创建转发消息
	forwardMsg := protocol.NewMessage(originalMsg.Type, targetSessionID, originalMsg.Data)
	forwardMsg.Data["forwarded_from"] = originalMsg.SessionID
	forwardMsg.Data["original_message_id"] = originalMsg.ID

	// 发送消息
	if err := r.sendMessage(targetSess, forwardMsg); err != nil {
		return fmt.Errorf("转发消息失败: %w", err)
	}

	r.messagesForwarded.Add(1)
	logging.LogInfo("消息已转发",
		logging.String("from", originalMsg.SessionID),
		logging.String("to", targetSessionID),
		logging.String("message_id", originalMsg.ID),
	)

	return nil
}

// BroadcastToAll 广播消息到所有会话（除发送者外）
func (r *Router) BroadcastToAll(msg *protocol.Message, excludeSender bool) error {
	if r.sessionManager == nil {
		return fmt.Errorf("会话管理器未设置")
	}

	sessions := r.sessionManager.GetAllSessions()
	successCount := 0

	for _, sess := range sessions {
		// 排除发送者
		if excludeSender && sess.ID == msg.SessionID {
			continue
		}

		// 创建广播消息
		broadcastMsg := protocol.NewMessage(msg.Type, sess.ID, msg.Data)
		broadcastMsg.Data["broadcast_from"] = msg.SessionID
		broadcastMsg.Data["original_message_id"] = msg.ID

		if err := r.sendMessage(sess, broadcastMsg); err != nil {
			logging.LogError("广播发送失败",
				logging.Err(err),
				logging.String("session_id", sess.ID),
			)
			continue
		}
		successCount++
	}

	r.messagesBroadcast.Add(int64(successCount))
	logging.LogInfo("消息已广播",
		logging.Int("count", successCount),
		logging.String("message_id", msg.ID),
	)

	return nil
}

// BroadcastToAgentType 广播消息到指定Agent类型的所有会话
func (r *Router) BroadcastToAgentType(msg *protocol.Message, agentType protocol.AgentType) error {
	if r.sessionManager == nil {
		return fmt.Errorf("会话管理器未设置")
	}

	sessions := r.sessionManager.GetAllSessions()
	successCount := 0

	for _, sess := range sessions {
		// 检查会话是否匹配Agent类型
		// 假设会话元数据中有agent_type字段
		sessAgentType, ok := sess.Metadata["agent_type"].(string)
		if !ok || sessAgentType != string(agentType) {
			continue
		}

		// 创建广播消息
		broadcastMsg := protocol.NewMessage(msg.Type, sess.ID, msg.Data)
		broadcastMsg.Data["broadcast_from"] = msg.SessionID
		broadcastMsg.Data["original_message_id"] = msg.ID

		if err := r.sendMessage(sess, broadcastMsg); err != nil {
			logging.LogError("广播发送失败",
				logging.Err(err),
				logging.String("session_id", sess.ID),
			)
			continue
		}
		successCount++
	}

	r.messagesBroadcast.Add(int64(successCount))
	logging.LogInfo("消息已广播到Agent类型",
		logging.String("agent_type", string(agentType)),
		logging.Int("count", successCount),
		logging.String("message_id", msg.ID),
	)

	return nil
}

// GetStats 获取路由统计信息
func (r *Router) GetStats() map[string]interface{} {
	return map[string]interface{}{
		"messages_routed":     r.messagesRouted.Load(),
		"messages_broadcast":  r.messagesBroadcast.Load(),
		"messages_forwarded":  r.messagesForwarded.Load(),
		"handlers_count":      len(r.handlers),
		"agent_handlers_count": len(r.agentHandlers),
	}
}

// === 默认处理器 ===

// handleHandshake 处理握手
func (r *Router) handleHandshake(ctx context.Context, msg *protocol.Message, sess *session.Session) error {
	// 解析握手请求
	handshakeReq, err := r.parseHandshakeRequest(msg)
	if err != nil {
		return r.sendError(sess, msg, "INVALID_HANDSHAKE", err.Error())
	}

	// 验证认证Token（TODO: 实现真正的认证）
	if handshakeReq.AuthToken == "" {
		return r.sendError(sess, msg, "AUTH_REQUIRED", "需要认证Token")
	}

	// 创建握手响应
	response := &protocol.HandshakeResponse{
		Message: protocol.Message{
			ID:        msg.ID,
			Type:      protocol.MessageTypeHandshake,
			Timestamp: GetCurrentTimestamp(),
			SessionID: sess.ID,
			Data:      make(map[string]interface{}),
		},
		SessionID:         sess.ID,
		ServerID:          "athena-gateway-v1",
		Capabilities:      []string{"task", "query", "progress", "notify"},
		HeartbeatInterval: 30,
	}

	// 发送响应
	return r.sendMessage(sess, &response.Message)
}

// handleTask 处理任务
func (r *Router) handleTask(ctx context.Context, msg *protocol.Message, sess *session.Session) error {
	// 解析任务请求
	taskReq, err := r.parseTaskRequest(msg)
	if err != nil {
		return r.sendError(sess, msg, "INVALID_TASK", err.Error())
	}

	// 路由到对应的Agent
	if err := r.RouteToAgent(taskReq.TargetAgent, msg, sess); err != nil {
		return r.sendError(sess, msg, "AGENT_ERROR", err.Error())
	}

	// 发送确认响应
	ack := protocol.NewResponse(sess.ID, true, map[string]interface{}{
		"task_id":   msg.ID,
		"status":    "queued",
		"agent":     string(taskReq.TargetAgent),
		"task_type": taskReq.TaskType,
	}, nil)

	return r.sendMessage(sess, &ack.Message)
}

// handleQuery 处理查询
func (r *Router) handleQuery(ctx context.Context, msg *protocol.Message, sess *session.Session) error {
	// TODO: 实现查询逻辑
	response := protocol.NewResponse(sess.ID, true, map[string]interface{}{
		"query_type": msg.Data["type"],
		"result":     "查询结果",
	}, nil)

	return r.sendMessage(sess, &response.Message)
}

// handleCancel 处理取消
func (r *Router) handleCancel(ctx context.Context, msg *protocol.Message, sess *session.Session) error {
	// TODO: 实现取消逻辑
	response := protocol.NewResponse(sess.ID, true, map[string]interface{}{
		"cancelled_task_id": msg.Data["task_id"],
		"status":            "cancelled",
	}, nil)

	return r.sendMessage(sess, &response.Message)
}

// handlePing 处理心跳
func (r *Router) handlePing(ctx context.Context, msg *protocol.Message, sess *session.Session) error {
	pong := protocol.NewMessage(protocol.MessageTypePong, sess.ID, map[string]interface{}{
		"ping_id": msg.ID,
	})

	return r.sendMessage(sess, pong)
}

// === 辅助方法 ===

// parseHandshakeRequest 解析握手请求
func (r *Router) parseHandshakeRequest(msg *protocol.Message) (*protocol.HandshakeRequest, error) {
	data, err := json.Marshal(msg.Data)
	if err != nil {
		return nil, err
	}

	var req protocol.HandshakeRequest
	if err := json.Unmarshal(data, &req); err != nil {
		return nil, err
	}

	req.Message = *msg
	return &req, nil
}

// parseTaskRequest 解析任务请求
func (r *Router) parseTaskRequest(msg *protocol.Message) (*protocol.TaskRequest, error) {
	data, err := json.Marshal(msg.Data)
	if err != nil {
		return nil, err
	}

	var req protocol.TaskRequest
	if err := json.Unmarshal(data, &req); err != nil {
		return nil, err
	}

	req.Message = *msg
	return &req, nil
}

// sendMessage 发送消息
func (r *Router) sendMessage(sess *session.Session, msg *protocol.Message) error {
	data, err := json.Marshal(msg)
	if err != nil {
		return err
	}

	return sess.SendToSession(data)
}

// sendError 发送错误消息
func (r *Router) sendError(sess *session.Session, originalMsg *protocol.Message, code, message string) error {
	errorResp := protocol.NewErrorResponse(sess.ID, code, message, "")
	errorResp.ID = originalMsg.ID // 使用原始消息ID

	return r.sendMessage(sess, &errorResp.Message)
}

// GetCurrentTimestamp 获取当前时间戳（辅助函数）
func GetCurrentTimestamp() int64 {
	return time.Now().UnixNano()
}
