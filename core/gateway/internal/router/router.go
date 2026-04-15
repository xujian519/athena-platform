package router

import (
	"github.com/athena-workspace/core/gateway/internal/config"
	"github.com/gin-gonic/gin"
)

type Router struct {
	config *config.Config
}

func NewRouter(cfg *config.Config) *Router {
	return &Router{
		config: cfg,
	}
}

func (r *Router) SetupRoutes(engine *gin.Engine) {
	api := engine.Group("/api/v1")

	for _, service := range r.config.Services {
		group := api.Group("/" + service.Name)
		group.Any("/*path", r.proxyToService(service))
	}
}

func (r *Router) proxyToService(service config.ServiceConfig) gin.HandlerFunc {
	return gin.HandlerFunc(func(c *gin.Context) {
		c.JSON(501, gin.H{
			"error":   "Proxy not implemented yet",
			"service": service.Name,
			"url":     service.URL,
		})
	})
}
