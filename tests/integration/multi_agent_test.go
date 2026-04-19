package integration

import (
	"context"
	"fmt"
	"log"
	"os"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"github.com/stretchr/testify/suite"
)

const (
	MaxResponseTimeMs   = 2000
	MinThroughput       = 100
	MaxErrorRate        = 0.01
	MaxMemoryUsageBytes = 512 * 1024 * 1024
	MaxCPUUsage         = 0.8
	OneHourSeconds      = 3600
)

type TestSuite struct {
	suite.Suite
	orchestrator *TestOrchestrator
	simulator    *AgentSimulator
	assertions   *AssertionEngine
	collector    *MetricsCollector
	generator    *DataGenerator
}

func (s *TestSuite) SetupSuite() {
	ctx := context.Background()

	s.orchestrator = NewTestOrchestrator(ctx)
	require.NotNil(s.T(), s.orchestrator, "测试编排器初始化失败")

	s.simulator = NewAgentSimulator(ctx)
	require.NotNil(s.T(), s.simulator, "智能体模拟器初始化失败")

	s.assertions = NewAssertionEngine()
	require.NotNil(s.T(), s.assertions, "断言引擎初始化失败")

	s.collector = NewMetricsCollector()
	require.NotNil(s.T(), s.collector, "指标收集器初始化失败")

	s.generator = NewDataGenerator()
	require.NotNil(s.T(), s.generator, "数据生成器初始化失败")

	err := s.orchestrator.PrepareEnvironment()
	require.NoError(s.T(), err, "测试环境准备失败")

	log.Printf("✅ 测试套件初始化完成")
}

func (s *TestSuite) TearDownSuite() {
	ctx := context.Background()

	err := s.orchestrator.CleanupEnvironment(ctx)
	if err != nil {
		log.Printf("⚠️ 测试环境清理失败: %v", err)
	}

	report, err := s.collector.GenerateReport()
	if err != nil {
		log.Printf("⚠️ 测试报告生成失败: %v", err)
	} else {
		log.Printf("📊 测试报告:\n%s", report)
	}

	log.Printf("🧹 测试套件清理完成")
}

func (s *TestSuite) TestBasicAgentCommunication() {
	ctx := context.Background()
	
	message := &AgentMessage{
		From:    "patent-analyzer",
		To:      "patent-retriever",
		Type:    MessageTypeTaskRequest,
		Payload: map[string]interface{}{
			"patent_id":  "TEST001",
			"action":     "analyze_patent",
			"parameters": map[string]string{
				"title":       "AI驱动的专利分析系统",
				"abstract":    "一种基于人工智能技术的专利分析和处理方法...",
				"claims":      "1. 一种AI驱动的专利分析系统，其特征在于...",
			},
		},
		Timestamp: time.Now(),
	}
	
	response, err := s.simulator.SendMessage(ctx, message)
	require.NoError(s.T(), err, "发送消息失败")
	require.NotNil(s.T(), response, "响应为空")
	
	s.assertions.AssertMessageResponse(s.T(), message, response)
	
	metrics := s.collector.GetCommunicationMetrics()
	assert.Greater(s.T(), metrics["success_rate"], float64(0.95), "通信成功率应大于95%")
}

