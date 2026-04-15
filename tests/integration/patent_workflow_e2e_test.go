package integration

import (
	"context"
	"fmt"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestPatentWritingWorkflowE2E(t *testing.T) {
	suite := &TestSuite{}
	suite.SetupSuite()
	defer suite.TearDownSuite()

	ctx := context.Background()

	t.Run("SimpleAIPatentWriting", func(t *testing.T) {
		testSimpleAIPatentWriting(ctx, t, suite)
	})

	t.Run("ComplexIoTPatentWriting", func(t *testing.T) {
		testComplexIoTPatentWriting(ctx, t, suite)
	})

	t.Run("BlockchainPatentWriting", func(t *testing.T) {
		testBlockchainPatentWriting(ctx, t, suite)
	})

	t.Run("ConcurrentPatentWriting", func(t *testing.T) {
		testConcurrentPatentWriting(ctx, t, suite)
	})
}

func testSimpleAIPatentWriting(ctx context.Context, t *testing.T, suite *TestSuite) {
	patentData := suite.generator.GeneratePatentData(&PatentDataConfig{
		Complexity: "simple",
		Technology: "AI",
		Country:    "CN",
	})

	workflowRequest := &WorkflowRequest{
		ID:          fmt.Sprintf("AI_SIMPLE_%d", time.Now().Unix()),
		Type:        "patent_writing",
		Priority:    "normal",
		InputData:   patentData,
		ExpectedAgents: []string{
			"patent-analyzer",
			"patent-retriever",
			"technical-analyst",
			"patent-drafter",
			"patent-reviewer",
		},
		CreatedAt: time.Now(),
	}

	startTime := time.Now()
	workflowResult, err := suite.orchestrator.ExecuteWorkflow(ctx, workflowRequest)
	executionTime := time.Since(startTime)

	require.NoError(t, err, "AI简单专利工作流执行失败")
	require.NotNil(t, workflowResult, "工作流结果为空")

	assert.Equal(t, workflowRequest.ID, workflowResult.ID, "工作流ID应匹配")
	assert.Equal(t, "completed", workflowResult.Status, "工作流状态应为完成")
	assert.True(t, workflowResult.Duration > 0, "执行时间应大于0")

	assert.Less(t, executionTime.Seconds(), 300.0, "AI简单专利执行时间应小于300秒")

	assert.Len(t, workflowResult.Stages, 5, "应有5个执行阶段")

	stageNames := make(map[string]bool)
	for _, stage := range workflowResult.Stages {
		stageNames[stage.Name] = true
		assert.Equal(t, "completed", stage.Status, "阶段 %s 应完成", stage.Name)
		assert.NotEmpty(t, stage.Output, "阶段 %s 应有输出", stage.Name)
		assert.True(t, stage.Duration > 0, "阶段 %s 执行时间应大于0", stage.Name)
	}

	expectedStages := []string{"analysis", "retrieval", "technical", "drafting", "review"}
	for _, expectedStage := range expectedStages {
		assert.True(t, stageNames[expectedStage], "应包含阶段: %s", expectedStage)
	}

	metrics := suite.collector.GetWorkflowMetrics()
	assert.Greater(t, metrics["success_rate"], 0.95, "成功率应大于95%")
	assert.Less(t, metrics["avg_execution_time"], 300.0, "平均执行时间应小于300秒")
}

	// 执行工作流
	startTime := time.Now()
	workflowResult, err := suite.orchestrator.ExecuteWorkflow(ctx, workflowRequest)
	executionTime := time.Since(startTime)

	require.NoError(t, err, "AI简单专利工作流执行失败")
	require.NotNil(t, workflowResult, "工作流结果为空")

	// 验证基本属性
	assert.Equal(t, workflowRequest.ID, workflowResult.ID, "工作流ID应匹配")
	assert.Equal(t, "completed", workflowResult.Status, "工作流状态应为完成")
	assert.True(t, workflowResult.Duration > 0, "执行时间应大于0")

	// 验证执行时间合理
	assert.Less(t, executionTime.Seconds(), 300.0, "AI简单专利执行时间应小于300秒")

	// 验证阶段完整性
	assert.Len(t, workflowResult.Stages, 5, "应有5个执行阶段")

	// 验证各阶段输出
	stageNames := make(map[string]bool)
	for _, stage := range workflowResult.Stages {
		stageNames[stage.Name] = true
		assert.Equal(t, "completed", stage.Status, "阶段 %s 应完成", stage.Name)
		assert.NotEmpty(t, stage.Output, "阶段 %s 应有输出", stage.Name)
		assert.True(t, stage.Duration > 0, "阶段 %s 执行时间应大于0", stage.Name)
	}

	expectedStages := []string{"analysis", "retrieval", "technical", "drafting", "review"}
	for _, expectedStage := range expectedStages {
		assert.True(t, stageNames[expectedStage], "应包含阶段: %s", expectedStage)
	}

	// 验证性能指标
	metrics := suite.collector.GetWorkflowMetrics()
	assert.Greater(t, metrics["success_rate"], 0.95, "成功率应大于95%")
	assert.Less(t, metrics["avg_execution_time"], 300.0, "平均执行时间应小于300秒")
}

