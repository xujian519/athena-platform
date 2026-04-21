package grpc

import (
	"context"
	"fmt"
	"sync"
	"sync/atomic"
	"time"

	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"

	pb "github.com/athena-workspace/gateway-unified/proto"
	"github.com/athena-workspace/gateway-unified/internal/logging"
)

// AgentServer Agent服务实现
type AgentServer struct {
	pb.UnimplementedAgentServiceServer

	// 任务管理
	tasks      map[string]*TaskContext
	tasksMutex sync.RWMutex

	// 统计
	totalCompleted atomic.Int64
	totalFailed    atomic.Int64

	// Agent状态
	agentStatus map[string]*AgentStats
	statusMutex sync.RWMutex

	// 启动时间
	startTime time.Time
}

// TaskContext 任务上下文
type TaskContext struct {
	TaskID      string
	AgentType   string
	Status      string
	CreatedAt   time.Time
	CompletedAt *time.Time
	Result      string
	Error       string
	CancelFunc  context.CancelFunc
}

// AgentStats Agent统计信息
type AgentStats struct {
	AgentType      string
	CurrentTasks   int32
	IsHealthy      bool
	CPUUsage       float64
	MemoryUsage    float64
	LastHeartbeat  time.Time
}

// NewAgentServer 创建Agent服务
func NewAgentServer() *AgentServer {
	server := &AgentServer{
		tasks:       make(map[string]*TaskContext),
		agentStatus: make(map[string]*AgentStats),
		startTime:   time.Now(),
	}

	// 初始化Agent状态
	server.initAgentStats()

	return server
}

// initAgentStats 初始化Agent统计
func (s *AgentServer) initAgentStats() {
	agentTypes := []string{"xiaona", "xiaonuo", "yunxi"}

	for _, agentType := range agentTypes {
		s.agentStatus[agentType] = &AgentStats{
			AgentType:     agentType,
			IsHealthy:     true,
			CPUUsage:      0.0,
			MemoryUsage:   0.0,
			LastHeartbeat: time.Now(),
		}
	}
}

// ExecuteTask 执行任务（流式响应）
func (s *AgentServer) ExecuteTask(
	req *pb.TaskRequest,
	stream pb.AgentService_ExecuteTaskServer,
) error {
	taskID := req.TaskId
	agentType := req.AgentType
	scenario := req.Scenario

	logging.LogInfo("gRPC执行任务",
		logging.String("task_id", taskID),
		logging.String("agent_type", agentType),
		logging.String("scenario", scenario),
		logging.String("user_input", req.UserInput),
	)

	// 创建任务上下文
	ctx, cancel := context.WithCancel(stream.Context())
	taskCtx := &TaskContext{
		TaskID:    taskID,
		AgentType: agentType,
		Status:    "running",
		CreatedAt: time.Now(),
		CancelFunc: cancel,
	}

	s.tasksMutex.Lock()
	s.tasks[taskID] = taskCtx
	s.tasksMutex.Unlock()

	defer func() {
		s.tasksMutex.Lock()
		if taskCtx.Status == "running" {
			taskCtx.Status = "completed"
			now := time.Now()
			taskCtx.CompletedAt = &now
		}
		s.tasksMutex.Unlock()
	}()

	// 执行任务（模拟流式响应）
	return s.executeTaskStreaming(ctx, req, stream, taskCtx)
}

// executeTaskStreaming 流式执行任务
func (s *AgentServer) executeTaskStreaming(
	ctx context.Context,
	req *pb.TaskRequest,
	stream pb.AgentService_ExecuteTaskServer,
	taskCtx *TaskContext,
) error {
	// 根据scenario选择处理器
	handler := s.getTaskHandler(req.Scenario)
	if handler == nil {
		return status.Errorf(codes.InvalidArgument, "未知的场景类型: %s", req.Scenario)
	}

	// 执行任务
	return handler(ctx, req, stream, taskCtx)
}

// TaskHandler 任务处理器函数
type TaskHandler func(
	ctx context.Context,
	req *pb.TaskRequest,
	stream pb.AgentService_ExecuteTaskServer,
	taskCtx *TaskContext,
) error

// getTaskHandler 获取任务处理器
func (s *AgentServer) getTaskHandler(scenario string) TaskHandler {
	handlers := map[string]TaskHandler{
		"patent_search":       s.handlePatentSearch,
		"legal_analysis":      s.handleLegalAnalysis,
		"patent_analysis":      s.handlePatentAnalysis,
		"invalidation_analysis": s.handleInvalidationAnalysis,
		"task_coordination":    s.handleTaskCoordination,
		"workflow_execution":   s.handleWorkflowExecution,
	}

	return handlers[scenario]
}

// ==================== 任务处理器 ====================

