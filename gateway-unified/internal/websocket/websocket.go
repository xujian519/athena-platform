package websocket

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"sync"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/gorilla/websocket"
	"github.com/athena-workspace/gateway-unified/internal/logging"
	"github.com/athena-workspace/gateway-unified/internal/websocket/canvas"
	"github.com/athena-workspace/gateway-unified/internal/websocket/protocol"
	"github.com/athena-workspace/gateway-unified/internal/websocket/router"
	"github.com/athena-workspace/gateway-unified/internal/websocket/session"
)

// Controller WebSocket控制器
type Controller struct {
	sessionManager *session.Manager
	messageRouter  *router.Router
	canvasHost     *canvas.CanvasHost
	upgrader       websocket.Upgrader
	mu             sync.RWMutex
	ctx            context.Context
	cancel         context.CancelFunc
}

// Config WebSocket控制器配置
type Config struct {
	// WebSocket升级配置
	ReadBufferSize  int
	WriteBufferSize int
	// 会话管理配置
	HeartbeatInterval int // 心跳间隔（秒）
	SessionTimeout    int // 会话超时（秒）
	// Canvas Host配置
	EnableCanvasHost bool
}

// DefaultConfig 默认配置
func DefaultConfig() *Config {
	return &Config{
		ReadBufferSize:    1024,
		WriteBufferSize:   1024,
		HeartbeatInterval: 30,
		SessionTimeout:    600,
		EnableCanvasHost:  true,
	}
}

// NewController 创建WebSocket控制器
func NewController(config *Config) *Controller {
	if config == nil {
		config = DefaultConfig()
	}

	ctx, cancel := context.WithCancel(context.Background())

	ctrl := &Controller{
		ctx:    ctx,
		cancel: cancel,
		upgrader: websocket.Upgrader{
			ReadBufferSize:  config.ReadBufferSize,
			WriteBufferSize: config.WriteBufferSize,
			CheckOrigin: func(r *http.Request) bool {
				// TODO: 实现更严格的Origin检查
				return true
			},
		},
	}

	// 创建会话管理器
	sessionConfig := &session.ManagerConfig{
		HeartbeatInterval: time.Duration(config.HeartbeatInterval) * time.Second,
		SessionTimeout:    time.Duration(config.SessionTimeout) * time.Second,
	}
	ctrl.sessionManager = session.NewManager(sessionConfig)

	// 创建消息路由器
	ctrl.messageRouter = router.NewRouter()

	// 创建Canvas Host（如果启用）
	if config.EnableCanvasHost {
		ctrl.canvasHost = canvas.NewCanvasHost()
	}

	// 注册Agent处理器
	ctrl.registerAgentHandlers()

	return ctrl
}

// registerAgentHandlers 注册Agent处理器
func (c *Controller) registerAgentHandlers() {
	// 小娜Agent
	c.messageRouter.RegisterAgentHandler(protocol.AgentTypeXiaona, c.handleXiaonaAgent)

	// 小诺Agent
	c.messageRouter.RegisterAgentHandler(protocol.AgentTypeXiaonuo, c.handleXiaonuoAgent)

	// 云熙Agent
	c.messageRouter.RegisterAgentHandler(protocol.AgentTypeYunxi, c.handleYunxiAgent)
}

// HandleWebSocket WebSocket连接处理器
func (c *Controller) HandleWebSocket(ginCtx *gin.Context) {
	// 获取客户端信息
	clientID := ginCtx.Query("client_id")
	if clientID == "" {
		clientID = generateClientID()
	}

	userAgent := ginCtx.GetHeader("User-Agent")
	remoteAddr := ginCtx.ClientIP()

	logging.LogInfo("WebSocket连接请求",
		logging.String("client_id", clientID),
		logging.String("remote_addr", remoteAddr),
		logging.String("user_agent", userAgent),
	)

	// 升级到WebSocket连接
	conn, err := c.upgrader.Upgrade(ginCtx.Writer, ginCtx.Request, nil)
	if err != nil {
		logging.LogError("WebSocket升级失败", logging.Err(err))
		ginCtx.JSON(http.StatusBadRequest, gin.H{
			"error": "WebSocket升级失败",
			"details": err.Error(),
		})
		return
	}

	// 创建会话（传递消息处理器）
	sess, err := c.sessionManager.CreateSession(conn, clientID, userAgent, remoteAddr, c.handleMessage)
	if err != nil {
		logging.LogError("创建会话失败", logging.Err(err))
		conn.Close()
		return
	}

	logging.LogInfo("WebSocket会话已创建",
		logging.String("session_id", sess.ID),
		logging.String("client_id", clientID),
	)

	// 不再需要messageLoop goroutine，readPump会处理消息
	// go c.messageLoop(sess)
}

// handleMessage 处理接收到的消息
func (c *Controller) handleMessage(sess *session.Session, data []byte) error {
	// 解析消息
	var msg protocol.Message
	if err := json.Unmarshal(data, &msg); err != nil {
		logging.LogError("解析消息失败",
			logging.Err(err),
			logging.String("data", string(data)),
		)
		return err
	}

	// DEBUG: 打印解析后的消息
	fmt.Printf("[DEBUG] 收到消息: ID=%s, Type=%s, SessionID=%s\n", msg.ID, msg.Type, sess.ID)

	// 路由消息
	if err := c.messageRouter.Route(&msg, sess); err != nil {
		logging.LogError("路由消息失败",
			logging.Err(err),
			logging.String("message_id", msg.ID),
			logging.String("message_type", string(msg.Type)),
		)
		return err
	}

	return nil
}

