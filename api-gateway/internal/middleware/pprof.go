package middleware

import (
	"net/http"
	"net/http/pprof"
	"strings"

	"athena-gateway/internal/config"
	"athena-gateway/internal/logging"
	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
)

// PprofMiddleware pprof性能分析中间件
func PprofMiddleware(cfg *config.PerformanceConfig) gin.HandlerFunc {
	if !cfg.EnablePprof {
		return func(c *gin.Context) {
			c.Next()
		}
	}

	return func(c *gin.Context) {
		path := c.Request.URL.Path

		if strings.HasPrefix(path, cfg.PprofPath) {
			logging.LogInfo("pprof访问",
				zap.String("path", path),
				zap.String("method", c.Request.Method),
				zap.String("remote_addr", c.ClientIP()),
			)
		}

		c.Next()
	}
}

// SetupPprofRoutes 设置pprof路由
func SetupPprofRoutes(router *gin.Engine, cfg *config.PerformanceConfig) {
	if !cfg.EnablePprof {
		return
	}

	pprofGroup := router.Group(cfg.PprofPath)
	{
		pprofGroup.GET("/", gin.WrapF(pprof.Index))
		pprofGroup.GET("/cmdline", gin.WrapF(pprof.Cmdline))
		pprofGroup.GET("/profile", gin.WrapF(pprof.Profile))
		pprofGroup.GET("/symbol", gin.WrapF(pprof.Symbol))
		pprofGroup.GET("/trace", gin.WrapF(pprof.Trace))

		pprofGroup.GET("/goroutine", gin.WrapF(pprof.Handler("goroutine").ServeHTTP))
		pprofGroup.GET("/heap", gin.WrapF(pprof.Handler("heap").ServeHTTP))
		pprofGroup.GET("/threadcreate", gin.WrapF(pprof.Handler("threadcreate").ServeHTTP))
		pprofGroup.GET("/block", gin.WrapF(pprof.Handler("block").ServeHTTP))
		pprofGroup.GET("/mutex", gin.WrapF(pprof.Handler("mutex").ServeHTTP))
		pprofGroup.GET("/allocs", gin.WrapF(pprof.Handler("allocs").ServeHTTP))

		pprofGroup.GET("/debug/pprof/heap", gin.WrapF(pprof.Handler("heap").ServeHTTP))
		pprofGroup.GET("/debug/pprof/goroutine", gin.WrapF(pprof.Handler("goroutine").ServeHTTP))
		pprofGroup.GET("/debug/pprof/threadcreate", gin.WrapF(pprof.Handler("threadcreate").ServeHTTP))
		pprofGroup.GET("/debug/pprof/block", gin.WrapF(pprof.Handler("block").ServeHTTP))
		pprofGroup.GET("/debug/pprof/mutex", gin.WrapF(pprof.Handler("mutex").ServeHTTP))
		pprofGroup.GET("/debug/pprof/allocs", gin.WrapF(pprof.Handler("allocs").ServeHTTP))
	}

	logging.LogInfo("pprof性能分析已启用",
		zap.String("pprof_path", cfg.PprofPath),
	)
}

// SecurityMiddlewareForPprof pprof安全中间件
func SecurityMiddlewareForPprof() gin.HandlerFunc {
	return func(c *gin.Context) {
		path := c.Request.URL.Path

		if !strings.Contains(path, "pprof") {
			c.Next()
			return
		}

		clientIP := c.ClientIP()
		if !isAllowedIP(clientIP) {
			logging.LogWarn("拒绝pprof访问",
				zap.String("client_ip", clientIP),
				zap.String("path", path),
			)
			c.JSON(http.StatusForbidden, gin.H{
				"error": "Access denied",
			})
			c.Abort()
			return
		}

		c.Header("X-Content-Type-Options", "nosniff")
		c.Header("X-Frame-Options", "DENY")

		c.Next()
	}
}

func isAllowedIP(ip string) bool {
	privateRanges := []string{
		"127.0.0.1",
		"localhost",
		"::1",
	}

	for _, allowed := range privateRanges {
		if strings.Contains(ip, allowed) {
			return true
		}
	}

	return strings.HasPrefix(ip, "192.168.") ||
		strings.HasPrefix(ip, "10.") ||
		strings.HasPrefix(ip, "172.16.") ||
		strings.HasPrefix(ip, "172.17.") ||
		strings.HasPrefix(ip, "172.18.") ||
		strings.HasPrefix(ip, "172.19.") ||
		strings.HasPrefix(ip, "172.20.") ||
		strings.HasPrefix(ip, "172.21.") ||
		strings.HasPrefix(ip, "172.22.") ||
		strings.HasPrefix(ip, "172.23.") ||
		strings.HasPrefix(ip, "172.24.") ||
		strings.HasPrefix(ip, "172.25.") ||
		strings.HasPrefix(ip, "172.26.") ||
		strings.HasPrefix(ip, "172.27.") ||
		strings.HasPrefix(ip, "172.28.") ||
		strings.HasPrefix(ip, "172.29.") ||
		strings.HasPrefix(ip, "172.30.") ||
		strings.HasPrefix(ip, "172.31.")
}
