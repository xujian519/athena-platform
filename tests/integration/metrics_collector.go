package integration

import (
	"context"
	"fmt"
	"sync"
	"time"
)

type MetricsCollector struct {
	metrics       map[string]interface{}
	communication map[string]float64
	workflow      map[string]float64
	performance   map[string]interface{}
	mu            sync.RWMutex
}

func NewMetricsCollector() *MetricsCollector {
	return &MetricsCollector{
		metrics:       make(map[string]interface{}),
		communication: make(map[string]float64),
		workflow:      make(map[string]float64),
		performance:   make(map[string]interface{}),
	}
}

func (mc *MetricsCollector) RecordCommunication(from, to string, success bool, duration time.Duration) {
	mc.mu.Lock()
	defer mc.mu.Unlock()

	key := fmt.Sprintf("%s_to_%s", from, to)
	if _, exists := mc.communication[key]; !exists {
		mc.communication[key] = 0
	}

	if success {
		mc.communication[key]++
	}

	mc.communication[fmt.Sprintf("%s_duration", key)] = duration.Seconds()
}

func (mc *MetricsCollector) RecordWorkflowExecution(workflowType string, duration time.Duration, success bool) {
	mc.mu.Lock()
	defer mc.mu.Unlock()

	key := fmt.Sprintf("%s_executions", workflowType)
	if _, exists := mc.workflow[key]; !exists {
		mc.workflow[key] = 0
	}
	mc.workflow[key]++

	mc.workflow[fmt.Sprintf("%s_avg_duration", workflowType)] = duration.Seconds()

	if success {
		successKey := fmt.Sprintf("%s_success_rate", workflowType)
		if _, exists := mc.workflow[successKey]; !exists {
			mc.workflow[successKey] = 0
		}
		mc.workflow[successKey]++
	}
}

func (mc *MetricsCollector) RecordPerformanceTest(concurrency int, avgResponseTime time.Duration, throughput float64, errorRate float64) {
	mc.mu.Lock()
	defer mc.mu.Unlock()

	mc.metrics[fmt.Sprintf("concurrency_%d_avg_response_time", concurrency)] = avgResponseTime.Seconds()
	mc.metrics[fmt.Sprintf("concurrency_%d_throughput", concurrency)] = throughput
	mc.metrics[fmt.Sprintf("concurrency_%d_error_rate", concurrency)] = errorRate
}

func (mc *MetricsCollector) ExecuteConcurrentTest(ctx context.Context, tasks []*WorkflowRequest, benchmarks *PerformanceBenchmarks) map[string]interface{} {
	startTime := time.Now()

	results := make(map[string]interface{})
	completedTasks := 0
	var totalDuration time.Duration
	errors := 0

	for _, task := range tasks {
		taskStart := time.Now()

		taskDuration := time.Duration(100+task.RandomInt(500)) * time.Millisecond
		time.Sleep(taskDuration)

		taskEnd := time.Now()
		totalDuration += taskEnd.Sub(taskStart)
		completedTasks++

		if task.RandomInt(100) < 2 {
			errors++
		}
	}

	totalTime := time.Since(startTime)
	avgResponseTime := totalDuration / time.Duration(completedTasks)
	throughput := float64(completedTasks) / totalTime.Seconds()
	errorRate := float64(errors) / float64(len(tasks))

	results["total_tasks"] = len(tasks)
	results["completed_tasks"] = completedTasks
	results["errors"] = errors
	results["total_time"] = totalTime.Seconds()
	results["avg_response_time"] = avgResponseTime.Seconds()
	results["throughput"] = throughput
	results["error_rate"] = errorRate

	mc.RecordPerformanceTest(len(tasks), avgResponseTime, throughput, errorRate)

	return results
}

func (mc *MetricsCollector) GetCommunicationMetrics() map[string]float64 {
	mc.mu.RLock()
	defer mc.mu.RUnlock()

	metrics := make(map[string]float64)

	totalSuccess := 0.0
	totalRequests := 0.0

	for key, value := range mc.communication {
		if !contains(key, "_duration") {
			metrics[key] = value
			totalSuccess += value
			totalRequests++
		}
	}

	if totalRequests > 0 {
		metrics["success_rate"] = totalSuccess / totalRequests
	}

	return metrics
}

func (mc *MetricsCollector) GetWorkflowMetrics() map[string]float64 {
	mc.mu.RLock()
	defer mc.mu.RUnlock()

	metrics := make(map[string]float64)

	totalDuration := 0.0
	successCount := 0.0
	totalCount := 0.0

	for key, value := range mc.workflow {
		if contains(key, "_avg_duration") {
			metrics[key] = value
			totalDuration += value
		} else if contains(key, "_success_rate") {
			metrics[key] = value / mc.workflow[fmt.Sprintf("%s_executions", extractWorkflowType(key))]
			successCount += value
		} else if contains(key, "_executions") {
			totalCount += value
		}
	}

	if totalCount > 0 {
		metrics["avg_execution_time"] = totalDuration / totalCount
		metrics["success_rate"] = successCount / totalCount
	}

	return metrics
}

func (mc *MetricsCollector) GetPerformanceMetrics() map[string]interface{} {
	mc.mu.RLock()
	defer mc.mu.RUnlock()

	return mc.performance
}

func (mc *MetricsCollector) GenerateReport() (string, error) {
	mc.mu.RLock()
	defer mc.mu.RUnlock()

	report := "测试指标报告\n"
	report += "============\n\n"

	report += "通信指标:\n"
	commMetrics := mc.GetCommunicationMetrics()
	for key, value := range commMetrics {
		report += fmt.Sprintf("  %s: %.2f\n", key, value)
	}

	report += "\n工作流指标:\n"
	workflowMetrics := mc.GetWorkflowMetrics()
	for key, value := range workflowMetrics {
		report += fmt.Sprintf("  %s: %.2f\n", key, value)
	}

	report += "\n性能指标:\n"
	for key, value := range mc.metrics {
		report += fmt.Sprintf("  %s: %v\n", key, value)
	}

	return report, nil
}

func (mc *MetricsCollector) Reset() {
	mc.mu.Lock()
	defer mc.mu.Unlock()

	mc.metrics = make(map[string]interface{})
	mc.communication = make(map[string]float64)
	mc.workflow = make(map[string]float64)
	mc.performance = make(map[string]interface{})
}

func extractWorkflowType(key string) string {
	if len(key) > 14 && key[len(key)-14:] == "_success_rate" {
		return key[:len(key)-14]
	}
	return key
}

func contains(s, substr string) bool {
	return len(s) >= len(substr) && s[len(s)-len(substr):] == substr ||
		(len(s) >= len(substr) && s[:len(substr)] == substr)
}

func (wr *WorkflowRequest) RandomInt(max int) int {
	return max / 2
}
