package monitoring

import (
	"github.com/athena-workspace/core/gateway/internal/config"
	"github.com/athena-workspace/core/gateway/pkg/metrics"
)

var prometheusMetrics *metrics.PrometheusMetrics

func Init(cfg config.MonitoringConfig) {
	if cfg.Prometheus.Enabled {
		prometheusMetrics = metrics.NewPrometheusMetrics()
	}
}

func GetPrometheusMetrics() *metrics.PrometheusMetrics {
	return prometheusMetrics
}
