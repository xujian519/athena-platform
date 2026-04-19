package gateway

import (
	"context"
	"fmt"
	"net/http"
	"net/http/httputil"
	"net/url"
	"strings"
	"sync"
	"time"

	"athena-gateway/internal/config"
	"athena-gateway/internal/middleware"
	"athena-gateway/internal/services"
	"athena-gateway/pkg/logger"

	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
)

// Gateway API网关结构
type Gateway struct {
	config     *config.Config
	services   *services.ServiceManager
	router     *gin.Engine
	httpClient *http.Client
	mu         sync.RWMutex
}

// NewGateway 创建新的网关实例
func NewGateway(cfg *config.Config) (*Gateway, error) {
	// 创建服务管理器
	serviceManager, err := services.NewServiceManager(cfg.Services)
	if err != nil {
		return nil, fmt.Errorf("创建服务管理器失败: %w", err)
	}

	// 创建HTTP客户端
	httpClient := &http.Client{
		Timeout: time.Duration(cfg.Server.ReadTimeout) * time.Second,
		Transport: &http.Transport{
			MaxIdleConns:        100,
			IdleConnTimeout:     90 * time.Second,
			DisableCompression:  false,
			TLSHandshakeTimeout: 10 * time.Second,
		},
	}

	gw := &Gateway{
		config:     cfg,
		services:   serviceManager,
		httpClient: httpClient,
	}

	// 初始化路由器
	gw.initRouter()

	return gw, nil
}

// initRouter 初始化路由器
func (gw *Gateway) initRouter() {
	// 创建Gin路由器
	gw.router = gin.New()

	// 添加全局中间件
	gw.router.Use(gin.Recovery())
	gw.router.Use(middleware.Logger())
	gw.router.Use(middleware.CORS(gw.config))
	gw.router.Use(middleware.RequestID())

	// 健康检查路由
	gw.setupHealthRoutes()

	// API路由组
	v1 := gw.router.Group("/api/v1")
	{
		// 认证路由（不需要认证中间件）
		auth := v1.Group("/auth")
		{
			auth.POST("/login", gw.handleLogin)
			auth.POST("/refresh", gw.handleRefreshToken)
			auth.POST("/logout", middleware.Auth(gw.config.JWT), gw.handleLogout)
		}

		// 需要认证的API路由
		protected := v1.Group("/")
		protected.Use(middleware.Auth(gw.config.JWT))
		protected.Use(middleware.RateLimit(gw.config))
		{
			// 用户相关路由
			users := protected.Group("/users")
			{
				users.GET("/profile", gw.handleGetUserProfile)
				users.PUT("/profile", gw.handleUpdateUserProfile)
			}

			// 代理路由
			gw.setupProxyRoutes(protected)
		}

		// 公开API路由（不需要认证，但有限流）
		public := v1.Group("/public")
		public.Use(middleware.RateLimit(gw.config))
		{
			public.GET("/patent/search", gw.proxyToService("patent_search"))
			public.GET("/patent/:id", gw.proxyToService("patent_search"))
		}
	}

	// 管理API路由组
	admin := gw.router.Group("/admin")
	admin.Use(middleware.Auth(gw.config.JWT))
	admin.Use(middleware.AdminAuth())
	{
		admin.GET("/stats", gw.handleGetStats)
		admin.GET("/health/detailed", gw.handleGetDetailedHealth)
		admin.GET("/routes", gw.handleGetRoutes)
	}
}

// setupHealthRoutes 设置健康检查路由
func (gw *Gateway) setupHealthRoutes() {
	gw.router.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"status":    "healthy",
			"timestamp": time.Now().UTC(),
			"version":   "1.0.0",
			"service":   "athena-gateway",
		})
	})

	gw.router.GET("/ready", func(c *gin.Context) {
		// 检查依赖服务状态
		ready := gw.checkReadiness()
		if ready {
			c.JSON(http.StatusOK, gin.H{
				"status": "ready",
			})
		} else {
			c.JSON(http.StatusServiceUnavailable, gin.H{
				"status": "not ready",
			})
		}
	})

	gw.router.GET("/live", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"status": "alive",
		})
	})
}

// setupProxyRoutes 设置代理路由
func (gw *Gateway) setupProxyRoutes(rg *gin.RouterGroup) {
	// 认证服务代理
	auth := rg.Group("/auth")
	auth.Any("/*path", gw.proxyToService("auth"))

	// 用户管理服务代理
	users := rg.Group("/users")
	users.Any("/*path", gw.proxyToService("user_management"))

	// 分析服务代理
	analytics := rg.Group("/analytics")
	analytics.Any("/*path", gw.proxyToService("analytics"))

	// 专利搜索服务代理
	patents := rg.Group("/patents")
	patents.Any("/*path", gw.proxyToService("patent_search"))
}