func testComplexIoTPatentWriting(ctx context.Context, t *testing.T, suite *TestSuite) {
	// 生成复杂IoT专利数据
	patentData := suite.generator.GeneratePatentData(&PatentDataConfig{
		Complexity: "complex",
		Technology: "IoT",
		Country:    "CN",
	})

	workflowRequest := &WorkflowRequest{
		ID:        fmt.Sprintf("IOT_COMPLEX_%d", time.Now().Unix()),
		Type:      "patent_writing",
		Priority:  "high",
		InputData: patentData,
		ExpectedAgents: []string{
			"patent-analyzer",
			"patent-retriever",
			"technical-analyst",
			"patent-drafter",
			"patent-reviewer",
			"documentation-agent",
		},
		CreatedAt: time.Now(),
	}

	startTime := time.Now()
	workflowResult, err := suite.orchestrator.ExecuteWorkflow(ctx, workflowRequest)
	executionTime := time.Since(startTime)

	require.NoError(t, err, "IoT复杂专利工作流执行失败")
	require.NotNil(t, workflowResult, "工作流结果为空")

	// 复杂专利应有更长的执行时间
	assert.Greater(t, executionTime.Seconds(), 200.0, "IoT复杂专利执行时间应大于200秒")
	assert.Less(t, executionTime.Seconds(), 600.0, "IoT复杂专利执行时间应小于600秒")

	// 验证复杂专利的阶段数量可能更多
	assert.GreaterOrEqual(t, len(workflowResult.Stages), 5, "阶段数量应至少为5个")

	// 验证各阶段的复杂度
	for _, stage := range workflowResult.Stages {
		assert.True(t, stage.Duration > 0, "阶段 %s 执行时间应大于0", stage.Name)
		assert.NotEmpty(t, stage.Output, "阶段 %s 应有输出", stage.Name)

		// 复杂专利的某些阶段应该更长
		if stage.Name == "drafting" || stage.Name == "technical" {
			assert.Greater(t, stage.Duration.Seconds(), 30.0, "复杂专利的 %s 阶段应大于30秒", stage.Name)
		}
	}
}

func testBlockchainPatentWriting(ctx context.Context, t *testing.T, suite *TestSuite) {
	// 生成区块链专利数据
	patentData := suite.generator.GeneratePatentData(&PatentDataConfig{
		Complexity: "medium",
		Technology: "Blockchain",
		Country:    "US",
	})

	workflowRequest := &WorkflowRequest{
		ID:        fmt.Sprintf("BLOCKCHAIN_%d", time.Now().Unix()),
		Type:      "patent_writing",
		Priority:  "medium",
		InputData: patentData,
		ExpectedAgents: []string{
			"patent-analyzer",
			"patent-retriever",
			"technical-analyst",
			"patent-drafter",
			"patent-reviewer",
			"translation-agent",
		},
		CreatedAt: time.Now(),
	}

	workflowResult, err := suite.orchestrator.ExecuteWorkflow(ctx, workflowRequest)

	require.NoError(t, err, "区块链专利工作流执行失败")
	require.NotNil(t, workflowResult, "工作流结果为空")

	// 验证区块链专利的特殊性
	assert.Contains(t, workflowResult.Stages[0].Output, "区块链", "第一阶段输出应包含区块链关键词")
	assert.Equal(t, "completed", workflowResult.Status, "工作流应完成")

	// 验证国际化支持
	assert.Equal(t, "US", patentData["country"], "应支持美国专利")
}

