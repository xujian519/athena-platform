package health

import (
	"context"
	"fmt"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

// TestNewChecker 测试创建健康检查器
func TestNewChecker(t *testing.T) {
	checker := NewChecker()
	if checker == nil {
		t.Fatal("NewChecker() returned nil")
	}
	if len(checker.checks) != 0 {
		t.Errorf("新建检查器应该没有检查，但有 %d 个", len(checker.checks))
	}
}

// TestRegisterUnregister 测试注册和注销
func TestRegisterUnregister(t *testing.T) {
	checker := NewChecker()

	// 创建测试检查
	check := NewCustomCheck("test", func(ctx context.Context) *CheckResult {
		return &CheckResult{Name: "test", Status: StatusUp}
	})

	// 注册
	checker.Register(check)
	if len(checker.checks) != 1 {
		t.Errorf("注册后应该有1个检查，但有 %d 个", len(checker.checks))
	}

	// 注销
	checker.Unregister("test")
	if len(checker.checks) != 0 {
		t.Errorf("注销后应该有0个检查，但有 %d 个", len(checker.checks))
	}
}

// TestCheck 测试执行健康检查
func TestCheck(t *testing.T) {
	checker := NewChecker()

	// 添加一些测试检查
	checker.Register(NewCustomCheck("check1", func(ctx context.Context) *CheckResult {
		return &CheckResult{Name: "check1", Status: StatusUp, Message: "OK"}
	}))
	checker.Register(NewCustomCheck("check2", func(ctx context.Context) *CheckResult {
		return &CheckResult{Name: "check2", Status: StatusDown, Message: "Failed"}
	}))
	checker.Register(NewCustomCheck("check3", func(ctx context.Context) *CheckResult {
		return &CheckResult{Name: "check3", Status: StatusDegraded, Message: "Slow"}
	}))

	// 执行检查
	ctx := context.Background()
	results := checker.Check(ctx)

	if len(results) != 3 {
		t.Errorf("应该返回3个结果，但有 %d 个", len(results))
	}

	// 验证结果
	if results["check1"].Status != StatusUp {
		t.Errorf("check1 状态 = %s, want UP", results["check1"].Status)
	}
	if results["check2"].Status != StatusDown {
		t.Errorf("check2 状态 = %s, want DOWN", results["check2"].Status)
	}
	if results["check3"].Status != StatusDegraded {
		t.Errorf("check3 状态 = %s, want DEGRADED", results["check3"].Status)
	}
}

// TestGetOverallStatus 测试整体状态计算
func TestGetOverallStatus(t *testing.T) {
	checker := NewChecker()

	tests := []struct {
		name     string
		results  map[string]*CheckResult
		expected HealthStatus
	}{
		{
			name:     "全部UP",
			results:  map[string]*CheckResult{"a": {Status: StatusUp}, "b": {Status: StatusUp}},
			expected: StatusUp,
		},
		{
			name:     "有DOWN",
			results:  map[string]*CheckResult{"a": {Status: StatusUp}, "b": {Status: StatusDown}},
			expected: StatusDown,
		},
		{
			name:     "有DEGRADED",
			results:  map[string]*CheckResult{"a": {Status: StatusUp}, "b": {Status: StatusDegraded}},
			expected: StatusDegraded,
		},
		{
			name:     "DOWN优先",
			results:  map[string]*CheckResult{"a": {Status: StatusDegraded}, "b": {Status: StatusDown}},
			expected: StatusDown,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			status := checker.GetOverallStatus(tt.results)
			if status != tt.expected {
				t.Errorf("GetOverallStatus() = %s, want %s", status, tt.expected)
			}
		})
	}
}

