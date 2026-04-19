package integration

import (
	"context"
	"fmt"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestAtomicToolSystem(t *testing.T) {
	suite := &TestSuite{}
	suite.SetupSuite()
	defer suite.TearDownSuite()

	ctx := context.Background()

	t.Run("ToolRegistration", func(t *testing.T) {
		testToolRegistration(ctx, t, suite)
	})

	t.Run("ToolDiscovery", func(t *testing.T) {
		testToolDiscovery(ctx, t, suite)
	})

	t.Run("ToolInvocation", func(t *testing.T) {
		testToolInvocation(ctx, t, suite)
	})

	t.Run("ToolParameters", func(t *testing.T) {
		testToolParameters(ctx, t, suite)
	})

	t.Run("ToolErrorHandling", func(t *testing.T) {
		testToolErrorHandling(ctx, t, suite)
	})
}

func testToolRegistration(ctx context.Context, t *testing.T, suite *TestSuite) {
	testTools := []*AtomicTool{
		{
			Name:        "text-analyzer",
			Description: "文本分析工具",
			Version:     "1.0.0",
			Category:    "nlp",
			Parameters: []Parameter{
				{Name: "text", Type: "string", Required: true},
				{Name: "language", Type: "string", Required: false, Default: "zh"},
			},
			Handler: func(ctx context.Context, params map[string]interface{}) (interface{}, error) {
				text := params["text"].(string)
				return map[string]interface{}{
					"word_count": len(text),
					"char_count": len([]rune(text)),
					"language":   "zh",
					"sentiment":  "positive",
				}, nil
			},
		},
		{
			Name:        "patent-searcher",
			Description: "专利搜索工具",
			Version:     "1.0.0",
			Category:    "patent",
			Parameters: []Parameter{
				{Name: "keywords", Type: "array", Required: true},
				{Name: "limit", Type: "integer", Required: false, Default: 10},
			},
			Handler: func(ctx context.Context, params map[string]interface{}) (interface{}, error) {
				keywords := params["keywords"].([]interface{})
				limit := params["limit"].(int)

				results := make([]map[string]interface{}, 0, limit)
				for i := 0; i < limit && i < 5; i++ {
					results = append(results, map[string]interface{}{
						"id":        fmt.Sprintf("PAT_%03d", i+1),
						"title":     fmt.Sprintf("相关专利%d", i+1),
						"abstract":  fmt.Sprintf("与%v相关的技术方案...", keywords),
						"relevance": 0.9 - float64(i)*0.1,
					})
				}
				return results, nil
			},
		},
	}

	for _, tool := range testTools {
		err := suite.orchestrator.RegisterTool(ctx, tool)
		require.NoError(t, err, "工具 %s 注册失败", tool.Name)
	}

	registeredTools, err := suite.orchestrator.ListTools(ctx)
	require.NoError(t, err, "获取工具列表失败")

	assert.Len(t, registeredTools, len(testTools), "注册的工具数量应正确")

	for _, expectedTool := range testTools {
		found := false
		for _, registeredTool := range registeredTools {
			if registeredTool.Name == expectedTool.Name {
				found = true
				assert.Equal(t, expectedTool.Description, registeredTool.Description, "工具描述应匹配")
				assert.Equal(t, expectedTool.Version, registeredTool.Version, "工具版本应匹配")
				assert.Equal(t, expectedTool.Category, registeredTool.Category, "工具类别应匹配")
				assert.Len(t, registeredTool.Parameters, len(expectedTool.Parameters), "参数数量应匹配")
				break
			}
		}
		assert.True(t, found, "工具 %s 应在注册列表中", expectedTool.Name)
	}
}

func testToolDiscovery(ctx context.Context, t *testing.T, suite *TestSuite) {
	discoveryTools := []*AtomicTool{
		{
			Name:        "data-processor",
			Description: "数据处理工具",
			Version:     "2.1.0",
			Category:    "data",
			Parameters: []Parameter{
				{Name: "data", Type: "object", Required: true},
				{Name: "operation", Type: "string", Required: true},
			},
			Handler: func(ctx context.Context, params map[string]interface{}) (interface{}, error) {
				operation := params["operation"].(string)
				return map[string]interface{}{
					"operation": operation,
					"status":    "completed",
					"timestamp": time.Now().Unix(),
				}, nil
			},
		},
		{
			Name:        "api-caller",
			Description: "API调用工具",
			Version:     "1.5.0",
			Category:    "network",
			Parameters: []Parameter{
				{Name: "url", Type: "string", Required: true},
				{Name: "method", Type: "string", Required: true},
				{Name: "headers", Type: "object", Required: false},
			},
			Handler: func(ctx context.Context, params map[string]interface{}) (interface{}, error) {
				url := params["url"].(string)
				method := params["method"].(string)
				return map[string]interface{}{
					"url":    url,
					"method": method,
					"status": "success",
				}, nil
			},
		},
	}

	for _, tool := range discoveryTools {
		err := suite.orchestrator.RegisterTool(ctx, tool)
		require.NoError(t, err, "工具 %s 注册失败", tool.Name)
	}

	allTools, err := suite.orchestrator.ListTools(ctx)
	require.NoError(t, err, "获取所有工具失败")

	categories := make(map[string][]*AtomicTool)
	for _, tool := range allTools {
		categories[tool.Category] = append(categories[tool.Category], tool)
	}

	assert.Contains(t, categories, "data", "应包含数据处理类别")
	assert.Contains(t, categories, "network", "应包含网络类别")
	assert.Greater(t, len(categories["data"]), 0, "数据处理类别应有工具")
	assert.Greater(t, len(categories["network"]), 0, "网络类别应有工具")

	for category, tools := range categories {
		for _, tool := range tools {
			assert.Equal(t, category, tool.Category, "工具类别应正确")
			assert.NotEmpty(t, tool.Description, "工具描述不应为空")
			assert.NotEmpty(t, tool.Version, "工具版本不应为空")
		}
	}
}

func testToolInvocation(ctx context.Context, t *testing.T, suite *TestSuite) {
	invokeTool := &AtomicTool{
		Name:        "calculator",
		Description: "数学计算工具",
		Version:     "1.0.0",
		Category:    "math",
		Parameters: []Parameter{
			{Name: "operation", Type: "string", Required: true},
			{Name: "operand1", Type: "number", Required: true},
			{Name: "operand2", Type: "number", Required: true},
		},
		Handler: func(ctx context.Context, params map[string]interface{}) (interface{}, error) {
			operation := params["operation"].(string)
			operand1 := params["operand1"].(float64)
			operand2 := params["operand2"].(float64)

			var result float64
			switch operation {
			case "add":
				result = operand1 + operand2
			case "subtract":
				result = operand1 - operand2
			case "multiply":
				result = operand1 * operand2
			case "divide":
				if operand2 == 0 {
					return nil, fmt.Errorf("除零错误")
				}
				result = operand1 / operand2
			default:
				return nil, fmt.Errorf("不支持的操作: %s", operation)
			}

			return map[string]interface{}{
				"operation": operation,
				"operand1":  operand1,
				"operand2":  operand2,
				"result":    result,
			}, nil
		},
	}

	err := suite.orchestrator.RegisterTool(ctx, invokeTool)
	require.NoError(t, err, "计算工具注册失败")

	testCases := []struct {
		name     string
		params   map[string]interface{}
		expected map[string]interface{}
		hasError bool
	}{
		{
			name: "加法测试",
			params: map[string]interface{}{
				"operation": "add",
				"operand1":  10.0,
				"operand2":  5.0,
			},
			expected: map[string]interface{}{
				"operation": "add",
				"operand1":  10.0,
				"operand2":  5.0,
				"result":    15.0,
			},
			hasError: false,
		},
		{
			name: "减法测试",
			params: map[string]interface{}{
				"operation": "subtract",
				"operand1":  10.0,
				"operand2":  3.0,
			},
			expected: map[string]interface{}{
				"operation": "subtract",
				"operand1":  10.0,
				"operand2":  3.0,
				"result":    7.0,
			},
			hasError: false,
		},
		{
			name: "乘法测试",
			params: map[string]interface{}{
				"operation": "multiply",
				"operand1":  4.0,
				"operand2":  6.0,
			},
			expected: map[string]interface{}{
				"operation": "multiply",
				"operand1":  4.0,
				"operand2":  6.0,
				"result":    24.0,
			},
			hasError: false,
		},
		{
			name: "除法测试",
			params: map[string]interface{}{
				"operation": "divide",
				"operand1":  20.0,
				"operand2":  4.0,
			},
			expected: map[string]interface{}{
				"operation": "divide",
				"operand1":  20.0,
				"operand2":  4.0,
				"result":    5.0,
			},
			hasError: false,
		},
		{
			name: "除零错误",
			params: map[string]interface{}{
				"operation": "divide",
				"operand1":  10.0,
				"operand2":  0.0,
			},
			expected: nil,
			hasError: true,
		},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			result, err := suite.orchestrator.CallTool(ctx, invokeTool.Name, tc.params)

			if tc.hasError {
				assert.Error(t, err, "应该返回错误")
				assert.Nil(t, result, "错误时结果应为空")
			} else {
				assert.NoError(t, err, "工具调用不应失败")
				assert.NotNil(t, result, "结果不应为空")

				resultMap, ok := result.(map[string]interface{})
				assert.True(t, ok, "结果应为map类型")

				for key, expectedValue := range tc.expected {
					actualValue, exists := resultMap[key]
					assert.True(t, exists, "结果应包含键: %s", key)
					assert.Equal(t, expectedValue, actualValue, "键 %s 的值应匹配", key)
				}
			}
		})
	}
}

