package router

import (
	"github.com/athena-workspace/gateway-unified/internal/config"
	"github.com/gin-gonic/gin"
)

// SetupRoutes 设置路由
func SetupRoutes(router *gin.Engine, cfg *config.Config) error {
	// 设置调试模式
	if !cfg.Server.Production {
		gin.SetMode(gin.DebugMode)
	} else {
		gin.SetMode(gin.ReleaseMode)
	}

	// 基础中间件已由Gateway设置
	// 这里可以添加额外的路由配置

	return nil
}
