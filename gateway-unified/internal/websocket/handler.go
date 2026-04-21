package websocket

import (
	"encoding/json"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/gorilla/websocket"
	"github.com/athena-workspace/gateway-unified/internal/logging"
)

// upgrader WebSocket升级器，将HTTP连接升级为WebSocket连接
var upgrader = websocket.Upgrader{
	ReadBufferSize:  1024,
	WriteBufferSize: 1024,
	CheckOrigin: func(r *http.Request) bool {
		// TODO: 生产环境需要验证Origin，防止CSRF攻击
		return true
	},
}

// HandleWebSocket 处理WebSocket连接请求
// 这是标准HTTP处理器，将HTTP连接升级为WebSocket
func (h *Hub) HandleWebSocket(w http.ResponseWriter, r *http.Request) {
	// 升级到WebSocket
	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		logging.LogError("WebSocket升级失败", logging.Err(err))
		return
	}

	// 获取或生成session_id
	sessionID := r.URL.Query().Get("session_id")
	if sessionID == "" {
		sessionID = generateSessionID()
	}

	// 创建客户端
	client := &Client{
		SessionID: sessionID,
		Conn:      &websocketConn{conn},
		Send:      make(chan WSMessage, 256),
	}

	// 注册客户端到Hub
	h.register <- client

	// 启动读写goroutine
	go h.readPump(client)
	go h.writePump(client)
}

// HandleWebSocketGin Gin框架的WebSocket处理器
func (h *Hub) HandleWebSocketGin(c *gin.Context) {
	h.HandleWebSocket(c.Writer, c.Request)
}

// readPump 从WebSocket读取消息的循环
// 每个客户端连接有一个独立的readPump goroutine
func (h *Hub) readPump(client *Client) {
	defer func() {
		h.unregister <- client
		client.Conn.Close()
	}()

	// 设置读取超时（60秒）
	client.Conn.SetReadDeadline(time.Now().Add(60 * time.Second))

	// 设置pong响应处理器
	client.Conn.SetPongHandler(func(string) error {
		client.Conn.SetReadDeadline(time.Now().Add(60 * time.Second))
		return nil
	})

	for {
		_, message, err := client.Conn.ReadMessage()
		if err != nil {
			if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseAbnormalClosure) {
				logging.LogError("WebSocket读取错误",
					logging.Err(err),
					logging.String("session_id", client.SessionID),
				)
			}
			break
		}

		// 解析消息
		var wsMsg WSMessage
		if err := json.Unmarshal(message, &wsMsg); err != nil {
			logging.LogError("JSON解析错误",
				logging.Err(err),
				logging.String("raw_message", string(message)),
			)
			continue
		}

		// 确保消息有session_id
		if wsMsg.SessionID == "" {
			wsMsg.SessionID = client.SessionID
		}

		// 处理消息
		h.handleMessage(client, wsMsg)
	}
}

// writePump 向WebSocket写入消息的循环
// 每个客户端连接有一个独立的writePump goroutine
func (h *Hub) writePump(client *Client) {
	// 心跳ticker（30秒）
	ticker := time.NewTicker(30 * time.Second)
	defer func() {
		ticker.Stop()
		client.Conn.Close()
	}()

	for {
		select {
		case message, ok := <-client.Send:
			if !ok {
				// 通道已关闭
				client.Conn.WriteMessage(websocket.CloseMessage, []byte{})
				return
			}

			// 序列化消息
			data, err := json.Marshal(message)
			if err != nil {
				logging.LogError("JSON序列化错误",
					logging.Err(err),
					logging.String("message_type", message.Type),
				)
				continue
			}

			// 发送消息
			client.Conn.SetWriteDeadline(time.Now().Add(10 * time.Second))
			err = client.Conn.WriteMessage(websocket.TextMessage, data)
			if err != nil {
				logging.LogError("WebSocket写入错误",
					logging.Err(err),
					logging.String("session_id", client.SessionID),
				)
				return
			}

		case <-ticker.C:
			// 发送心跳
			client.Conn.SetWriteDeadline(time.Now().Add(10 * time.Second))
			if err := client.Conn.WriteMessage(websocket.PingMessage, nil); err != nil {
				logging.LogError("心跳发送失败",
					logging.Err(err),
					logging.String("session_id", client.SessionID),
				)
				return
			}
		}
	}
}

