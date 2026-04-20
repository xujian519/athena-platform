package canvas

import (
	"fmt"
	"sync"
	"time"
)

// ComponentType UI组件类型
type ComponentType string

const (
	ComponentTypeProgressBar ComponentType = "progress_bar"
	ComponentTypeStatusCard ComponentType = "status_card"
	ComponentTypeAgentView  ComponentType = "agent_view"
	ComponentTypeTaskList   ComponentType = "task_list"
	ComponentTypeMetricCard ComponentType = "metric_card"
	ComponentTypeLogPanel   ComponentType = "log_panel"
)

// Component UI组件接口
type Component interface {
	Type() ComponentType
	Render() string
	Update(data map[string]interface{}) error
}

// ProgressBar 进度条组件
type ProgressBar struct {
	ID          string
	Progress    int
	Label       string
	Description string
	ShowPercent bool
	Color       string
	mu          sync.RWMutex
}

// NewProgressBar 创建进度条组件
func NewProgressBar(id, label string) *ProgressBar {
	return &ProgressBar{
		ID:          id,
		Progress:    0,
		Label:       label,
		Description: "",
		ShowPercent: true,
		Color:       "#667eea",
	}
}

// Type 返回组件类型
func (pb *ProgressBar) Type() ComponentType {
	return ComponentTypeProgressBar
}

// Render 渲染进度条
func (pb *ProgressBar) Render() string {
	pb.mu.RLock()
	defer pb.mu.RUnlock()

	percentText := ""
	if pb.ShowPercent {
		percentText = fmt.Sprintf("%d%%", pb.Progress)
	}

	return fmt.Sprintf(`
<div class="progress-component" id="%s">
    <div class="progress-label">
        <strong>%s</strong>
        %s
    </div>
    %s
    <div class="progress-description">%s</div>
</div>`,
		pb.ID,
		pb.Label,
		percentText,
		pb.renderBar(),
		pb.Description,
	)
}

// renderBar 渲染进度条元素
func (pb *ProgressBar) renderBar() string {
	return fmt.Sprintf(`
<div class="progress-bar-component">
    <div class="progress-fill-component" style="width: %d%%; background: %s;"></div>
</div>`, pb.Progress, pb.Color)
}

// Update 更新进度条
func (pb *ProgressBar) Update(data map[string]interface{}) error {
	pb.mu.Lock()
	defer pb.mu.Unlock()

	if progress, ok := data["progress"].(int); ok {
		if progress < 0 {
			progress = 0
		} else if progress > 100 {
			progress = 100
		}
		pb.Progress = progress
	}

	if label, ok := data["label"].(string); ok {
		pb.Label = label
	}

	if desc, ok := data["description"].(string); ok {
		pb.Description = desc
	}

	if color, ok := data["color"].(string); ok {
		pb.Color = color
	}

	return nil
}

// StatusCard 状态卡片组件
type StatusCard struct {
	ID       string
	Title    string
	Status   string
	Message  string
	Icon     string
	Updated  time.Time
	mu       sync.RWMutex
}

// NewStatusCard 创建状态卡片
func NewStatusCard(id, title string) *StatusCard {
	return &StatusCard{
		ID:      id,
		Title:   title,
		Status:  "idle",
		Message: "",
		Icon:    "circle",
		Updated: time.Now(),
	}
}

// Type 返回组件类型
func (sc *StatusCard) Type() ComponentType {
	return ComponentTypeStatusCard
}

// Render 渲染状态卡片
func (sc *StatusCard) Render() string {
	sc.mu.RLock()
	defer sc.mu.RUnlock()

	statusClass := "status-" + sc.Status
	iconHTML := sc.renderIcon()

	return fmt.Sprintf(`
<div class="status-card %s" id="%s">
    <div class="status-icon">%s</div>
    <div class="status-content">
        <h4 class="status-title">%s</h4>
        <p class="status-message">%s</p>
        <span class="status-time">%s</span>
    </div>
</div>`,
		statusClass,
		sc.ID,
		iconHTML,
		sc.Title,
		sc.Message,
		sc.Updated.Format("15:04:05"),
	)
}

// renderIcon 渲染图标
func (sc *StatusCard) renderIcon() string {
	icons := map[string]string{
		"idle":     "○",
		"running":  "◌",
		"success":  "✓",
		"error":    "✗",
		"warning":  "⚠",
		"circle":   "○",
	}

	if icon, ok := icons[sc.Icon]; ok {
		return icon
	}
	return "○"
}

