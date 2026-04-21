package websocket

import (
	"log"
	"sync"

	"github.com/athena-workspace/gateway-unified/internal/logging"
)

// Client WebSocket客户端
type Client struct {
	SessionID string
	Conn      *websocketConn
	Send      chan WSMessage
	mu        sync.Mutex
}

// Hub WebSocket连接管理器
// Hub管理所有WebSocket客户端连接，提供并发安全的客户端注册、注销和消息广播功能
type Hub struct {
	clients    map[string]*Client // 所有连接的客户端，key为session_id
	register   chan *Client       // 客户端注册通道
	unregister chan *Client       // 客户端注销通道
	broadcast  chan WSMessage     // 消息广播通道
	mu         sync.RWMutex       // 读写锁，保护clients map的并发访问
}

// NewHub 创建新的Hub实例
func NewHub() *Hub {
	return &Hub{
		clients:    make(map[string]*Client),
		register:   make(chan *Client),
		unregister: make(chan *Client),
		broadcast:  make(chan WSMessage, 256), // 缓冲通道，容量256
	}
}

// Run 运行Hub事件循环
// 这是一个阻塞方法，应该在独立的goroutine中运行
// 它处理三种事件：客户端注册、客户端注销、消息广播
func (h *Hub) Run() {
	log.Println("WebSocket Hub启动")
	for {
		select {
		case client := <-h.register:
			h.handleRegister(client)

		case client := <-h.unregister:
			h.handleUnregister(client)

		case message := <-h.broadcast:
			h.broadcastMessage(message)
		}
	}
}

// handleRegister 处理客户端注册
func (h *Hub) handleRegister(client *Client) {
	h.mu.Lock()
	h.clients[client.SessionID] = client
	h.mu.Unlock()

	logging.LogInfo("WebSocket客户端注册",
		logging.String("session_id", client.SessionID),
		logging.Int("total_clients", len(h.clients)),
	)
}

// handleUnregister 处理客户端注销
func (h *Hub) handleUnregister(client *Client) {
	h.mu.Lock()
	if _, ok := h.clients[client.SessionID]; ok {
		delete(h.clients, client.SessionID)
		close(client.Send)
	}
	h.mu.Unlock()

	logging.LogInfo("WebSocket客户端断开",
		logging.String("session_id", client.SessionID),
		logging.Int("remaining_clients", len(h.clients)),
	)
}

// broadcastMessage 广播消息到指定会话
func (h *Hub) broadcastMessage(message WSMessage) {
	h.mu.RLock()
	client, exists := h.clients[message.SessionID]
	h.mu.RUnlock()

	if exists {
		select {
		case client.Send <- message:
			logging.LogDebug("消息已发送到客户端",
				logging.String("session_id", client.SessionID),
				logging.String("message_type", message.Type),
			)
		default:
			logging.LogWarn("客户端发送缓冲区满",
				logging.String("session_id", client.SessionID),
			)
		}
	} else {
		logging.LogWarn("客户端不存在",
			logging.String("session_id", message.SessionID),
		)
	}
}

// BroadcastToSession 广播消息到指定会话
func (h *Hub) BroadcastToSession(sessionID string, message WSMessage) {
	message.SessionID = sessionID
	h.broadcast <- message
}

// BroadcastToAll 广播消息到所有会话
func (h *Hub) BroadcastToAll(message WSMessage) {
	h.mu.RLock()
	defer h.mu.RUnlock()

	for sessionID := range h.clients {
		msg := message
		msg.SessionID = sessionID
		h.broadcast <- msg
	}
}

// GetConnectedSessions 获取所有连接的会话ID列表
func (h *Hub) GetConnectedSessions() []string {
	h.mu.RLock()
	defer h.mu.RUnlock()

	sessions := make([]string, 0, len(h.clients))
	for sessionID := range h.clients {
		sessions = append(sessions, sessionID)
	}
	return sessions
}

// GetSessionCount 获取当前连接的会话数量
func (h *Hub) GetSessionCount() int {
	h.mu.RLock()
	defer h.mu.RUnlock()
	return len(h.clients)
}

// GetClient 获取指定会话的客户端
func (h *Hub) GetClient(sessionID string) (*Client, bool) {
	h.mu.RLock()
	defer h.mu.RUnlock()
	client, exists := h.clients[sessionID]
	return client, exists
}

// Close 关闭Hub，断开所有客户端连接
func (h *Hub) Close() {
	h.mu.Lock()
	defer h.mu.Unlock()

	// 关闭所有客户端的发送通道
	for _, client := range h.clients {
		close(client.Send)
	}

	// 清空客户端map
	h.clients = make(map[string]*Client)

	log.Println("WebSocket Hub已关闭")
}
