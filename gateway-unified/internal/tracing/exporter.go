// Package tracing - 导出器和采样器实现
package tracing

import (
	"context"

	otlptracehttp "go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp"
	otelsdktrace "go.opentelemetry.io/otel/sdk/trace"
)

// newExporter 创建OTLP HTTP追踪导出器
// 根据JaegerConfig配置创建安全的或不安全的HTTP导出器
func newExporter(cfg JaegerConfig) (otelsdktrace.SpanExporter, error) {
	opts := []otlptracehttp.Option{
		otlptracehttp.WithEndpoint(cfg.Endpoint),
	}

	// 如果配置了用户名和密码，添加基本认证
	if cfg.Username != "" && cfg.Password != "" {
		opts = append(opts, otlptracehttp.WithHeaders(map[string]string{
			"Authorization": "Basic " + basicAuth(cfg.Username, cfg.Password),
		}))
	}

	if cfg.Insecure {
		opts = append(opts, otlptracehttp.WithInsecure())
	}

	return otlptracehttp.New(context.Background(), opts...)
}

// newSampler 根据配置创建采样器
// 支持多种采样策略：
// - always_on: 始终采样
// - always_off: 从不采样
// - probabilistic: 基于概率采样
// - parentbased_always_on: 基于父span的always_on
// - parentbased_always_off: 基于父span的always_off
// - parentbased_probabilistic: 基于父span的概率采样
func newSampler(cfg SamplingConfig) otelsdktrace.Sampler {
	switch cfg.Type {
	case "always_on":
		return otelsdktrace.AlwaysSample()
	case "always_off":
		return otelsdktrace.NeverSample()
	case "probabilistic":
		return otelsdktrace.TraceIDRatioBased(cfg.Param)
	case "parentbased_always_on":
		return otelsdktrace.ParentBased(otelsdktrace.AlwaysSample())
	case "parentbased_always_off":
		return otelsdktrace.ParentBased(otelsdktrace.NeverSample())
	case "parentbased_probabilistic":
		return otelsdktrace.ParentBased(otelsdktrace.TraceIDRatioBased(cfg.Param))
	default:
		// 默认使用10%采样率
		return otelsdktrace.TraceIDRatioBased(0.1)
	}
}

// basicAuth 生成基本认证字符串（简化版，生产环境应使用更安全的方式）
func basicAuth(username, password string) string {
	// TODO: 使用标准库的encoding/base64进行编码
	return username + ":" + password
}
