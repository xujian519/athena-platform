// Package tracing - OpenTelemetry追踪器核心实现
package tracing

import (
	"context"
	"fmt"

	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/codes"
	"go.opentelemetry.io/otel/propagation"
	"go.opentelemetry.io/otel/sdk/resource"
	otelsdktrace "go.opentelemetry.io/otel/sdk/trace"
	semconv "go.opentelemetry.io/otel/semconv/v1.26.0"
	"go.opentelemetry.io/otel/trace"
)

// Tracer OpenTelemetry追踪器
// 封装了TracerProvider和Tracer，提供统一的追踪接口
type Tracer struct {
	provider *otelsdktrace.TracerProvider
	tracer   trace.Tracer
	config   Config
}

// NewTracer 创建新的追踪器
// 根据配置初始化OpenTelemetry追踪器，包括：
// - 资源标识（服务名、版本、环境）
// - 导出器（OTLP HTTP）
// - 采样器
// - 全局传播器配置
func NewTracer(cfg Config) (*Tracer, error) {
	if !cfg.Enabled {
		return &Tracer{
			config: cfg,
		}, nil
	}

	// 创建资源标识
	res := newResource(cfg)

	// 创建导出器
	exporter, err := newExporter(cfg.Jaeger)
	if err != nil {
		return nil, fmt.Errorf("failed to create exporter: %w", err)
	}

	// 创建采样器
	sampler := newSampler(cfg.Sampling)

	// 创建TracerProvider
	provider := otelsdktrace.NewTracerProvider(
		otelsdktrace.WithBatcher(exporter,
			otelsdktrace.WithBatchTimeout(cfg.BatchTimeout),
			otelsdktrace.WithMaxExportBatchSize(cfg.MaxExportBatchSize),
			otelsdktrace.WithExportTimeout(cfg.ExportTimeout),
		),
		otelsdktrace.WithResource(res),
		otelsdktrace.WithSampler(sampler),
	)

	// 设置全局TracerProvider和传播器
	otel.SetTracerProvider(provider)
	otel.SetTextMapPropagator(propagation.NewCompositeTextMapPropagator(
		propagation.TraceContext{},
		propagation.Baggage{},
	))

	// 创建Tracer
	tracer := provider.Tracer(
		cfg.ServiceName,
		trace.WithInstrumentationVersion(cfg.ServiceVersion),
		trace.WithSchemaURL(semconv.SchemaURL),
	)

	return &Tracer{
		provider: provider,
		tracer:   tracer,
		config:   cfg,
	}, nil
}

// Tracer 返回底层的OpenTelemetry Tracer
func (t *Tracer) Tracer() trace.Tracer {
	return t.tracer
}

// Shutdown 优雅关闭追踪器
// 刷新所有待导出的span并关闭连接
func (t *Tracer) Shutdown(ctx context.Context) error {
	if t.provider != nil {
		return t.provider.Shutdown(ctx)
	}
	return nil
}

// StartSpan 启动一个新的span
// 返回包含新span的context和span对象
func (t *Tracer) StartSpan(ctx context.Context, name string, opts ...trace.SpanStartOption) (context.Context, trace.Span) {
	if t.tracer == nil {
		// 如果追踪器未启用，返回 noop span
		return ctx, trace.SpanFromContext(ctx)
	}
	return t.tracer.Start(ctx, name, opts...)
}

// IsEnabled 检查追踪器是否启用
func (t *Tracer) IsEnabled() bool {
	return t.config.Enabled && t.provider != nil
}

// GetConfig 获取当前配置
func (t *Tracer) GetConfig() Config {
	return t.config
}

// newResource 创建OpenTelemetry资源
// 包含服务的标识信息和SDK元数据
func newResource(cfg Config) *resource.Resource {
	attrs := []attribute.KeyValue{
		semconv.ServiceName(cfg.ServiceName),
		semconv.ServiceVersion(cfg.ServiceVersion),
		semconv.DeploymentEnvironment(cfg.Environment),
		semconv.TelemetrySDKName("opentelemetry"),
		semconv.TelemetrySDKLanguageKey.String("go"),
		semconv.TelemetrySDKVersion("1.26.0"),
	}

	return resource.NewWithAttributes(
		semconv.SchemaURL,
		attrs...,
	)
}

// Helper functions for common tracing patterns

// WithSpan 在函数中使用span的辅助函数
func WithSpan(ctx context.Context, tracer *Tracer, name string, fn func(context.Context) error) error {
	if !tracer.IsEnabled() {
		return fn(ctx)
	}

	ctx, span := tracer.StartSpan(ctx, name)
	defer span.End()

	if err := fn(ctx); err != nil {
		span.RecordError(err)
		span.SetStatus(codes.Error, err.Error())
		return err
	}

	span.SetStatus(codes.Ok, "")
	return nil
}

// AddEvent 添加事件到当前span
func AddEvent(span trace.Span, name string, attrs ...trace.EventOption) {
	span.AddEvent(name, attrs...)
}

// SetError 设置错误到当前span
func SetError(span trace.Span, err error) {
	if err != nil {
		span.RecordError(err)
		span.SetStatus(codes.Error, err.Error())
	}
}
