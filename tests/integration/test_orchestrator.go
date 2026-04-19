package integration

import (
	"context"
	"fmt"
	"log"
	"sync"
	"time"

	"go.uber.org/zap"
)

type TestOrchestrator struct {
	logger      *zap.Logger
	tools       map[string]*AtomicTool
	agents      map[string]*AgentInstance
	workflows   map[string]*WorkflowDefinition
	environment *TestEnvironment
	mu          sync.RWMutex
}

func NewTestOrchestrator(ctx context.Context) *TestOrchestrator {
	logger, _ := zap.NewDevelopment()

	return &TestOrchestrator{
		logger:      logger,
		tools:       make(map[string]*AtomicTool),
		agents:      make(map[string]*AgentInstance),
		workflows:   make(map[string]*WorkflowDefinition),
		environment: NewTestEnvironment(),
	}
}

func (to *TestOrchestrator) PrepareEnvironment() error {
	to.logger.Info("准备测试环境")

	if err := to.environment.Setup(); err != nil {
		return fmt.Errorf("测试环境设置失败: %w", err)
	}

	if err := to.registerDefaultAgents(); err != nil {
		return fmt.Errorf("默认智能体注册失败: %w", err)
	}

	if err := to.loadWorkflowDefinitions(); err != nil {
		return fmt.Errorf("工作流定义加载失败: %w", err)
	}

	to.logger.Info("测试环境准备完成")
	return nil
}

func (to *TestOrchestrator) CleanupEnvironment(ctx context.Context) error {
	to.logger.Info("清理测试环境")

	if err := to.environment.Cleanup(); err != nil {
		to.logger.Error("测试环境清理失败", zap.Error(err))
		return err
	}

	to.logger.Info("测试环境清理完成")
	return nil
}

func (to *TestOrchestrator) ExecuteWorkflow(ctx context.Context, request *WorkflowRequest) (*WorkflowResult, error) {
	to.logger.Info("开始执行工作流", zap.String("workflow_id", request.ID))

	workflow, exists := to.workflows[request.Type]
	if !exists {
		return nil, fmt.Errorf("工作流类型 %s 不存在", request.Type)
	}

	result := &WorkflowResult{
		ID:        request.ID,
		Type:      request.Type,
		StartTime: time.Now(),
		Status:    "running",
		Stages:    make([]*WorkflowStage, 0),
	}

	for _, stageDef := range workflow.Stages {
		stage, err := to.executeWorkflowStage(ctx, stageDef, request, result)
		if err != nil {
			result.Status = "failed"
			result.Error = err.Error()
			result.EndTime = time.Now()
			return result, err
		}

		result.Stages = append(result.Stages, stage)
	}

	result.Status = "completed"
	result.EndTime = time.Now()
	result.Duration = result.EndTime.Sub(result.StartTime)

	to.logger.Info("工作流执行完成",
		zap.String("workflow_id", result.ID),
		zap.Duration("duration", result.Duration))

	return result, nil
}

func (to *TestOrchestrator) ExecuteOrchestration(ctx context.Context, task *OrchestrationTask) (*OrchestrationResult, error) {
	to.logger.Info("开始执行编排任务", zap.String("task_id", task.ID))

	result := &OrchestrationResult{
		ID:          task.ID,
		Description: task.Description,
		StartTime:   time.Now(),
		Status:      "running",
		SubTasks:    make([]*SubTask, 0),
	}

	subTasks := to.decomposeTask(task)

	for _, subTask := range subTasks {
		agent := to.selectOptimalAgent(subTask, task.Requirements)
		subTask.AssignedAgent = agent.Name
		subTask.Status = "pending"
		result.SubTasks = append(result.SubTasks, subTask)
	}

	for _, subTask := range result.SubTasks {
		subTask.StartTime = time.Now()
		subTask.Status = "running"

		executionTime := time.Duration(subTask.EstimatedDuration) * time.Second
		time.Sleep(executionTime)

		subTask.EndTime = time.Now()
		subTask.Duration = subTask.EndTime.Sub(subTask.StartTime)
		subTask.Status = "completed"
		subTask.Output = fmt.Sprintf("子任务 %s 执行完成", subTask.Name)
	}

	result.Status = "completed"
	result.EndTime = time.Now()
	result.Duration = result.EndTime.Sub(result.StartTime)

	to.logger.Info("编排任务执行完成",
		zap.String("task_id", result.ID),
		zap.Duration("duration", result.Duration))

	return result, nil
}

