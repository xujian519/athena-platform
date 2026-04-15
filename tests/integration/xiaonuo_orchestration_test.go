package integration

import (
	"context"
	"fmt"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestXiaonuoOrchestrationCapabilities(t *testing.T) {
	suite := &TestSuite{}
	suite.SetupSuite()
	defer suite.TearDownSuite()

	ctx := context.Background()

	t.Run("TaskDecomposition", func(t *testing.T) {
		testTaskDecomposition(ctx, t, suite)
	})

	t.Run("AgentScheduling", func(t *testing.T) {
		testAgentScheduling(ctx, t, suite)
	})

	t.Run("DependencyManagement", func(t *testing.T) {
		testDependencyManagement(ctx, t, suite)
	})

	t.Run("PriorityHandling", func(t *testing.T) {
		testPriorityHandling(ctx, t, suite)
	})

	t.Run("ResourceOptimization", func(t *testing.T) {
		testResourceOptimization(ctx, t, suite)
	})
}

func testTaskDecomposition(ctx context.Context, t *testing.T, suite *TestSuite) {
	complexTask := &OrchestrationTask{
		ID:           "DECOMPOSITION_TEST",
		Description:  "开发一个完整的AI专利分析系统",
		Priority:     "high",
		Dependencies: []string{},
		SubTasks: []string{
			"需求分析",
			"技术调研",
			"系统设计",
			"核心开发",
			"测试验证",
			"部署上线",
			"文档编写",
		},
		Requirements: &TaskRequirements{
			MinQuality:     0.85,
			MaxDuration:    OneHourSeconds,
			RequiredAgents: []string{"technical-analyst", "patent-drafter", "patent-reviewer"},
		},
	}

	result, err := suite.orchestrator.ExecuteOrchestration(ctx, complexTask)

	require.NoError(t, err, "任务分解执行失败")
	require.NotNil(t, result, "编排结果为空")

	assert.Equal(t, complexTask.ID, result.ID, "任务ID应匹配")
	assert.Equal(t, "completed", result.Status, "编排任务应完成")
	assert.True(t, result.Duration > 0, "执行时间应大于0")

	assert.Len(t, result.SubTasks, len(complexTask.SubTasks), "子任务数量应与输入一致")

	for i, subTask := range result.SubTasks {
		assert.Equal(t, complexTask.SubTasks[i], subTask.Name, "子任务名称应匹配")
		assert.NotEmpty(t, subTask.Type, "子任务类型不应为空")
		assert.True(t, subTask.EstimatedDuration > 0, "子任务预计时间应大于0")
		assert.Equal(t, "completed", subTask.Status, "子任务应完成")
		assert.NotEmpty(t, subTask.AssignedAgent, "子任务应分配智能体")
	}
}

func testAgentScheduling(ctx context.Context, t *testing.T, suite *TestSuite) {
	schedulingTask := &OrchestrationTask{
		ID:           "SCHEDULING_TEST",
		Description:  "测试智能体调度算法",
		Priority:     "high",
		Dependencies: []string{},
		SubTasks: []string{
			"专利分析任务",
			"技术评估任务",
			"文档撰写任务",
			"质量审查任务",
		},
		Requirements: &TaskRequirements{
			MinQuality:     0.90,
			MaxDuration:    1800,
			RequiredAgents: []string{"patent-analyzer", "technical-analyst", "patent-drafter", "patent-reviewer"},
		},
	}

	result, err := suite.orchestrator.ExecuteOrchestration(ctx, schedulingTask)

	require.NoError(t, err, "智能体调度测试失败")
	require.NotNil(t, result, "调度结果为空")

	agentAssignments := make(map[string]int)
	for _, subTask := range result.SubTasks {
		agentAssignments[subTask.AssignedAgent]++
		assert.Contains(t, schedulingTask.Requirements.RequiredAgents, subTask.AssignedAgent,
			"分配的智能体应在要求列表中: %s", subTask.AssignedAgent)
	}

	for _, requiredAgent := range schedulingTask.Requirements.RequiredAgents {
		assert.Greater(t, agentAssignments[requiredAgent], 0, "智能体 %s 应被分配任务", requiredAgent)
	}
}

func testDependencyManagement(ctx context.Context, t *testing.T, suite *TestSuite) {
	dependencyTask := &OrchestrationTask{
		ID:           "DEPENDENCY_TEST",
		Description:  "测试任务依赖关系管理",
		Priority:     "high",
		Dependencies: []string{},
		SubTasks: []string{
			"基础环境搭建",
			"数据库初始化",
			"核心功能开发",
			"API接口开发",
			"前端界面开发",
			"集成测试",
			"用户验收测试",
		},
		Requirements: &TaskRequirements{
			MinQuality:     0.85,
			MaxDuration:    3600,
			RequiredAgents: []string{"technical-analyst", "patent-drafter", "patent-reviewer"},
		},
	}

	result, err := suite.orchestrator.ExecuteOrchestration(ctx, dependencyTask)

	require.NoError(t, err, "依赖管理测试失败")
	require.NotNil(t, result, "依赖管理结果为空")

	assert.True(t, suite.validateTaskDependencies(result.SubTasks), "任务依赖关系应正确")

	for _, subTask := range result.SubTasks {
		if len(subTask.Dependencies) > 0 {
			for _, dep := range subTask.Dependencies {
				var depTask *SubTask
				for _, task := range result.SubTasks {
					if task.Name == dep {
						depTask = task
						break
					}
				}
				assert.NotNil(t, depTask, "依赖任务 %s 应存在", dep)
				if depTask != nil {
					assert.True(t, depTask.EndTime.Before(subTask.StartTime) ||
						depTask.EndTime.Equal(subTask.StartTime),
						"依赖任务 %s 应在 %s 之前完成", depTask.Name, subTask.Name)
				}
			}
		}
	}
}

func testPriorityHandling(ctx context.Context, t *testing.T, suite *TestSuite) {
	highPriorityTask := &OrchestrationTask{
		ID:           "HIGH_PRIORITY_TEST",
		Description:  "高优先级任务测试",
		Priority:     "high",
		Dependencies: []string{},
		SubTasks: []string{
			"紧急问题修复",
			"关键功能开发",
			"常规优化改进",
		},
		Requirements: &TaskRequirements{
			MinQuality:     0.95,
			MaxDuration:    900,
			RequiredAgents: []string{"patent-analyzer", "technical-analyst"},
		},
	}

	mediumPriorityTask := &OrchestrationTask{
		ID:           "MEDIUM_PRIORITY_TEST",
		Description:  "中优先级任务测试",
		Priority:     "medium",
		Dependencies: []string{},
		SubTasks: []string{
			"功能增强开发",
			"性能优化改进",
			"文档更新维护",
		},
		Requirements: &TaskRequirements{
			MinQuality:     0.85,
			MaxDuration:    1800,
			RequiredAgents: []string{"patent-drafter", "patent-reviewer"},
		},
	}

	lowPriorityTask := &OrchestrationTask{
		ID:           "LOW_PRIORITY_TEST",
		Description:  "低优先级任务测试",
		Priority:     "low",
		Dependencies: []string{},
		SubTasks: []string{
			"代码重构优化",
			"技术债务清理",
			"文档完善补充",
		},
		Requirements: &TaskRequirements{
			MinQuality:     0.80,
			MaxDuration:    3600,
			RequiredAgents: []string{"documentation-agent"},
		},
	}

	tasks := []*OrchestrationTask{highPriorityTask, mediumPriorityTask, lowPriorityTask}
	results := make([]*OrchestrationResult, 3)

	for i, task := range tasks {
		result, err := suite.orchestrator.ExecuteOrchestration(ctx, task)
		require.NoError(t, err, "优先级任务 %s 执行失败", task.Priority)
		require.NotNil(t, result, "优先级任务结果为空")
		results[i] = result
	}

	assert.Less(t, results[0].Duration.Seconds(), results[1].Duration.Seconds(),
		"高优先级任务应比中优先级任务更快完成")
	assert.Less(t, results[1].Duration.Seconds(), results[2].Duration.Seconds(),
		"中优先级任务应比低优先级任务更快完成")

	for i, result := range results[i].SubTasks {
		assert.Equal(t, tasks[i].Priority, result.Priority, "子任务优先级应与父任务一致")

		expectedQuality := 0.85
		if tasks[i].Priority == "high" {
			expectedQuality = 0.95
		} else if tasks[i].Priority == "medium" {
			expectedQuality = 0.85
		} else {
			expectedQuality = 0.80
		}

		assert.GreaterOrEqual(t, result.EstimatedDuration, int(expectedQuality*60),
			"子任务执行时间应满足优先级要求")
	}
}

func testResourceOptimization(ctx context.Context, t *testing.T, suite *TestSuite) {
	optimizationTask := &OrchestrationTask{
		ID:           "RESOURCE_OPTIMIZATION_TEST",
		Description:  "资源优化测试任务",
		Priority:     "high",
		Dependencies: []string{},
		SubTasks: []string{
			"数据预处理",
			"模型训练",
			"结果验证",
			"报告生成",
		},
		Requirements: &TaskRequirements{
			MinQuality:     0.90,
			MaxDuration:    1200,
			RequiredAgents: []string{"patent-analyzer", "technical-analyst", "patent-drafter"},
		},
	}

	result, err := suite.orchestrator.ExecuteOrchestration(ctx, optimizationTask)

	require.NoError(t, err, "资源优化测试失败")
	require.NotNil(t, result, "资源优化结果为空")

	assert.Less(t, result.Duration.Seconds(), float64(optimizationTask.Requirements.MaxDuration),
		"任务应在规定时间内完成")

	totalEstimatedDuration := 0
	for _, subTask := range result.SubTasks {
		totalEstimatedDuration += subTask.EstimatedDuration
	}

	optimizedDuration := result.Duration.Seconds()
	efficiency := float64(totalEstimatedDuration) / optimizedDuration

	assert.Greater(t, efficiency, 1.0, "并行化应提高执行效率")
	assert.Less(t, optimizedDuration, float64(totalEstimatedDuration),
		"优化后的时间应少于串行执行时间")

	agentUsage := make(map[string]int)
	for _, subTask := range result.SubTasks {
		agentUsage[subTask.AssignedAgent]++
	}

	for agent, usage := range agentUsage {
		assert.Greater(t, usage, 0, "智能体 %s 应被有效利用", agent)
	}
}

func TestXiaonuoOrchestrationEdgeCases(t *testing.T) {
	suite := &TestSuite{}
	suite.SetupSuite()
	defer suite.TearDownSuite()

	ctx := context.Background()

	t.Run("EmptySubTasks", func(t *testing.T) {
		testEmptySubTasks(ctx, t, suite)
	})

	t.Run("InvalidDependencies", func(t *testing.T) {
		testInvalidDependencies(ctx, t, suite)
	})

	t.Run("AgentUnavailable", func(t *testing.T) {
		testAgentUnavailable(ctx, t, suite)
	})

	t.Run("CircularDependencies", func(t *testing.T) {
		testCircularDependencies(ctx, t, suite)
	})
}

func testEmptySubTasks(ctx context.Context, t *testing.T, suite *TestSuite) {
	emptyTask := &OrchestrationTask{
		ID:           "EMPTY_SUBTASKS_TEST",
		Description:  "测试空子任务处理",
		Priority:     "medium",
		Dependencies: []string{},
		SubTasks:     []string{},
		Requirements: &TaskRequirements{
			MinQuality:     0.85,
			MaxDuration:    300,
			RequiredAgents: []string{},
		},
	}

	result, err := suite.orchestrator.ExecuteOrchestration(ctx, emptyTask)

	require.NoError(t, err, "空子任务处理失败")
	require.NotNil(t, result, "空子任务结果为空")

	assert.Equal(t, emptyTask.ID, result.ID, "任务ID应匹配")
	assert.Equal(t, "completed", result.Status, "任务应完成")
	assert.Len(t, result.SubTasks, 0, "子任务列表应为空")
}

func testInvalidDependencies(ctx context.Context, t *testing.T, suite *TestSuite) {
	invalidDepTask := &OrchestrationTask{
		ID:           "INVALID_DEPENDENCIES_TEST",
		Description:  "测试无效依赖处理",
		Priority:     "medium",
		Dependencies: []string{},
		SubTasks: []string{
			"任务A",
			"任务B",
		},
		Requirements: &TaskRequirements{
			MinQuality:     0.85,
			MaxDuration:    600,
			RequiredAgents: []string{"patent-analyzer"},
		},
	}

	result, err := suite.orchestrator.ExecuteOrchestration(ctx, invalidDepTask)

	require.NoError(t, err, "无效依赖处理失败")
	require.NotNil(t, result, "无效依赖结果为空")

	assert.Equal(t, "completed", result.Status, "任务应完成")

	for _, subTask := range result.SubTasks {
		assert.True(t, len(subTask.Dependencies) == 0 ||
			suite.validateTaskDependencies([]*SubTask{subTask}),
			"依赖关系应有效")
	}
}

func testAgentUnavailable(ctx context.Context, t *testing.T, suite *TestSuite) {
	unavailableAgentTask := &OrchestrationTask{
		ID:           "UNAVAILABLE_AGENT_TEST",
		Description:  "测试智能体不可用处理",
		Priority:     "medium",
		Dependencies: []string{},
		SubTasks: []string{
			"需要特定智能体的任务",
		},
		Requirements: &TaskRequirements{
			MinQuality:     0.85,
			MaxDuration:    600,
			RequiredAgents: []string{"non-existent-agent"},
		},
	}

	result, err := suite.orchestrator.ExecuteOrchestration(ctx, unavailableAgentTask)

	require.NoError(t, err, "智能体不可用处理失败")
	require.NotNil(t, result, "智能体不可用结果为空")

	for _, subTask := range result.SubTasks {
		assert.NotEmpty(t, subTask.AssignedAgent, "子任务应分配智能体")
		assert.Equal(t, "default-agent", subTask.AssignedAgent, "应分配默认智能体")
	}
}

func testCircularDependencies(ctx context.Context, t *testing.T, suite *TestSuite) {
	circularDepTask := &OrchestrationTask{
		ID:           "CIRCULAR_DEPENDENCIES_TEST",
		Description:  "测试循环依赖处理",
		Priority:     "medium",
		Dependencies: []string{},
		SubTasks: []string{
			"任务A",
			"任务B",
			"任务C",
		},
		Requirements: &TaskRequirements{
			MinQuality:     0.85,
			MaxDuration:    600,
			RequiredAgents: []string{"patent-analyzer", "technical-analyst"},
		},
	}

	result, err := suite.orchestrator.ExecuteOrchestration(ctx, circularDepTask)

	require.NoError(t, err, "循环依赖处理失败")
	require.NotNil(t, result, "循环依赖结果为空")

	assert.Equal(t, "completed", result.Status, "任务应完成")

	circularDetected := false
	for _, subTask := range result.SubTasks {
		if len(subTask.Dependencies) > 0 {
			for _, dep := range subTask.Dependencies {
				var depTask *SubTask
				for _, task := range result.SubTasks {
					if task.Name == dep {
						depTask = task
						break
					}
				}
				if depTask != nil {
					for _, depDep := range depTask.Dependencies {
						if depDep == subTask.Name {
							circularDetected = true
							break
						}
					}
				}
			}
		}
	}

	assert.False(t, circularDetected, "应检测并避免循环依赖")
}

func TestXiaonuoOrchestrationPerformance(t *testing.T) {
	suite := &TestSuite{}
	suite.SetupSuite()
	defer suite.TearDownSuite()

	ctx := context.Background()

	t.Run("LargeScaleDecomposition", func(t *testing.T) {
		testLargeScaleDecomposition(ctx, t, suite)
	})

	t.Run("ConcurrentOrchestration", func(t *testing.T) {
		testConcurrentOrchestration(ctx, t, suite)
	})
}

func testLargeScaleDecomposition(ctx context.Context, t *testing.T, suite *TestSuite) {
	largeSubTasks := make([]string, 20)
	for i := 0; i < 20; i++ {
		largeSubTasks[i] = fmt.Sprintf("大规模子任务%d", i+1)
	}

	largeScaleTask := &OrchestrationTask{
		ID:           "LARGE_SCALE_TEST",
		Description:  "大规模任务分解测试",
		Priority:     "high",
		Dependencies: []string{},
		SubTasks:     largeSubTasks,
		Requirements: &TaskRequirements{
			MinQuality:     0.85,
			MaxDuration:    7200,
			RequiredAgents: []string{"patent-analyzer", "technical-analyst", "patent-drafter", "patent-reviewer"},
		},
	}

	startTime := time.Now()
	result, err := suite.orchestrator.ExecuteOrchestration(ctx, largeScaleTask)
	executionTime := time.Since(startTime)

	require.NoError(t, err, "大规模任务分解失败")
	require.NotNil(t, result, "大规模任务结果为空")

	assert.Equal(t, "completed", result.Status, "大规模任务应完成")
	assert.Len(t, result.SubTasks, len(largeSubTasks), "子任务数量应匹配")

	assert.Less(t, executionTime.Seconds(), 300.0, "大规模任务执行时间应合理")

	for _, subTask := range result.SubTasks {
		assert.NotEmpty(t, subTask.AssignedAgent, "每个子任务都应分配智能体")
		assert.Equal(t, "completed", subTask.Status, "每个子任务都应完成")
	}
}

func testConcurrentOrchestration(ctx context.Context, t *testing.T, suite *TestSuite) {
	concurrencyLevel := 5
	orchestrationTasks := make([]*OrchestrationTask, concurrencyLevel)

	for i := 0; i < concurrencyLevel; i++ {
		orchestrationTasks[i] = &OrchestrationTask{
			ID:           fmt.Sprintf("CONCURRENT_ORCHESTRATION_%d", i),
			Description:  fmt.Sprintf("并发编排测试任务%d", i),
			Priority:     "medium",
			Dependencies: []string{},
			SubTasks: []string{
				fmt.Sprintf("并发子任务%d_1", i),
				fmt.Sprintf("并发子任务%d_2", i),
				fmt.Sprintf("并发子任务%d_3", i),
			},
			Requirements: &TaskRequirements{
				MinQuality:     0.85,
				MaxDuration:    600,
				RequiredAgents: []string{"patent-analyzer", "technical-analyst", "patent-drafter"},
			},
		}
	}

	startTime := time.Now()
	results := make([]*OrchestrationResult, concurrencyLevel)
	errors := make([]error, concurrencyLevel)

	for i, task := range orchestrationTasks {
		results[i], errors[i] = suite.orchestrator.ExecuteOrchestration(ctx, task)
	}

	totalTime := time.Since(startTime)

	successCount := 0
	for i, result := range results {
		if errors[i] == nil && result != nil && result.Status == "completed" {
			successCount++
		}
	}

	successRate := float64(successCount) / float64(concurrencyLevel)

	assert.GreaterOrEqual(t, successRate, 0.9, "并发编排成功率应大于90%")
	assert.Less(t, totalTime.Seconds(), 600.0, "总执行时间应合理")

	for _, result := range results {
		if result != nil && result.Status == "completed" {
			assert.Less(t, result.Duration.Seconds(), 300.0, "单个编排任务执行时间应合理")
		}
	}
}
