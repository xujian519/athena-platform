// Package handlers - 健康检查和系统状态API
package handlers

import (
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
)

// HealthHandler 健康检查处理器
type HealthHandler struct {
	registry *ServiceRegistry
	startTime time.Time
}

// NewHealthHandler 创建健康检查处理器
func NewHealthHandler(registry *ServiceRegistry) *HealthHandler {
	return &HealthHandler{
		registry: registry,
		startTime: time.Now(),
	}
}

// Health 健康检查端点
// @Summary 健康检查
// @Tags health
// @Produce json
// @Success 200 {object} map[string]interface{} "健康状态"
// @Router /health [get]
func (h *HealthHandler) Health(c *gin.Context) {
	h.registry.mu.RLock()
	defer h.registry.mu.RUnlock()

	// 计算健康实例数
	instanceCount := len(h.registry.instances)
	healthyCount := 0
	for _, inst := range h.registry.instances {
		if inst.Status == "UP" {
			healthyCount++
		}
	}

	// 计算运行时间
	uptime := time.Since(h.startTime)

	// 确定整体状态
	status := "UP"
	if instanceCount == 0 {
		status = "NOT_READY"
	} else if healthyCount == 0 {
		status = "UNHEALTHY"
	}

	info := map[string]interface{}{
		"status":            status,
		"total_instances":   instanceCount,
		"healthy_instances": healthyCount,
		"unhealthy_instances": instanceCount - healthyCount,
		"total_routes":      len(h.registry.routes),
		"uptime_seconds":    uptime.Seconds(),
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":     info,
	})
}

// HealthAlert 健康告警端点
// @Summary 发送健康告警
// @Tags health
// @Accept json
// @Produce json
// @Param message body string true "告警消息"
// @Success 200 {object} map[string]interface{} "成功响应"
// @Router /api/v1/health/alerts [post]
func (h *HealthHandler) HealthAlert(c *gin.Context) {
	var req struct {
		Message string `json:"message" binding:"required"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"error":   err.Error(),
		})
		return
	}

	// TODO: 集成实际的告警系统（如Prometheus AlertManager、邮件等）

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data": gin.H{
			"alert":     "triggered",
			"message":   req.Message,
			"timestamp": time.Now().Unix(),
		},
	})
}

// Ready 就绪检查端点
// @Summary 就绪检查
// @Tags health
// @Produce json
// @Success 200 {object} map[string]interface{} "就绪状态"
// @Failure 503 {object} map[string]interface{} "未就绪"
// @Router /ready [get]
func (h *HealthHandler) Ready(c *gin.Context) {
	h.registry.mu.RLock()
	defer h.registry.mu.RUnlock()

	// 检查是否有健康的服务实例
	healthyCount := 0
	for _, inst := range h.registry.instances {
		if inst.Status == "UP" {
			healthyCount++
		}
	}

	if healthyCount == 0 {
		c.JSON(http.StatusServiceUnavailable, gin.H{
			"success": false,
			"error":   "No healthy instances",
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data": gin.H{
			"status": "ready",
		},
	})
}

// Live 存活检查端点
// @Summary 存活检查
// @Tags health
// @Produce json
// @Success 200 {object} map[string]interface{} "存活状态"
// @Router /live [get]
func (h *HealthHandler) Live(c *gin.Context) {
	// 简单的存活检查，如果服务能响应则认为是存活的
	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data": gin.H{
			"status": "alive",
		},
	})
}
