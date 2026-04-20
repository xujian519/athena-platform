package session

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/google/uuid"
	"github.com/gorilla/websocket"
)

// MessageHandler 消息处理函数
type MessageHandler func(session *Session, data []byte) error

// Session WebSocket会话
type Session struct {
	ID            string
	ClientID      string
	Conn          *websocket.Conn
	Send          chan []byte
	CreatedAt     time.Time
	LastActiveAt  time.Time
	Metadata      map[string]interface{}
	UserAgent     string
	RemoteAddr    string
	closed        bool
	closeOnce     sync.Once
	closeChan     chan struct{}
	mu            sync.RWMutex
	messageHandler MessageHandler // 消息处理器
}

// Manager 会话管理器
type Manager struct {
	sessions      map[string]*Session
	sessionsByClient map[string]*Session // 按ClientID索引
	mu            sync.RWMutex
	ctx           context.Context
	cancel        context.CancelFunc
	heartbeatInterval time.Duration
	sessionTimeout  time.Duration
}

// ManagerConfig 会话管理器配置
type ManagerConfig struct {
	HeartbeatInterval time.Duration // 心跳间隔（默认30秒）
	SessionTimeout    time.Duration // 会话超时（默认10分钟）
}

// DefaultManagerConfig 默认配置
func DefaultManagerConfig() *ManagerConfig {
	return &ManagerConfig{
		HeartbeatInterval: 30 * time.Second,
		SessionTimeout:    10 * time.Minute,
	}
}

// NewManager 创建会话管理器
func NewManager(config *ManagerConfig) *Manager {
	if config == nil {
		config = DefaultManagerConfig()
	}

	ctx, cancel := context.WithCancel(context.Background())

	mgr := &Manager{
		sessions:         make(map[string]*Session),
		sessionsByClient: make(map[string]*Session),
		ctx:              ctx,
		cancel:           cancel,
		heartbeatInterval: config.HeartbeatInterval,
		sessionTimeout:   config.SessionTimeout,
	}

	// 启动后台任务
	go mgr.backgroundTasks()

	return mgr
}

// CreateSession 创建新会话
func (m *Manager) CreateSession(conn *websocket.Conn, clientID, userAgent, remoteAddr string, handler MessageHandler) (*Session, error) {
	sessionID := uuid.New().String()

	session := &Session{
		ID:           sessionID,
		ClientID:     clientID,
		Conn:         conn,
		Send:         make(chan []byte, 256), // 缓冲通道
		CreatedAt:    time.Now(),
		LastActiveAt: time.Now(),
		Metadata:     make(map[string]interface{}),
		UserAgent:    userAgent,
		RemoteAddr:   remoteAddr,
		closeChan:    make(chan struct{}),
		messageHandler: handler,
	}

	m.mu.Lock()
	// 检查是否已存在该客户端的会话
	if oldSession, exists := m.sessionsByClient[clientID]; exists {
		// 关闭旧会话
		m.mu.Unlock()
		oldSession.Close()
		m.mu.Lock()
	}

	m.sessions[sessionID] = session
	m.sessionsByClient[clientID] = session
	m.mu.Unlock()

	// 启动发送和接收goroutine
	go session.writePump()
	go session.readPump(m)

	return session, nil
}

// GetSession 获取会话
func (m *Manager) GetSession(sessionID string) (*Session, bool) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	session, exists := m.sessions[sessionID]
	return session, exists
}

// GetSessionByClient 根据ClientID获取会话
func (m *Manager) GetSessionByClient(clientID string) (*Session, bool) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	session, exists := m.sessionsByClient[clientID]
	return session, exists
}

// RemoveSession 移除会话
func (m *Manager) RemoveSession(sessionID string) {
	m.mu.Lock()
	defer m.mu.Unlock()

	if session, exists := m.sessions[sessionID]; exists {
		delete(m.sessions, sessionID)
		if session.ClientID != "" {
			delete(m.sessionsByClient, session.ClientID)
		}
		session.Close()
	}
}

// GetAllSessions 获取所有会话
func (m *Manager) GetAllSessions() []*Session {
	m.mu.RLock()
	defer m.mu.RUnlock()

	sessions := make([]*Session, 0, len(m.sessions))
	for _, session := range m.sessions {
		sessions = append(sessions, session)
	}
	return sessions
}

// GetSessionCount 获取会话数量
func (m *Manager) GetSessionCount() int {
	m.mu.RLock()
	defer m.mu.RUnlock()

	return len(m.sessions)
}

// BroadcastToAll 向所有会话广播消息
func (m *Manager) BroadcastToAll(message []byte) {
	m.mu.RLock()
	sessions := make([]*Session, 0, len(m.sessions))
	for _, session := range m.sessions {
		sessions = append(sessions, session)
	}
	m.mu.RUnlock()

	for _, session := range sessions {
		select {
		case session.Send <- message:
		default:
			// 发送缓冲区满，关闭会话
			session.Close()
		}
	}
}

