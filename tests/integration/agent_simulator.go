package integration

import (
	"context"
	"fmt"
	"log"
	"sync"
	"time"
)

type AgentSimulator struct {
	agents map[string]*SimulatedAgent
	mu     sync.RWMutex
	logger *SimulatedLogger
}

type SimulatedAgent struct {
	Name      string                 `json:"name"`
	Type      string                 `json:"type"`
	Status    string                 `json:"status"`
	Responses map[string]interface{} `json:"responses"`
	Config    *AgentConfig           `json:"config"`
}

type AgentConfig struct {
	ResponseDelay  time.Duration `json:"response_delay"`
	ErrorRate      float64       `json:"error_rate"`
	MaxConcurrency int           `json:"max_concurrency"`
}

type SimulatedLogger struct {
	entries []LogEntry
	mu      sync.Mutex
}

type LogEntry struct {
	Timestamp time.Time              `json:"timestamp"`
	Level     string                 `json:"level"`
	Source    string                 `json:"source"`
	Message   string                 `json:"message"`
	Data      map[string]interface{} `json:"data,omitempty"`
}

func NewAgentSimulator(ctx context.Context) *AgentSimulator {
	return &AgentSimulator{
		agents: make(map[string]*SimulatedAgent),
		logger: &SimulatedLogger{entries: make([]LogEntry, 0)},
	}
}

func (as *AgentSimulator) SendMessage(ctx context.Context, message *AgentMessage) (*AgentMessage, error) {
	as.mu.RLock()
	agent, exists := as.agents[message.To]
	as.mu.RUnlock()

	if !exists {
		return nil, fmt.Errorf("智能体 %s 不存在", message.To)
	}

	as.logger.Info(fmt.Sprintf("发送消息到 %s", message.To), map[string]interface{}{
		"from": message.From,
		"type": message.Type,
	})

	time.Sleep(agent.Config.ResponseDelay)

	if shouldSimulateError(agent.Config.ErrorRate) {
		return nil, fmt.Errorf("模拟智能体错误")
	}

	response := &AgentMessage{
		From:      message.To,
		To:        message.From,
		Type:      MessageTypeTaskResponse,
		Payload:   as.generateResponse(message, agent),
		Timestamp: time.Now(),
	}

	as.logger.Info(fmt.Sprintf("从 %s 收到响应", message.From), map[string]interface{}{
		"to":   response.To,
		"type": response.Type,
	})

	return response, nil
}

func (as *AgentSimulator) ExecuteFailureScenario(ctx context.Context, scenario *FailureScenario) (*RecoveryResult, error) {
	startTime := time.Now()

	as.logger.Info("开始执行故障场景", map[string]interface{}{
		"scenario": scenario.Name,
		"type":     scenario.Type,
		"target":   scenario.Target,
	})

	switch scenario.Type {
	case "agent_failure":
		as.simulateAgentFailure(scenario.Target)
	case "network_failure":
		as.simulateNetworkFailure(scenario.Target)
	case "resource_exhaustion":
		as.simulateResourceExhaustion(scenario.Target)
	}

	recoveryTime := time.Duration(5+scenario.RandomInt(10)) * time.Second
	time.Sleep(recoveryTime)

	as.recoverFromFailure(scenario)

	result := &RecoveryResult{
		ScenarioName:   scenario.Name,
		RecoveryTime:   time.Since(startTime),
		Success:        true,
		DataLoss:       false,
		PartialFailure: false,
	}

	as.logger.Info("故障场景执行完成", map[string]interface{}{
		"scenario":      scenario.Name,
		"recovery_time": result.RecoveryTime,
		"success":       result.Success,
	})

	return result, nil
}

func (as *AgentSimulator) RegisterAgent(agent *SimulatedAgent) {
	as.mu.Lock()
	defer as.mu.Unlock()

	as.agents[agent.Name] = agent
	as.logger.Info("注册智能体", map[string]interface{}{
		"name": agent.Name,
		"type": agent.Type,
	})
}

func (as *AgentSimulator) generateResponse(message *AgentMessage, agent *SimulatedAgent) map[string]interface{} {
	response := make(map[string]interface{})

	switch message.Type {
	case MessageTypeTaskRequest:
		response["status"] = "success"
		response["message"] = fmt.Sprintf("智能体 %s 处理完成", agent.Name)
		response["data"] = agent.Responses
	default:
		response["status"] = "unknown"
		response["message"] = "未知消息类型"
	}

	return response
}

func (as *AgentSimulator) simulateAgentFailure(agentName string) {
	as.mu.Lock()
	defer as.mu.Unlock()

	if agent, exists := as.agents[agentName]; exists {
		agent.Status = "failed"
		as.logger.Warn("模拟智能体故障", map[string]interface{}{
			"agent": agentName,
		})
	}
}

func (as *AgentSimulator) simulateNetworkFailure(target string) {
	as.logger.Warn("模拟网络故障", map[string]interface{}{
		"target": target,
	})
}

func (as *AgentSimulator) simulateResourceExhaustion(resource string) {
	as.logger.Warn("模拟资源耗尽", map[string]interface{}{
		"resource": resource,
	})
}

func (as *AgentSimulator) recoverFromFailure(scenario *FailureScenario) {
	as.mu.Lock()
	defer as.mu.Unlock()

	switch scenario.Type {
	case "agent_failure":
		if agent, exists := as.agents[scenario.Target]; exists {
			agent.Status = "active"
			as.logger.Info("智能体恢复", map[string]interface{}{
				"agent": scenario.Target,
			})
		}
	default:
		as.logger.Info("系统恢复", map[string]interface{}{
			"scenario": scenario.Name,
		})
	}
}

func (sl *SimulatedLogger) Info(message string, data map[string]interface{}) {
	sl.mu.Lock()
	defer sl.mu.Unlock()

	entry := LogEntry{
		Timestamp: time.Now(),
		Level:     "INFO",
		Source:    "AgentSimulator",
		Message:   message,
		Data:      data,
	}
	sl.entries = append(sl.entries, entry)
	log.Printf("[INFO] %s: %s %+v", sl.entries[len(sl.entries)-1].Timestamp.Format(time.RFC3339), message, data)
}

func (sl *SimulatedLogger) Warn(message string, data map[string]interface{}) {
	sl.mu.Lock()
	defer sl.mu.Unlock()

	entry := LogEntry{
		Timestamp: time.Now(),
		Level:     "WARN",
		Source:    "AgentSimulator",
		Message:   message,
		Data:      data,
	}
	sl.entries = append(sl.entries, entry)
	log.Printf("[WARN] %s: %s %+v", sl.entries[len(sl.entries)-1].Timestamp.Format(time.RFC3339), message, data)
}

func shouldSimulateError(errorRate float64) bool {
	return false
}

func (fs *FailureScenario) RandomInt(max int) int {
	return max / 2
}