// messageLoop 消息处理循环
func (c *Controller) messageLoop(sess *session.Session) {
	defer func() {
		if r := recover(); r != nil {
			logging.LogError("消息循环panic",
				logging.Any("error", r),
				logging.String("session_id", sess.ID),
			)
		}
	}()

	for {
		_, data, err := sess.Conn.ReadMessage()
		if err != nil {
			if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseAbnormalClosure) {
				logging.LogError("读取消息失败",
					logging.Err(err),
					logging.String("session_id", sess.ID),
				)
			}
			break
		}

		// DEBUG: 打印原始消息
		fmt.Printf("[DEBUG] 读取到原始消息: %s\n", string(data))

		// 解析消息
		var msg protocol.Message
		if err := json.Unmarshal(data, &msg); err != nil {
			logging.LogError("解析消息失败",
				logging.Err(err),
				logging.String("data", string(data)),
			)
			continue
		}

		// DEBUG: 打印解析后的消息
		fmt.Printf("[DEBUG] 解析后的消息: ID=%s, Type=%s\n", msg.ID, msg.Type)

		// 路由消息
		if err := c.messageRouter.Route(&msg, sess); err != nil {
			logging.LogError("路由消息失败",
				logging.Err(err),
				logging.String("message_id", msg.ID),
				logging.String("message_type", string(msg.Type)),
			)
		}
	}

	logging.LogInfo("消息循环结束", logging.String("session_id", sess.ID))
}

// BroadcastToAll 向所有会话广播消息
func (c *Controller) BroadcastToAll(message *protocol.Message) error {
	data, err := json.Marshal(message)
	if err != nil {
		return err
	}

	c.sessionManager.BroadcastToAll(data)
	return nil
}

// SendToSession 向指定会话发送消息
func (c *Controller) SendToSession(sessionID string, message *protocol.Message) error {
	sess, exists := c.sessionManager.GetSession(sessionID)
	if !exists {
		return fmt.Errorf("会话不存在: %s", sessionID)
	}

	data, err := json.Marshal(message)
	if err != nil {
		return err
	}

	return sess.SendToSession(data)
}

// SendToClient 向指定客户端发送消息
func (c *Controller) SendToClient(clientID string, message *protocol.Message) error {
	sess, exists := c.sessionManager.GetSessionByClient(clientID)
	if !exists {
		return fmt.Errorf("客户端会话不存在: %s", clientID)
	}

	data, err := json.Marshal(message)
	if err != nil {
		return err
	}

	return sess.SendToSession(data)
}

// GetStats 获取统计信息
func (c *Controller) GetStats() map[string]interface{} {
	c.mu.RLock()
	defer c.mu.RUnlock()

	return map[string]interface{}{
		"session_count": c.sessionManager.GetSessionCount(),
		"active_sessions": c.sessionManager.GetAllSessions(),
	}
}

// Close 关闭控制器
func (c *Controller) Close() error {
	c.cancel()

	if c.sessionManager != nil {
		c.sessionManager.Close()
	}

	if c.messageRouter != nil {
		c.messageRouter.Close()
	}

	if c.canvasHost != nil {
		c.canvasHost.Close()
	}

	return nil
}

// === Agent处理器 ===

// handleXiaonaAgent 处理小娜Agent
func (c *Controller) handleXiaonaAgent(ctx context.Context, msg *protocol.Message, sess *session.Session) error {
	logging.LogInfo("路由到小娜Agent",
		logging.String("message_id", msg.ID),
		logging.String("session_id", sess.ID),
	)

	// TODO: 实现与小娜Agent的通信
	// 这里应该通过gRPC/HTTP调用Python的小娜Agent

	// 临时响应
	response := protocol.NewResponse(sess.ID, true, map[string]interface{}{
		"agent":  "xiaona",
		"status": "processing",
		"task_id": msg.ID,
	}, nil)

	data, _ := json.Marshal(response)
	return sess.SendToSession(data)
}

// handleXiaonuoAgent 处理小诺Agent
func (c *Controller) handleXiaonuoAgent(ctx context.Context, msg *protocol.Message, sess *session.Session) error {
	logging.LogInfo("路由到小诺Agent",
		logging.String("message_id", msg.ID),
		logging.String("session_id", sess.ID),
	)

	// TODO: 实现与小诺Agent的通信

	response := protocol.NewResponse(sess.ID, true, map[string]interface{}{
		"agent":  "xiaonuo",
		"status": "coordinating",
		"task_id": msg.ID,
	}, nil)

	data, _ := json.Marshal(response)
	return sess.SendToSession(data)
}

// handleYunxiAgent 处理云熙Agent
func (c *Controller) handleYunxiAgent(ctx context.Context, msg *protocol.Message, sess *session.Session) error {
	logging.LogInfo("路由到云熙Agent",
		logging.String("message_id", msg.ID),
		logging.String("session_id", sess.ID),
	)

	// TODO: 实现与云熙Agent的通信

	response := protocol.NewResponse(sess.ID, true, map[string]interface{}{
		"agent":  "yunxi",
		"status": "processing",
		"task_id": msg.ID,
	}, nil)

	data, _ := json.Marshal(response)
	return sess.SendToSession(data)
}

// === 辅助函数 ===

// generateClientID 生成客户端ID
func generateClientID() string {
	return fmt.Sprintf("client_%d", time.Now().UnixNano())
}