func testConcurrentPatentWriting(ctx context.Context, t *testing.T, suite *TestSuite) {
	concurrencyLevel := 3
	workflowRequests := make([]*WorkflowRequest, concurrencyLevel)

	technologies := []string{"AI", "IoT", "Blockchain"}

	// 创建并发工作流请求
	for i := 0; i < concurrencyLevel; i++ {
		patentData := suite.generator.GeneratePatentData(&PatentDataConfig{
			Complexity: "simple",
			Technology: technologies[i],
			Country:    "CN",
		})

		workflowRequests[i] = &WorkflowRequest{
			ID:        fmt.Sprintf("CONCURRENT_%d_%d", i, time.Now().Unix()),
			Type:      "patent_writing",
			Priority:  "normal",
			InputData: patentData,
			ExpectedAgents: []string{
				"patent-analyzer",
				"patent-retriever",
				"technical-analyst",
				"patent-drafter",
				"patent-reviewer",
			},
			CreatedAt: time.Now(),
		}
	}

	// 并发执行工作流
	startTime := time.Now()
	results := make([]*WorkflowResult, concurrencyLevel)
	errors := make([]error, concurrencyLevel)

	for i, request := range workflowRequests {
		results[i], errors[i] = suite.orchestrator.ExecuteWorkflow(ctx, request)
	}

	// 验证所有工作流都成功
	successCount := 0
	for i, result := range results {
		if errors[i] == nil && result != nil && result.Status == "completed" {
			successCount++
		}
	}

	totalTime := time.Since(startTime)

	// 并发测试断言
	assert.GreaterOrEqual(t, float64(successCount)/float64(concurrencyLevel), 0.9, "并发成功率应大于90%")
	assert.Less(t, totalTime.Seconds(), 600.0, "总执行时间应小于600秒")

	// 验证性能指标
	metrics := suite.collector.GetPerformanceMetrics()
	assert.NotNil(t, metrics, "性能指标不应为空")

	// 记录并发测试结果
	suite.collector.RecordPerformanceTest(
		concurrencyLevel,
		totalTime/time.Duration(concurrencyLevel),
		float64(successCount)/totalTime.Seconds(),
		float64(concurrencyLevel-successCount)/float64(concurrencyLevel),
	)
}

func TestPatentWritingWorkflowErrorHandling(t *testing.T) {
	suite := &TestSuite{}
	suite.SetupSuite()
	defer suite.TearDownSuite()

	ctx := context.Background()

	t.Run("InvalidPatentData", func(t *testing.T) {
		testInvalidPatentData(ctx, t, suite)
	})

	t.Run("MissingRequiredFields", func(t *testing.T) {
		testMissingRequiredFields(ctx, t, suite)
	})

	t.Run("AgentFailure", func(t *testing.T) {
		testAgentFailure(ctx, t, suite)
	})
}

func testInvalidPatentData(ctx context.Context, t *testing.T, suite *TestSuite) {
	// 创建无效的专利数据
	invalidPatentData := map[string]interface{}{
		"patent_id": "", // 空ID
		"title":     "", // 空标题
	}

	workflowRequest := &WorkflowRequest{
		ID:             "INVALID_DATA_TEST",
		Type:           "patent_writing",
		Priority:       "normal",
		InputData:      invalidPatentData,
		ExpectedAgents: []string{"patent-analyzer"},
		CreatedAt:      time.Now(),
	}

	workflowResult, err := suite.orchestrator.ExecuteWorkflow(ctx, workflowRequest)

	// 应该处理错误而不是崩溃
	assert.NotNil(t, err, "应该返回错误")
	assert.True(t, workflowResult == nil || workflowResult.Status == "failed", "工作流应该失败")
}

func testMissingRequiredFields(ctx context.Context, t *testing.T, suite *TestSuite) {
	// 创建缺少必需字段的请求
	workflowRequest := &WorkflowRequest{
		Type:           "patent_writing",
		Priority:       "normal",
		InputData:      map[string]interface{}{},
		ExpectedAgents: []string{"patent-analyzer"},
		CreatedAt:      time.Now(),
	}

	workflowResult, err := suite.orchestrator.ExecuteWorkflow(ctx, workflowRequest)

	assert.Error(t, err, "缺少ID应该返回错误")
	assert.True(t, workflowResult == nil || workflowResult.Status == "failed", "工作流应该失败")
}