func (s *TestSuite) TestPatentWorkflowExecution() {
	ctx := context.Background()
	
	patentData := s.generator.GeneratePatentData(&PatentDataConfig{
		Complexity: "medium",
		Technology: "AI",
		Country:    "CN",
	})
	
	workflowRequest := &WorkflowRequest{
		ID:          fmt.Sprintf("WF_%d", time.Now().Unix()),
		Type:        "patent_writing",
		Priority:    "high",
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
	
	workflowResult, err := s.orchestrator.ExecuteWorkflow(ctx, workflowRequest)
	require.NoError(s.T(), err, "工作流执行失败")
	require.NotNil(s.T(), workflowResult, "工作流结果为空")
	
	s.assertions.AssertWorkflowResult(s.T(), workflowRequest, workflowResult)
	
	for _, stage := range workflowResult.Stages {
		assert.NotEmpty(s.T(), stage.Output, "阶段 %s 输出不应为空", stage.Name)
		assert.Greater(s.T(), stage.Duration.Seconds(), float64(0), "阶段 %s 执行时间应大于0", stage.Name)
	}
	
	metrics := s.collector.GetWorkflowMetrics()
	assert.Less(s.T(), metrics["avg_execution_time"], float64(300), "平均执行时间应小于300秒")
	assert.Greater(s.T(), metrics["success_rate"], float64(0.90), "工作流成功率应大于90%")
}

func (s *TestSuite) TestXiaonuoOrchestration() {
	ctx := context.Background()
	
	complexTask := &OrchestrationTask{
		ID:          "TASK_XIAONUO_001",
		Description: "撰写一份AI驱动的智能专利分析系统专利",
		Priority:    "high",
		Dependencies: []string{},
		SubTasks: []string{
			"技术方案分析",
			"现有专利检索", 
			"创新点识别",
			"权利要求书撰写",
			"说明书撰写",
			"图纸设计",
			"审查意见准备",
		},
		Requirements: &TaskRequirements{
			MinQuality:     0.85,
			MaxDuration:   OneHourSeconds,
			RequiredAgents: []string{"technical-analyst", "patent-drafter", "patent-reviewer"},
		},
	}
	
	orchestrationResult, err := s.orchestrator.ExecuteOrchestration(ctx, complexTask)
	require.NoError(s.T(), err, "编排任务执行失败")
	require.NotNil(s.T(), orchestrationResult, "编排结果为空")
	
	assert.Len(s.T(), orchestrationResult.SubTasks, len(complexTask.SubTasks), 
		"子任务数量应与预期一致")
	
	for _, subTask := range orchestrationResult.SubTasks {
		assert.NotEmpty(s.T(), subTask.AssignedAgent, "子任务 %s 应分配智能体", subTask.Name)
		assert.Contains(s.T(), complexTask.Requirements.RequiredAgents, subTask.AssignedAgent,
			"分配的智能体应在要求的列表中")
	}
	
	assert.True(s.T(), s.validateTaskDependencies(orchestrationResult.SubTasks), 
		"任务执行顺序应符合依赖关系")
}

	// 发送消息
	response, err := s.simulator.SendMessage(ctx, message)
	require.NoError(s.T(), err, "发送消息失败")
	require.NotNil(s.T(), response, "响应为空")

	// 验证响应
	s.assertions.AssertMessageResponse(s.T(), message, response)

	// 验证通信指标
	metrics := s.collector.GetCommunicationMetrics()
	assert.Greater(s.T(), metrics["success_rate"], float64(0.95), "通信成功率应大于95%")
}

