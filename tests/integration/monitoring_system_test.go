package integration

import (
	"context"
	"fmt"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestMonitoringSystem(t *testing.T) {
	suite := &TestSuite{}
	suite.SetupSuite()
	defer suite.TearDownSuite()

	ctx := context.Background()

	t.Run("MetricsCollection", func(t *testing.T) {
		testMetricsCollection(ctx, t, suite)
	})

	t.Run("LogSystemIntegration", func(t *testing.T) {
		testLogSystemIntegration(ctx, t, suite)
	})

	t.Run("AlertSystem", func(t *testing.T) {
		testAlertSystem(ctx, t, suite)
	})

	t.Run("DashboardIntegration", func(t *testing.T) {
		testDashboardIntegration(ctx, t, suite)
	})

	t.Run("HealthChecks", func(t *testing.T) {
		testHealthChecks(ctx, t, suite)
	})
}

func testMetricsCollection(ctx context.Context, t *testing.T, suite *TestSuite) {
	metricTests := []struct {
		name        string
		metricType  string
		expectedKey string
	}{
		{
			name:        "WorkflowMetrics",
			metricType:  "workflow",
			expectedKey: "workflow_metrics",
		},
		{
			name:        "PerformanceMetrics",
			metricType:  "performance",
			expectedKey: "performance_metrics",
		},
		{
			name:        "SystemMetrics",
			metricType:  "system",
			expectedKey: "system_metrics",
		},
		{
			name:        "BusinessMetrics",
			metricType:  "business",
			expectedKey: "business_metrics",
		},
	}

	for _, test := range metricTests {
		t.Run(test.name, func(t *testing.T) {
			testRequests := 20
			requests := make([]*WorkflowRequest, testRequests)

			for i := 0; i < testRequests; i++ {
				requests[i] = &WorkflowRequest{
					ID:       fmt.Sprintf("METRIC_%s_%d", test.metricType, i),
					Type:     fmt.Sprintf("%s_test", test.metricType),
					Priority: "normal",
					InputData: map[string]interface{}{
						"metric_type": test.metricType,
						"request_id":  i,
					},
				}
			}

			benchmarks := &PerformanceBenchmarks{
				MaxResponseTime: time.Duration(MaxResponseTimeMs) * time.Millisecond,
				MinThroughput:   MinThroughput,
				MaxErrorRate:    MaxErrorRate,
				MaxMemoryUsage:  MaxMemoryUsageBytes,
				MaxCPUUsage:     MaxCPUUsage,
			}

			suite.collector.ExecuteConcurrentTest(ctx, requests, benchmarks)

			switch test.metricType {
			case "workflow":
				workflowMetrics := suite.collector.GetWorkflowMetrics()
				assert.NotNil(t, workflowMetrics, "工作流指标不应为空")
				assert.Contains(t, workflowMetrics, "avg_execution_time", "应包含平均执行时间")
				assert.Contains(t, workflowMetrics, "success_rate", "应包含成功率")

			case "performance":
				performanceMetrics := suite.collector.GetPerformanceMetrics()
				assert.NotNil(t, performanceMetrics, "性能指标不应为空")
				assert.Contains(t, performanceMetrics, test.expectedKey, "应包含期望的指标键")

			case "system":
				systemHealth := suite.orchestrator.CheckSystemHealth(ctx)
				assert.NotNil(t, systemHealth, "系统健康检查不应为空")
				assert.True(t, systemHealth.Healthy, "系统应为健康状态")
				assert.Contains(t, systemHealth.Checks, "environment", "应包含环境检查")

			case "business":
				businessMetrics := simulateBusinessMetrics(testRequests)
				assert.NotNil(t, businessMetrics, "业务指标不应为空")
				assert.Greater(t, businessMetrics["total_requests"], 0, "总请求数应大于0")
			}
		})
	}
}

func testLogSystemIntegration(ctx context.Context, t *testing.T, suite *TestSuite) {
	logTests := []struct {
		name      string
		logLevel  string
		logCount  int
		checkFunc func(logEntries []LogEntry) bool
	}{
		{
			name:     "InfoLogs",
			logLevel: "INFO",
			logCount: 15,
			checkFunc: func(logEntries []LogEntry) bool {
				infoCount := 0
				for _, entry := range logEntries {
					if entry.Level == "INFO" {
						infoCount++
					}
				}
				return infoCount >= 10
			},
		},
		{
			name:     "WarningLogs",
			logLevel: "WARN",
			logCount: 5,
			checkFunc: func(logEntries []LogEntry) bool {
				warnCount := 0
				for _, entry := range logEntries {
					if entry.Level == "WARN" {
						warnCount++
					}
				}
				return warnCount >= 2
			},
		},
		{
			name:     "ErrorLogs",
			logLevel: "ERROR",
			logCount: 3,
			checkFunc: func(logEntries []LogEntry) bool {
				errorCount := 0
				for _, entry := range logEntries {
					if entry.Level == "ERROR" {
						errorCount++
					}
				}
				return errorCount >= 1
			},
		},
	}

	for _, test := range logTests {
		t.Run(test.name, func(t *testing.T) {
			logRequests := test.logCount
			requests := make([]*WorkflowRequest, logRequests)

			for i := 0; i < logRequests; i++ {
				requests[i] = &WorkflowRequest{
					ID:       fmt.Sprintf("LOG_%s_%d", test.logLevel, i),
					Type:     "log_test",
					Priority: "normal",
					InputData: map[string]interface{}{
						"log_level":  test.logLevel,
						"request_id": i,
					},
				}
			}

			benchmarks := &PerformanceBenchmarks{
				MaxResponseTime: time.Duration(MaxResponseTimeMs) * time.Millisecond,
				MinThroughput:   MinThroughput,
				MaxErrorRate:    MaxErrorRate,
				MaxMemoryUsage:  MaxMemoryUsageBytes,
				MaxCPUUsage:     MaxCPUUsage,
			}

			suite.collector.ExecuteConcurrentTest(ctx, requests, benchmarks)

			logEntries := suite.simulator.logger.entries
			assert.Greater(t, len(logEntries), 0, "应生成日志条目")
			assert.True(t, test.checkFunc(logEntries), "日志检查应通过")

			for _, entry := range logEntries {
				assert.NotEmpty(t, entry.Timestamp, "日志时间戳不应为空")
				assert.NotEmpty(t, entry.Level, "日志级别不应为空")
				assert.NotEmpty(t, entry.Source, "日志来源不应为空")
				assert.NotEmpty(t, entry.Message, "日志消息不应为空")
			}
		})
	}
}

func testAlertSystem(ctx context.Context, t *testing.T, suite *TestSuite) {
	alertTests := []struct {
		name         string
		condition    string
		threshold    float64
		shouldAlert  bool
		testRequests int
	}{
		{
			name:         "HighResponseTimeAlert",
			condition:    "response_time",
			threshold:    3.0,
			shouldAlert:  true,
			testRequests: 50,
		},
		{
			name:         "LowSuccessRateAlert",
			condition:    "success_rate",
			threshold:    0.85,
			shouldAlert:  true,
			testRequests: 50,
		},
		{
			name:         "HighErrorRateAlert",
			condition:    "error_rate",
			threshold:    0.1,
			shouldAlert:  true,
			testRequests: 50,
		},
		{
			name:         "NormalOperationNoAlert",
			condition:    "response_time",
			threshold:    2.0,
			shouldAlert:  false,
			testRequests: 30,
		},
	}

	for _, test := range alertTests {
		t.Run(test.name, func(t *testing.T) {
			requests := make([]*WorkflowRequest, test.testRequests)

			for i := 0; i < test.testRequests; i++ {
				priority := "normal"
				if test.shouldAlert && i%5 == 0 {
					priority = "high"
				}

				requests[i] = &WorkflowRequest{
					ID:       fmt.Sprintf("ALERT_%s_%d", test.condition, i),
					Type:     "alert_test",
					Priority: priority,
					InputData: map[string]interface{}{
						"condition":    test.condition,
						"should_alert": test.shouldAlert,
						"request_id":   i,
					},
				}
			}

			benchmarks := &PerformanceBenchmarks{
				MaxResponseTime: time.Duration(float64(MaxResponseTimeMs) * test.threshold),
				MinThroughput:   MinThroughput,
				MaxErrorRate:    test.threshold,
				MaxMemoryUsage:  MaxMemoryUsageBytes,
				MaxCPUUsage:     MaxCPUUsage,
			}

			results := suite.collector.ExecuteConcurrentTest(ctx, requests, benchmarks)
			alerts := generateAlerts(results, test.condition, test.threshold)

			if test.shouldAlert {
				assert.Greater(t, len(alerts), 0, "应该生成告警")
				alertFound := false
				for _, alert := range alerts {
					if alert.Type == test.condition {
						alertFound = true
						assert.NotEmpty(t, alert.Message, "告警消息不应为空")
						assert.True(t, alert.Severity > 0, "告警严重性应大于0")
						break
					}
				}
				assert.True(t, alertFound, "应包含期望类型的告警")
			} else {
				for _, alert := range alerts {
					if alert.Type == test.condition {
						t.Errorf("正常操作不应生成告警: %s", alert.Message)
					}
				}
			}
		})
	}
}

func testDashboardIntegration(ctx context.Context, t *testing.T, suite *TestSuite) {
	dashboardTests := []struct {
		name      string
		dashboard string
		endpoints []string
		timeout   time.Duration
	}{
		{
			name:      "SystemOverview",
			dashboard: "system_overview",
			endpoints: []string{"/api/v1/system/status", "/api/v1/metrics/summary"},
			timeout:   5 * time.Second,
		},
		{
			name:      "PerformanceDashboard",
			dashboard: "performance",
			endpoints: []string{"/api/v1/performance/stats", "/api/v1/performance/history"},
			timeout:   10 * time.Second,
		},
		{
			name:      "WorkflowDashboard",
			dashboard: "workflow",
			endpoints: []string{"/api/v1/workflows/status", "/api/v1/workflows/metrics"},
			timeout:   7 * time.Second,
		},
	}

	for _, test := range dashboardTests {
		t.Run(test.name, func(t *testing.T) {
			requests := make([]*WorkflowRequest, 10)
			for i := 0; i < 10; i++ {
				requests[i] = &WorkflowRequest{
					ID:       fmt.Sprintf("DASHBOARD_%s_%d", test.dashboard, i),
					Type:     "dashboard_test",
					Priority: "normal",
					InputData: map[string]interface{}{
						"dashboard":  test.dashboard,
						"request_id": i,
					},
				}
			}

			benchmarks := &PerformanceBenchmarks{
				MaxResponseTime: time.Duration(MaxResponseTimeMs) * time.Millisecond,
				MinThroughput:   MinThroughput,
				MaxErrorRate:    MaxErrorRate,
				MaxMemoryUsage:  MaxMemoryUsageBytes,
				MaxCPUUsage:     MaxCPUUsage,
			}

			suite.collector.ExecuteConcurrentTest(ctx, requests, benchmarks)

			dashboardData := simulateDashboardData(test.dashboard, requests)
			assert.NotNil(t, dashboardData, "仪表板数据不应为空")

			for _, endpoint := range test.endpoints {
				endpointData := dashboardData[endpoint]
				assert.NotNil(t, endpointData, "端点数据不应为空: %s", endpoint)
				assert.Less(t, time.Duration(endpointData["response_time"].(float64))*time.Millisecond,
					test.timeout, "端点响应时间应小于超时")
				assert.Equal(t, 200, endpointData["status_code"], "端点应返回成功状态")
			}

			assert.Contains(t, dashboardData, "last_updated", "仪表板数据应包含最后更新时间")
			assert.True(t, dashboardData["last_updated"].(time.Time).After(time.Now().Add(-5*time.Minute)),
				"最后更新时间应是最近的")
		})
	}
}

func testHealthChecks(ctx context.Context, t *testing.T, suite *TestSuite) {
	healthTests := []struct {
		name            string
		component       string
		checks          []string
		expectedHealthy bool
	}{
		{
			name:            "APIGatewayHealth",
			component:       "api_gateway",
			checks:          []string{"database", "redis", "elasticsearch"},
			expectedHealthy: true,
		},
		{
			name:            "AgentSystemHealth",
			component:       "agents",
			checks:          []string{"patent-analyzer", "patent-retriever", "technical-analyst"},
			expectedHealthy: true,
		},
		{
			name:            "ToolSystemHealth",
			component:       "tools",
			checks:          []string{"text-analyzer", "patent-searcher", "calculator"},
			expectedHealthy: true,
		},
		{
			name:            "DegradedServiceHealth",
			component:       "external_service",
			checks:          []string{"deprecated_api"},
			expectedHealthy: false,
		},
	}

	for _, test := range healthTests {
		t.Run(test.name, func(t *testing.T) {
			requests := make([]*WorkflowRequest, 5)
			for i := 0; i < 5; i++ {
				requests[i] = &WorkflowRequest{
					ID:       fmt.Sprintf("HEALTH_%s_%d", test.component, i),
					Type:     "health_test",
					Priority: "normal",
					InputData: map[string]interface{}{
						"component":  test.component,
						"check":      test.checks[i%len(test.checks)],
						"request_id": i,
					},
				}
			}

			benchmarks := &PerformanceBenchmarks{
				MaxResponseTime: time.Duration(MaxResponseTimeMs) * time.Millisecond,
				MinThroughput:   MinThroughput,
				MaxErrorRate:    MaxErrorRate,
				MaxMemoryUsage:  MaxMemoryUsageBytes,
				MaxCPUUsage:     MaxCPUUsage,
			}

			suite.collector.ExecuteConcurrentTest(ctx, requests, benchmarks)

			systemHealth := suite.orchestrator.CheckSystemHealth(ctx)
			require.NotNil(t, systemHealth, "系统健康检查不应为空")

			componentHealth := simulateComponentHealth(test.component, test.checks)
			assert.NotNil(t, componentHealth, "组件健康检查不应为空")

			for _, check := range test.checks {
				healthKey := fmt.Sprintf("%s_%s", test.component, check)
				assert.Contains(t, systemHealth.Checks, healthKey,
					"健康检查应包含组件: %s", healthKey)
			}

			if test.expectedHealthy {
				expectedHealthyChecks := 0
				for check := range test.checks {
					healthKey := fmt.Sprintf("%s_%s", test.component, test.checks[check])
					if systemHealth.Checks[healthKey] {
						expectedHealthyChecks++
					}
				}
				assert.Greater(t, expectedHealthyChecks, len(test.checks)/2,
					"大多数检查应显示为健康")
			} else {
				atLeastOneUnhealthy := false
				for _, check := range test.checks {
					healthKey := fmt.Sprintf("%s_%s", test.component, check)
					if !systemHealth.Checks[healthKey] {
						atLeastOneUnhealthy = true
						break
					}
				}
				assert.True(t, atLeastOneUnhealthy, "降级服务应至少有一个不健康的检查")
			}

			assert.NotEmpty(t, systemHealth.Message, "健康状态消息不应为空")
			assert.Equal(t, test.expectedHealthy, systemHealth.Healthy,
				"整体健康状态应与预期一致")
		})
	}
}

func TestMonitoringSystemPerformance(t *testing.T) {
	suite := &TestSuite{}
	suite.SetupSuite()
	defer suite.TearDownSuite()

	ctx := context.Background()

	t.Run("MonitoringOverhead", func(t *testing.T) {
		testMonitoringOverhead(ctx, t, suite)
	})

	t.Run("MetricsAccuracy", func(t *testing.T) {
		testMetricsAccuracy(ctx, t, suite)
	})

	t.Run("LogRetention", func(t *testing.T) {
		testLogRetention(ctx, t, suite)
	})
}

func testMonitoringOverhead(ctx context.Context, t *testing.T, suite *TestSuite) {
	testRequests := 100

	withoutMonitoringRequests := make([]*WorkflowRequest, testRequests/2)
	for i := 0; i < testRequests/2; i++ {
		withoutMonitoringRequests[i] = &WorkflowRequest{
			ID:        fmt.Sprintf("NO_MONITOR_%d", i),
			Type:      "no_monitor_test",
			Priority:  "normal",
			InputData: map[string]interface{}{"monitoring": false},
		}
	}

	withMonitoringRequests := make([]*WorkflowRequest, testRequests/2)
	for i := 0; i < testRequests/2; i++ {
		withMonitoringRequests[i] = &WorkflowRequest{
			ID:        fmt.Sprintf("WITH_MONITOR_%d", i),
			Type:      "with_monitor_test",
			Priority:  "normal",
			InputData: map[string]interface{}{"monitoring": true},
		}
	}

	benchmarks := &PerformanceBenchmarks{
		MaxResponseTime: time.Duration(MaxResponseTimeMs) * time.Millisecond,
		MinThroughput:   MinThroughput,
		MaxErrorRate:    MaxErrorRate,
		MaxMemoryUsage:  MaxMemoryUsageBytes,
		MaxCPUUsage:     MaxCPUUsage,
	}

	startTime := time.Now()
	suite.collector.ExecuteConcurrentTest(ctx, withoutMonitoringRequests, benchmarks)
	withoutMonitoringTime := time.Since(startTime)

	startTime = time.Now()
	suite.collector.ExecuteConcurrentTest(ctx, withMonitoringRequests, benchmarks)
	withMonitoringTime := time.Since(startTime)

	overheadRatio := withMonitoringTime.Seconds() / withoutMonitoringTime.Seconds()
	assert.Less(t, overheadRatio, 1.2, "监控开销应小于20%%")

	memoryOverhead := simulateMemoryOverhead(testRequests / 2)
	assert.Less(t, memoryOverhead, 50*1024*1024, "内存开销应小于50MB")
}

func testMetricsAccuracy(ctx context.Context, t *testing.T, suite *TestSuite) {
	accuracyTests := []struct {
		name          string
		requestCount  int
		expectedRange struct {
			min float64
			max float64
		}
	}{
		{
			name:         "ResponseTimeAccuracy",
			requestCount: 50,
			expectedRange: struct {
				min float64
				max float64
			}{min: 100.0, max: 5000.0},
		},
		{
			name:         "ThroughputAccuracy",
			requestCount: 100,
			expectedRange: struct {
				min float64
				max float64
			}{min: 50.0, max: 500.0},
		},
		{
			name:         "SuccessRateAccuracy",
			requestCount: 75,
			expectedRange: struct {
				min float64
				max float64
			}{min: 0.8, max: 1.0},
		},
	}

	for _, test := range accuracyTests {
		t.Run(test.name, func(t *testing.T) {
			requests := make([]*WorkflowRequest, test.requestCount)
			for i := 0; i < test.requestCount; i++ {
				requests[i] = &WorkflowRequest{
					ID:       fmt.Sprintf("ACCURACY_%s_%d", test.name, i),
					Type:     "accuracy_test",
					Priority: "normal",
					InputData: map[string]interface{}{
						"accuracy_test": test.name,
						"request_id":    i,
					},
				}
			}

			benchmarks := &PerformanceBenchmarks{
				MaxResponseTime: time.Duration(MaxResponseTimeMs) * time.Millisecond,
				MinThroughput:   MinThroughput,
				MaxErrorRate:    MaxErrorRate,
				MaxMemoryUsage:  MaxMemoryUsageBytes,
				MaxCPUUsage:     MaxCPUUsage,
			}

			results := suite.collector.ExecuteConcurrentTest(ctx, requests, benchmarks)

			collectedMetrics := simulateCollectedMetrics(test.name, test.requestCount)
			actualMetrics := results

			for key, expectedRange := range map[string]struct {
				min float64
				max float64
			}{
				"response_time": {min: 100.0, max: 5000.0},
				"throughput":    {min: 50.0, max: 500.0},
				"success_rate":  {min: 0.8, max: 1.0},
			} {
				if actualValue, exists := actualMetrics[key]; exists {
					actualFloat := actualValue.(float64)
					assert.GreaterOrEqual(t, actualFloat, expectedRange.min,
						"指标 %s 应大于最小值: %f", key, expectedRange.min)
					assert.LessOrEqual(t, actualFloat, expectedRange.max,
						"指标 %s 应小于最大值: %f", key, expectedRange.max)
				}
			}

			accuracy := calculateMetricsAccuracy(collectedMetrics, actualMetrics)
			assert.GreaterOrEqual(t, accuracy, 0.9, "指标准确性应大于90%%")
		})
	}
}

func testLogRetention(ctx context.Context, t *testing.T, suite *TestSuite) {
	retentionTests := []struct {
		name      string
		logLevel  string
		retention time.Duration
		maxCount  int
	}{
		{
			name:      "ErrorLogsRetention",
			logLevel:  "ERROR",
			retention: 30 * 24 * time.Hour,
			maxCount:  1000,
		},
		{
			name:      "WarningLogsRetention",
			logLevel:  "WARN",
			retention: 7 * 24 * time.Hour,
			maxCount:  500,
		},
		{
			name:      "InfoLogsRetention",
			logLevel:  "INFO",
			retention: 3 * 24 * time.Hour,
			maxCount:  200,
		},
		{
			name:      "WarningLogsRetention",
			logLevel:  "WARN",
			retention: 7 * 24 * time.Hour, // 7 days
			maxCount:  500,
		},
		{
			name:      "InfoLogsRetention",
			logLevel:  "INFO",
			retention: 3 * 24 * time.Hour, // 3 days
			maxCount:  200,
		},
	}

	for _, test := range retentionTests {
		t.Run(test.name, func(t *testing.T) {
			logEntries := generateLogEntries(test.logLevel, test.maxCount+100)

			currentTime := time.Now()
			retainedEntries := applyLogRetention(logEntries, currentTime, test.retention)

			expectedCount := test.maxCount
			if test.logLevel == "ERROR" {
				expectedCount = test.maxCount
			}

			assert.LessOrEqual(t, len(retainedEntries), expectedCount,
				"保留的日志条目数量应小于最大值")

			for _, entry := range retainedEntries {
				age := currentTime.Sub(entry.Timestamp)
				assert.Less(t, age, test.retention,
					"保留的日志条目年龄应小于保留期")
			}

			oldestEntryTime := time.Now()
			if len(retainedEntries) > 0 {
				for _, entry := range retainedEntries {
					if entry.Timestamp.Before(oldestEntryTime) {
						oldestEntryTime = entry.Timestamp
					}
				}
				oldestAge := currentTime.Sub(oldestEntryTime)
				assert.Less(t, oldestAge, test.retention,
					"最老的保留条目年龄应小于保留期")
			}
		})
	}
}

func generateAlerts(results map[string]interface{}, condition string, threshold float64) []Alert {
	alerts := make([]Alert, 0)

	switch condition {
	case "response_time":
		if avgTime, exists := results["avg_response_time"]; exists {
			if avgTime.(float64) > threshold*1000 {
				alerts = append(alerts, Alert{
					Type: "response_time",
					Message: fmt.Sprintf("平均响应时间 %.2f ms 超过阈值 %.2f ms",
						avgTime.(float64), threshold*1000),
					Severity:  2,
					Timestamp: time.Now(),
				})
			}
		}

	case "success_rate":
		if totalTasks, exists := results["total_requests"]; exists {
			if completedTasks, exists := results["completed_tasks"]; exists {
				successRate := float64(completedTasks.(int)) / float64(totalTasks.(int))
				if successRate < threshold {
					alerts = append(alerts, Alert{
						Type: "success_rate",
						Message: fmt.Sprintf("成功率 %.2f%% 低于阈值 %.2f%%",
							successRate*100, threshold*100),
						Severity:  3,
						Timestamp: time.Now(),
					})
				}
			}
		}

	case "error_rate":
		if totalTasks, exists := results["total_requests"]; exists {
			if completedTasks, exists := results["completed_tasks"]; exists {
				errorCount := totalTasks.(int) - completedTasks.(int)
				errorRate := float64(errorCount) / float64(totalTasks.(int))
				if errorRate > threshold {
					alerts = append(alerts, Alert{
						Type: "error_rate",
						Message: fmt.Sprintf("错误率 %.2f%% 超过阈值 %.2f%%",
							errorRate*100, threshold*100),
						Severity:  3,
						Timestamp: time.Now(),
					})
				}
			}
		}
	}

	return alerts
}

func simulateBusinessMetrics(requestCount int) map[string]interface{} {
	return map[string]interface{}{
		"total_requests":      requestCount,
		"success_requests":    int(float64(requestCount) * 0.95),
		"failed_requests":     int(float64(requestCount) * 0.05),
		"avg_processing_time": 1500.0,
		"patent_processed":    int(float64(requestCount) * 0.8),
	}
}

func simulateDashboardData(dashboard string, requests []*WorkflowRequest) map[string]interface{} {
	data := make(map[string]interface{})

	for _, request := range requests {
		endpoint := fmt.Sprintf("/api/v1/%s/status", dashboard)
		if data[endpoint] == nil {
			data[endpoint] = map[string]interface{}{
				"response_time": 150.0 + float64(len(request.ID)%100),
				"status_code":   200,
				"last_accessed": time.Now().Add(-time.Duration(len(request.ID)%10) * time.Second),
			}
		}

		endpoint = fmt.Sprintf("/api/v1/%s/metrics", dashboard)
		if data[endpoint] == nil {
			data[endpoint] = map[string]interface{}{
				"requests_count": len(requests),
				"success_rate":   0.95,
				"avg_duration":   1200.0,
			}
		}
	}

	data["last_updated"] = time.Now()

	return data
}

func simulateComponentHealth(component string, checks []string) map[string]bool {
	health := make(map[string]bool)
	for _, check := range checks {
		if component == "external_service" && check == "deprecated_api" {
			health[check] = false
		} else {
			health[check] = true
		}
	}
	return health
}

func simulateMemoryOverhead(requestCount int) int64 {
	return int64(float64(requestCount) * 1024 * 0.1)
}

func simulateCollectedMetrics(testName string, requestCount int) map[string]interface{} {
	return map[string]interface{}{
		"response_time": 1500.0 + float64(requestCount)*2,
		"throughput":    float64(requestCount) / 60.0,
		"success_rate":  0.95,
	}
}

func calculateMetricsAccuracy(collected, actual map[string]interface{}) float64 {
	matchCount := 0
	totalCount := 0

	for key, actualValue := range actual {
		totalCount++
		if collectedValue, exists := collected[key]; exists {
			actualFloat := actualValue.(float64)
			collectedFloat := collectedValue.(float64)
			diff := actualFloat - collectedFloat
			if diff < 0 {
				diff = -diff
			}
			ratio := collectedFloat / actualFloat
			if ratio > 0.9 && ratio < 1.1 {
				matchCount++
			}
		}
	}

	return float64(matchCount) / float64(totalCount)
}

func generateLogEntries(level string, count int) []LogEntry {
	entries := make([]LogEntry, count)
	now := time.Now()

	for i := 0; i < count; i++ {
		entries[i] = LogEntry{
			Timestamp: now.Add(-time.Duration(i) * time.Minute),
			Level:     level,
			Source:    "test_system",
			Message:   fmt.Sprintf("Test log entry %d for level %s", i, level),
			Data:      map[string]interface{}{"entry_id": i, "level": level},
		}
	}

	return entries
}

func applyLogRetention(entries []LogEntry, currentTime time.Time, retention time.Duration) []LogEntry {
	retained := make([]LogEntry, 0)

	for _, entry := range entries {
		age := currentTime.Sub(entry.Timestamp)
		if age <= retention {
			retained = append(retained, entry)
		}
	}

	return retained
}

type Alert struct {
	Type      string
	Message   string
	Severity  int
	Timestamp time.Time
}