func testToolParameters(ctx context.Context, t *testing.T, suite *TestSuite) {
	parameterTool := &AtomicTool{
		Name:        "parameter-validator",
		Description: "参数验证工具",
		Version:     "1.0.0",
		Category:    "validation",
		Parameters: []Parameter{
			{Name: "required_string", Type: "string", Required: true},
			{Name: "optional_string", Type: "string", Required: false, Default: "default_value"},
			{Name: "required_number", Type: "number", Required: true},
			{Name: "optional_number", Type: "number", Required: false, Default: 42},
			{Name: "required_array", Type: "array", Required: true},
			{Name: "optional_object", Type: "object", Required: false},
		},
		Handler: func(ctx context.Context, params map[string]interface{}) (interface{}, error) {
			result := make(map[string]interface{})
			for key, value := range params {
				result[key] = value
			}
			result["validation_status"] = "passed"
			return result, nil
		},
	}

	err := suite.orchestrator.RegisterTool(ctx, parameterTool)
	require.NoError(t, err, "参数验证工具注册失败")

	testCases := []struct {
		name     string
		params   map[string]interface{}
		valid    bool
		expected map[string]interface{}
	}{
		{
			name: "完整必需参数",
			params: map[string]interface{}{
				"required_string": "test_string",
				"required_number": 123.45,
				"required_array":  []interface{}{1, 2, 3},
			},
			valid: true,
			expected: map[string]interface{}{
				"required_string":   "test_string",
				"required_number":   123.45,
				"required_array":    []interface{}{1, 2, 3},
				"optional_string":   "default_value",
				"optional_number":   42.0,
				"validation_status": "passed",
			},
		},
		{
			name: "包含可选参数",
			params: map[string]interface{}{
				"required_string": "test_string",
				"required_number": 123.45,
				"required_array":  []interface{}{1, 2, 3},
				"optional_string": "custom_value",
				"optional_number": 100,
				"optional_object": map[string]interface{}{"key": "value"},
			},
			valid: true,
			expected: map[string]interface{}{
				"required_string":   "test_string",
				"required_number":   123.45,
				"required_array":    []interface{}{1, 2, 3},
				"optional_string":   "custom_value",
				"optional_number":   100.0,
				"optional_object":   map[string]interface{}{"key": "value"},
				"validation_status": "passed",
			},
		},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			result, err := suite.orchestrator.CallTool(ctx, parameterTool.Name, tc.params)

			if tc.valid {
				assert.NoError(t, err, "有效参数不应返回错误")
				assert.NotNil(t, result, "结果不应为空")

				resultMap, ok := result.(map[string]interface{})
				assert.True(t, ok, "结果应为map类型")

				for key, expectedValue := range tc.expected {
					actualValue, exists := resultMap[key]
					assert.True(t, exists, "结果应包含键: %s", key)
					assert.Equal(t, expectedValue, actualValue, "键 %s 的值应匹配", key)
				}
			} else {
				assert.Error(t, err, "无效参数应返回错误")
			}
		})
	}
}