// BroadcastToClients 向指定客户端广播消息
func (m *Manager) BroadcastToClients(clientIDs []string, message []byte) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	for _, clientID := range clientIDs {
		if session, exists := m.sessionsByClient[clientID]; exists {
			select {
			case session.Send <- message:
			default:
				// 发送缓冲区满，关闭会话
				session.Close()
			}
		}
	}
}

// Close 关闭管理器
func (m *Manager) Close() {
	m.cancel()

	m.mu.Lock()
	defer m.mu.Unlock()

	// 关闭所有会话
	for _, session := range m.sessions {
		session.Close()
	}

	m.sessions = make(map[string]*Session)
	m.sessionsByClient = make(map[string]*Session)
}

// backgroundTasks 后台任务
func (m *Manager) backgroundTasks() {
	// 会话超时检查
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			m.checkSessionTimeout()

		case <-m.ctx.Done():
			return
		}
	}
}

// checkSessionTimeout 检查会话超时
func (m *Manager) checkSessionTimeout() {
	m.mu.Lock()
	defer m.mu.Unlock()

	now := time.Now()
	for sessionID, session := range m.sessions {
		if now.Sub(session.LastActiveAt) > m.sessionTimeout {
			fmt.Printf("会话超时: %s (客户端: %s)\n", sessionID, session.ClientID)
			session.Close()
			delete(m.sessions, sessionID)
			if session.ClientID != "" {
				delete(m.sessionsByClient, session.ClientID)
			}
		}
	}
}

// === Session方法 ===

// SendToSession 向会话发送消息
func (s *Session) SendToSession(message []byte) error {
	s.mu.RLock()
	if s.closed {
		s.mu.RUnlock()
		return fmt.Errorf("会话已关闭: %s", s.ID)
	}
	s.mu.RUnlock()

	select {
	case s.Send <- message:
		s.UpdateLastActive()
		return nil
	default:
		return fmt.Errorf("发送缓冲区满")
	}
}

// Close 关闭会话
func (s *Session) Close() error {
	s.closeOnce.Do(func() {
		s.mu.Lock()
		s.closed = true
		close(s.closeChan)
		close(s.Send)
		s.mu.Unlock()

		// 关闭WebSocket连接
		if s.Conn != nil {
			s.Conn.WriteMessage(websocket.CloseMessage, []byte{})
			s.Conn.Close()
		}
	})
	return nil
}

// IsClosed 检查会话是否已关闭
func (s *Session) IsClosed() bool {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.closed
}

// UpdateLastActive 更新最后活跃时间
func (s *Session) UpdateLastActive() {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.LastActiveAt = time.Now()
}

// SetMetadata 设置元数据
func (s *Session) SetMetadata(key string, value interface{}) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.Metadata[key] = value
}

// GetMetadata 获取元数据
func (s *Session) GetMetadata(key string) (interface{}, bool) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	val, exists := s.Metadata[key]
	return val, exists
}

// writePump 写入循环（发送消息到客户端）
func (s *Session) writePump() {
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()
	defer s.Close()

	for {
		select {
		case message, ok := <-s.Send:
			if !ok {
				// 通道已关闭
				s.Conn.WriteMessage(websocket.CloseMessage, []byte{})
				return
			}

			s.Conn.SetWriteDeadline(time.Now().Add(10 * time.Second))
			if err := s.Conn.WriteMessage(websocket.TextMessage, message); err != nil {
				return
			}

		case <-ticker.C:
			// 发送心跳
			s.Conn.SetWriteDeadline(time.Now().Add(10 * time.Second))
			if err := s.Conn.WriteMessage(websocket.PingMessage, nil); err != nil {
				return
			}

		case <-s.closeChan:
			return
		}
	}
}

// readPump 读取循环（从客户端接收消息）
func (s *Session) readPump(manager *Manager) {
	defer s.Close()
	defer manager.RemoveSession(s.ID)

	s.Conn.SetReadDeadline(time.Now().Add(60 * time.Second))
	s.Conn.SetPongHandler(func(string) error {
		s.Conn.SetReadDeadline(time.Now().Add(60 * time.Second))
		s.UpdateLastActive()
		return nil
	})

	for {
		_, message, err := s.Conn.ReadMessage()
		if err != nil {
			if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseAbnormalClosure) {
				fmt.Printf("读取错误: %v\n", err)
			}
			break
		}

		s.UpdateLastActive()

		// 调用消息处理器
		if s.messageHandler != nil {
			if err := s.messageHandler(s, message); err != nil {
				fmt.Printf("消息处理错误: %v\n", err)
			}
		}
	}
}