func (to *TestOrchestrator) RegisterTool(ctx context.Context, tool *AtomicTool) error {
	to.mu.Lock()
	defer to.mu.Unlock()

	to.tools[tool.Name] = tool
	to.logger.Info("工具注册成功", zap.String("tool_name", tool.Name))
	return nil
}

func (to *TestOrchestrator) CallTool(ctx context.Context, toolName string, params map[string]interface{}) (interface{}, error) {
	to.mu.RLock()
	tool, exists := to.tools[toolName]
	to.mu.RUnlock()

	if !exists {
		return nil, fmt.Errorf("工具 %s 不存在", toolName)
	}

	result, err := tool.Handler(ctx, params)
	if err != nil {
		to.logger.Error("工具调用失败",
			zap.String("tool_name", toolName),
			zap.Error(err))
		return nil, err
	}

	to.logger.Info("工具调用成功",
		zap.String("tool_name", toolName),
		zap.Any("params", params))

	return result, nil
}

func (to *TestOrchestrator) ListTools(ctx context.Context) ([]*AtomicTool, error) {
	to.mu.RLock()
	defer to.mu.RUnlock()

	tools := make([]*AtomicTool, 0, len(to.tools))
	for _, tool := range to.tools {
		tools = append(tools, tool)
	}

	return tools, nil
}

func (to *TestOrchestrator) CheckSystemHealth(ctx context.Context) *SystemHealth {
	health := &SystemHealth{
		Healthy: true,
		Checks:  make(map[string]bool),
		Message: "系统健康",
	}

	envHealthy := to.environment.IsHealthy()
	health.Checks["environment"] = envHealthy

	for name, agent := range to.agents {
		agentHealthy := agent.IsHealthy()
		health.Checks["agent_"+name] = agentHealthy
		if !agentHealthy {
			health.Healthy = false
		}
	}

	if !health.Healthy {
		health.Message = "系统存在问题"
	}

	return health
}

// NewTestOrchestrator 创建测试编排器
func NewTestOrchestrator(ctx context.Context) *TestOrchestrator {
	logger, _ := zap.NewDevelopment()

	return &TestOrchestrator{
		logger:      logger,
		tools:       make(map[string]*AtomicTool),
		agents:      make(map[string]*AgentInstance),
		workflows:   make(map[string]*WorkflowDefinition),
		environment: NewTestEnvironment(),
	}
}

// PrepareEnvironment 准备测试环境
func (to *TestOrchestrator) PrepareEnvironment() error {
	to.logger.Info("准备测试环境")

	if err := to.environment.Setup(); err != nil {
		return fmt.Errorf("测试环境设置失败: %w", err)
	}

	if err := to.registerDefaultAgents(); err != nil {
		return fmt.Errorf("默认智能体注册失败: %w", err)
	}

	if err := to.loadWorkflowDefinitions(); err != nil {
		return fmt.Errorf("工作流定义加载失败: %w", err)
	}

	to.logger.Info("测试环境准备完成")
	return nil
}

// CleanupEnvironment 清理测试环境
func (to *TestOrchestrator) CleanupEnvironment(ctx context.Context) error {
	to.logger.Info("清理测试环境")

	if err := to.environment.Cleanup(); err != nil {
		to.logger.Error("测试环境清理失败", zap.Error(err))
		return err
	}

	to.logger.Info("测试环境清理完成")
	return nil
}

// ExecuteWorkflow 执行工作流
func (to *TestOrchestrator) ExecuteWorkflow(ctx context.Context, request *WorkflowRequest) (*WorkflowResult, error) {
	to.logger.Info("开始执行工作流", zap.String("workflow_id", request.ID))

	workflow, exists := to.workflows[request.Type]
	if !exists {
		return nil, fmt.Errorf("工作流类型 %s 不存在", request.Type)
	}

	result := &WorkflowResult{
		ID:        request.ID,
		Type:      request.Type,
		StartTime: time.Now(),
		Status:    "running",
		Stages:    make([]*WorkflowStage, 0),
	}

	// 执行各个阶段
	for _, stageDef := range workflow.Stages {
		stage, err := to.executeWorkflowStage(ctx, stageDef, request, result)
		if err != nil {
			result.Status = "failed"
			result.Error = err.Error()
			result.EndTime = time.Now()
			return result, err
		}

		result.Stages = append(result.Stages, stage)
	}

	result.Status = "completed"
	result.EndTime = time.Now()
	result.Duration = result.EndTime.Sub(result.StartTime)

	to.logger.Info("工作流执行完成",
		zap.String("workflow_id", result.ID),
		zap.Duration("duration", result.Duration))

	return result, nil
}