// TestPatentWorkflowExecution 测试专利撰写完整工作流
func (s *TestSuite) TestPatentWorkflowExecution() {
	ctx := context.Background()

	// 生成测试专利数据
	patentData := s.generator.GeneratePatentData(&PatentDataConfig{
		Complexity: "medium",
		Technology: "AI",
		Country:    "CN",
	})

	// 创建工作流请求
	workflowRequest := &WorkflowRequest{
		ID:        fmt.Sprintf("WF_%d", time.Now().Unix()),
		Type:      "patent_writing",
		Priority:  "high",
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

	// 执行工作流
	workflowResult, err := s.orchestrator.ExecuteWorkflow(ctx, workflowRequest)
	require.NoError(s.T(), err, "工作流执行失败")
	require.NotNil(s.T(), workflowResult, "工作流结果为空")

	// 验证工作流结果
	s.assertions.AssertWorkflowResult(s.T(), workflowRequest, workflowResult)

	// 验证各个阶段的输出
	for _, stage := range workflowResult.Stages {
		assert.NotEmpty(s.T(), stage.Output, "阶段 %s 输出不应为空", stage.Name)
		assert.Greater(s.T(), stage.Duration.Seconds(), float64(0), "阶段 %s 执行时间应大于0", stage.Name)
	}

	// 验证整体性能指标
	metrics := s.collector.GetWorkflowMetrics()
	assert.Less(s.T(), metrics["avg_execution_time"], float64(300), "平均执行时间应小于300秒")
	assert.Greater(s.T(), metrics["success_rate"], float64(0.90), "工作流成功率应大于90%")
}

// TestXiaonuoOrchestration 测试小诺智能编排器功能
func (s *TestSuite) TestXiaonuoOrchestration() {
	ctx := context.Background()

	// 创建复杂任务
	complexTask := &OrchestrationTask{
		ID:           "TASK_XIAONUO_001",
		Description:  "撰写一份AI驱动的智能专利分析系统专利",
		Priority:     "high",
		Dependencies: []string{},
		SubTasks: []string{
			"技术方案分析",
			"现有专利检索",
			"创新点识别",
			"权利要求书撰写",
			"说明书撰写",
			"图纸设计",
			"审查意见准备",
		},
		Requirements: &TaskRequirements{
			MinQuality:     0.85,
			MaxDuration:    3600, // 1小时
			RequiredAgents: []string{"technical-analyst", "patent-drafter", "patent-reviewer"},
		},
	}

	// 执行编排任务
	orchestrationResult, err := s.orchestrator.ExecuteOrchestration(ctx, complexTask)
	require.NoError(s.T(), err, "编排任务执行失败")
	require.NotNil(s.T(), orchestrationResult, "编排结果为空")

	// 验证任务分解
	assert.Len(s.T(), orchestrationResult.SubTasks, len(complexTask.SubTasks),
		"子任务数量应与预期一致")

	// 验证智能体分配
	for _, subTask := range orchestrationResult.SubTasks {
		assert.NotEmpty(s.T(), subTask.AssignedAgent, "子任务 %s 应分配智能体", subTask.Name)
		assert.Contains(s.T(), complexTask.Requirements.RequiredAgents, subTask.AssignedAgent,
			"分配的智能体应在要求的列表中")
	}

	// 验证执行顺序
	assert.True(s.T(), s.validateTaskDependencies(orchestrationResult.SubTasks),
		"任务执行顺序应符合依赖关系")
}

func (s *TestSuite) TestAtomicToolSystem() {
	ctx := context.Background()
	
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
					"word_count":    len(text),
					"char_count":    len([]rune(text)),
					"language":      "zh",
					"sentiment":     "positive",
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
						"id":          fmt.Sprintf("PAT_%03d", i+1),
						"title":       fmt.Sprintf("相关专利%d", i+1),
						"abstract":    fmt.Sprintf("与%v相关的技术方案...", keywords),
						"relevance":   0.9 - float64(i)*0.1,
					})
				}
				return results, nil
			},
		},
	}
	
	for _, tool := range testTools {
		err := s.orchestrator.RegisterTool(ctx, tool)
		require.NoError(s.T(), err, "工具 %s 注册失败", tool.Name)
	}
	
	for _, tool := range testTools {
		testParams := make(map[string]interface{})
		for _, param := range tool.Parameters {
			if param.Required {
				switch param.Type {
				case "string":
					testParams[param.Name] = "测试文本内容"
				case "array":
					testParams[param.Name] = []interface{}{"AI", "专利", "分析"}
				case "integer":
					testParams[param.Name] = 5
				}
			} else if param.Default != nil {
				testParams[param.Name] = param.Default
			}
		}
		
		result, err := s.orchestrator.CallTool(ctx, tool.Name, testParams)
		require.NoError(s.T(), err, "工具 %s 调用失败", tool.Name)
		require.NotNil(s.T(), result, "工具 %s 结果为空", tool.Name)
		
		s.assertions.AssertToolResult(s.T(), tool, testParams, result)
	}
	
	tools, err := s.orchestrator.ListTools(ctx)
	require.NoError(s.T(), err, "获取工具列表失败")
	assert.Len(s.T(), tools, len(testTools), "工具数量应正确")
}