func testToolErrorHandling(ctx context.Context, t *testing.T, suite *TestSuite) {
	errorTool := &AtomicTool{
		Name:        "error-generator",
		Description: "错误生成工具",
		Version:     "1.0.0",
		Category:    "testing",
		Parameters: []Parameter{
			{Name: "error_type", Type: "string", Required: true},
		},
		Handler: func(ctx context.Context, params map[string]interface{}) (interface{}, error) {
			errorType := params["error_type"].(string)
			switch errorType {
			case "panic":
				panic("故意触发的panic")
			case "error":
				return nil, fmt.Errorf("故意生成的错误")
			case "timeout":
				time.Sleep(5 * time.Second)
				return map[string]interface{}{"status": "timeout"}, nil
			default:
				return map[string]interface{}{"status": "success"}, nil
			}
		},
	}

	err := suite.orchestrator.RegisterTool(ctx, errorTool)
	require.NoError(t, err, "错误生成工具注册失败")

	testCases := []struct {
		name        string
		params      map[string]interface{}
		expectError bool
		expectPanic bool
	}{
		{
			name: "正常执行",
			params: map[string]interface{}{
				"error_type": "normal",
			},
			expectError: false,
			expectPanic: false,
		},
		{
			name: "返回错误",
			params: map[string]interface{}{
				"error_type": "error",
			},
			expectError: true,
			expectPanic: false,
		},
		{
			name: "超时执行",
			params: map[string]interface{}{
				"error_type": "timeout",
			},
			expectError: false,
			expectPanic: false,
		},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			if tc.expectPanic {
				assert.Panics(t, func() {
					suite.orchestrator.CallTool(ctx, errorTool.Name, tc.params)
				}, "应该触发panic")
			} else {
				result, err := suite.orchestrator.CallTool(ctx, errorTool.Name, tc.params)

				if tc.expectError {
					assert.Error(t, err, "应该返回错误")
					assert.Nil(t, result, "错误时结果应为空")
				} else {
					assert.NoError(t, err, "正常执行不应返回错误")
					assert.NotNil(t, result, "正常执行结果不应为空")
				}
			}
		})
	}
}

