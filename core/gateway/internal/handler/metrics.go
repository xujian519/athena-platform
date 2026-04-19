package handler

import (
	"net/http"

	"github.com/athena-workspace/core/gateway/internal/monitoring"
	"github.com/gin-gonic/gin"
)

type MetricsHandler struct{}

func NewMetricsHandler() *MetricsHandler {
	return &MetricsHandler{}
}

func (h *MetricsHandler) Prometheus(c *gin.Context) {
	prometheusMetrics := monitoring.GetPrometheusMetrics()
	if prometheusMetrics != nil {
		prometheusMetrics.Handler().ServeHTTP(c.Writer, c.Request)
	} else {
		c.JSON(http.StatusServiceUnavailable, gin.H{
			"error": "Prometheus metrics not available",
		})
	}
}