// handlePatentSearch 专利检索处理器
func (s *AgentServer) handlePatentSearch(
	ctx context.Context,
	req *pb.TaskRequest,
	stream pb.AgentService_ExecuteTaskServer,
	taskCtx *TaskContext,
) error {
	stages := []struct {
		progress int32
		message  string
	}{
		{10, "正在解析检索需求"},
		{30, "正在构建检索式"},
		{50, "正在检索专利数据库"},
		{70, "正在筛选相关专利"},
		{90, "正在生成检索报告"},
		{100, "检索完成"},
	}

	for _, stage := range stages {
		select {
		case <-ctx.Done():
			logging.LogInfo("任务已取消", logging.String("task_id", req.TaskId))
			return status.Error(codes.Canceled, "任务已取消")
		default:
		}

		// 发送进度更新
		err := stream.Send(&pb.TaskResponse{
			TaskId:    req.TaskId,
			AgentType: req.AgentType,
			Type:      pb.ResponseType_PROGRESS,
			Timestamp: time.Now().UnixNano(),
			Payload: &pb.TaskResponse_Progress{
				Progress: &pb.ProgressUpdate{
					Percentage:  stage.progress,
					Message:     stage.message,
					CurrentStep: fmt.Sprintf("%d%%", stage.progress),
					TotalSteps:  100,
				},
			},
		})
		if err != nil {
			logging.LogError("发送进度失败", logging.Err(err))
			return err
		}

		// 模拟处理时间
		time.Sleep(500 * time.Millisecond)
	}

	// 发送最终结果
	taskCtx.Result = fmt.Sprintf("专利检索完成，找到 %d 篇相关专利", 15)
	taskCtx.Status = "completed"
	s.totalCompleted.Add(1)

	return stream.Send(&pb.TaskResponse{
		TaskId:    req.TaskId,
		AgentType: req.AgentType,
		Type:      pb.ResponseType_FINAL,
		Timestamp: time.Now().UnixNano(),
		Payload: &pb.TaskResponse_FinalResult{
			FinalResult: taskCtx.Result,
		},
	})
}

// handleLegalAnalysis 法律分析处理器
func (s *AgentServer) handleLegalAnalysis(
	ctx context.Context,
	req *pb.TaskRequest,
	stream pb.AgentService_ExecuteTaskServer,
	taskCtx *TaskContext,
) error {
	stages := []struct {
		progress int32
		message  string
	}{
		{10, "正在读取法律文献"},
		{30, "正在提取法律要点"},
		{50, "正在进行案例分析"},
		{70, "正在关联相关法条"},
		{90, "正在生成分析报告"},
		{100, "分析完成"},
	}

	for _, stage := range stages {
		select {
		case <-ctx.Done():
			return status.Error(codes.Canceled, "任务已取消")
		default:
		}

		err := stream.Send(&pb.TaskResponse{
			TaskId:    req.TaskId,
			AgentType: req.AgentType,
			Type:      pb.ResponseType_PROGRESS,
			Timestamp: time.Now().UnixNano(),
			Payload: &pb.TaskResponse_Progress{
				Progress: &pb.ProgressUpdate{
					Percentage: stage.progress,
					Message:    stage.message,
					TotalSteps: 100,
				},
			},
		})
		if err != nil {
			return err
		}

		time.Sleep(400 * time.Millisecond)
	}

	taskCtx.Result = "法律分析完成"
	taskCtx.Status = "completed"
	s.totalCompleted.Add(1)

	return stream.Send(&pb.TaskResponse{
		TaskId:    req.TaskId,
		AgentType: req.AgentType,
		Type:      pb.ResponseType_FINAL,
		Timestamp: time.Now().UnixNano(),
		Payload: &pb.TaskResponse_FinalResult{
			FinalResult: taskCtx.Result,
		},
	})
}

// handlePatentAnalysis 专利分析处理器
func (s *AgentServer) handlePatentAnalysis(
	ctx context.Context,
	req *pb.TaskRequest,
	stream pb.AgentService_ExecuteTaskServer,
	taskCtx *TaskContext,
) error {
	return s.handlePatentSearch(ctx, req, stream, taskCtx)
}

