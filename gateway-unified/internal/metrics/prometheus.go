// Package metrics - Prometheus增强功能
// 提供自定义指标注册、独立registry等功能
package metrics

import (
	"net/http"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

// PrometheusMetrics Prometheus指标管理器
type PrometheusMetrics struct {
	systemCollector *SystemMetricsCollector
	registry        prometheus.Gatherer
	registerer      prometheus.Registerer
}

// NewPrometheusMetrics 创建Prometheus指标管理器
func NewPrometheusMetrics() *PrometheusMetrics {
	// 使用默认的registry
	return &PrometheusMetrics{
		systemCollector: NewSystemMetricsCollector(),
		registry:        prometheus.DefaultGatherer,
		registerer:      prometheus.DefaultRegisterer,
	}
}

// NewPrometheusMetricsWithRegistry 使用指定registry创建Prometheus指标管理器
func NewPrometheusMetricsWithRegistry(registry *prometheus.Registry) *PrometheusMetrics {
	return &PrometheusMetrics{
		systemCollector: NewSystemMetricsCollector(),
		registry:        registry,
		registerer:      registry,
	}
}

// Start 启动系统指标收集
func (p *PrometheusMetrics) Start() {
	p.systemCollector.Start()
}

// Stop 停止系统指标收集
func (p *PrometheusMetrics) Stop() {
	p.systemCollector.Stop()
}

// Handler 返回Prometheus指标HTTP处理器
func (p *PrometheusMetrics) Handler() http.Handler {
	return promhttp.HandlerFor(p.registry, promhttp.HandlerOpts{
		EnableOpenMetrics: true,
	})
}

// HandlerForRegistry 返回指定registry的HTTP处理器
func HandlerForRegistry(registry prometheus.Gatherer) http.Handler {
	return promhttp.HandlerFor(registry, promhttp.HandlerOpts{
		EnableOpenMetrics: true,
	})
}

// RegisterCustomMetrics 注册自定义指标收集器
func (p *PrometheusMetrics) RegisterCustomMetrics(collector ...prometheus.Collector) error {
	for _, c := range collector {
		if err := p.registerer.Register(c); err != nil {
			return err
		}
	}
	return nil
}

// MustRegister 注册自定义指标，失败时panic
func (p *PrometheusMetrics) MustRegister(collector ...prometheus.Collector) {
	p.registerer.MustRegister(collector...)
}

// GetRegistry 获取当前registry
func (p *PrometheusMetrics) GetRegistry() prometheus.Gatherer {
	return p.registry
}

// GetRegisterer 获取当前registerer
func (p *PrometheusMetrics) GetRegisterer() prometheus.Registerer {
	return p.registerer
}

// ==================== 全局辅助函数 ====================

// MustRegister 注册自定义指标到默认registry，失败时panic
func MustRegister(collector ...prometheus.Collector) {
	prometheus.MustRegister(collector...)
}

// NewRegistry 创建新的Prometheus registry
func NewRegistry() *prometheus.Registry {
	return prometheus.NewRegistry()
}

// DefaultHandler 返回默认Prometheus指标处理器
func DefaultHandler() http.Handler {
	return promhttp.Handler()
}

// HandlerWithOptions 返回带选项的Prometheus处理器
func HandlerWithOptions(registry prometheus.Gatherer, opts promhttp.HandlerOpts) http.Handler {
	return promhttp.HandlerFor(registry, opts)
}