func TestAtomicToolPerformance(t *testing.T) {
	suite := &TestSuite{}
	suite.SetupSuite()
	defer suite.TearDownSuite()

	ctx := context.Background()

	t.Run("ConcurrentToolCalls", func(t *testing.T) {
		testConcurrentToolCalls(ctx, t, suite)
	})

	t.Run("ToolCallLatency", func(t *testing.T) {
		testToolCallLatency(ctx, t, suite)
	})
}

func testConcurrentToolCalls(ctx context.Context, t *testing.T, suite *TestSuite) {
	concurrentTool := &AtomicTool{
		Name:        "concurrent-processor",
		Description: "并发处理工具",
		Version:     "1.0.0",
		Category:    "performance",
		Parameters: []Parameter{
			{Name: "data_size", Type: "integer", Required: true},
		},
		Handler: func(ctx context.Context, params map[string]interface{}) (interface{}, error) {
			dataSize := params["data_size"].(int)
			time.Sleep(time.Duration(dataSize) * time.Millisecond)
			return map[string]interface{}{
				"processed_size": dataSize,
				"status":         "completed",
			}, nil
		},
	}

	err := suite.orchestrator.RegisterTool(ctx, concurrentTool)
	require.NoError(t, err, "并发处理工具注册失败")

	concurrencyLevel := 10
	results := make([]interface{}, concurrencyLevel)
	errors := make([]error, concurrencyLevel)
	startTime := time.Now()

	for i := 0; i < concurrencyLevel; i++ {
		params := map[string]interface{}{
			"data_size": 50 + i*10,
		}
		results[i], errors[i] = suite.orchestrator.CallTool(ctx, concurrentTool.Name, params)
	}

	totalTime := time.Since(startTime)

	successCount := 0
	for i := range results {
		if errors[i] == nil && results[i] != nil {
			successCount++
		}
	}

	successRate := float64(successCount) / float64(concurrencyLevel)
	avgResponseTime := totalTime / time.Duration(concurrencyLevel)

	assert.GreaterOrEqual(t, successRate, 0.9, "并发成功率应大于90%")
	assert.Less(t, avgResponseTime.Seconds(), 1.0, "平均响应时间应小于1秒")

	for i, result := range results {
		if errors[i] == nil && result != nil {
			resultMap, ok := result.(map[string]interface{})
			assert.True(t, ok, "结果应为map类型")
			assert.Equal(t, "completed", resultMap["status"], "状态应为完成")
		}
	}
}