// Update 更新状态卡片
func (sc *StatusCard) Update(data map[string]interface{}) error {
	sc.mu.Lock()
	defer sc.mu.Unlock()

	if status, ok := data["status"].(string); ok {
		sc.Status = status
	}

	if message, ok := data["message"].(string); ok {
		sc.Message = message
	}

	if icon, ok := data["icon"].(string); ok {
		sc.Icon = icon
	}

	sc.Updated = time.Now()
	return nil
}

// AgentView Agent状态视图组件
type AgentView struct {
	ID          string
	AgentName   string
	AgentType   string
	Status      string
	CurrentTask string
	Metrics     map[string]int
	Logs        []string
	mu          sync.RWMutex
}

// NewAgentView 创建Agent视图
func NewAgentView(id, agentName, agentType string) *AgentView {
	return &AgentView{
		ID:        id,
		AgentName: agentName,
		AgentType: agentType,
		Status:    "idle",
		Metrics:   make(map[string]int),
		Logs:      make([]string, 0),
	}
}

// Type 返回组件类型
func (av *AgentView) Type() ComponentType {
	return ComponentTypeAgentView
}

// Render 渲染Agent视图
func (av *AgentView) Render() string {
	defer av.mu.RUnlock()

	statusBadge := fmt.Sprintf(`<span class="agent-status agent-%s">%s</span>`, av.Status, av.getStatusText())

	metricsHTML := av.renderMetrics()
	logsHTML := av.renderLogs()

	return fmt.Sprintf(`
<div class="agent-view" id="%s">
    <div class="agent-header">
        <div class="agent-info">
            <h3 class="agent-name">%s</h3>
            <span class="agent-type">%s</span>
        </div>
        %s
    </div>
    <div class="agent-task">
        <strong>当前任务:</strong> %s
    </div>
    <div class="agent-metrics">
        <h4>指标</h4>
        %s
    </div>
    <div class="agent-logs">
        <h4>日志</h4>
        %s
    </div>
</div>`,
		av.ID,
		av.AgentName,
		av.AgentType,
		statusBadge,
		av.CurrentTask,
		metricsHTML,
		logsHTML,
	)
}

// getStatusText 获取状态文本
func (av *AgentView) getStatusText() string {
	statusTexts := map[string]string{
		"idle":      "空闲",
		"busy":      "忙碌",
		"error":     "错误",
		"offline":   "离线",
		"processing": "处理中",
	}

	if text, ok := statusTexts[av.Status]; ok {
		return text
	}
	return av.Status
}

// renderMetrics 渲染指标
func (av *AgentView) renderMetrics() string {
	if len(av.Metrics) == 0 {
		return `<p class="no-metrics">暂无指标</p>`
	}

	html := `<div class="metrics-grid">`
	for key, value := range av.Metrics {
		html += fmt.Sprintf(`
<div class="metric-item">
    <span class="metric-key">%s</span>
    <span class="metric-value">%d</span>
</div>`, key, value)
	}
	html += `</div>`
	return html
}

// renderLogs 渲染日志
func (av *AgentView) renderLogs() string {
	if len(av.Logs) == 0 {
		return `<p class="no-logs">暂无日志</p>`
	}

	html := `<div class="logs-list">`
	for _, log := range av.Logs {
		html += fmt.Sprintf(`<div class="log-entry">%s</div>`, log)
	}
	html += `</div>`
	return html
}

// Update 更新Agent视图
func (av *AgentView) Update(data map[string]interface{}) error {
	av.mu.Lock()
	defer av.mu.Unlock()

	if status, ok := data["status"].(string); ok {
		av.Status = status
	}

	if task, ok := data["current_task"].(string); ok {
		av.CurrentTask = task
	}

	if metrics, ok := data["metrics"].(map[string]int); ok {
		av.Metrics = metrics
	}

	if log, ok := data["log"].(string); ok {
		av.Logs = append(av.Logs, log)
		if len(av.Logs) > 50 { // 限制日志数量
			av.Logs = av.Logs[len(av.Logs)-50:]
		}
	}

	return nil
}

// TaskList 任务列表组件
type TaskList struct {
	ID     string
	Title  string
	Tasks  []*TaskItem
	mu     sync.RWMutex
}

// TaskItem 任务项
type TaskItem struct {
	ID          string
	Title       string
	Status      string
	Progress    int
	Assignee    string
	CreatedAt   time.Time
}

// NewTaskList 创建任务列表
func NewTaskList(id, title string) *TaskList {
	return &TaskList{
		ID:    id,
		Title: title,
		Tasks: make([]*TaskItem, 0),
	}
}

