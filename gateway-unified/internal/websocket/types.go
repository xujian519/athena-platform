package websocket

// MessageType 消息类型
type MessageType string

const (
	// 控制消息
	TaskCreate  MessageType = "task_create"
	TaskStart   MessageType = "task_start"
	TaskPause   MessageType = "task_pause"
	TaskResume  MessageType = "task_resume"
	TaskCancel  MessageType = "task_cancel"

	// 状态消息
	TaskProgress MessageType = "task_progress"
	TaskComplete MessageType = "task_complete"
	TaskError    MessageType = "task_error"

	// 用户交互
	UserConfirmRequest  MessageType = "user_confirm_request"
	UserConfirmResponse MessageType = "user_confirm_response"
	UserInterrupt       MessageType = "user_interrupt"

	// 智能体消息
	AgentMessage       MessageType = "agent_message"
	AgentCollaboration MessageType = "agent_collaboration"
)

// WSMessage WebSocket消息
type WSMessage struct {
	Type      string      `json:"type"`
	SessionID string      `json:"session_id"`
	Timestamp string      `json:"timestamp"`
	Payload   interface{} `json:"payload"`
}

// TaskCreatePayload 任务创建载荷
type TaskCreatePayload struct {
	TaskID      string `json:"task_id"`
	TaskType    string `json:"task_type"`
	UserInput   string `json:"user_input"`
	ProjectPath string `json:"project_path,omitempty"`
	Priority    string `json:"priority,omitempty"` // low, medium, high
}

// TaskProgressPayload 任务进度载荷
type TaskProgressPayload struct {
	TaskID    string                 `json:"task_id"`
	AgentName string                 `json:"agent_name"`
	Progress  int                    `json:"progress"` // 0-100
	Message   string                 `json:"message"`
	Details   map[string]interface{} `json:"details,omitempty"`
}

// TaskStartPayload 任务开始载荷
type TaskStartPayload struct {
	TaskID string `json:"task_id"`
}

// TaskPausePayload 任务暂停载荷
type TaskPausePayload struct {
	TaskID  string `json:"task_id"`
	Reason  string `json:"reason,omitempty"`
}

// TaskResumePayload 任务恢复载荷
type TaskResumePayload struct {
	TaskID string `json:"task_id"`
}

// TaskCancelPayload 任务取消载荷
type TaskCancelPayload struct {
	TaskID string `json:"task_id"`
	Reason string `json:"reason,omitempty"`
}

// TaskCompletePayload 任务完成载荷
type TaskCompletePayload struct {
	TaskID       string                 `json:"task_id"`
	Success      bool                   `json:"success"`
	Result       map[string]interface{} `json:"result,omitempty"`
	ExecutionTime int64                 `json:"execution_time_ms"`
}

// TaskErrorPayload 任务错误载荷
type TaskErrorPayload struct {
	TaskID   string `json:"task_id"`
	Error    string `json:"error"`
	Code     string `json:"code,omitempty"`
	Details  string `json:"details,omitempty"`
}

// UserConfirmRequestPayload 用户确认请求载荷
type UserConfirmRequestPayload struct {
	TaskID      string `json:"task_id"`
	Title       string `json:"title"`
	Message     string `json:"message"`
	Options     []string `json:"options"`
	Timeout     int    `json:"timeout,omitempty"` // 超时时间（秒）
}

// UserConfirmResponsePayload 用户确认响应载荷
type UserConfirmResponsePayload struct {
	TaskID      string `json:"task_id"`
	Confirmed   bool   `json:"confirmed"`
	Selection   string `json:"selection,omitempty"`
	Input       string `json:"input,omitempty"`
}

// UserInterruptPayload 用户中断载荷
type UserInterruptPayload struct {
	TaskID   string `json:"task_id"`
	Reason   string `json:"reason,omitempty"`
	Force    bool   `json:"force"` // 是否强制中断
}

// AgentMessagePayload 智能体消息载荷
type AgentMessagePayload struct {
	AgentName string                 `json:"agent_name"`
	Content   string                 `json:"content"`
	Metadata  map[string]interface{} `json:"metadata,omitempty"`
}

// AgentCollaborationPayload 智能体协作载荷
type AgentCollaborationPayload struct {
	Initiator string                 `json:"initiator"` // 发起方
	Targets   []string               `json:"targets"`   // 目标智能体列表
	Content   string                 `json:"content"`
	Context   map[string]interface{} `json:"context,omitempty"`
}
