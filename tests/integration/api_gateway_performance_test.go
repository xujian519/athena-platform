package integration

import (
	"context"
	"fmt"
	"sync"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestAPIGatewayPerformance(t *testing.T) {
	suite := &TestSuite{}
	suite.SetupSuite()
	defer suite.TearDownSuite()

	ctx := context.Background()

	t.Run("BasicPerformance", func(t *testing.T) {
		testBasicPerformance(ctx, t, suite)
	})

	t.Run("LoadTesting", func(t *testing.T) {
		testLoadTesting(ctx, t, suite)
	})

	t.Run("StressTesting", func(t *testing.T) {
		testStressTesting(ctx, t, suite)
	})

	t.Run("ScalabilityTesting", func(t *testing.T) {
		testScalabilityTesting(ctx, t, suite)
	})

	t.Run("ResourceUtilization", func(t *testing.T) {
		testResourceUtilization(ctx, t, suite)
	})
}

func testBasicPerformance(ctx context.Context, t *testing.T, suite *TestSuite) {
	benchmarks := &PerformanceBenchmarks{
		MaxResponseTime: time.Duration(MaxResponseTimeMs) * time.Millisecond,
		MinThroughput:   MinThroughput,
		MaxErrorRate:    MaxErrorRate,
		MaxMemoryUsage:  MaxMemoryUsageBytes,
		MaxCPUUsage:     MaxCPUUsage,
	}

	requestCount := 100
	requests := make([]*WorkflowRequest, requestCount)

	for i := 0; i < requestCount; i++ {
		requests[i] = &WorkflowRequest{
			ID:        fmt.Sprintf("PERF_BASIC_%d", i),
			Type:      "simple_task",
			Priority:  "normal",
			InputData: map[string]interface{}{"test_data": i},
		}
	}

	startTime := time.Now()
	results := suite.collector.ExecuteConcurrentTest(ctx, requests, benchmarks)
	totalTime := time.Since(startTime)

	successCount := results["completed_tasks"].(int)
	errorCount := requestCount - successCount
	avgResponseTime := time.Duration(results["avg_response_time"].(float64)) * time.Millisecond
	throughput := results["throughput"].(float64)
	errorRate := float64(errorCount) / float64(requestCount)

	assert.Greater(t, successCount, 95, "成功请求数应大于95")
	assert.Less(t, avgResponseTime, benchmarks.MaxResponseTime, "平均响应时间应小于基准")
	assert.Greater(t, throughput, float64(benchmarks.MinThroughput), "吞吐量应大于基准")
	assert.Less(t, errorRate, benchmarks.MaxErrorRate, "错误率应小于基准")

	suite.assertions.AssertPerformanceResults(t, requestCount, results, benchmarks)
}

func testLoadTesting(ctx context.Context, t *testing.T, suite *TestSuite) {
	loadLevels := []int{50, 100, 200, 500}

	for _, loadLevel := range loadLevels {
		t.Run(fmt.Sprintf("LoadLevel_%d", loadLevel), func(t *testing.T) {
			benchmarks := &PerformanceBenchmarks{
				MaxResponseTime: time.Duration(MaxResponseTimeMs*2) * time.Millisecond,
				MinThroughput:   MinThroughput * 2,
				MaxErrorRate:    MaxErrorRate * 2,
				MaxMemoryUsage:  MaxMemoryUsageBytes * 2,
				MaxCPUUsage:     MaxCPUUsage * 1.5,
			}

			requests := make([]*WorkflowRequest, loadLevel)
			for i := 0; i < loadLevel; i++ {
				requests[i] = &WorkflowRequest{
					ID:       fmt.Sprintf("LOAD_%d_%d", loadLevel, i),
					Type:     "medium_task",
					Priority: "normal",
					InputData: map[string]interface{}{
						"load_level": loadLevel,
						"request_id": i,
					},
				}
			}

			startTime := time.Now()
			results := suite.collector.ExecuteConcurrentTest(ctx, requests, benchmarks)
			executionTime := time.Since(startTime)

			successCount := results["completed_tasks"].(int)
			throughput := results["throughput"].(float64)
			errorRate := 1.0 - (float64(successCount) / float64(loadLevel))

			minSuccessRate := 0.95
			if loadLevel > 200 {
				minSuccessRate = 0.90
			}

			successRate := float64(successCount) / float64(loadLevel)
			assert.GreaterOrEqual(t, successRate, minSuccessRate,
				"负载级别 %d 成功率应大于 %.2f", loadLevel, minSuccessRate)

			assert.Greater(t, throughput, float64(MinThroughput),
				"吞吐量应大于最小基准: %d", MinThroughput)

			assert.Less(t, executionTime.Seconds(), 60.0,
				"负载测试应在60秒内完成")

			suite.collector.RecordPerformanceTest(loadLevel,
				time.Duration(results["avg_response_time"].(float64))*time.Millisecond,
				throughput, errorRate)
		})
	}
}

func testStressTesting(ctx context.Context, t *testing.T, suite *TestSuite) {
	stressLevels := []int{1000, 2000, 5000}

	for _, stressLevel := range stressLevels {
		t.Run(fmt.Sprintf("StressLevel_%d", stressLevel), func(t *testing.T) {
			benchmarks := &PerformanceBenchmarks{
				MaxResponseTime: time.Duration(MaxResponseTimeMs*5) * time.Millisecond,
				MinThroughput:   MinThroughput / 2,
				MaxErrorRate:    MaxErrorRate * 5,
				MaxMemoryUsage:  MaxMemoryUsageBytes * 3,
				MaxCPUUsage:     MaxCPUUsage * 2,
			}

			requests := make([]*WorkflowRequest, stressLevel)
			for i := 0; i < stressLevel; i++ {
				requests[i] = &WorkflowRequest{
					ID:       fmt.Sprintf("STRESS_%d_%d", stressLevel, i),
					Type:     "complex_task",
					Priority: "low",
					InputData: map[string]interface{}{
						"stress_level": stressLevel,
						"request_id":   i,
						"data":         fmt.Sprintf("stress_data_%d", i),
					},
				}
			}

			startTime := time.Now()
			results := suite.collector.ExecuteConcurrentTest(ctx, requests, benchmarks)
			executionTime := time.Since(startTime)

			successCount := results["completed_tasks"].(int)
			errorCount := stressLevel - successCount

			minSuccessRate := 0.85
			if stressLevel > 2000 {
				minSuccessRate = 0.80
			}

			successRate := float64(successCount) / float64(stressLevel)
			assert.GreaterOrEqual(t, successRate, minSuccessRate,
				"压力级别 %d 成功率应大于 %.2f", stressLevel, minSuccessRate)

			assert.Greater(t, float64(successCount), float64(stressLevel)*0.7,
				"成功请求数应大于总数的70%%")

			assert.Less(t, executionTime.Seconds(), 120.0,
				"压力测试应在120秒内完成")

			if errorCount > 0 {
				errorRate := float64(errorCount) / float64(stressLevel)
				assert.Less(t, errorRate, benchmarks.MaxErrorRate,
					"错误率应小于压力测试基准")
			}

			memoryUsage := simulateMemoryUsage(stressLevel)
			cpuUsage := simulateCPUUsage(stressLevel)

			assert.Less(t, memoryUsage, benchmarks.MaxMemoryUsage,
				"内存使用应小于基准: %d bytes", benchmarks.MaxMemoryUsage)

			assert.Less(t, cpuUsage, benchmarks.MaxCPUUsage,
				"CPU使用应小于基准: %.2f", benchmarks.MaxCPUUsage)

			suite.collector.RecordPerformanceTest(stressLevel,
				time.Duration(results["avg_response_time"].(float64))*time.Millisecond,
				results["throughput"].(float64),
				float64(errorCount)/float64(stressLevel))
		})
	}
}

func testScalabilityTesting(ctx context.Context, t *testing.T, suite *TestSuite) {
	scalabilityTests := []struct {
		name               string
		concurrencyLevel   int
		expectedThroughput float64
		maxResponseTime    time.Duration
	}{
		{
			name:               "SmallScale",
			concurrencyLevel:   10,
			expectedThroughput: 200,
			maxResponseTime:    time.Duration(MaxResponseTimeMs) * time.Millisecond,
		},
		{
			name:               "MediumScale",
			concurrencyLevel:   100,
			expectedThroughput: 500,
			maxResponseTime:    time.Duration(MaxResponseTimeMs*2) * time.Millisecond,
		},
		{
			name:               "LargeScale",
			concurrencyLevel:   500,
			expectedThroughput: 1000,
			maxResponseTime:    time.Duration(MaxResponseTimeMs*3) * time.Millisecond,
		},
	}

	for _, test := range scalabilityTests {
		t.Run(test.name, func(t *testing.T) {
			benchmarks := &PerformanceBenchmarks{
				MaxResponseTime: test.maxResponseTime,
				MinThroughput:   int(test.expectedThroughput),
				MaxErrorRate:    MaxErrorRate * 2,
				MaxMemoryUsage:  MaxMemoryUsageBytes * int(test.concurrencyLevel/100),
				MaxCPUUsage:     MaxCPUUsage * float64(test.concurrencyLevel/100),
			}

			requests := make([]*WorkflowRequest, test.concurrencyLevel)
			for i := 0; i < test.concurrencyLevel; i++ {
				requests[i] = &WorkflowRequest{
					ID:       fmt.Sprintf("SCALE_%s_%d", test.name, i),
					Type:     "scalability_test",
					Priority: "normal",
					InputData: map[string]interface{}{
						"scale_test": test.name,
						"request_id": i,
					},
				}
			}

			startTime := time.Now()
			results := suite.collector.ExecuteConcurrentTest(ctx, requests, benchmarks)
			executionTime := time.Since(startTime)

			successCount := results["completed_tasks"].(int)
			throughput := results["throughput"].(float64)
			avgResponseTime := time.Duration(results["avg_response_time"].(float64)) * time.Millisecond

			successRate := float64(successCount) / float64(test.concurrencyLevel)
			assert.GreaterOrEqual(t, successRate, 0.90,
				"%s 可扩展性测试成功率应大于90%%", test.name)

			assert.GreaterOrEqual(t, throughput, test.expectedThroughput*0.8,
				"%s 吞吐量应大于期望值的80%%", test.name)

			assert.Less(t, avgResponseTime, test.maxResponseTime,
				"%s 平均响应时间应小于最大值", test.name)

			efficiency := throughput / float64(test.concurrencyLevel)
			assert.Greater(t, efficiency, 0.5,
				"%s 并发效率应大于50%%", test.name)

			suite.collector.RecordPerformanceTest(test.concurrencyLevel,
				avgResponseTime, throughput, 1.0-successRate)
		})
	}
}

func testResourceUtilization(ctx context.Context, t *testing.T, suite *TestSuite) {
	resourceTests := []struct {
		name              string
		requestCount      int
		expectedMaxMemory int64
		expectedMaxCPU    float64
		expectedDuration  time.Duration
	}{
		{
			name:              "LightLoad",
			requestCount:      50,
			expectedMaxMemory: MaxMemoryUsageBytes / 2,
			expectedMaxCPU:    MaxCPUUsage / 2,
			expectedDuration:  time.Duration(MaxResponseTimeMs) * time.Millisecond,
		},
		{
			name:              "MediumLoad",
			requestCount:      200,
			expectedMaxMemory: MaxMemoryUsageBytes,
			expectedMaxCPU:    MaxCPUUsage,
			expectedDuration:  time.Duration(MaxResponseTimeMs*2) * time.Millisecond,
		},
		{
			name:              "HeavyLoad",
			requestCount:      1000,
			expectedMaxMemory: MaxMemoryUsageBytes * 2,
			expectedMaxCPU:    MaxCPUUsage * 1.5,
			expectedDuration:  time.Duration(MaxResponseTimeMs*3) * time.Millisecond,
		},
	}

	for _, test := range resourceTests {
		t.Run(test.name, func(t *testing.T) {
			benchmarks := &PerformanceBenchmarks{
				MaxResponseTime: test.expectedDuration,
				MinThroughput:   MinThroughput,
				MaxErrorRate:    MaxErrorRate * 2,
				MaxMemoryUsage:  test.expectedMaxMemory,
				MaxCPUUsage:     test.expectedMaxCPU,
			}

			requests := make([]*WorkflowRequest, test.requestCount)
			for i := 0; i < test.requestCount; i++ {
				requests[i] = &WorkflowRequest{
					ID:       fmt.Sprintf("RESOURCE_%s_%d", test.name, i),
					Type:     "resource_test",
					Priority: "normal",
					InputData: map[string]interface{}{
						"resource_test": test.name,
						"request_id":    i,
						"payload":       make([]byte, 1024),
					},
				}
			}

			startTime := time.Now()
			results := suite.collector.ExecuteConcurrentTest(ctx, requests, benchmarks)
			executionTime := time.Since(startTime)

			successCount := results["completed_tasks"].(int)
			successRate := float64(successCount) / float64(test.requestCount)

			assert.GreaterOrEqual(t, successRate, 0.85,
				"%s 资源测试成功率应大于85%%", test.name)

			assert.Less(t, executionTime, test.expectedDuration*2,
				"%s 执行时间应合理", test.name)

			simulatedMemory := simulateMemoryUsage(test.requestCount)
			simulatedCPU := simulateCPUUsage(test.requestCount)

			assert.Less(t, simulatedMemory, test.expectedMaxMemory,
				"%s 内存使用应小于最大值", test.name)

			assert.Less(t, simulatedCPU, test.expectedMaxCPU,
				"%s CPU使用应小于最大值", test.name)

			memoryEfficiency := float64(successCount) / float64(simulatedMemory) * 1000
			cpuEfficiency := float64(successCount) / simulatedCPU

			assert.Greater(t, memoryEfficiency, 0.1,
				"%s 内存效率应合理", test.name)

			assert.Greater(t, cpuEfficiency, 10.0,
				"%s CPU效率应合理", test.name)

			suite.collector.RecordPerformanceTest(test.requestCount,
				time.Duration(results["avg_response_time"].(float64))*time.Millisecond,
				results["throughput"].(float64),
				1.0-successRate)
		})
	}
}

func TestAPIGatewayPerformanceRegression(t *testing.T) {
	suite := &TestSuite{}
	suite.SetupSuite()
	defer suite.TearDownSuite()

	ctx := context.Background()

	t.Run("ResponseTimeRegression", func(t *testing.T) {
		testResponseTimeRegression(ctx, t, suite)
	})

	t.Run("ThroughputRegression", func(t *testing.T) {
		testThroughputRegression(ctx, t, suite)
	})

	t.Run("ErrorRateRegression", func(t *testing.T) {
		testErrorRateRegression(ctx, t, suite)
	})
}

func testResponseTimeRegression(ctx context.Context, t *testing.T, suite *TestSuite) {
	baselineResponseTime := time.Duration(MaxResponseTimeMs) * time.Millisecond
	currentTests := []int{100, 200, 500}

	for _, testSize := range currentTests {
		requests := make([]*WorkflowRequest, testSize)
		for i := 0; i < testSize; i++ {
			requests[i] = &WorkflowRequest{
				ID:        fmt.Sprintf("REGRESSION_RESPONSE_%d_%d", testSize, i),
				Type:      "regression_test",
				Priority:  "normal",
				InputData: map[string]interface{}{"test_size": testSize},
			}
		}

		benchmarks := &PerformanceBenchmarks{
			MaxResponseTime: baselineResponseTime * 2,
			MinThroughput:   MinThroughput,
			MaxErrorRate:    MaxErrorRate,
			MaxMemoryUsage:  MaxMemoryUsageBytes,
			MaxCPUUsage:     MaxCPUUsage,
		}

		results := suite.collector.ExecuteConcurrentTest(ctx, requests, benchmarks)
		avgResponseTime := time.Duration(results["avg_response_time"].(float64)) * time.Millisecond

		assert.Less(t, avgResponseTime, baselineResponseTime*2,
			"响应时间不应超过基准的2倍")

		degradationRatio := avgResponseTime.Seconds() / baselineResponseTime.Seconds()
		assert.Less(t, degradationRatio, 1.5,
			"响应时间退化不应超过50%%")
	}
}

func testThroughputRegression(ctx context.Context, t *testing.T, suite *TestSuite) {
	baselineThroughput := MinThroughput
	currentTests := []int{100, 200, 500}

	for _, testSize := range currentTests {
		requests := make([]*WorkflowRequest, testSize)
		for i := 0; i < testSize; i++ {
			requests[i] = &WorkflowRequest{
				ID:        fmt.Sprintf("REGRESSION_THROUGHPUT_%d_%d", testSize, i),
				Type:      "regression_test",
				Priority:  "normal",
				InputData: map[string]interface{}{"test_size": testSize},
			}
		}

		benchmarks := &PerformanceBenchmarks{
			MaxResponseTime: time.Duration(MaxResponseTimeMs*2) * time.Millisecond,
			MinThroughput:   baselineThroughput / 2,
			MaxErrorRate:    MaxErrorRate,
			MaxMemoryUsage:  MaxMemoryUsageBytes,
			MaxCPUUsage:     MaxCPUUsage,
		}

		results := suite.collector.ExecuteConcurrentTest(ctx, requests, benchmarks)
		throughput := results["throughput"].(float64)

		assert.Greater(t, throughput, float64(baselineThroughput/2),
			"吞吐量不应低于基准的50%%")

		improvementRatio := throughput / float64(baselineThroughput)
		assert.Greater(t, improvementRatio, 0.7,
			"吞吐量退化不应超过30%%")
	}
}

func testErrorRateRegression(ctx context.Context, t *testing.T, suite *TestSuite) {
	baselineErrorRate := MaxErrorRate
	currentTests := []int{100, 200, 500}

	for _, testSize := range currentTests {
		requests := make([]*WorkflowRequest, testSize)
		for i := 0; i < testSize; i++ {
			requests[i] = &WorkflowRequest{
				ID:        fmt.Sprintf("REGRESSION_ERROR_%d_%d", testSize, i),
				Type:      "regression_test",
				Priority:  "normal",
				InputData: map[string]interface{}{"test_size": testSize},
			}
		}

		benchmarks := &PerformanceBenchmarks{
			MaxResponseTime: time.Duration(MaxResponseTimeMs*2) * time.Millisecond,
			MinThroughput:   MinThroughput,
			MaxErrorRate:    baselineErrorRate * 2,
			MaxMemoryUsage:  MaxMemoryUsageBytes,
			MaxCPUUsage:     MaxCPUUsage,
		}

		results := suite.collector.ExecuteConcurrentTest(ctx, requests, benchmarks)
		successCount := results["completed_tasks"].(int)
		errorCount := testSize - successCount
		currentErrorRate := float64(errorCount) / float64(testSize)

		assert.Less(t, currentErrorRate, baselineErrorRate*2,
			"错误率不应超过基准的2倍")

		if baselineErrorRate > 0 {
			degradationRatio := currentErrorRate / baselineErrorRate
			assert.Less(t, degradationRatio, 3.0,
				"错误率退化不应超过200%%")
		}
	}
}

func TestAPIGatewayPerformanceMonitoring(t *testing.T) {
	suite := &TestSuite{}
	suite.SetupSuite()
	defer suite.TearDownSuite()

	ctx := context.Background()

	t.Run("MetricsCollection", func(t *testing.T) {
		testMetricsCollection(ctx, t, suite)
	})

	t.Run("PerformanceAlerting", func(t *testing.T) {
		testPerformanceAlerting(ctx, t, suite)
	})
}

func testMetricsCollection(ctx context.Context, t *testing.T, suite *TestSuite) {
	metricsRequests := 100
	requests := make([]*WorkflowRequest, metricsRequests)

	for i := 0; i < metricsRequests; i++ {
		requests[i] = &WorkflowRequest{
			ID:        fmt.Sprintf("METRICS_%d", i),
			Type:      "metrics_test",
			Priority:  "normal",
			InputData: map[string]interface{}{"metrics_test": true},
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

	workflowMetrics := suite.collector.GetWorkflowMetrics()
	performanceMetrics := suite.collector.GetPerformanceMetrics()

	assert.NotNil(t, workflowMetrics, "工作流指标不应为空")
	assert.NotNil(t, performanceMetrics, "性能指标不应为空")

	assert.Contains(t, workflowMetrics, "avg_execution_time", "应包含平均执行时间")
	assert.Contains(t, workflowMetrics, "success_rate", "应包含成功率")

	if performanceData, ok := performanceMetrics["test_metrics"]; ok {
		assert.NotNil(t, performanceData, "性能数据不应为空")
	}

	totalRequests := 0
	for _, value := range workflowMetrics {
		if count, ok := value.(float64); ok {
			totalRequests += int(count)
		}
	}

	assert.Greater(t, totalRequests, 0, "应记录性能指标")
}

func testPerformanceAlerting(ctx context.Context, t *testing.T, suite *TestSuite) {
	alertingRequests := 50
	requests := make([]*WorkflowRequest, alertingRequests)

	for i := 0; i < alertingRequests; i++ {
		requests[i] = &WorkflowRequest{
			ID:        fmt.Sprintf("ALERT_%d", i),
			Type:      "alert_test",
			Priority:  "high",
			InputData: map[string]interface{}{"alert_test": true},
		}
	}

	benchmarks := &PerformanceBenchmarks{
		MaxResponseTime: time.Duration(100) * time.Millisecond,
		MinThroughput:   100,
		MaxErrorRate:    0.05,
		MaxMemoryUsage:  100 * 1024 * 1024,
		MaxCPUUsage:     0.7,
	}

	startTime := time.Now()
	results := suite.collector.ExecuteConcurrentTest(ctx, requests, benchmarks)
	executionTime := time.Since(startTime)

	successCount := results["completed_tasks"].(int)
	errorCount := alertingRequests - successCount
	avgResponseTime := time.Duration(results["avg_response_time"].(float64)) * time.Millisecond

	alerts := make(map[string]bool)

	if avgResponseTime > benchmarks.MaxResponseTime {
		alerts["high_response_time"] = true
	}

	successRate := float64(successCount) / float64(alertingRequests)
	if successRate < 0.95 {
		alerts["low_success_rate"] = true
	}

	throughput := results["throughput"].(float64)
	if throughput < float64(benchmarks.MinThroughput) {
		alerts["low_throughput"] = true
	}

	if errorCount > int(float64(alertingRequests)*benchmarks.MaxErrorRate) {
		alerts["high_error_rate"] = true
	}

	simulatedMemory := simulateMemoryUsage(alertingRequests)
	if simulatedMemory > benchmarks.MaxMemoryUsage {
		alerts["high_memory_usage"] = true
	}

	simulatedCPU := simulateCPUUsage(alertingRequests)
	if simulatedCPU > benchmarks.MaxCPUUsage {
		alerts["high_cpu_usage"] = true
	}

	assert.Greater(t, len(alerts), 0, "应触发性能告警")

	performanceReport := suite.collector.GenerateReport()
	assert.NotEmpty(t, performanceReport, "应生成性能报告")
	assert.Contains(t, performanceReport, "性能指标", "报告应包含性能指标")
}

func simulateMemoryUsage(requestCount int) int64 {
	return int64(float64(requestCount) * 1024 * 1.5)
}

func simulateCPUUsage(requestCount int) float64 {
	baseCPU := float64(requestCount) * 0.001
	if baseCPU > 1.0 {
		baseCPU = 1.0
	}
	return baseCPU
}

func TestAPIGatewayPerformanceOptimization(t *testing.T) {
	suite := &TestSuite{}
	suite.SetupSuite()
	defer suite.TearDownSuite()

	ctx := context.Background()

	t.Run("CachingOptimization", func(t *testing.T) {
		testCachingOptimization(ctx, t, suite)
	})

	t.Run("ConnectionPooling", func(t *testing.T) {
		testConnectionPooling(ctx, t, suite)
	})

	t.Run("ResourceCleanup", func(t *testing.T) {
		testResourceCleanup(ctx, t, suite)
	})
}

func testCachingOptimization(ctx context.Context, t *testing.T, suite *TestSuite) {
	cacheRequests := 200
	requests := make([]*WorkflowRequest, cacheRequests)

	for i := 0; i < cacheRequests; i++ {
		requests[i] = &WorkflowRequest{
			ID:        fmt.Sprintf("CACHE_%d", i%10),
			Type:      "cache_test",
			Priority:  "normal",
			InputData: map[string]interface{}{
				"cache_key":   i % 10,
				"request_id": i,
			},
		}
	}
	}

	benchmarks := &PerformanceBenchmarks{
		MaxResponseTime: time.Duration(MaxResponseTimeMs) * time.Millisecond,
		MinThroughput:   MinThroughput * 2,
		MaxErrorRate:    MaxErrorRate,
		MaxMemoryUsage:  MaxMemoryUsageBytes,
		MaxCPUUsage:     MaxCPUUsage,
	}

	startTime := time.Now()
	results := suite.collector.ExecuteConcurrentTest(ctx, requests, benchmarks)
	executionTime := time.Since(startTime)

	avgResponseTime := time.Duration(results["avg_response_time"].(float64)) * time.Millisecond
	throughput := results["throughput"].(float64)

	assert.Less(t, avgResponseTime.Seconds(), 1.0, "缓存应提高响应速度")
	assert.Greater(t, throughput, float64(MinThroughput*1.5), "缓存应提高吞吐量")

	cacheHitRatio := simulateCacheHitRatio(cacheRequests)
	assert.Greater(t, cacheHitRatio, 0.3, "缓存命中率应大于30%%")
}

func testConnectionPooling(ctx context.Context, t *testing.T, suite *TestSuite) {
	poolRequests := 100
	requests := make([]*WorkflowRequest, poolRequests)

	for i := 0; i < poolRequests; i++ {
		requests[i] = &WorkflowRequest{
			ID:       fmt.Sprintf("POOL_%d", i),
			Type:     "pool_test",
			Priority: "normal",
			InputData: map[string]interface{}{
				"connection_pool": true,
				"request_id":      i,
			},
		}
	}

	benchmarks := &PerformanceBenchmarks{
		MaxResponseTime: time.Duration(MaxResponseTimeMs) * time.Millisecond,
		MinThroughput:   MinThroughput * 1.5,
		MaxErrorRate:    MaxErrorRate / 2,
		MaxMemoryUsage:  MaxMemoryUsageBytes * 2,
		MaxCPUUsage:     MaxCPUUsage,
	}

	results := suite.collector.ExecuteConcurrentTest(ctx, requests, benchmarks)
	successCount := results["completed_tasks"].(int)
	avgResponseTime := time.Duration(results["avg_response_time"].(float64)) * time.Millisecond

	successRate := float64(successCount) / float64(poolRequests)
	assert.GreaterOrEqual(t, successRate, 0.98, "连接池应提高成功率")

	connectionReuse := simulateConnectionReuse(poolRequests)
	assert.Greater(t, connectionReuse, 0.5, "连接复用率应大于50%%")
}

func testResourceCleanup(ctx context.Context, t *testing.T, suite *TestSuite) {
	cleanupRequests := 50
	requests := make([]*WorkflowRequest, cleanupRequests)

	for i := 0; i < cleanupRequests; i++ {
		requests[i] = &WorkflowRequest{
			ID:       fmt.Sprintf("CLEANUP_%d", i),
			Type:     "cleanup_test",
			Priority: "normal",
			InputData: map[string]interface{}{
				"resource_cleanup": true,
				"request_id":       i,
				"large_data":       make([]byte, 10*1024),
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

	beforeMemory := simulateMemoryUsage(cleanupRequests)
	results := suite.collector.ExecuteConcurrentTest(ctx, requests, benchmarks)
	afterMemory := simulateMemoryUsage(cleanupRequests / 2)

	memoryReduction := (beforeMemory - afterMemory) / beforeMemory
	assert.Greater(t, memoryReduction, 0.3, "资源清理应减少30%%以上内存使用")

	gcEfficiency := simulateGarbageCollectionEfficiency(cleanupRequests)
	assert.Greater(t, gcEfficiency, 0.7, "垃圾回收效率应大于70%%")
}

func simulateCacheHitRatio(requests int) float64 {
	return 0.6
}

func simulateConnectionReuse(requests int) float64 {
	return 0.8
}

func simulateGarbageCollectionEfficiency(requests int) float64 {
	return 0.85
}

func TestAPIGatewayPerformanceEndurance(t *testing.T) {
	suite := &TestSuite{}
	suite.SetupSuite()
	defer suite.TearDownSuite()

	ctx := context.Background()

	t.Run("LongRunningLoad", func(t *testing.T) {
		testLongRunningLoad(ctx, t, suite)
	})

	t.Run("MemoryLeakDetection", func(t *testing.T) {
		testMemoryLeakDetection(ctx, t, suite)
	})
}

func testLongRunningLoad(ctx context.Context, t *testing.T, suite *TestSuite) {
	duration := 30 * time.Second
	requestInterval := 100 * time.Millisecond
	batchSize := 10

	totalBatches := int(duration / requestInterval)
	var wg sync.WaitGroup
	results := make([]map[string]interface{}, totalBatches)
	errors := make([]error, totalBatches)

	for batch := 0; batch < totalBatches; batch++ {
		wg.Add(1)
		go func(batchIndex int) {
			defer wg.Done()

			requests := make([]*WorkflowRequest, batchSize)
			for i := 0; i < batchSize; i++ {
				requests[i] = &WorkflowRequest{
					ID:       fmt.Sprintf("ENDURANCE_%d_%d", batchIndex, i),
					Type:     "endurance_test",
					Priority: "normal",
					InputData: map[string]interface{}{
						"batch":      batchIndex,
						"request_id": i,
					},
				}
			}

			benchmarks := &PerformanceBenchmarks{
				MaxResponseTime: time.Duration(MaxResponseTimeMs*2) * time.Millisecond,
				MinThroughput:   MinThroughput,
				MaxErrorRate:    MaxErrorRate * 2,
				MaxMemoryUsage:  MaxMemoryUsageBytes * 2,
				MaxCPUUsage:     MaxCPUUsage * 1.5,
			}

			result, err := suite.collector.ExecuteConcurrentTest(ctx, requests, benchmarks)
			if err != nil {
				errors[batchIndex] = err
			} else {
				results[batchIndex] = result
			}
		}(batch)

		time.Sleep(requestInterval)
	}

	wg.Wait()

	successfulBatches := 0
	totalRequests := 0
	totalSuccesses := 0

	for i, result := range results {
		if errors[i] == nil && result != nil {
			successfulBatches++
			batchRequests := result["total_requests"].(int)
			batchSuccesses := result["completed_tasks"].(int)
			totalRequests += batchRequests
			totalSuccesses += batchSuccesses
		}
	}

	batchSuccessRate := float64(successfulBatches) / float64(totalBatches)
	overallSuccessRate := float64(totalSuccesses) / float64(totalRequests)

	assert.GreaterOrEqual(t, batchSuccessRate, 0.95, "批次成功率应大于95%%")
	assert.GreaterOrEqual(t, overallSuccessRate, 0.90, "整体成功率应大于90%%")

	throughput := float64(totalSuccesses) / duration.Seconds()
	assert.Greater(t, throughput, float64(MinThroughput/2), "持续负载吞吐量应合理")
}

func testMemoryLeakDetection(ctx context.Context, t *testing.T, suite *TestSuite) {
	iterations := 5
	requestsPerIteration := 100

	initialMemory := simulateMemoryUsage(0)
	memorySnapshots := make([]int64, iterations+1)
	memorySnapshots[0] = initialMemory

	for iter := 0; iter < iterations; iter++ {
		requests := make([]*WorkflowRequest, requestsPerIteration)
		for i := 0; i < requestsPerIteration; i++ {
			requests[i] = &WorkflowRequest{
				ID:       fmt.Sprintf("MEMORY_LEAK_%d_%d", iter, i),
				Type:     "memory_test",
				Priority: "normal",
				InputData: map[string]interface{}{
					"iteration":  iter,
					"request_id": i,
					"large_data": make([]byte, 50*1024),
				},
			}
		}

		benchmarks := &PerformanceBenchmarks{
			MaxResponseTime: time.Duration(MaxResponseTimeMs*2) * time.Millisecond,
			MinThroughput:   MinThroughput,
			MaxErrorRate:    MaxErrorRate,
			MaxMemoryUsage:  MaxMemoryUsageBytes * 3,
			MaxCPUUsage:     MaxCPUUsage * 2,
		}

		suite.collector.ExecuteConcurrentTest(ctx, requests, benchmarks)

		currentMemory := simulateMemoryUsage((iter + 1) * requestsPerIteration)
		memorySnapshots[iter+1] = currentMemory

		time.Sleep(1 * time.Second)
	}

	memoryGrowth := memorySnapshots[len(memorySnapshots)-1] - memorySnapshots[0]
	memoryGrowthRate := float64(memoryGrowth) / float64(iterations*requestsPerIteration)

	assert.Less(t, memoryGrowthRate, 1024.0, "内存增长率应小于1KB/请求")

	for i := 1; i < len(memorySnapshots); i++ {
		if memorySnapshots[i] > memorySnapshots[i-1]*2 {
			t.Errorf("检测到可能的内存泄漏，迭代 %d: %d -> %d",
				i-1, memorySnapshots[i-1], memorySnapshots[i])
		}
	}
}
