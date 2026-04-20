package protocol

import (
	"fmt"
	"math/rand"
	"time"
)

// MessageType 消息类型
type MessageType string

const (
	// 客户端请求类型
	MessageTypeHandshake   MessageType = "handshake"    // 握手
	MessageTypeTask        MessageType = "task"         // 任务请求
	MessageTypeQuery       MessageType = "query"        // 查询请求
	MessageTypeCancel      MessageType = "cancel"       // 取消请求

	// 服务器响应类型
	MessageTypeResponse    MessageType = "response"     // 响应
	MessageTypeProgress    MessageType = "progress"     // 进度更新
	MessageTypeError       MessageType = "error"        // 错误消息
	MessageTypeNotify      MessageType = "notify"       // 通知消息

	// 系统消息类型
	MessageTypePing        MessageType = "ping"         // 心跳
	MessageTypePong        MessageType = "pong"         // 心跳响应
	MessageTypeClose       MessageType = "close"        // 关闭连接
)

// AgentType Agent类型
type AgentType string

const (
	AgentTypeXiaona  AgentType = "xiaona"  // 法律专家
	AgentTypeXiaonuo AgentType = "xiaonuo" // 调度官
	AgentTypeYunxi   AgentType = "yunxi"   // IP管理
	AgentTypeUnknown AgentType = "unknown" // 未知
)

// Message WebSocket消息基础结构
type Message struct {
	ID        string                 `json:"id"`         // 消息唯一ID
	Type      MessageType            `json:"type"`       // 消息类型
	Timestamp int64                  `json:"timestamp"`  // 时间戳（Unix纳秒）
	SessionID string                 `json:"session_id"` // 会话ID
	Data      map[string]interface{} `json:"data"`       // 消息数据
}

// TaskRequest 任务请求
type TaskRequest struct {
	Message
	TaskType   string   `json:"task_type"`   // 任务类型
	TargetAgent AgentType `json:"target_agent"` // 目标Agent
	Priority   int      `json:"priority"`    // 优先级（0-10）
	Parameters map[string]interface{} `json:"parameters"` // 任务参数
}

// ProgressUpdate 进度更新
type ProgressUpdate struct {
	Message
	Progress   int     `json:"progress"`    // 进度百分比（0-100）
	Status     string  `json:"status"`      // 状态描述
	CurrentStep string `json:"current_step"` // 当前步骤
	TotalSteps int     `json:"total_steps"` // 总步骤数
}

// ErrorResponse 错误响应
type ErrorResponse struct {
	Message
	ErrorCode  string `json:"error_code"`  // 错误码
	ErrorMsg   string `json:"error_msg"`   // 错误消息
	Details    string `json:"details"`     // 详细信息
}

// Response 通用响应
type Response struct {
	Message
	Success    bool                   `json:"success"`    // 是否成功
	Result     map[string]interface{} `json:"result"`     // 结果数据
	Metadata   map[string]interface{} `json:"metadata"`   // 元数据
}

// HandshakeRequest 握手请求
type HandshakeRequest struct {
	Message
	ClientID   string            `json:"client_id"`   // 客户端ID
	AuthToken  string            `json:"auth_token"`  // 认证Token
	Capabilities []string        `json:"capabilities"` // 客户端能力
	UserAgent  string            `json:"user_agent"`  // 用户代理
}

// HandshakeResponse 握手响应
type HandshakeResponse struct {
	Message
	SessionID  string   `json:"session_id"`  // 会话ID
	ServerID   string   `json:"server_id"`   // 服务器ID
	Capabilities []string `json:"capabilities"` // 服务器能力
	HeartbeatInterval int `json:"heartbeat_interval"` // 心跳间隔（秒）
}

// Notification 通知消息
type Notification struct {
	Message
	Level     string `json:"level"`     // 级别（info/warn/error）
	Title     string `json:"title"`     // 标题
	Body      string `json:"body"`      // 内容
}

// NewMessage 创建新消息
func NewMessage(msgType MessageType, sessionID string, data map[string]interface{}) *Message {
	return &Message{
		ID:        generateMessageID(),
		Type:      msgType,
		Timestamp: getCurrentTimestamp(),
		SessionID: sessionID,
		Data:      data,
	}
}

// NewTaskRequest 创建任务请求
func NewTaskRequest(sessionID, taskType string, targetAgent AgentType, parameters map[string]interface{}) *TaskRequest {
	return &TaskRequest{
		Message: Message{
			ID:        generateMessageID(),
			Type:      MessageTypeTask,
			Timestamp: getCurrentTimestamp(),
			SessionID: sessionID,
			Data:      make(map[string]interface{}),
		},
		TaskType:    taskType,
		TargetAgent: targetAgent,
		Priority:    5, // 默认中等优先级
		Parameters:  parameters,
	}
}

// NewProgressUpdate 创建进度更新
func NewProgressUpdate(sessionID string, progress int, status, currentStep string, totalSteps int) *ProgressUpdate {
	return &ProgressUpdate{
		Message: Message{
			ID:        generateMessageID(),
			Type:      MessageTypeProgress,
			Timestamp: getCurrentTimestamp(),
			SessionID: sessionID,
			Data:      make(map[string]interface{}),
		},
		Progress:    progress,
		Status:      status,
		CurrentStep: currentStep,
		TotalSteps:  totalSteps,
	}
}

// NewErrorResponse 创建错误响应
func NewErrorResponse(sessionID, errorCode, errorMsg, details string) *ErrorResponse {
	return &ErrorResponse{
		Message: Message{
			ID:        generateMessageID(),
			Type:      MessageTypeError,
			Timestamp: getCurrentTimestamp(),
			SessionID: sessionID,
			Data:      make(map[string]interface{}),
		},
		ErrorCode: errorCode,
		ErrorMsg:  errorMsg,
		Details:   details,
	}
}

// NewResponse 创建响应
func NewResponse(sessionID string, success bool, result, metadata map[string]interface{}) *Response {
	return &Response{
		Message: Message{
			ID:        generateMessageID(),
			Type:      MessageTypeResponse,
			Timestamp: getCurrentTimestamp(),
			SessionID: sessionID,
			Data:      make(map[string]interface{}),
		},
		Success:  success,
		Result:   result,
		Metadata: metadata,
	}
}

// generateMessageID 生成消息ID
func generateMessageID() string {
	return fmt.Sprintf("msg_%d_%s", time.Now().UnixNano(), randomString(8))
}

// getCurrentTimestamp 获取当前时间戳
func getCurrentTimestamp() int64 {
	return time.Now().UnixNano()
}

// randomString 生成随机字符串
func randomString(length int) string {
	const charset = "abcdefghijklmnopqrstuvwxyz0123456789"
	b := make([]byte, length)
	for i := range b {
		b[i] = charset[rand.Intn(len(charset))]
	}
	return string(b)
}