// proxyToService 创建代理处理器
func (gw *Gateway) proxyToService(serviceName string) gin.HandlerFunc {
	return func(c *gin.Context) {
		service, err := gw.services.GetService(serviceName)
		if err != nil {
			logger.Error("获取服务失败", zap.String("service", serviceName), zap.Error(err))
			c.JSON(http.StatusServiceUnavailable, gin.H{
				"error": "服务不可用",
			})
			return
		}

		// 检查服务健康状态
		if !service.IsHealthy() {
			logger.Error("服务不健康", zap.String("service", serviceName))
			c.JSON(http.StatusServiceUnavailable, gin.H{
				"error": "服务暂时不可用",
			})
			return
		}

		// 创建反向代理
		target, err := url.Parse(service.URL)
		if err != nil {
			logger.Error("解析服务URL失败", zap.String("url", service.URL), zap.Error(err))
			c.JSON(http.StatusInternalServerError, gin.H{
				"error": "内部服务器错误",
			})
			return
		}

		proxy := httputil.NewSingleHostReverseProxy(target)

		// 设置代理头信息
		proxy.Director = func(req *http.Request) {
			req.Header.Set("X-Forwarded-Host", req.Host)
			req.Header.Set("X-Origin-Host", target.Host)
			req.Header.Set("X-Real-IP", c.ClientIP())
			req.Header.Set("X-Forwarded-For", c.Request.Header.Get("X-Forwarded-For"))
			req.Header.Set("X-Forwarded-Proto", "https")
			req.URL.Scheme = target.Scheme
			req.URL.Host = target.Host
		}

		// 修改错误处理器
		proxy.ErrorHandler = func(rw http.ResponseWriter, req *http.Request, err error) {
			logger.Error("代理请求失败", zap.String("path", req.URL.Path), zap.Error(err))
			c.JSON(http.StatusBadGateway, gin.H{
				"error": "网关错误",
			})
		}

		// 执行代理请求
		proxy.ServeHTTP(c.Writer, c.Request)
	}
}

// Router 返回Gin路由器
func (gw *Gateway) Router() *gin.Engine {
	return gw.router
}

// Close 关闭网关资源
func (gw *Gateway) Close() error {
	gw.mu.Lock()
	defer gw.mu.Unlock()

	// 关闭服务管理器
	if err := gw.services.Close(); err != nil {
		logger.Error("关闭服务管理器失败", zap.Error(err))
		return err
	}

	return nil
}

// checkReadiness 检查就绪状态
func (gw *Gateway) checkReadiness() bool {
	// 检查关键服务是否就绪
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	services := []string{"auth", "user_management"}
	for _, serviceName := range services {
		service, err := gw.services.GetService(serviceName)
		if err != nil {
			logger.Error("服务不可用", zap.String("service", serviceName), zap.Error(err))
			return false
		}

		if !service.IsHealthy() {
			logger.Error("服务不健康", zap.String("service", serviceName))
			return false
		}
	}

	return true
}

// 认证相关处理器
func (gw *Gateway) handleLogin(c *gin.Context) {
	// TODO: 实现登录逻辑
	c.JSON(http.StatusOK, gin.H{
		"message": "登录功能待实现",
	})
}

func (gw *Gateway) handleRefreshToken(c *gin.Context) {
	// TODO: 实现刷新Token逻辑
	c.JSON(http.StatusOK, gin.H{
		"message": "刷新Token功能待实现",
	})
}

func (gw *Gateway) handleLogout(c *gin.Context) {
	// TODO: 实现登出逻辑
	c.JSON(http.StatusOK, gin.H{
		"message": "登出成功",
	})
}

// 用户相关处理器
func (gw *Gateway) handleGetUserProfile(c *gin.Context) {
	// TODO: 实现获取用户资料逻辑
	c.JSON(http.StatusOK, gin.H{
		"message": "获取用户资料功能待实现",
	})
}

func (gw *Gateway) handleUpdateUserProfile(c *gin.Context) {
	// TODO: 实现更新用户资料逻辑
	c.JSON(http.StatusOK, gin.H{
		"message": "更新用户资料功能待实现",
	})
}

// 管理相关处理器
func (gw *Gateway) handleGetStats(c *gin.Context) {
	// TODO: 实现获取统计信息逻辑
	c.JSON(http.StatusOK, gin.H{
		"message": "统计信息功能待实现",
	})
}

func (gw *Gateway) handleGetDetailedHealth(c *gin.Context) {
	// TODO: 实现获取详细健康状态逻辑
	c.JSON(http.StatusOK, gin.H{
		"message": "详细健康状态功能待实现",
	})
}

func (gw *Gateway) handleGetRoutes(c *gin.Context) {
	routes := []gin.RouteInfo{}
	for _, route := range gw.router.Routes() {
		if !strings.Contains(route.Path, "/admin") {
			routes = append(routes, route)
		}
	}

	c.JSON(http.StatusOK, gin.H{
		"routes": routes,
	})
}
