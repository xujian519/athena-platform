package integration

import (
	"context"
	"time"
)

type MessageType string

const (
	MessageTypeTaskRequest  MessageType = "task_request"
	MessageTypeTaskResponse MessageType = "task_response"
	MessageTypeHeartbeat    MessageType = "heartbeat"
)

type AgentMessage struct {
	From      string                 `json:"from"`
	To        string                 `json:"to"`
	Type      MessageType            `json:"type"`
	Payload   map[string]interface{} `json:"payload"`
	Timestamp time.Time              `json:"timestamp"`
}

type WorkflowRequest struct {
	ID             string                 `json:"id"`
	Type           string                 `json:"type"`
	Priority       string                 `json:"priority"`
	InputData      map[string]interface{} `json:"input_data"`
	ExpectedAgents []string               `json:"expected_agents"`
	CreatedAt      time.Time              `json:"created_at"`
}

type WorkflowResult struct {
	ID        string           `json:"id"`
	Type      string           `json:"type"`
	Status    string           `json:"status"`
	StartTime time.Time        `json:"start_time"`
	EndTime   time.Time        `json:"end_time"`
	Duration  time.Duration    `json:"duration"`
	Error     string           `json:"error,omitempty"`
	Stages    []*WorkflowStage `json:"stages"`
}

type WorkflowStage struct {
	Name      string        `json:"name"`
	Agent     string        `json:"agent"`
	Status    string        `json:"status"`
	StartTime time.Time     `json:"start_time"`
	EndTime   time.Time     `json:"end_time"`
	Duration  time.Duration `json:"duration"`
	Output    string        `json:"output"`
	Error     string        `json:"error,omitempty"`
}

type WorkflowDefinition struct {
	Type   string                     `json:"type"`
	Stages []*WorkflowStageDefinition `json:"stages"`
}

type WorkflowStageDefinition struct {
	Name              string `json:"name"`
	Agent             string `json:"agent"`
	EstimatedDuration int    `json:"estimated_duration"`
}

type OrchestrationTask struct {
	ID           string            `json:"id"`
	Description  string            `json:"description"`
	Priority     string            `json:"priority"`
	Dependencies []string          `json:"dependencies"`
	SubTasks     []string          `json:"sub_tasks"`
	Requirements *TaskRequirements `json:"requirements"`
}

type TaskRequirements struct {
	MinQuality     float64  `json:"min_quality"`
	MaxDuration    int      `json:"max_duration"`
	RequiredAgents []string `json:"required_agents"`
}

type OrchestrationResult struct {
	ID          string        `json:"id"`
	Description string        `json:"description"`
	Status      string        `json:"status"`
	StartTime   time.Time     `json:"start_time"`
	EndTime     time.Time     `json:"end_time"`
	Duration    time.Duration `json:"duration"`
	SubTasks    []*SubTask    `json:"sub_tasks"`
}

type SubTask struct {
	ID                string        `json:"id"`
	Name              string        `json:"name"`
	Type              string        `json:"type"`
	AssignedAgent     string        `json:"assigned_agent"`
	Status            string        `json:"status"`
	Priority          string        `json:"priority"`
	EstimatedDuration int           `json:"estimated_duration"`
	Dependencies      []string      `json:"dependencies"`
	CreatedAt         time.Time     `json:"created_at"`
	StartedAt         time.Time     `json:"started_at,omitempty"`
	EndTime           time.Time     `json:"end_time,omitempty"`
	Duration          time.Duration `json:"duration,omitempty"`
	Output            string        `json:"output,omitempty"`
}

type AtomicTool struct {
	Name        string      `json:"name"`
	Description string      `json:"description"`
	Version     string      `json:"version"`
	Category    string      `json:"category"`
	Parameters  []Parameter `json:"parameters"`
	Handler     ToolHandler `json:"-"`
}

type Parameter struct {
	Name     string      `json:"name"`
	Type     string      `json:"type"`
	Required bool        `json:"required"`
	Default  interface{} `json:"default,omitempty"`
}

type ToolHandler func(ctx context.Context, params map[string]interface{}) (interface{}, error)

type AgentInstance struct {
	Name   string `json:"name"`
	Type   string `json:"type"`
	Status string `json:"status"`
}

func (a *AgentInstance) IsHealthy() bool {
	return a.Status == "active"
}

type PatentDataConfig struct {
	Complexity string `json:"complexity"`
	Technology string `json:"technology"`
	Country    string `json:"country"`
}

type PerformanceBenchmarks struct {
	MaxResponseTime time.Duration `json:"max_response_time"`
	MinThroughput   int           `json:"min_throughput"`
	MaxErrorRate    float64       `json:"max_error_rate"`
	MaxMemoryUsage  int64         `json:"max_memory_usage"`
	MaxCPUUsage     float64       `json:"max_cpu_usage"`
}

type FailureScenario struct {
	Name        string `json:"name"`
	Description string `json:"description"`
	Type        string `json:"type"`
	Target      string `json:"target"`
	Action      string `json:"action"`
}

type RecoveryResult struct {
	ScenarioName   string        `json:"scenario_name"`
	RecoveryTime   time.Duration `json:"recovery_time"`
	Success        bool          `json:"success"`
	DataLoss       bool          `json:"data_loss"`
	PartialFailure bool          `json:"partial_failure"`
}

type SystemHealth struct {
	Healthy bool            `json:"healthy"`
	Checks  map[string]bool `json:"checks"`
	Message string          `json:"message"`
}

type TestEnvironment struct {
	Name      string            `json:"name"`
	Status    string            `json:"status"`
	Endpoints map[string]string `json:"endpoints"`
}

func NewTestEnvironment() *TestEnvironment {
	return &TestEnvironment{
		Name:   "integration-test",
		Status: "initializing",
		Endpoints: map[string]string{
			"api_gateway": "http://localhost:8080",
			"redis":       "localhost:6379",
			"postgres":    "localhost:5432",
		},
	}
}

func (te *TestEnvironment) Setup() error {
	te.Status = "ready"
	return nil
}

func (te *TestEnvironment) Cleanup() error {
	te.Status = "cleaned"
	return nil
}

func (te *TestEnvironment) IsHealthy() bool {
	return te.Status == "ready"
}