func (s *TestSuite) TestPerformanceAndLoad() {
	ctx := context.Background()
	
	benchmarks := &PerformanceBenchmarks{
		MaxResponseTime:      time.Duration(MaxResponseTimeMs) * time.Millisecond,
		MinThroughput:        MinThroughput,
		MaxErrorRate:         MaxErrorRate,
		MaxMemoryUsage:       MaxMemoryUsageBytes,
		MaxCPUUsage:          MaxCPUUsage,
	}
	
	concurrencyLevels := []int{10, 50, 100, 200}
	
	for _, concurrency := range concurrencyLevels {
		s.T().Run(fmt.Sprintf("并发_%d", concurrency), func(t *testing.T) {
			tasks := make([]*WorkflowRequest, concurrency)
			for i := 0; i < concurrency; i++ {
				tasks[i] = &WorkflowRequest{
					ID:        fmt.Sprintf("PERF_%d_%d", concurrency, i),
					Type:      "simple_task",
					Priority:  "normal",
					InputData: map[string]interface{}{"test_data": i},
				}
			}
			
			results := s.collector.ExecuteConcurrentTest(ctx, tasks, benchmarks)
			
			s.assertions.AssertPerformanceResults(s.T(), concurrency, results, benchmarks)
		})
	}
}

func (s *TestSuite) TestFaultTolerance() {
	ctx := context.Background()
	
	failureScenarios := []FailureScenario{
		{
			Name:        "智能体故障",
			Description: "模拟智能体服务不可用",
			Type:        "agent_failure",
			Target:      "patent-analyzer",
			Action:      "shutdown",
		},
		{
			Name:        "网络中断",
			Description: "模拟网络连接中断",
			Type:        "network_failure",
			Target:      "redis",
			Action:      "disconnect",
		},
		{
			Name:        "资源耗尽",
			Description: "模拟内存资源不足",
			Type:        "resource_exhaustion",
			Target:      "memory",
			Action:      "limit",
		},
	}
	
	for _, scenario := range failureScenarios {
		s.T().Run(scenario.Name, func(t *testing.T) {
			recoveryResult, err := s.simulator.ExecuteFailureScenario(ctx, &scenario)
			require.NoError(t, err, "故障场景 %s 执行失败", scenario.Name)
			
			s.assertions.AssertFaultTolerance(t, &scenario, recoveryResult)
			
			health := s.orchestrator.CheckSystemHealth(ctx)
			assert.True(t, health.Healthy, "故障恢复后系统应健康")
		})
	}
}

func (s *TestSuite) validateTaskDependencies(tasks []*SubTask) bool {
	for _, task := range tasks {
		for _, dep := range task.Dependencies {
			found := false
			for _, other := range tasks {
				if other.ID == dep && other.CompletedAt.Before(task.StartedAt) {
					found = true
					break
				}
			}
			if !found {
				return false
			}
		}
	}
	return true
}

func TestMain(m *testing.M) {
	if err := os.Setenv("TEST_MODE", "true"); err != nil {
		log.Fatalf("设置测试环境失败: %v", err)
	}
	
	code := m.Run()
	
	os.Unsetenv("TEST_MODE")
	
	os.Exit(code)
}

func TestIntegrationSuite(t *testing.T) {
	suite.Run(t, new(TestSuite))
}
				return results, nil
			},
		},
	}

	// 注册工具
	for _, tool := range testTools {
		err := s.orchestrator.RegisterTool(ctx, tool)
		require.NoError(s.T(), err, "工具 %s 注册失败", tool.Name)
	}

	// 测试工具调用
	for _, tool := range testTools {
		// 准备测试参数
		testParams := make(map[string]interface{})
		for _, param := range tool.Parameters {
			if param.Required {
				switch param.Type {
				case "string":
					testParams[param.Name] = "测试文本内容"
				case "array":
					testParams[param.Name] = []interface{}{"AI", "专利", "分析"}
				case "integer":
					testParams[param.Name] = 5
				}
			} else if param.Default != nil {
				testParams[param.Name] = param.Default
			}
		}

		// 调用工具
		result, err := s.orchestrator.CallTool(ctx, tool.Name, testParams)
		require.NoError(s.T(), err, "工具 %s 调用失败", tool.Name)
		require.NotNil(s.T(), result, "工具 %s 结果为空", tool.Name)

		// 验证结果格式
		s.assertions.AssertToolResult(s.T(), tool, testParams, result)
	}

	// 验证工具发现
	tools, err := s.orchestrator.ListTools(ctx)
	require.NoError(s.T(), err, "获取工具列表失败")
	assert.Len(s.T(), tools, len(testTools), "工具数量应正确")
}