// handleMessage 处理接收到的消息
// 根据消息类型分发到不同的处理器
func (h *Hub) handleMessage(client *Client, msg WSMessage) {
	logging.LogInfo("收到WebSocket消息",
		logging.String("type", msg.Type),
		logging.String("session_id", msg.SessionID),
	)

	switch msg.Type {
	case string(TaskCreate):
		h.handleTaskCreate(client, msg)
	case string(UserConfirmResponse):
		h.handleUserConfirmResponse(client, msg)
	case string(UserInterrupt):
		h.handleUserInterrupt(client, msg)
	case string(TaskStart):
		h.handleTaskStart(client, msg)
	case string(TaskPause):
		h.handleTaskPause(client, msg)
	case string(TaskResume):
		h.handleTaskResume(client, msg)
	case string(TaskCancel):
		h.handleTaskCancel(client, msg)
	default:
		logging.LogWarn("未知消息类型",
			logging.String("message_type", msg.Type),
			logging.String("session_id", msg.SessionID),
		)
	}
}

// handleTaskCreate 处理任务创建请求
func (h *Hub) handleTaskCreate(client *Client, msg WSMessage) {
	var payload TaskCreatePayload
	payloadData, err := json.Marshal(msg.Payload)
	if err != nil {
		logging.LogError("Payload序列化失败", logging.Err(err))
		return
	}

	if err := json.Unmarshal(payloadData, &payload); err != nil {
		logging.LogError("解析TaskCreatePayload失败", logging.Err(err))
		h.sendError(client, msg.SessionID, "INVALID_PAYLOAD", "无法解析任务创建载荷")
		return
	}

	logging.LogInfo("任务创建请求",
		logging.String("task_id", payload.TaskID),
		logging.String("task_type", payload.TaskType),
		logging.String("user_input", payload.UserInput),
	)

	// TODO: 实现任务创建逻辑
	// 这里应该将任务发送到任务管理器或调度器

	// 临时响应
	response := WSMessage{
		Type:      string(TaskProgress),
		SessionID: msg.SessionID,
		Timestamp: time.Now().Format(time.RFC3339),
		Payload: TaskProgressPayload{
			TaskID:    payload.TaskID,
			AgentName: "xiaona",
			Progress:  0,
			Message:   "任务已接收，正在处理",
		},
	}

	h.BroadcastToSession(msg.SessionID, response)
}

// handleTaskStart 处理任务开始请求
func (h *Hub) handleTaskStart(client *Client, msg WSMessage) {
	var payload TaskStartPayload
	if err := parsePayload(msg.Payload, &payload); err != nil {
		h.sendError(client, msg.SessionID, "INVALID_PAYLOAD", err.Error())
		return
	}

	logging.LogInfo("任务开始请求", logging.String("task_id", payload.TaskID))
	// TODO: 实现任务开始逻辑
}

// handleTaskPause 处理任务暂停请求
func (h *Hub) handleTaskPause(client *Client, msg WSMessage) {
	var payload TaskPausePayload
	if err := parsePayload(msg.Payload, &payload); err != nil {
		h.sendError(client, msg.SessionID, "INVALID_PAYLOAD", err.Error())
		return
	}

	logging.LogInfo("任务暂停请求",
		logging.String("task_id", payload.TaskID),
		logging.String("reason", payload.Reason),
	)
	// TODO: 实现任务暂停逻辑
}

// handleTaskResume 处理任务恢复请求
func (h *Hub) handleTaskResume(client *Client, msg WSMessage) {
	var payload TaskResumePayload
	if err := parsePayload(msg.Payload, &payload); err != nil {
		h.sendError(client, msg.SessionID, "INVALID_PAYLOAD", err.Error())
		return
	}

	logging.LogInfo("任务恢复请求", logging.String("task_id", payload.TaskID))
	// TODO: 实现任务恢复逻辑
}