// Type 返回组件类型
func (tl *TaskList) Type() ComponentType {
	return ComponentTypeTaskList
}

// Render 渲染任务列表
func (tl *TaskList) Render() string {
	tl.mu.RLock()
	defer tl.mu.RUnlock()

	tasksHTML := ""
	for _, task := range tl.Tasks {
		tasksHTML += tl.renderTaskItem(task)
	}

	return fmt.Sprintf(`
<div class="task-list" id="%s">
    <h3 class="task-list-title">%s</h3>
    <div class="task-items">
        %s
    </div>
</div>`,
		tl.ID,
		tl.Title,
		tasksHTML,
	)
}

// renderTaskItem 渲染任务项
func (tl *TaskList) renderTaskItem(task *TaskItem) string {
	return fmt.Sprintf(`
<div class="task-item task-%s" id="task-%s">
    <div class="task-header">
        <h4 class="task-title">%s</h4>
        <span class="task-status">%s</span>
    </div>
    <div class="task-progress">
        <div class="task-progress-bar">
            <div class="task-progress-fill" style="width: %d%%;"></div>
        </div>
        <span class="task-progress-text">%d%%</span>
    </div>
    <div class="task-meta">
        <span class="task-assignee">负责人: %s</span>
        <span class="task-time">%s</span>
    </div>
</div>`,
		task.Status,
		task.ID,
		task.Title,
		task.getStatusText(),
		task.Progress,
		task.Progress,
		task.Assignee,
		task.CreatedAt.Format("15:04"),
	)
}

// getStatusText 获取任务状态文本
func (ti *TaskItem) getStatusText() string {
	statusTexts := map[string]string{
		"pending":    "待处理",
		"in_progress": "进行中",
		"completed":  "已完成",
		"failed":     "失败",
		"cancelled":  "已取消",
	}

	if text, ok := statusTexts[ti.Status]; ok {
		return text
	}
	return ti.Status
}

// Update 更新任务列表
func (tl *TaskList) Update(data map[string]interface{}) error {
	tl.mu.Lock()
	defer tl.mu.Unlock()

	if taskData, ok := data["task"].(map[string]interface{}); ok {
		task := &TaskItem{
			ID:        generateID("task"),
			Title:     getString(taskData, "title"),
			Status:    getString(taskData, "status"),
			Progress:  getInt(taskData, "progress"),
			Assignee:  getString(taskData, "assignee"),
			CreatedAt: time.Now(),
		}
		tl.Tasks = append(tl.Tasks, task)
	}

	if updateData, ok := data["update"].(map[string]interface{}); ok {
		taskID := getString(updateData, "task_id")
		for _, task := range tl.Tasks {
			if task.ID == taskID {
				if status, ok := updateData["status"].(string); ok {
					task.Status = status
				}
				if progress, ok := updateData["progress"].(int); ok {
					task.Progress = progress
				}
			}
		}
	}

	return nil
}

// MetricCard 指标卡片组件
type MetricCard struct {
	ID     string
	Title  string
	Value  string
	Delta  string
	Trend  string
	Color  string
	mu     sync.RWMutex
}

// NewMetricCard 创建指标卡片
func NewMetricCard(id, title, value string) *MetricCard {
	return &MetricCard{
		ID:    id,
		Title: title,
		Value: value,
		Trend: "neutral",
		Color: "#667eea",
	}
}

// Type 返回组件类型
func (mc *MetricCard) Type() ComponentType {
	return ComponentTypeMetricCard
}

// Render 渲染指标卡片
func (mc *MetricCard) Render() string {
	mc.mu.RLock()
	defer mc.mu.RUnlock()

	trendIcon := mc.getTrendIcon()
	deltaHTML := ""
	if mc.Delta != "" {
		deltaHTML = fmt.Sprintf(`<span class="metric-delta metric-%s">%s %s</span>`,
			mc.Trend, trendIcon, mc.Delta)
	}

	return fmt.Sprintf(`
<div class="metric-card" id="%s">
    <div class="metric-header">
        <h4 class="metric-title">%s</h4>
        <div class="metric-trend" style="color: %s;">%s</div>
    </div>
    <div class="metric-value" style="color: %s;">%s</div>
    %s
</div>`,
		mc.ID,
		mc.Title,
		mc.getColor(),
		trendIcon,
		mc.Color,
		mc.Value,
		deltaHTML,
	)
}