// TestPerformanceAndLoad 测试性能和负载
func (s *TestSuite) TestPerformanceAndLoad() {
	ctx := context.Background()

	// 性能基准
	benchmarks := &PerformanceBenchmarks{
		MaxResponseTime: 2000 * time.Millisecond, // 2秒
		MinThroughput:   100,                     // 每秒100个请求
		MaxErrorRate:    0.01,                    // 错误率小于1%
		MaxMemoryUsage:  512 * 1024 * 1024,       // 512MB
		MaxCPUUsage:     0.8,                     // 80%
	}

	// 执行并发测试
	concurrencyLevels := []int{10, 50, 100, 200}

	for _, concurrency := range concurrencyLevels {
		s.T().Run(fmt.Sprintf("并发_%d", concurrency), func(t *testing.T) {
			// 准备并发任务
			tasks := make([]*WorkflowRequest, concurrency)
			for i := 0; i < concurrency; i++ {
				tasks[i] = &WorkflowRequest{
					ID:        fmt.Sprintf("PERF_%d_%d", concurrency, i),
					Type:      "simple_task",
					Priority:  "normal",
					InputData: map[string]interface{}{"test_data": i},
				}
			}

			// 执行并发测试
			results := s.collector.ExecuteConcurrentTest(ctx, tasks, benchmarks)

			// 验证性能指标
			s.assertions.AssertPerformanceResults(s.T(), concurrency, results, benchmarks)
		})
	}
}

// TestFaultTolerance 测试故障容错能力
func (s *TestSuite) TestFaultTolerance() {
	ctx := context.Background()

	// 故障场景测试
	failureScenarios := []FailureScenario{
		{
			Name:        "智能体故障",
			Description: "模拟智能体服务不可用",
			Type:        "agent_failure",
			Target:      "patent-analyzer",
			Action:      "shutdown",
		},
		{
			Name:        "网络中断",
			Description: "模拟网络连接中断",
			Type:        "network_failure",
			Target:      "redis",
			Action:      "disconnect",
		},
		{
			Name:        "资源耗尽",
			Description: "模拟内存资源不足",
			Type:        "resource_exhaustion",
			Target:      "memory",
			Action:      "limit",
		},
	}

	for _, scenario := range failureScenarios {
		s.T().Run(scenario.Name, func(t *testing.T) {
			// 执行故障场景
			recoveryResult, err := s.simulator.ExecuteFailureScenario(ctx, &scenario)
			require.NoError(t, err, "故障场景 %s 执行失败", scenario.Name)

			// 验证恢复能力
			s.assertions.AssertFaultTolerance(t, &scenario, recoveryResult)

			// 验证系统完整性
			health := s.orchestrator.CheckSystemHealth(ctx)
			assert.True(t, health.Healthy, "故障恢复后系统应健康")
		})
	}
}

// validateTaskDependencies 验证任务依赖关系
func (s *TestSuite) validateTaskDependencies(tasks []*SubTask) bool {
	for _, task := range tasks {
		for _, dep := range task.Dependencies {
			found := false
			for _, other := range tasks {
				if other.ID == dep && other.CompletedAt.Before(task.StartedAt) {
					found = true
					break
				}
			}
			if !found {
				return false
			}
		}
	}
	return true
}

// TestMain 测试主入口
func TestMain(m *testing.M) {
	// 设置测试环境
	if err := os.Setenv("TEST_MODE", "true"); err != nil {
		log.Fatalf("设置测试环境失败: %v", err)
	}

	// 运行测试
	code := m.Run()

	// 清理
	os.Unsetenv("TEST_MODE")

	os.Exit(code)
}

// TestIntegrationSuite 运行完整集成测试
func TestIntegrationSuite(t *testing.T) {
	suite.Run(t, new(TestSuite))
}