// ExecuteOrchestration 执行编排任务
func (to *TestOrchestrator) ExecuteOrchestration(ctx context.Context, task *OrchestrationTask) (*OrchestrationResult, error) {
	to.logger.Info("开始执行编排任务", zap.String("task_id", task.ID))

	result := &OrchestrationResult{
		ID:          task.ID,
		Description: task.Description,
		StartTime:   time.Now(),
		Status:      "running",
		SubTasks:    make([]*SubTask, 0),
	}

	// 任务分解
	subTasks := to.decomposeTask(task)

	// 智能体分配
	for _, subTask := range subTasks {
		agent := to.selectOptimalAgent(subTask, task.Requirements)
		subTask.AssignedAgent = agent.Name
		subTask.Status = "pending"
		result.SubTasks = append(result.SubTasks, subTask)
	}

	// 执行子任务
	for _, subTask := range result.SubTasks {
		subTask.StartTime = time.Now()
		subTask.Status = "running"

		// 模拟执行时间
		executionTime := time.Duration(subTask.EstimatedDuration) * time.Second
		time.Sleep(executionTime)

		subTask.EndTime = time.Now()
		subTask.Duration = subTask.EndTime.Sub(subTask.StartTime)
		subTask.Status = "completed"
		subTask.Output = fmt.Sprintf("子任务 %s 执行完成", subTask.Name)
	}

	result.Status = "completed"
	result.EndTime = time.Now()
	result.Duration = result.EndTime.Sub(result.StartTime)

	to.logger.Info("编排任务执行完成",
		zap.String("task_id", result.ID),
		zap.Duration("duration", result.Duration))

	return result, nil
}

// RegisterTool 注册工具
func (to *TestOrchestrator) RegisterTool(ctx context.Context, tool *AtomicTool) error {
	to.mu.Lock()
	defer to.mu.Unlock()

	to.tools[tool.Name] = tool
	to.logger.Info("工具注册成功", zap.String("tool_name", tool.Name))
	return nil
}

// CallTool 调用工具
func (to *TestOrchestrator) CallTool(ctx context.Context, toolName string, params map[string]interface{}) (interface{}, error) {
	to.mu.RLock()
	tool, exists := to.tools[toolName]
	to.mu.RUnlock()

	if !exists {
		return nil, fmt.Errorf("工具 %s 不存在", toolName)
	}

	result, err := tool.Handler(ctx, params)
	if err != nil {
		to.logger.Error("工具调用失败",
			zap.String("tool_name", toolName),
			zap.Error(err))
		return nil, err
	}

	to.logger.Info("工具调用成功",
		zap.String("tool_name", toolName),
		zap.Any("params", params))

	return result, nil
}

// ListTools 列出所有工具
func (to *TestOrchestrator) ListTools(ctx context.Context) ([]*AtomicTool, error) {
	to.mu.RLock()
	defer to.mu.RUnlock()

	tools := make([]*AtomicTool, 0, len(to.tools))
	for _, tool := range to.tools {
		tools = append(tools, tool)
	}

	return tools, nil
}

// CheckSystemHealth 检查系统健康状态
func (to *TestOrchestrator) CheckSystemHealth(ctx context.Context) *SystemHealth {
	health := &SystemHealth{
		Healthy: true,
		Checks:  make(map[string]bool),
		Message: "系统健康",
	}

	// 检查环境
	envHealthy := to.environment.IsHealthy()
	health.Checks["environment"] = envHealthy

	// 检查智能体
	for name, agent := range to.agents {
		agentHealthy := agent.IsHealthy()
		health.Checks["agent_"+name] = agentHealthy
		if !agentHealthy {
			health.Healthy = false
		}
	}

	if !health.Healthy {
		health.Message = "系统存在问题"
	}

	return health
}

func (to *TestOrchestrator) registerDefaultAgents() error {
	defaultAgents := []*AgentInstance{
		{Name: "patent-analyzer", Type: "analysis", Status: "active"},
		{Name: "patent-retriever", Type: "retrieval", Status: "active"},
		{Name: "technical-analyst", Type: "technical", Status: "active"},
		{Name: "patent-drafter", Type: "drafting", Status: "active"},
		{Name: "patent-reviewer", Type: "review", Status: "active"},
		{Name: "documentation-agent", Type: "documentation", Status: "active"},
		{Name: "translation-agent", Type: "translation", Status: "active"},
	}
	
	for _, agent := range defaultAgents {
		to.agents[agent.Name] = agent
	}
	
	return nil
}