// handleInvalidationAnalysis 无效分析处理器
func (s *AgentServer) handleInvalidationAnalysis(
	ctx context.Context,
	req *pb.TaskRequest,
	stream pb.AgentService_ExecuteTaskServer,
	taskCtx *TaskContext,
) error {
	stages := []struct {
		progress int32
		message  string
	}{
		{10, "正在读取专利文献"},
		{30, "正在分析权利要求"},
		{50, "正在检索对比文件"},
		{70, "正在进行特征对比"},
		{90, "正在评估创造性"},
		{100, "分析完成"},
	}

	for _, stage := range stages {
		select {
		case <-ctx.Done():
			return status.Error(codes.Canceled, "任务已取消")
		default:
		}

		err := stream.Send(&pb.TaskResponse{
			TaskId:    req.TaskId,
			AgentType: req.AgentType,
			Type:      pb.ResponseType_PROGRESS,
			Timestamp: time.Now().UnixNano(),
			Payload: &pb.TaskResponse_Progress{
				Progress: &pb.ProgressUpdate{
					Percentage: stage.progress,
					Message:    stage.message,
					TotalSteps: 100,
				},
			},
		})
		if err != nil {
			return err
		}

		time.Sleep(450 * time.Millisecond)
	}

	taskCtx.Result = "无效分析完成"
	taskCtx.Status = "completed"
	s.totalCompleted.Add(1)

	return stream.Send(&pb.TaskResponse{
		TaskId:    req.TaskId,
		AgentType: req.AgentType,
		Type:      pb.ResponseType_FINAL,
		Timestamp: time.Now().UnixNano(),
		Payload: &pb.TaskResponse_FinalResult{
			FinalResult: taskCtx.Result,
		},
	})
}

// handleTaskCoordination 任务协调处理器
func (s *AgentServer) handleTaskCoordination(
	ctx context.Context,
	req *pb.TaskRequest,
	stream pb.AgentService_ExecuteTaskServer,
	taskCtx *TaskContext,
) error {
	stages := []struct {
		progress int32
		message  string
	}{
		{10, "正在分析任务需求"},
		{30, "正在选择执行Agent"},
		{50, "正在分派子任务"},
		{70, "正在收集执行结果"},
		{90, "正在整合结果"},
		{100, "协调完成"},
	}

	for _, stage := range stages {
		select {
		case <-ctx.Done():
			return status.Error(codes.Canceled, "任务已取消")
		default:
		}

		err := stream.Send(&pb.TaskResponse{
			TaskId:    req.TaskId,
			AgentType: req.AgentType,
			Type:      pb.ResponseType_PROGRESS,
			Timestamp: time.Now().UnixNano(),
			Payload: &pb.TaskResponse_Progress{
				Progress: &pb.ProgressUpdate{
					Percentage: stage.progress,
					Message:    stage.message,
					TotalSteps: 100,
				},
			},
		})
		if err != nil {
			return err
		}

		time.Sleep(350 * time.Millisecond)
	}

	taskCtx.Result = "任务协调完成"
	taskCtx.Status = "completed"
	s.totalCompleted.Add(1)

	return stream.Send(&pb.TaskResponse{
		TaskId:    req.TaskId,
		AgentType: req.AgentType,
		Type:      pb.ResponseType_FINAL,
		Timestamp: time.Now().UnixNano(),
		Payload: &pb.TaskResponse_FinalResult{
			FinalResult: taskCtx.Result,
		},
	})
}

// handleWorkflowExecution 工作流执行处理器
func (s *AgentServer) handleWorkflowExecution(
	ctx context.Context,
	req *pb.TaskRequest,
	stream pb.AgentService_ExecuteTaskServer,
	taskCtx *TaskContext,
) error {
	stages := []struct {
		progress int32
		message  string
		step     string
	}{
		{5, "正在加载工作流定义", "加载中"},
		{15, "正在初始化工作流上下文", "初始化"},
		{30, "正在执行第1阶段", "阶段1"},
		{50, "正在执行第2阶段", "阶段2"},
		{70, "正在执行第3阶段", "阶段3"},
		{85, "正在整合阶段结果", "整合"},
		{95, "正在生成最终输出", "输出"},
		{100, "工作流执行完成", "完成"},
	}

	for _, stage := range stages {
		select {
		case <-ctx.Done():
			return status.Error(codes.Canceled, "任务已取消")
		default:
		}

		err := stream.Send(&pb.TaskResponse{
			TaskId:    req.TaskId,
			AgentType: req.AgentType,
			Type:      pb.ResponseType_PROGRESS,
			Timestamp: time.Now().UnixNano(),
			Payload: &pb.TaskResponse_Progress{
				Progress: &pb.ProgressUpdate{
					Percentage:  stage.progress,
					Message:     stage.message,
					CurrentStep: stage.step,
					TotalSteps:  8,
				},
			},
		})
		if err != nil {
			return err
		}

		time.Sleep(400 * time.Millisecond)
	}

	taskCtx.Result = "工作流执行完成"
	taskCtx.Status = "completed"
	s.totalCompleted.Add(1)

	return stream.Send(&pb.TaskResponse{
		TaskId:    req.TaskId,
		AgentType: req.AgentType,
		Type:      pb.ResponseType_FINAL,
		Timestamp: time.Now().UnixNano(),
		Payload: &pb.TaskResponse_FinalResult{
			FinalResult: taskCtx.Result,
		},
	})
}