// getTrendIcon 获取趋势图标
func (mc *MetricCard) getTrendIcon() string {
	icons := map[string]string{
		"up":      "↑",
		"down":    "↓",
		"neutral": "→",
	}

	if icon, ok := icons[mc.Trend]; ok {
		return icon
	}
	return "→"
}

// getColor 获取颜色
func (mc *MetricCard) getColor() string {
	colors := map[string]string{
		"up":      "#10b981", // 绿色
		"down":    "#ef4444", // 红色
		"neutral": "#6b7280", // 灰色
	}

	if color, ok := colors[mc.Trend]; ok {
		return color
	}
	return "#6b7280"
}

// Update 更新指标卡片
func (mc *MetricCard) Update(data map[string]interface{}) error {
	mc.mu.Lock()
	defer mc.mu.Unlock()

	if value, ok := data["value"].(string); ok {
		mc.Value = value
	}

	if delta, ok := data["delta"].(string); ok {
		mc.Delta = delta
	}

	if trend, ok := data["trend"].(string); ok {
		mc.Trend = trend
	}

	if color, ok := data["color"].(string); ok {
		mc.Color = color
	}

	return nil
}

// LogPanel 日志面板组件
type LogPanel struct {
	ID       string
	Title    string
	Logs     []LogEntry
	AutoScroll bool
	MaxLogs  int
	mu       sync.RWMutex
}

// LogEntry 日志条目
type LogEntry struct {
	Timestamp time.Time
	Level     string
	Message   string
	Source    string
}

// NewLogPanel 创建日志面板
func NewLogPanel(id, title string) *LogPanel {
	return &LogPanel{
		ID:         id,
		Title:      title,
		Logs:       make([]LogEntry, 0),
		AutoScroll: true,
		MaxLogs:    100,
	}
}

// Type 返回组件类型
func (lp *LogPanel) Type() ComponentType {
	return ComponentTypeLogPanel
}

// Render 渲染日志面板
func (lp *LogPanel) Render() string {
	lp.mu.RLock()
	defer lp.mu.RUnlock()

	logsHTML := ""
	for _, log := range lp.Logs {
		logsHTML += lp.renderLogEntry(log)
	}

	return fmt.Sprintf(`
<div class="log-panel" id="%s">
    <div class="log-panel-header">
        <h4>%s</h4>
        <button class="log-clear-btn" onclick="clearLogs('%s')">清除</button>
    </div>
    <div class="log-entries" id="%s-entries">
        %s
    </div>
</div>`,
		lp.ID,
		lp.Title,
		lp.ID,
		lp.ID,
		logsHTML,
	)
}

// renderLogEntry 渲染日志条目
func (lp *LogPanel) renderLogEntry(log LogEntry) string {
	return fmt.Sprintf(`
<div class="log-entry log-%s">
    <span class="log-time">%s</span>
    <span class="log-source">[%s]</span>
    <span class="log-message">%s</span>
</div>`,
		log.Level,
		log.Timestamp.Format("15:04:05.000"),
		log.Source,
		log.Message,
	)
}

// Update 更新日志面板
func (lp *LogPanel) Update(data map[string]interface{}) error {
	lp.mu.Lock()
	defer lp.mu.Unlock()

	if level, ok := data["level"].(string); ok {
		if message, ok := data["message"].(string); ok {
			source := getString(data, "source")
			log := LogEntry{
				Timestamp: time.Now(),
				Level:     level,
				Message:   message,
				Source:    source,
			}
			lp.Logs = append(lp.Logs, log)

			// 限制日志数量
			if len(lp.Logs) > lp.MaxLogs {
				lp.Logs = lp.Logs[len(lp.Logs)-lp.MaxLogs:]
			}
		}
	}

	if clear, ok := data["clear"].(bool); ok && clear {
		lp.Logs = make([]LogEntry, 0)
	}

	return nil
}

// === 辅助函数 ===

// generateID 生成唯一ID
func generateID(prefix string) string {
	return fmt.Sprintf("%s_%d", prefix, time.Now().UnixNano())
}

// getString 从map中获取字符串值
func getString(m map[string]interface{}, key string) string {
	if val, ok := m[key]; ok {
		if str, ok := val.(string); ok {
			return str
		}
	}
	return ""
}

// getInt 从map中获取整数值
func getInt(m map[string]interface{}, key string) int {
	if val, ok := m[key]; ok {
		if num, ok := val.(int); ok {
			return num
		}
		if f, ok := val.(float64); ok {
			return int(f)
		}
	}
	return 0
}
