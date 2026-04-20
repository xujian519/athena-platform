package canvas

import (
	"encoding/json"
	"fmt"
	"sync"
	"time"

	"github.com/athena-workspace/gateway-unified/internal/logging"
)

// AgentState Agent状态
type AgentState struct {
	ID            string                 `json:"id"`
	Name          string                 `json:"name"`
	Type          string                 `json:"type"`
	Status        string                 `json:"status"`        // idle, busy, error, offline
	CurrentTask   string                 `json:"current_task"`
	LastActive    time.Time              `json:"last_active"`
	Metrics       map[string]interface{} `json:"metrics"`
	Capabilities  []string               `json:"capabilities"`
	Error         string                 `json:"error"`
	mu            sync.RWMutex
}

// AgentRegistry Agent注册表
type AgentRegistry struct {
	agents map[string]*AgentState
	mu     sync.RWMutex
}

// NewAgentRegistry 创建Agent注册表
func NewAgentRegistry() *AgentRegistry {
	return &AgentRegistry{
		agents: make(map[string]*AgentState),
	}
}

// Register 注册Agent
func (ar *AgentRegistry) Register(agent *AgentState) {
	ar.mu.Lock()
	defer ar.mu.Unlock()

	ar.agents[agent.ID] = agent
	logging.LogInfo("Agent已注册",
		logging.String("agent_id", agent.ID),
		logging.String("agent_name", agent.Name),
		logging.String("agent_type", agent.Type),
	)
}

// Unregister 注销Agent
func (ar *AgentRegistry) Unregister(agentID string) {
	ar.mu.Lock()
	defer ar.mu.Unlock()

	if _, exists := ar.agents[agentID]; exists {
		delete(ar.agents, agentID)
		logging.LogInfo("Agent已注销",
			logging.String("agent_id", agentID),
		)
	}
}

// Get 获取Agent
func (ar *AgentRegistry) Get(agentID string) (*AgentState, bool) {
	ar.mu.RLock()
	defer ar.mu.RUnlock()

	agent, exists := ar.agents[agentID]
	return agent, exists
}

// GetAll 获取所有Agent
func (ar *AgentRegistry) GetAll() []*AgentState {
	ar.mu.RLock()
	defer ar.mu.RUnlock()

	agents := make([]*AgentState, 0, len(ar.agents))
	for _, agent := range ar.agents {
		agents = append(agents, agent)
	}
	return agents
}

// GetByType 按类型获取Agent
func (ar *AgentRegistry) GetByType(agentType string) []*AgentState {
	ar.mu.RLock()
	defer ar.mu.RUnlock()

	agents := make([]*AgentState, 0)
	for _, agent := range ar.agents {
		if agent.Type == agentType {
			agents = append(agents, agent)
		}
	}
	return agents
}

// UpdateStatus 更新Agent状态
func (ar *AgentRegistry) UpdateStatus(agentID, status string) error {
	ar.mu.Lock()
	defer ar.mu.Unlock()

	agent, exists := ar.agents[agentID]
	if !exists {
		return fmt.Errorf("Agent不存在: %s", agentID)
	}

	agent.mu.Lock()
	agent.Status = status
	agent.LastActive = time.Now()
	agent.mu.Unlock()

	return nil
}

// UpdateTask 更新Agent当前任务
func (ar *AgentRegistry) UpdateTask(agentID, task string) error {
	ar.mu.Lock()
	defer ar.mu.Unlock()

	agent, exists := ar.agents[agentID]
	if !exists {
		return fmt.Errorf("Agent不存在: %s", agentID)
	}

	agent.mu.Lock()
	agent.CurrentTask = task
	agent.LastActive = time.Now()
	agent.mu.Unlock()

	return nil
}

// UpdateMetrics 更新Agent指标
func (ar *AgentRegistry) UpdateMetrics(agentID string, metrics map[string]interface{}) error {
	ar.mu.Lock()
	defer ar.mu.Unlock()

	agent, exists := ar.agents[agentID]
	if !exists {
		return fmt.Errorf("Agent不存在: %s", agentID)
	}

	agent.mu.Lock()
	for k, v := range metrics {
		agent.Metrics[k] = v
	}
	agent.LastActive = time.Now()
	agent.mu.Unlock()

	return nil
}

// SetError 设置Agent错误
func (ar *AgentRegistry) SetError(agentID, errMsg string) error {
	ar.mu.Lock()
	defer ar.mu.Unlock()

	agent, exists := ar.agents[agentID]
	if !exists {
		return fmt.Errorf("Agent不存在: %s", agentID)
	}

	agent.mu.Lock()
	agent.Error = errMsg
	agent.Status = "error"
	agent.LastActive = time.Now()
	agent.mu.Unlock()

	return nil
}

// ClearError 清除Agent错误
func (ar *AgentRegistry) ClearError(agentID string) error {
	ar.mu.Lock()
	defer ar.mu.Unlock()

	agent, exists := ar.agents[agentID]
	if !exists {
		return fmt.Errorf("Agent不存在: %s", agentID)
	}

	agent.mu.Lock()
	agent.Error = ""
	if agent.Status == "error" {
		agent.Status = "idle"
	}
	agent.mu.Unlock()

	return nil
}