func testToolCallLatency(ctx context.Context, t *testing.T, suite *TestSuite) {
	latencyTool := &AtomicTool{
		Name:        "latency-measurer",
		Description: "延迟测量工具",
		Version:     "1.0.0",
		Category:    "performance",
		Parameters: []Parameter{
			{Name: "processing_time", Type: "integer", Required: true},
		},
		Handler: func(ctx context.Context, params map[string]interface{}) (interface{}, error) {
			processingTime := params["processing_time"].(int)
			time.Sleep(time.Duration(processingTime) * time.Millisecond)
			return map[string]interface{}{
				"processing_time": processingTime,
				"actual_time":     time.Now().UnixNano(),
			}, nil
		},
	}

	err := suite.orchestrator.RegisterTool(ctx, latencyTool)
	require.NoError(t, err, "延迟测量工具注册失败")

	testTimes := []int{10, 50, 100, 200, 500}
	latencies := make([]time.Duration, len(testTimes))

	for i, testTime := range testTimes {
		params := map[string]interface{}{
			"processing_time": testTime,
		}

		startTime := time.Now()
		_, err := suite.orchestrator.CallTool(ctx, latencyTool.Name, params)
		latency := time.Since(startTime)

		assert.NoError(t, err, "工具调用不应失败")
		latencies[i] = latency

		assert.Greater(t, latency.Milliseconds(), int64(testTime),
			"延迟应大于处理时间: %dms", testTime)
		assert.Less(t, latency.Milliseconds(), int64(testTime+100),
			"延迟不应过大: %dms", testTime)
	}

	avgLatency := time.Duration(0)
	for _, latency := range latencies {
		avgLatency += latency
	}
	avgLatency /= time.Duration(len(latencies))

	assert.Less(t, avgLatency.Milliseconds(), int64(300), "平均延迟应小于300ms")
}

func TestAtomicToolSystemIntegration(t *testing.T) {
	suite := &TestSuite{}
	suite.SetupSuite()
	defer suite.TearDownSuite()

	ctx := context.Background()

	t.Run("ToolWorkflowIntegration", func(t *testing.T) {
		testToolWorkflowIntegration(ctx, t, suite)
	})

	t.Run("ToolChaining", func(t *testing.T) {
		testToolChaining(ctx, t, suite)
	})
}

