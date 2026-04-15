package tracing

import (
	"context"
	"fmt"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/propagation"
	"go.opentelemetry.io/otel/sdk/resource"
	otelsdktrace "go.opentelemetry.io/otel/sdk/trace"
	semconv "go.opentelemetry.io/otel/semconv/v1.21.0"
	"go.opentelemetry.io/otel/trace"
)

type Tracer struct {
	provider *otelsdktrace.TracerProvider
	tracer   trace.Tracer
}

func NewTracer(cfg Config) (*Tracer, error) {
	if !cfg.Enabled {
		return &Tracer{}, nil
	}

	res, err := newResource(cfg)
	if err != nil {
		return nil, fmt.Errorf("failed to create resource: %w", err)
	}

	exporter, err := newExporter(cfg.Jaeger)
	if err != nil {
		return nil, fmt.Errorf("failed to create exporter: %w", err)
	}

	sampler, err := newSampler(cfg.Sampling)
	if err != nil {
		return nil, fmt.Errorf("failed to create sampler: %w", err)
	}

	provider := otelsdktrace.NewTracerProvider(
		otelsdktrace.WithBatcher(exporter,
			otelsdktrace.WithBatchTimeout(cfg.BatchTimeout),
			otelsdktrace.WithMaxExportBatchSize(cfg.MaxExportBatchSize),
		),
		otelsdktrace.WithResource(res),
		otelsdktrace.WithSampler(sampler),
	)

	otel.SetTracerProvider(provider)
	otel.SetTextMapPropagator(propagation.NewCompositeTextMapPropagator(
		propagation.TraceContext{},
		propagation.Baggage{},
	))

	tracer := provider.Tracer(
		cfg.ServiceName,
		trace.WithInstrumentationVersion(cfg.ServiceVersion),
	)

	return &Tracer{
		provider: provider,
		tracer:   tracer,
	}, nil
}

func (t *Tracer) Tracer() trace.Tracer {
	return t.tracer
}

func (t *Tracer) Shutdown(ctx context.Context) error {
	if t.provider != nil {
		return t.provider.Shutdown(ctx)
	}
	return nil
}

func newResource(cfg Config) (*resource.Resource, error) {
	return resource.NewWithAttributes(
		semconv.SchemaURL,
		semconv.ServiceNameKey.String(cfg.ServiceName),
		semconv.ServiceVersionKey.String(cfg.ServiceVersion),
		semconv.DeploymentEnvironmentKey.String(cfg.Environment),
		semconv.TelemetrySDKNameKey.String("opentelemetry"),
		semconv.TelemetrySDKLanguageKey.String("go"),
	), nil
}

func (t *Tracer) StartSpan(ctx context.Context, name string, opts ...trace.SpanStartOption) (context.Context, trace.Span) {
	return t.tracer.Start(ctx, name, opts...)
}