// GetStats 获取统计信息
func (ar *AgentRegistry) GetStats() map[string]interface{} {
	ar.mu.RLock()
	defer ar.mu.RUnlock()

	stats := map[string]interface{}{
		"total":     len(ar.agents),
		"by_status": make(map[string]int),
		"by_type":   make(map[string]int),
	}

	for _, agent := range ar.agents {
		agent.mu.RLock()
		status := agent.Status
		agentType := agent.Type
		agent.mu.RUnlock()

		if statusCount, ok := stats["by_status"].(map[string]int); ok {
			statusCount[status]++
		}

		if typeCount, ok := stats["by_type"].(map[string]int); ok {
			typeCount[agentType]++
		}
	}

	return stats
}

// AgentVisualizer Agent可视化器
type AgentVisualizer struct {
	registry    *AgentRegistry
	components  map[string]*AgentView
	updater     *IncrementalUpdater
	mu          sync.RWMutex
}

// NewAgentVisualizer 创建Agent可视化器
func NewAgentVisualizer(registry *AgentRegistry) *AgentVisualizer {
	return &AgentVisualizer{
		registry:   registry,
		components: make(map[string]*AgentView),
		updater:    NewIncrementalUpdater(),
	}
}

// CreateAgentView 创建Agent视图
func (av *AgentVisualizer) CreateAgentView(agentID string) (*AgentView, error) {
	agent, exists := av.registry.Get(agentID)
	if !exists {
		return nil, fmt.Errorf("Agent不存在: %s", agentID)
	}

	agent.mu.RLock()
	view := NewAgentView(
		"agent_view_"+agent.ID,
		agent.Name,
		agent.Type,
	)
	view.Status = agent.Status
	view.CurrentTask = agent.CurrentTask
	agent.mu.RUnlock()

	av.mu.Lock()
	av.components[agentID] = view
	av.mu.Unlock()

	return view, nil
}

// GetAgentView 获取Agent视图
func (av *AgentVisualizer) GetAgentView(agentID string) (*AgentView, bool) {
	av.mu.RLock()
	defer av.mu.RUnlock()

	view, exists := av.components[agentID]
	return view, exists
}

// RefreshAgentView 刷新Agent视图
func (av *AgentVisualizer) RefreshAgentView(agentID string) error {
	view, exists := av.GetAgentView(agentID)
	if !exists {
		return fmt.Errorf("Agent视图不存在: %s", agentID)
	}

	agent, exists := av.registry.Get(agentID)
	if !exists {
		return fmt.Errorf("Agent不存在: %s", agentID)
	}

	agent.mu.RLock()
	updateData := map[string]interface{}{
		"status":       agent.Status,
		"current_task": agent.CurrentTask,
		"metrics":      convertMetrics(agent.Metrics),
	}
	agent.mu.RUnlock()

	return view.Update(updateData)
}

// RefreshAllViews 刷新所有视图
func (av *AgentVisualizer) RefreshAllViews() error {
	av.mu.RLock()
	agentIDs := make([]string, 0, len(av.components))
	for id := range av.components {
		agentIDs = append(agentIDs, id)
	}
	av.mu.RUnlock()

	for _, agentID := range agentIDs {
		if err := av.RefreshAgentView(agentID); err != nil {
			logging.LogError("刷新Agent视图失败",
				logging.Err(err),
				logging.String("agent_id", agentID),
			)
		}
	}

	return nil
}

// GenerateVisualizationScript 生成可视化脚本
func (av *AgentVisualizer) GenerateVisualizationScript() string {
	agents := av.registry.GetAll()

	// 准备Agent数据
	agentData := make([]map[string]interface{}, 0)
	for _, agent := range agents {
		agent.mu.RLock()
		data := map[string]interface{}{
			"id":           agent.ID,
			"name":         agent.Name,
			"type":         agent.Type,
			"status":       agent.Status,
			"current_task": agent.CurrentTask,
			"last_active":  agent.LastActive.Format("15:04:05"),
		}
		agent.mu.RUnlock()
		agentData = append(agentData, data)
	}

	// 序列化为JSON
	dataJSON, _ := json.Marshal(agentData)

	// 生成JavaScript脚本（使用反引号包裹，避免转义问题）
	script := `// Agent状态可视化
(function() {
    const agents = ` + string(dataJSON) + `;
    renderAgentGrid(agents);
})(window);

function renderAgentGrid(agents) {
    const container = document.getElementById('agent-grid');
    if (!container) return;

    container.innerHTML = agents.map(agent => {
        return '<div class="agent-card agent-' + agent.status + '">' +
            '<div class="agent-header">' +
            '<span class="agent-name">' + agent.name + '</span>' +
            '<span class="agent-status">' + agent.status + '</span>' +
            '</div>' +
            '<div class="agent-body">' +
            '<div class="agent-info">类型: ' + agent.type + '</div>' +
            '<div class="agent-info">任务: ' + (agent.current_task || '无') + '</div>' +
            '<div class="agent-info">最后活跃: ' + agent.last_active + '</div>' +
            '</div>' +
            '</div>';
    }).join('');

    // 添加状态样式
    agents.forEach(agent => {
        const statusClass = 'agent-' + agent.status;
        container.classList.add(statusClass);
    });
}
`

	return script
}

// convertMetrics 转换指标数据
func convertMetrics(metrics map[string]interface{}) map[string]interface{} {
	return metrics
}