// GetAgentStatus 获取Agent状态
func (s *AgentServer) GetAgentStatus(
	ctx context.Context,
	req *pb.AgentStatusRequest,
) (*pb.AgentStatusResponse, error) {
	logging.LogInfo("gRPC获取Agent状态",
		logging.String("agent_type", req.AgentType),
	)

	s.statusMutex.RLock()
	stats, exists := s.agentStatus[req.AgentType]
	s.statusMutex.RUnlock()

	if !exists {
		return nil, status.Errorf(codes.NotFound, "未知的Agent类型: %s", req.AgentType)
	}

	// 获取当前任务数
	s.tasksMutex.RLock()
	var activeTaskIDs []string
	for _, task := range s.tasks {
		if task.AgentType == req.AgentType && task.Status == "running" {
			activeTaskIDs = append(activeTaskIDs, task.TaskID)
		}
	}
	s.tasksMutex.RUnlock()

	return &pb.AgentStatusResponse{
		AgentType:      req.AgentType,
		IsHealthy:      stats.IsHealthy,
		Status:         "idle",
		CurrentTasks:   int32(len(activeTaskIDs)),
		TotalCompleted: s.totalCompleted.Load(),
		TotalFailed:    s.totalFailed.Load(),
		CpuUsage:       stats.CPUUsage,
		MemoryUsage:    stats.MemoryUsage,
		UptimeSeconds:  int64(time.Since(s.startTime).Seconds()),
		ActiveTaskIds:  activeTaskIDs,
	}, nil
}

// Heartbeat 心跳
func (s *AgentServer) Heartbeat(
	ctx context.Context,
	req *pb.HeartbeatRequest,
) (*pb.HeartbeatResponse, error) {
	logging.LogDebug("gRPC心跳",
		logging.String("agent_type", req.AgentType),
	)

	// 更新最后心跳时间
	s.statusMutex.Lock()
	if stats, exists := s.agentStatus[req.AgentType]; exists {
		stats.LastHeartbeat = time.Now()
		stats.IsHealthy = true
	}
	s.statusMutex.Unlock()

	return &pb.HeartbeatResponse{
		Status:    "ok",
		Timestamp: time.Now().UnixNano(),
		Metadata:  req.Metadata,
	}, nil
}

// ExecuteBatch 批量执行任务
func (s *AgentServer) ExecuteBatch(
	req *pb.BatchRequest,
	stream pb.AgentService_ExecuteBatchServer,
) error {
	batchID := fmt.Sprintf("batch_%d", time.Now().UnixNano())

	logging.LogInfo("gRPC批量执行",
		logging.String("batch_id", batchID),
		logging.Int("task_count", len(req.Tasks)),
		logging.Int("concurrency", int(req.Concurrency)),
	)

	// 简化实现：直接发送批量响应
	for i, task := range req.Tasks {
		select {
		case <-stream.Context().Done():
			return status.Error(codes.Canceled, "批量任务已取消")
		default:
		}

		// 发送进度更新
		err := stream.Send(&pb.BatchResponse{
			BatchId: batchID,
			TaskId:  task.TaskId,
			Type:    pb.ResponseType_PROGRESS,
			Payload: &pb.BatchResponse_FinalResult{
				FinalResult: fmt.Sprintf("批量任务 %d/%d 处理中", i+1, len(req.Tasks)),
			},
		})
		if err != nil {
			return err
		}

		// 模拟处理时间
		time.Sleep(100 * time.Millisecond)
	}

	// 发送完成响应
	return stream.Send(&pb.BatchResponse{
		BatchId: batchID,
		TaskId:  "",
		Type:    pb.ResponseType_FINAL,
		Payload: &pb.BatchResponse_FinalResult{
			FinalResult: fmt.Sprintf("批量任务完成，共 %d 个任务", len(req.Tasks)),
		},
	})
}

// CancelTask 取消任务
func (s *AgentServer) CancelTask(
	ctx context.Context,
	req *pb.CancelRequest,
) (*pb.CancelResponse, error) {
	logging.LogInfo("gRPC取消任务",
		logging.String("task_id", req.TaskId),
		logging.String("reason", req.Reason),
	)

	s.tasksMutex.Lock()
	task, exists := s.tasks[req.TaskId]
	if exists {
		task.Status = "cancelled"
		if task.CancelFunc != nil {
			task.CancelFunc()
		}
	}
	s.tasksMutex.Unlock()

	if !exists {
		return &pb.CancelResponse{
			TaskId:  req.TaskId,
			Success: false,
			Message: "任务不存在",
		}, nil
	}

	return &pb.CancelResponse{
		TaskId:  req.TaskId,
		Success: true,
		Message: "任务已取消",
	}, nil
}
