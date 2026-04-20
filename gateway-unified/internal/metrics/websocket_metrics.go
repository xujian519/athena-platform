package metrics

import (
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
)

var (
	// WebSocket会话指标
	websocketSessionsTotal = promauto.NewCounter(prometheus.CounterOpts{
		Name: "websocket_sessions_total",
		Help: "WebSocket总会话数",
	})

	websocketActiveSessions = promauto.NewGauge(prometheus.GaugeOpts{
		Name: "websocket_active_sessions",
		Help: "WebSocket活跃会话数",
	})

	// WebSocket消息指标
	websocketMessagesTotal = promauto.NewCounterVec(prometheus.CounterOpts{
		Name: "websocket_messages_total",
		Help: "WebSocket消息总数",
	}, []string{"type", "agent"})

	websocketMessageDuration = promauto.NewHistogram(prometheus.HistogramOpts{
		Name: "websocket_message_duration_seconds",
		Help: "WebSocket消息处理延迟",
		Buckets: []float64{0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10},
	})

	// WebSocket错误指标
	websocketErrorsTotal = promauto.NewCounterVec(prometheus.CounterOpts{
		Name: "websocket_errors_total",
		Help: "WebSocket错误总数",
	}, []string{"type"})

	// Agent任务指标
	agentTasksTotal = promauto.NewCounterVec(prometheus.CounterOpts{
		Name: "agent_tasks_total",
		Help: "Agent任务总数",
	}, []string{"agent", "type", "status"})

	agentTaskDuration = promauto.NewHistogramVec(prometheus.HistogramOpts{
		Name: "agent_task_duration_seconds",
		Help: "Agent任务处理时长",
		Buckets: []float64{0.1, 0.5, 1, 2.5, 5, 10, 30, 60, 120, 300},
	}, []string{"agent", "type"})

	// Canvas Host指标
	canvasRenderTotal = promauto.NewCounter(prometheus.CounterOpts{
		Name: "canvas_render_total",
		Help: "Canvas渲染总数",
	})

	canvasRenderDuration = promauto.NewHistogram(prometheus.HistogramOpts{
		Name: "canvas_render_duration_seconds",
		Help: "Canvas渲染时长",
		Buckets: []float64{0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5},
	})

	// Gateway性能指标
	gatewayRequestDuration = promauto.NewHistogramVec(prometheus.HistogramOpts{
		Name: "gateway_request_duration_seconds",
		Help: "Gateway请求处理时长",
		Buckets: []float64{0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5},
	}, []string{"endpoint", "method"})

	gatewayRequestsTotal = promauto.NewCounterVec(prometheus.CounterOpts{
		Name: "gateway_requests_total",
		Help: "Gateway请求总数",
	}, []string{"endpoint", "method", "status"})
)

// WebSocketMetricsHelper WebSocket指标辅助函数
type WebSocketMetricsHelper struct{}

// NewWebSocketMetricsHelper 创建WebSocket指标辅助器
func NewWebSocketMetricsHelper() *WebSocketMetricsHelper {
	return &WebSocketMetricsHelper{}
}

// RecordSessionCreated 记录会话创建
func (h *WebSocketMetricsHelper) RecordSessionCreated() {
	websocketSessionsTotal.Inc()
	websocketActiveSessions.Inc()
}

// RecordSessionClosed 记录会话关闭
func (h *WebSocketMetricsHelper) RecordSessionClosed() {
	websocketActiveSessions.Dec()
}

// RecordMessage 记录消息
func (h *WebSocketMetricsHelper) RecordMessage(msgType, agent string) {
	websocketMessagesTotal.WithLabelValues(msgType, agent).Inc()
}

// RecordMessageDuration 记录消息处理时长
func (h *WebSocketMetricsHelper) RecordMessageDuration(duration float64) {
	websocketMessageDuration.Observe(duration)
}

// RecordError 记录错误
func (h *WebSocketMetricsHelper) RecordError(errorType string) {
	websocketErrorsTotal.WithLabelValues(errorType).Inc()
}

// AgentMetricsHelper Agent指标辅助函数
type AgentMetricsHelper struct{}

// NewAgentMetricsHelper 创建Agent指标辅助器
func NewAgentMetricsHelper() *AgentMetricsHelper {
	return &AgentMetricsHelper{}
}

// RecordTaskStarted 记录任务开始
func (h *AgentMetricsHelper) RecordTaskStarted(agent, taskType string) {
	agentTasksTotal.WithLabelValues(agent, taskType, "started").Inc()
}

// RecordTaskCompleted 记录任务完成
func (h *AgentMetricsHelper) RecordTaskCompleted(agent, taskType string) {
	agentTasksTotal.WithLabelValues(agent, taskType, "completed").Inc()
}

// RecordTaskFailed 记录任务失败
func (h *AgentMetricsHelper) RecordTaskFailed(agent, taskType string) {
	agentTasksTotal.WithLabelValues(agent, taskType, "failed").Inc()
}

// RecordTaskDuration 记录任务处理时长
func (h *AgentMetricsHelper) RecordTaskDuration(agent, taskType string, duration float64) {
	agentTaskDuration.WithLabelValues(agent, taskType).Observe(duration)
}

// CanvasMetricsHelper Canvas指标辅助函数
type CanvasMetricsHelper struct{}

// NewCanvasMetricsHelper 创建Canvas指标辅助器
func NewCanvasMetricsHelper() *CanvasMetricsHelper {
	return &CanvasMetricsHelper{}
}

// RecordRender 记录Canvas渲染
func (h *CanvasMetricsHelper) RecordRender(duration float64) {
	canvasRenderTotal.Inc()
	canvasRenderDuration.Observe(duration)
}

// GatewayMetricsHelper Gateway指标辅助函数
type GatewayMetricsHelper struct{}

// NewGatewayMetricsHelper 创建Gateway指标辅助器
func NewGatewayMetricsHelper() *GatewayMetricsHelper {
	return &GatewayMetricsHelper{}
}

// RecordRequest 记录请求
func (h *GatewayMetricsHelper) RecordRequest(endpoint, method, status string) {
	gatewayRequestsTotal.WithLabelValues(endpoint, method, status).Inc()
}

// RecordRequestDuration 记录请求处理时长
func (h *GatewayMetricsHelper) RecordRequestDuration(endpoint, method string, duration float64) {
	gatewayRequestDuration.WithLabelValues(endpoint, method).Observe(duration)
}