func (to *TestOrchestrator) loadWorkflowDefinitions() error {
	patentWorkflow := &WorkflowDefinition{
		Type: "patent_writing",
		Stages: []*WorkflowStageDefinition{
			{Name: "analysis", Agent: "patent-analyzer", EstimatedDuration: 30},
			{Name: "retrieval", Agent: "patent-retriever", EstimatedDuration: 45},
			{Name: "technical", Agent: "technical-analyst", EstimatedDuration: 60},
			{Name: "drafting", Agent: "patent-drafter", EstimatedDuration: 120},
			{Name: "review", Agent: "patent-reviewer", EstimatedDuration: 45},
		},
	}
	
	to.workflows[patentWorkflow.Type] = patentWorkflow
	return nil
}

func (to *TestOrchestrator) executeWorkflowStage(ctx context.Context, stageDef *WorkflowStageDefinition, request *WorkflowRequest, result *WorkflowResult) (*WorkflowStage, error) {
	stage := &WorkflowStage{
		Name:      stageDef.Name,
		Agent:     stageDef.Agent,
		StartTime: time.Now(),
		Status:    "running",
	}
	
	executionTime := time.Duration(stageDef.EstimatedDuration) * time.Second
	time.Sleep(executionTime)
	
	stage.EndTime = time.Now()
	stage.Duration = stage.EndTime.Sub(stage.StartTime)
	stage.Status = "completed"
	stage.Output = fmt.Sprintf("阶段 %s 执行完成", stage.Name)
	
	return stage, nil
}

func (to *TestOrchestrator) decomposeTask(task *OrchestrationTask) []*SubTask {
	subTasks := make([]*SubTask, 0, len(task.SubTasks))
	
	for i, subTaskName := range task.SubTasks {
		subTask := &SubTask{
			ID:                fmt.Sprintf("%s_sub_%d", task.ID, i),
			Name:              subTaskName,
			Type:              to.inferSubTaskType(subTaskName),
			EstimatedDuration:  to.estimateDuration(subTaskName),
			Dependencies:      to.getDependencies(subTaskName, task.SubTasks),
			Priority:          task.Priority,
			CreatedAt:         time.Now(),
		}
		subTasks = append(subTasks, subTask)
	}
	
	return subTasks
}

func (to *TestOrchestrator) inferSubTaskType(subTaskName string) string {
	if contains(subTaskName, "分析") {
		return "analysis"
	} else if contains(subTaskName, "检索") {
		return "retrieval"
	} else if contains(subTaskName, "撰写") {
		return "drafting"
	} else if contains(subTaskName, "审查") {
		return "review"
	}
	return "general"
}

func (to *TestOrchestrator) estimateDuration(subTaskName string) int {
	taskType := to.inferSubTaskType(subTaskName)
	switch taskType {
	case "analysis":
		return 30
	case "retrieval":
		return 45
	case "drafting":
		return 120
	case "review":
		return 45
	default:
		return 60
	}
}

func (to *TestOrchestrator) getDependencies(subTaskName string, allTasks []string) []string {
	dependencies := make([]string, 0)
	
	if contains(subTaskName, "撰写") {
		if containsAll(allTasks, []string{"分析", "检索"}) {
			dependencies = append(dependencies, "技术方案分析", "现有专利检索")
		}
	} else if contains(subTaskName, "审查") {
		if contains(allTasks, "撰写") {
			dependencies = append(dependencies, "权利要求书撰写", "说明书撰写")
		}
	}
	
	return dependencies
}

func (to *TestOrchestrator) selectOptimalAgent(subTask *SubTask, requirements *TaskRequirements) *AgentInstance {
	taskType := subTask.Type
	
	var bestAgent *AgentInstance
	for _, agent := range to.agents {
		if agent.Type == taskType && agent.Status == "active" {
			bestAgent = agent
			break
		}
	}
	
	if bestAgent == nil {
		for _, agent := range to.agents {
			if agent.Status == "active" {
				bestAgent = agent
				break
			}
		}
	}
	
	if bestAgent == nil {
		bestAgent = &AgentInstance{
			Name:   "default-agent",
			Type:   "general",
			Status: "active",
		}
	}
	
	return bestAgent
}

func contains(slice []string, item string) bool {
	for _, s := range slice {
		if s == item {
			return true
		}
	}
	return false
}

func containsAll(slice []string, items []string) bool {
	for _, item := range items {
		if !contains(slice, item) {
			return false
		}
	}
	return true
}

	for _, agent := range defaultAgents {
		to.agents[agent.Name] = agent
	}

	return nil
}

