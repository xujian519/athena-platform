package tracing

import (
	"context"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp"
	otelsdktrace "go.opentelemetry.io/otel/sdk/trace"
)

func newExporter(cfg JaegerConfig) (otelsdktrace.SpanExporter, error) {
	if cfg.Insecure {
		return otlptracehttp.New(context.Background(),
			otlptracehttp.WithEndpoint(cfg.Endpoint),
			otlptracehttp.WithInsecure(),
		)
	}
	return otlptracehttp.New(context.Background(),
		otlptracehttp.WithEndpoint(cfg.Endpoint),
	)
}

func newSampler(cfg SamplingConfig) (otelsdktrace.Sampler, error) {
	switch cfg.Type {
	case "always_on":
		return otelsdktrace.AlwaysSample(), nil
	case "always_off":
		return otelsdktrace.NeverSample(), nil
	case "probabilistic":
		return otelsdktrace.TraceIDRatioBased(cfg.Param), nil
	case "parentbased_always_on":
		return otelsdktrace.ParentBased(otelsdktrace.AlwaysSample()), nil
	case "parentbased_always_off":
		return otelsdktrace.ParentBased(otelsdktrace.NeverSample()), nil
	case "parentbased_probabilistic":
		return otelsdktrace.ParentBased(otelsdktrace.TraceIDRatioBased(cfg.Param)), nil
	default:
		return otelsdktrace.TraceIDRatioBased(0.1), nil
	}
}
