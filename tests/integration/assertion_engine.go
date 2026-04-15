package integration

import (
	"testing"
	"time"
)

type AssertionEngine struct {
	assertions []AssertionResult
}

type AssertionResult struct {
	Name      string    `json:"name"`
	Passed    bool      `json:"passed"`
	Message   string    `json:"message"`
	Timestamp time.Time `json:"timestamp"`
}

func NewAssertionEngine() *AssertionEngine {
	return &AssertionEngine{
		assertions: make([]AssertionResult, 0),
	}
}

func (ae *AssertionEngine) AssertMessageResponse(t *testing.T, request *AgentMessage, response *AgentMessage) {
	result := AssertionResult{
		Name:      "MessageResponse",
		Timestamp: time.Now(),
	}

	if response.From != request.To {
		result.Passed = false
		result.Message = "响应来源不匹配"
		ae.assertions = append(ae.assertions, result)
		t.Errorf(result.Message)
		return
	}

	if response.To != request.From {
		result.Passed = false
		result.Message = "响应目标不匹配"
		ae.assertions = append(ae.assertions, result)
		t.Errorf(result.Message)
		return
	}

	result.Passed = true
	result.Message = "消息响应正确"
	ae.assertions = append(ae.assertions, result)
}

func (ae *AssertionEngine) AssertWorkflowResult(t *testing.T, request *WorkflowRequest, result *WorkflowResult) {
	result.AssertionResult = AssertionResult{
		Name:      "WorkflowResult",
		Timestamp: time.Now(),
	}

	if result.ID != request.ID {
		result.AssertionResult.Passed = false
		result.AssertionResult.Message = "工作流ID不匹配"
		ae.assertions = append(ae.assertions, result.AssertionResult)
		t.Errorf(result.AssertionResult.Message)
		return
	}

	if result.Type != request.Type {
		result.AssertionResult.Passed = false
		result.AssertionResult.Message = "工作流类型不匹配"
		ae.assertions = append(ae.assertions, result.AssertionResult)
		t.Errorf(result.AssertionResult.Message)
		return
	}

	if result.Status != "completed" {
		result.AssertionResult.Passed = false
		result.AssertionResult.Message = "工作流未完成"
		ae.assertions = append(ae.assertions, result.AssertionResult)
		t.Errorf(result.AssertionResult.Message)
		return
	}

	result.AssertionResult.Passed = true
	result.AssertionResult.Message = "工作流结果正确"
	ae.assertions = append(ae.assertions, result.AssertionResult)
}

func (ae *AssertionEngine) AssertToolResult(t *testing.T, tool *AtomicTool, params map[string]interface{}, result interface{}) {
	assertionResult := AssertionResult{
		Name:      "ToolResult",
		Timestamp: time.Now(),
	}

	if result == nil {
		assertionResult.Passed = false
		assertionResult.Message = "工具结果为空"
		ae.assertions = append(ae.assertions, assertionResult)
		t.Errorf(assertionResult.Message)
		return
	}

	assertionResult.Passed = true
	assertionResult.Message = "工具结果正确"
	ae.assertions = append(ae.assertions, assertionResult)
}

func (ae *AssertionEngine) AssertPerformanceResults(t *testing.T, concurrency int, results map[string]interface{}, benchmarks *PerformanceBenchmarks) {
	assertionResult := AssertionResult{
		Name:      "PerformanceResults",
		Timestamp: time.Now(),
	}

	avgResponseTime, ok := results["avg_response_time"].(time.Duration)
	if !ok || avgResponseTime > benchmarks.MaxResponseTime {
		assertionResult.Passed = false
		assertionResult.Message = "平均响应时间超过基准"
		ae.assertions = append(ae.assertions, assertionResult)
		t.Errorf(assertionResult.Message)
		return
	}

	throughput, ok := results["throughput"].(float64)
	if !ok || throughput < float64(benchmarks.MinThroughput) {
		assertionResult.Passed = false
		assertionResult.Message = "吞吐量低于基准"
		ae.assertions = append(ae.assertions, assertionResult)
		t.Errorf(assertionResult.Message)
		return
	}

	assertionResult.Passed = true
	assertionResult.Message = "性能测试通过"
	ae.assertions = append(ae.assertions, assertionResult)
}

func (ae *AssertionEngine) AssertFaultTolerance(t *testing.T, scenario *FailureScenario, result *RecoveryResult) {
	assertionResult := AssertionResult{
		Name:      "FaultTolerance",
		Timestamp: time.Now(),
	}

	if !result.Success {
		assertionResult.Passed = false
		assertionResult.Message = "故障恢复失败"
		ae.assertions = append(ae.assertions, assertionResult)
		t.Errorf(assertionResult.Message)
		return
	}

	if result.DataLoss {
		assertionResult.Passed = false
		assertionResult.Message = "存在数据丢失"
		ae.assertions = append(ae.assertions, assertionResult)
		t.Errorf(assertionResult.Message)
		return
	}

	assertionResult.Passed = true
	assertionResult.Message = "故障容错测试通过"
	ae.assertions = append(ae.assertions, assertionResult)
}

func (ae *AssertionEngine) GetResults() []AssertionResult {
	return ae.assertions
}

func (ae *AssertionEngine) GetPassedCount() int {
	count := 0
	for _, result := range ae.assertions {
		if result.Passed {
			count++
		}
	}
	return count
}

func (ae *AssertionEngine) GetFailedCount() int {
	count := 0
	for _, result := range ae.assertions {
		if !result.Passed {
			count++
		}
	}
	return count
}
