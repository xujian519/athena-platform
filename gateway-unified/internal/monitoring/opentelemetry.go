package monitoring

import (
	"context"
	"fmt"

	"github.com/athena-workspace/gateway-unified/internal/config"
	"github.com/athena-workspace/gateway-unified/internal/logging"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp"
	"go.opentelemetry.io/otel/propagation"
	"go.opentelemetry.io/otel/sdk/resource"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	semconv "go.opentelemetry.io/otel/semconv/v1.4.0"
	"go.opentelemetry.io/otel/trace"
)

var (
	tracer trace.Tracer
)

// InitOpenTelemetry 初始化OpenTelemetry
func InitOpenTelemetry(cfg config.MonitoringConfig) (trace.Tracer, error) {
	// 默认配置
	serviceName := "gateway-unified"
	collectorEndpoint := "http://localhost:4318" // 默认OTLP HTTP端点
	sampleRatio := 0.1                           // 默认10%采样

	// 创建资源
	res, err := resource.New(
		context.Background(),
		resource.WithAttributes(
			semconv.ServiceNameKey.String(serviceName),
			semconv.ServiceVersionKey.String("1.0.0"),
		),
	)
	if err != nil {
		return nil, fmt.Errorf("创建资源失败: %w", err)
	}

	// 创建OTLP HTTP exporter
	exporter, err := otlptracehttp.New(
		context.Background(),
		otlptracehttp.WithEndpoint(collectorEndpoint),
		otlptracehttp.WithInsecure(),
	)
	if err != nil {
		return nil, fmt.Errorf("创建OTLP exporter失败: %w", err)
	}

	// 创建基于采样率的Trace Provider
	tp := sdktrace.NewTracerProvider(
		sdktrace.WithBatcher(exporter),
		sdktrace.WithResource(res),
		sdktrace.WithSampler(sdktrace.TraceIDRatioBased(sampleRatio)),
	)

	// 设置全局TracerProvider
	otel.SetTracerProvider(tp)

	// 设置全局Propagators（支持HTTP和gRPC）
	otel.SetTextMapPropagator(propagation.NewCompositeTextMapPropagator(
		propagation.TraceContext{},
		propagation.Baggage{},
	))

	// 创建全局Tracer
	tracer = otel.Tracer(serviceName)

	logging.LogInfo("OpenTelemetry初始化成功",
		logging.String("collector", collectorEndpoint),
		logging.String("sample_ratio", fmt.Sprintf("%.0f%%", sampleRatio*100)),
	)

	return tracer, nil
}

// GetTracer 获取全局Tracer
func GetTracer() trace.Tracer {
	if tracer == nil {
		// 如果未初始化，返回noop tracer
		return otel.GetTracerProvider().Tracer("gateway-unified")
	}
	return tracer
}

// ShutdownOpenTelemetry 关闭OpenTelemetry
func ShutdownOpenTelemetry(ctx context.Context) error {
	if tp, ok := otel.GetTracerProvider().(*sdktrace.TracerProvider); ok {
		if err := tp.Shutdown(ctx); err != nil {
			return err
		}
		logging.LogInfo("OpenTelemetry已关闭")
	}
	return nil
}