func testAgentFailure(ctx context.Context, t *testing.T, suite *TestSuite) {
	// 创建正常请求，但模拟智能体故障
	patentData := suite.generator.GeneratePatentData(&PatentDataConfig{
		Complexity: "simple",
		Technology: "AI",
		Country:    "CN",
	})

	workflowRequest := &WorkflowRequest{
		ID:             "AGENT_FAILURE_TEST",
		Type:           "patent_writing",
		Priority:       "normal",
		InputData:      patentData,
		ExpectedAgents: []string{"non-existent-agent"},
		CreatedAt:      time.Now(),
	}

	workflowResult, err := suite.orchestrator.ExecuteWorkflow(ctx, workflowRequest)

	// 系统应该优雅地处理智能体故障
	assert.Error(t, err, "不存在的智能体应该返回错误")
	assert.True(t, workflowResult == nil || workflowResult.Status == "failed", "工作流应该失败")
}

func TestPatentWritingWorkflowDataIntegrity(t *testing.T) {
	suite := &TestSuite{}
	suite.SetupSuite()
	defer suite.TearDownSuite()

	ctx := context.Background()

	t.Run("DataConsistency", func(t *testing.T) {
		testDataConsistency(ctx, t, suite)
	})

	t.Run("OutputValidation", func(t *testing.T) {
		testOutputValidation(ctx, t, suite)
	})
}

func testDataConsistency(ctx context.Context, t *testing.T, suite *TestSuite) {
	patentData := suite.generator.GeneratePatentData(&PatentDataConfig{
		Complexity: "simple",
		Technology: "AI",
		Country:    "CN",
	})

	// 记录输入数据
	inputID := patentData["patent_id"]
	inputTitle := patentData["title"]

	workflowRequest := &WorkflowRequest{
		ID:        fmt.Sprintf("CONSISTENCY_%d", time.Now().Unix()),
		Type:      "patent_writing",
		Priority:  "normal",
		InputData: patentData,
		ExpectedAgents: []string{
			"patent-analyzer",
			"patent-retriever",
			"technical-analyst",
			"patent-drafter",
			"patent-reviewer",
		},
		CreatedAt: time.Now(),
	}

	workflowResult, err := suite.orchestrator.ExecuteWorkflow(ctx, workflowRequest)

	require.NoError(t, err, "工作流执行失败")
	require.NotNil(t, workflowResult, "工作流结果为空")

	// 验证数据一致性
	assert.Equal(t, workflowRequest.ID, workflowResult.ID, "工作流ID应保持一致")

	// 验证各阶段数据的连续性
	for i, stage := range workflowResult.Stages {
		if i > 0 {
			prevStage := workflowResult.Stages[i-1]
			assert.True(t, stage.StartTime.After(prevStage.EndTime) ||
				stage.StartTime.Equal(prevStage.EndTime),
				"阶段 %s 应在阶段 %s 之后开始", stage.Name, prevStage.Name)
		}
	}
}

func testOutputValidation(ctx context.Context, t *testing.T, suite *TestSuite) {
	patentData := suite.generator.GeneratePatentData(&PatentDataConfig{
		Complexity: "simple",
		Technology: "AI",
		Country:    "CN",
	})

	workflowRequest := &WorkflowRequest{
		ID:        fmt.Sprintf("OUTPUT_VALIDATION_%d", time.Now().Unix()),
		Type:      "patent_writing",
		Priority:  "normal",
		InputData: patentData,
		ExpectedAgents: []string{
			"patent-analyzer",
			"patent-retriever",
			"technical-analyst",
			"patent-drafter",
			"patent-reviewer",
		},
		CreatedAt: time.Now(),
	}

	workflowResult, err := suite.orchestrator.ExecuteWorkflow(ctx, workflowRequest)

	require.NoError(t, err, "工作流执行失败")
	require.NotNil(t, workflowResult, "工作流结果为空")

	// 验证输出格式
	assert.NotEmpty(t, workflowResult.ID, "结果ID不应为空")
	assert.NotEmpty(t, workflowResult.Type, "结果类型不应为空")
	assert.NotEmpty(t, workflowResult.Status, "结果状态不应为空")
	assert.True(t, workflowResult.StartTime.Before(workflowResult.EndTime), "开始时间应早于结束时间")

	// 验证阶段输出
	for _, stage := range workflowResult.Stages {
		assert.NotEmpty(t, stage.Name, "阶段名称不应为空")
		assert.NotEmpty(t, stage.Agent, "阶段智能体不应为空")
		assert.NotEmpty(t, stage.Status, "阶段状态不应为空")
		assert.NotEmpty(t, stage.Output, "阶段输出不应为空")
	}
}