// TestHTTPCheck 测试HTTP健康检查
func TestHTTPCheck(t *testing.T) {
	// 创建测试服务器
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("OK"))
	}))
	defer server.Close()

	// 创建健康检查
	check := NewHTTPCheck("test-api", server.URL, http.StatusOK)

	result := check.Check(context.Background())

	if result.Name != "test-api" {
		t.Errorf("Name = %s, want test-api", result.Name)
	}
	if result.Status != StatusUp {
		t.Errorf("Status = %s, want UP", result.Status)
	}
	if result.Message != "OK" {
		t.Errorf("Message = %s, want OK", result.Message)
	}
}

// TestHTTPCheckFailure 测试HTTP健康检查失败场景
func TestHTTPCheckFailure(t *testing.T) {
	// 创建返回错误状态码的测试服务器
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
	}))
	defer server.Close()

	check := NewHTTPCheck("test-api", server.URL, http.StatusOK)
	result := check.Check(context.Background())

	if result.Status != StatusDown {
		t.Errorf("Status = %s, want DOWN", result.Status)
	}
}

// TestCustomCheck 测试自定义健康检查
func TestCustomCheck(t *testing.T) {
	called := false
	check := NewCustomCheck("custom", func(ctx context.Context) *CheckResult {
		called = true
		return &CheckResult{
			Name:    "custom",
			Status:  StatusUp,
			Message: "Custom check passed",
		}
	})

	result := check.Check(context.Background())

	if !called {
		t.Error("自定义检查函数未被调用")
	}
	if result.Status != StatusUp {
		t.Errorf("Status = %s, want UP", result.Status)
	}
	if result.Message != "Custom check passed" {
		t.Errorf("Message = %s, want 'Custom check passed'", result.Message)
	}
}

// TestCheckTimeout 测试检查超时
func TestCheckTimeout(t *testing.T) {
	checker := NewChecker()
	checker.SetTimeout(100 * time.Millisecond)

	// 添加一个会超时的检查
	slowCheck := NewCustomCheck("slow", func(ctx context.Context) *CheckResult {
		select {
		case <-ctx.Done():
			return &CheckResult{Name: "slow", Status: StatusDown, Message: "Timeout"}
		case <-time.After(1 * time.Second):
			return &CheckResult{Name: "slow", Status: StatusUp}
		}
	})

	checker.Register(slowCheck)

	results := checker.Check(context.Background())

	if len(results) != 1 {
		t.Fatalf("应该返回1个结果，但有 %d 个", len(results))
	}

	result := results["slow"]
	if result.Status != StatusDown {
		t.Errorf("超时检查状态 = %s, want DOWN", result.Status)
	}
}

// TestConcurrentChecks 测试并发检查
func TestConcurrentChecks(t *testing.T) {
	checker := NewChecker()

	// 添加多个并发检查
	for i := 0; i < 10; i++ {
		idx := i
		check := NewCustomCheck(fmt.Sprintf("check-%d", idx), func(ctx context.Context) *CheckResult {
			time.Sleep(10 * time.Millisecond)
			return &CheckResult{
				Name:   fmt.Sprintf("check-%d", idx),
				Status: StatusUp,
			}
		})
		checker.Register(check)
	}

	start := time.Now()
	results := checker.Check(context.Background())
	duration := time.Since(start)

	if len(results) != 10 {
		t.Errorf("应该返回10个结果，但有 %d 个", len(results))
	}

	// 并发执行应该比串行快
	// 串行需要 10 * 10ms = 100ms，并发应该接近 10ms
	if duration > 50*time.Millisecond {
		t.Logf("警告: 并发检查耗时 %v，可能未正确并发执行", duration)
	}
}

// TestEmptyChecker 测试空检查器
func TestEmptyChecker(t *testing.T) {
	checker := NewChecker()

	results := checker.Check(context.Background())

	if len(results) != 0 {
		t.Errorf("空检查器应该返回0个结果，但有 %d 个", len(results))
	}

	status := checker.GetOverallStatus(results)
	if status != StatusUp {
		t.Errorf("空检查器状态应该是UP，但是 %s", status)
	}
}
