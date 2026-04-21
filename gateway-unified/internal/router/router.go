package router

import (
	"github.com/athena-workspace/gateway-unified/internal/config"
	"github.com/athena-workspace/gateway-unified/internal/websocket"
	"github.com/gin-gonic/gin"
)

// SetupRoutes 设置路由
func SetupRoutes(router *gin.Engine, cfg *config.Config, wsController *websocket.Controller, wsHub *websocket.Hub) error {
	// 设置调试模式
	if !cfg.Server.Production {
		gin.SetMode(gin.DebugMode)
	} else {
		gin.SetMode(gin.ReleaseMode)
	}

	// 添加WebSocket路由（现有的Controller）
	if wsController != nil {
		router.GET("/ws", wsController.HandleWebSocket)

		// WebSocket统计信息API
		wsGroup := router.Group("/api/websocket")
		{
			wsGroup.GET("/stats", func(c *gin.Context) {
				stats := wsController.GetStats()
				c.JSON(200, gin.H{
					"success": true,
					"data":    stats,
				})
			})
		}
	}

	// 添加新的Hub模式WebSocket路由
	if wsHub != nil {
		router.GET("/ws/hub", wsHub.HandleWebSocketGin)

		// Hub统计信息API
		hubGroup := router.Group("/api/hub")
		{
			hubGroup.GET("/stats", func(c *gin.Context) {
				c.JSON(200, gin.H{
					"success": true,
					"data": gin.H{
						"session_count":      wsHub.GetSessionCount(),
						"connected_sessions": wsHub.GetConnectedSessions(),
					},
				})
			})
		}
	}

	return nil
}