func testToolWorkflowIntegration(ctx context.Context, t *testing.T, suite *TestSuite) {
	workflowTools := []*AtomicTool{
		{
			Name:        "data-ingestion",
			Description: "数据摄入工具",
			Version:     "1.0.0",
			Category:    "workflow",
			Parameters: []Parameter{
				{Name: "source", Type: "string", Required: true},
			},
			Handler: func(ctx context.Context, params map[string]interface{}) (interface{}, error) {
				return map[string]interface{}{
					"data_id": fmt.Sprintf("DATA_%d", time.Now().Unix()),
					"source":  params["source"],
					"records": 100,
					"status":  "ingested",
				}, nil
			},
		},
		{
			Name:        "data-transformation",
			Description: "数据转换工具",
			Version:     "1.0.0",
			Category:    "workflow",
			Parameters: []Parameter{
				{Name: "data_id", Type: "string", Required: true},
				{Name: "transformation", Type: "string", Required: true},
			},
			Handler: func(ctx context.Context, params map[string]interface{}) (interface{}, error) {
				return map[string]interface{}{
					"data_id":             params["data_id"],
					"transformation":      params["transformation"],
					"transformed_records": 95,
					"status":              "transformed",
				}, nil
			},
		},
		{
			Name:        "data-output",
			Description: "数据输出工具",
			Version:     "1.0.0",
			Category:    "workflow",
			Parameters: []Parameter{
				{Name: "data_id", Type: "string", Required: true},
				{Name: "destination", Type: "string", Required: true},
			},
			Handler: func(ctx context.Context, params map[string]interface{}) (interface{}, error) {
				return map[string]interface{}{
					"data_id":        params["data_id"],
					"destination":    params["destination"],
					"output_records": 90,
					"status":         "outputted",
				}, nil
			},
		},
	}

	for _, tool := range workflowTools {
		err := suite.orchestrator.RegisterTool(ctx, tool)
		require.NoError(t, err, "工作流工具 %s 注册失败", tool.Name)
	}

	ingestionResult, err := suite.orchestrator.CallTool(ctx, "data-ingestion", map[string]interface{}{
		"source": "patent_database",
	})
	require.NoError(t, err, "数据摄入失败")
	require.NotNil(t, ingestionResult, "摄入结果为空")

	ingestionMap := ingestionResult.(map[string]interface{})
	dataID := ingestionMap["data_id"].(string)

	transformResult, err := suite.orchestrator.CallTool(ctx, "data-transformation", map[string]interface{}{
		"data_id":        dataID,
		"transformation": "patent_format",
	})
	require.NoError(t, err, "数据转换失败")
	require.NotNil(t, transformResult, "转换结果为空")

	outputResult, err := suite.orchestrator.CallTool(ctx, "data-output", map[string]interface{}{
		"data_id":     dataID,
		"destination": "output_storage",
	})
	require.NoError(t, err, "数据输出失败")
	require.NotNil(t, outputResult, "输出结果为空")

	outputMap := outputResult.(map[string]interface{})
	assert.Equal(t, dataID, outputMap["data_id"], "数据ID应一致")
	assert.Equal(t, "outputted", outputMap["status"], "输出状态应正确")
}

func testToolChaining(ctx context.Context, t *testing.T, suite *TestSuite) {
	chainingTools := []*AtomicTool{
		{
			Name:        "text-extractor",
			Description: "文本提取工具",
			Version:     "1.0.0",
			Category:    "chaining",
			Parameters: []Parameter{
				{Name: "document", Type: "string", Required: true},
			},
			Handler: func(ctx context.Context, params map[string]interface{}) (interface{}, error) {
				document := params["document"].(string)
				return map[string]interface{}{
					"extracted_text":  "这是提取的文本内容",
					"word_count":      len(document),
					"paragraph_count": 3,
				}, nil
			},
		},
		{
			Name:        "text-analyzer",
			Description: "文本分析工具",
			Version:     "1.0.0",
			Category:    "chaining",
			Parameters: []Parameter{
				{Name: "text", Type: "string", Required: true},
				{Name: "analysis_type", Type: "string", Required: true},
			},
			Handler: func(ctx context.Context, params map[string]interface{}) (interface{}, error) {
				text := params["text"].(string)
				analysisType := params["analysis_type"].(string)
				return map[string]interface{}{
					"text":          text,
					"analysis_type": analysisType,
					"sentiment":     "positive",
					"keywords":      []string{"技术", "创新", "专利"},
					"confidence":    0.85,
				}, nil
			},
		},
	}

	for _, tool := range chainingTools {
		err := suite.orchestrator.RegisterTool(ctx, tool)
		require.NoError(t, err, "链式工具 %s 注册失败", tool.Name)
	}

	extractResult, err := suite.orchestrator.CallTool(ctx, "text-extractor", map[string]interface{}{
		"document": "这是一份包含技术内容的专利文档，描述了创新的算法和技术实现方案。",
	})
	require.NoError(t, err, "文本提取失败")
	require.NotNil(t, extractResult, "提取结果为空")

	extractMap := extractResult.(map[string]interface{})
	extractedText := extractMap["extracted_text"].(string)

	analyzeResult, err := suite.orchestrator.CallTool(ctx, "text-analyzer", map[string]interface{}{
		"text":          extractedText,
		"analysis_type": "sentiment",
	})
	require.NoError(t, err, "文本分析失败")
	require.NotNil(t, analyzeResult, "分析结果为空")

	analyzeMap := analyzeResult.(map[string]interface{})
	assert.Equal(t, extractedText, analyzeMap["text"], "传递的文本应一致")
	assert.Equal(t, "sentiment", analyzeMap["analysis_type"], "分析类型应正确")
	assert.Equal(t, "positive", analyzeMap["sentiment"], "情感分析结果应正确")
}
