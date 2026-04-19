// Package tracing - OpenTelemetry追踪器测试
package tracing

import (
	"context"
	"testing"
)

// TestDefaultConfig 测试默认配置
func TestDefaultConfig(t *testing.T) {
	cfg := DefaultConfig()

	if cfg.ServiceName != "athena-gateway" {
		t.Errorf("期望服务名为 'athena-gateway'，实际为 '%s'", cfg.ServiceName)
	}

	if cfg.ServiceVersion != "1.0.0" {
		t.Errorf("期望服务版本为 '1.0.0'，实际为 '%s'", cfg.ServiceVersion)
	}

	if !cfg.Enabled {
		t.Error("期望追踪默认启用")
	}

	if cfg.Sampling.Type != "probabilistic" {
		t.Errorf("期望采样类型为 'probabilistic'，实际为 '%s'", cfg.Sampling.Type)
	}

	if cfg.Sampling.Param != 0.1 {
		t.Errorf("期望采样参数为 0.1，实际为 %f", cfg.Sampling.Param)
	}
}

// TestDevelopmentConfig 测试开发环境配置
func TestDevelopmentConfig(t *testing.T) {
	cfg := DevelopmentConfig()

	if cfg.Environment != "development" {
		t.Errorf("期望环境为 'development'，实际为 '%s'", cfg.Environment)
	}

	if cfg.Sampling.Param != 1.0 {
		t.Errorf("开发环境期望100%%采样，实际为 %f", cfg.Sampling.Param)
	}
}

// TestProductionConfig 测试生产环境配置
func TestProductionConfig(t *testing.T) {
	cfg := ProductionConfig()

	if cfg.Environment != "production" {
		t.Errorf("期望环境为 'production'，实际为 '%s'", cfg.Environment)
	}

	if cfg.Sampling.Param != 0.1 {
		t.Errorf("生产环境期望10%%采样，实际为 %f", cfg.Sampling.Param)
	}

	if cfg.Jaeger.Endpoint != "http://jaeger:14268/api/traces" {
		t.Errorf("期望Jaeger端点为 'http://jaeger:14268/api/traces'，实际为 '%s'", cfg.Jaeger.Endpoint)
	}
}

// TestNewTracerDisabled 测试禁用追踪器
func TestNewTracerDisabled(t *testing.T) {
	cfg := Config{
		ServiceName: "test-service",
		Enabled:     false,
	}

	tracer, err := NewTracer(cfg)
	if err != nil {
		t.Fatalf("创建禁用追踪器失败: %v", err)
	}

	if tracer == nil {
		t.Fatal("追踪器不应为nil")
	}

	if tracer.IsEnabled() {
		t.Error("禁用的追踪器应返回false")
	}
}

// TestNewTracerEnabled 测试启用追踪器
func TestNewTracerEnabled(t *testing.T) {
	cfg := Config{
		ServiceName: "test-service",
		Enabled:     true,
		Jaeger: JaegerConfig{
			Endpoint: "http://localhost:14268/api/traces",
			Insecure: true,
		},
		Sampling: SamplingConfig{
			Type:  "always_on",
			Param: 1.0,
		},
	}

	tracer, err := NewTracer(cfg)
	if err != nil {
		t.Fatalf("创建追踪器失败: %v", err)
	}

	if tracer == nil {
		t.Fatal("追踪器不应为nil")
	}

	// 注意：由于没有实际的Jaeger服务，我们主要测试创建过程
	// 在实际环境中应该有可用的OTLP collector
}

// TestTracerStartSpan 测试启动span
func TestTracerStartSpan(t *testing.T) {
	cfg := Config{
		ServiceName: "test-service",
		Enabled:     false, // 禁用以避免实际连接
	}

	tracer, _ := NewTracer(cfg)
	ctx := context.Background()

	ctx, span := tracer.StartSpan(ctx, "test-operation")

	if span == nil {
		t.Fatal("span不应为nil")
	}

	span.End()
}

// TestWithSpan 测试WithSpan辅助函数
func TestWithSpan(t *testing.T) {
	cfg := Config{
		ServiceName: "test-service",
		Enabled:     false,
	}

	tracer, _ := NewTracer(cfg)
	ctx := context.Background()

	executed := false
	err := WithSpan(ctx, tracer, "test-operation", func(ctx context.Context) error {
		executed = true
		return nil
	})

	if err != nil {
		t.Errorf("WithSpan执行失败: %v", err)
	}

	if !executed {
		t.Error("WithSpan未执行提供的函数")
	}
}

// TestAddEvent 测试添加事件
func TestAddEvent(t *testing.T) {
	cfg := Config{
		ServiceName: "test-service",
		Enabled:     false,
	}

	tracer, _ := NewTracer(cfg)
	ctx := context.Background()

	ctx, span := tracer.StartSpan(ctx, "test-operation")
	AddEvent(span, "test-event")
	span.End()

	// 如果没有panic，则测试通过
}

// TestSetError 测试设置错误
func TestSetError(t *testing.T) {
	cfg := Config{
		ServiceName: "test-service",
		Enabled:     false,
	}

	tracer, _ := NewTracer(cfg)
	ctx := context.Background()

	ctx, span := tracer.StartSpan(ctx, "test-operation")
	testErr := &testError{msg: "test error"}
	SetError(span, testErr)
	span.End()

	// 如果没有panic，则测试通过
}

// TestGetConfig 测试获取配置
func TestGetConfig(t *testing.T) {
	expectedCfg := Config{
		ServiceName: "test-service",
		Enabled:     true,
		Sampling: SamplingConfig{
			Type: "probabilistic",
			Param: 0.5,
		},
	}

	tracer, err := NewTracer(expectedCfg)
	if err != nil {
		t.Fatalf("创建追踪器失败: %v", err)
	}

	actualCfg := tracer.GetConfig()
	if actualCfg.ServiceName != expectedCfg.ServiceName {
		t.Errorf("配置不匹配")
	}
}

// TestShutdown 测试关闭追踪器
func TestShutdown(t *testing.T) {
	cfg := Config{
		ServiceName: "test-service",
		Enabled:     false,
	}

	tracer, _ := NewTracer(cfg)
	ctx := context.Background()

	err := tracer.Shutdown(ctx)
	if err != nil {
		t.Errorf("关闭追踪器失败: %v", err)
	}
}

// BenchmarkStartSpan 性能测试
func BenchmarkStartSpan(b *testing.B) {
	cfg := Config{
		ServiceName: "test-service",
		Enabled:     false,
	}

	tracer, _ := NewTracer(cfg)
	ctx := context.Background()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, span := tracer.StartSpan(ctx, "test-operation")
		span.End()
	}
}

// 测试用的错误类型
type testError struct {
	msg string
}

func (e *testError) Error() string {
	return e.msg
}
