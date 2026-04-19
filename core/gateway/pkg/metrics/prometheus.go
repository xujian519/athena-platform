package metrics

import (
	"net/http"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

type PrometheusMetrics struct {
	systemCollector *SystemMetricsCollector
}

func NewPrometheusMetrics() *PrometheusMetrics {
	return &PrometheusMetrics{
		systemCollector: NewSystemMetricsCollector(),
	}
}

func (p *PrometheusMetrics) Handler() http.Handler {
	return promhttp.Handler()
}

func (p *PrometheusMetrics) RegisterCustomMetrics() {
}

func (p *PrometheusMetrics) Shutdown() {
	if p.systemCollector != nil {
		p.systemCollector.Stop()
	}
}

func MustRegister(collector ...prometheus.Collector) {
	prometheus.MustRegister(collector...)
}

func NewRegistry() *prometheus.Registry {
	return prometheus.NewRegistry()
}