func (to *TestOrchestrator) loadWorkflowDefinitions() error {
	patentWorkflow := &WorkflowDefinition{
		Type: "patent_writing",
		Stages: []*WorkflowStageDefinition{
			{Name: "analysis", Agent: "patent-analyzer", EstimatedDuration: 30},
			{Name: "retrieval", Agent: "patent-retriever", EstimatedDuration: 45},
			{Name: "technical", Agent: "technical-analyst", EstimatedDuration: 60},
			{Name: "drafting", Agent: "patent-drafter", EstimatedDuration: 120},
			{Name: "review", Agent: "patent-reviewer", EstimatedDuration: 45},
		},
	}

	to.workflows[patentWorkflow.Type] = patentWorkflow
	return nil
}

func (to *TestOrchestrator) executeWorkflowStage(ctx context.Context, stageDef *WorkflowStageDefinition, request *WorkflowRequest, result *WorkflowResult) (*WorkflowStage, error) {
	stage := &WorkflowStage{
		Name:      stageDef.Name,
		Agent:     stageDef.Agent,
		StartTime: time.Now(),
		Status:    "running",
	}

	// 模拟执行时间
	executionTime := time.Duration(stageDef.EstimatedDuration) * time.Second
	time.Sleep(executionTime)

	stage.EndTime = time.Now()
	stage.Duration = stage.EndTime.Sub(stage.StartTime)
	stage.Status = "completed"
	stage.Output = fmt.Sprintf("阶段 %s 执行完成", stage.Name)

	return stage, nil
}

func (to *TestOrchestrator) decomposeTask(task *OrchestrationTask) []*SubTask {
	subTasks := make([]*SubTask, 0, len(task.SubTasks))

	for i, subTaskName := range task.SubTasks {
		subTask := &SubTask{
			ID:                fmt.Sprintf("%s_sub_%d", task.ID, i),
			Name:              subTaskName,
			Type:              to.inferSubTaskType(subTaskName),
			EstimatedDuration: to.estimateDuration(subTaskName),
			Dependencies:      to.getDependencies(subTaskName, task.SubTasks),
			Priority:          task.Priority,
			CreatedAt:         time.Now(),
		}
		subTasks = append(subTasks, subTask)
	}

	return subTasks
}

func (to *TestOrchestrator) inferSubTaskType(subTaskName string) string {
	if contains(subTaskName, "分析") {
		return "analysis"
	} else if contains(subTaskName, "检索") {
		return "retrieval"
	} else if contains(subTaskName, "撰写") {
		return "drafting"
	} else if contains(subTaskName, "审查") {
		return "review"
	}
	return "general"
}

func (to *TestOrchestrator) estimateDuration(subTaskName string) int {
	taskType := to.inferSubTaskType(subTaskName)
	switch taskType {
	case "analysis":
		return 30
	case "retrieval":
		return 45
	case "drafting":
		return 120
	case "review":
		return 45
	default:
		return 60
	}
}

func (to *TestOrchestrator) getDependencies(subTaskName string, allTasks []string) []string {
	dependencies := make([]string, 0)

	// 简单的依赖关系逻辑
	if contains(subTaskName, "撰写") {
		if containsAll(allTasks, []string{"分析", "检索"}) {
			dependencies = append(dependencies, "技术方案分析", "现有专利检索")
		}
	} else if contains(subTaskName, "审查") {
		if contains(allTasks, "撰写") {
			dependencies = append(dependencies, "权利要求书撰写", "说明书撰写")
		}
	}

	return dependencies
}

func (to *TestOrchestrator) selectOptimalAgent(subTask *SubTask, requirements *TaskRequirements) *AgentInstance {
	taskType := subTask.Type

	// 根据任务类型选择最优智能体
	var bestAgent *AgentInstance
	for _, agent := range to.agents {
		if agent.Type == taskType && agent.Status == "active" {
			bestAgent = agent
			break
		}
	}

	// 如果没有找到合适类型的智能体，选择一个活跃的
	if bestAgent == nil {
		for _, agent := range to.agents {
			if agent.Status == "active" {
				bestAgent = agent
				break
			}
		}
	}

	if bestAgent == nil {
		// 创建默认智能体
		bestAgent = &AgentInstance{
			Name:   "default-agent",
			Type:   "general",
			Status: "active",
		}
	}

	return bestAgent
}

// 辅助函数

func contains(slice []string, item string) bool {
	for _, s := range slice {
		if s == item {
			return true
		}
	}
	return false
}

func containsAll(slice []string, items []string) bool {
	for _, item := range items {
		if !contains(slice, item) {
			return false
		}
	}
	return true
}