// handleTaskCancel 处理任务取消请求
func (h *Hub) handleTaskCancel(client *Client, msg WSMessage) {
	var payload TaskCancelPayload
	if err := parsePayload(msg.Payload, &payload); err != nil {
		h.sendError(client, msg.SessionID, "INVALID_PAYLOAD", err.Error())
		return
	}

	logging.LogInfo("任务取消请求",
		logging.String("task_id", payload.TaskID),
		logging.String("reason", payload.Reason),
	)
	// TODO: 实现任务取消逻辑
}

// handleUserConfirmResponse 处理用户确认响应
func (h *Hub) handleUserConfirmResponse(client *Client, msg WSMessage) {
	var payload UserConfirmResponsePayload
	if err := parsePayload(msg.Payload, &payload); err != nil {
		h.sendError(client, msg.SessionID, "INVALID_PAYLOAD", err.Error())
		return
	}

	logging.LogInfo("用户确认响应",
		logging.String("task_id", payload.TaskID),
		logging.Bool("confirmed", payload.Confirmed),
		logging.String("selection", payload.Selection),
	)
	// TODO: 实现用户确认逻辑
}

// handleUserInterrupt 处理用户中断请求
func (h *Hub) handleUserInterrupt(client *Client, msg WSMessage) {
	var payload UserInterruptPayload
	if err := parsePayload(msg.Payload, &payload); err != nil {
		h.sendError(client, msg.SessionID, "INVALID_PAYLOAD", err.Error())
		return
	}

	logging.LogInfo("用户中断",
		logging.String("task_id", payload.TaskID),
		logging.String("reason", payload.Reason),
		logging.Bool("force", payload.Force),
	)
	// TODO: 实现用户中断逻辑
}

// sendError 发送错误消息
func (h *Hub) sendError(client *Client, sessionID, code, message string) {
	response := WSMessage{
		Type:      string(TaskError),
		SessionID: sessionID,
		Timestamp: time.Now().Format(time.RFC3339),
		Payload: TaskErrorPayload{
			Error: message,
			Code:  code,
		},
	}

	h.BroadcastToSession(sessionID, response)
}

// parsePayload 解析载荷
func parsePayload(payload interface{}, target interface{}) error {
	data, err := json.Marshal(payload)
	if err != nil {
		return err
	}
	return json.Unmarshal(data, target)
}

// generateSessionID 生成会话ID
func generateSessionID() string {
	return "session_" + time.Now().Format("20060102150405")
}

// websocketConn WebSocket连接的包装类型
// 用于抽象底层的websocket.Conn
type websocketConn struct {
	*websocket.Conn
}

// Close 关闭连接
func (w *websocketConn) Close() error {
	if w.Conn != nil {
		return w.Conn.Close()
	}
	return nil
}

// SetReadDeadline 设置读取超时
func (w *websocketConn) SetReadDeadline(t time.Time) error {
	if w.Conn != nil {
		return w.Conn.SetReadDeadline(t)
	}
	return nil
}

// SetWriteDeadline 设置写入超时
func (w *websocketConn) SetWriteDeadline(t time.Time) error {
	if w.Conn != nil {
		return w.Conn.SetWriteDeadline(t)
	}
	return nil
}

// SetPongHandler 设置pong响应处理器
func (w *websocketConn) SetPongHandler(h func(string) error) {
	if w.Conn != nil {
		w.Conn.SetPongHandler(h)
	}
}

// ReadMessage 读取消息
func (w *websocketConn) ReadMessage() (int, []byte, error) {
	if w.Conn != nil {
		return w.Conn.ReadMessage()
	}
	return 0, nil, nil
}

// WriteMessage 写入消息
func (w *websocketConn) WriteMessage(messageType int, data []byte) error {
	if w.Conn != nil {
		return w.Conn.WriteMessage(messageType, data)
	}
	return nil
}
