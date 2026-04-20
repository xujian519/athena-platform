package gateway

import (
	"bytes"
	"context"
	"fmt"
	"net/http"
	"os"
	"sync"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/athena-workspace/gateway-unified/internal/config"
	"github.com/athena-workspace/gateway-unified/internal/handlers"
	"github.com/athena-workspace/gateway-unified/internal/middleware"
)

// Gateway 网关核心结构
type Gateway struct {
	config         *config.Config
	router         *gin.Engine
	handlers       *Handlers
	versionConfig  *middleware.VersionConfig
	done           chan struct{}
	mu             sync.RWMutex
}

// GetRegistry 获取服务注册表
func (g *Gateway) GetRegistry() *ServiceRegistry {
	return g.handlers.GetServiceRegistry()
}

// GetRouteManager 获取路由管理器
func (g *Gateway) GetRouteManager() *RouteManager {
	return g.handlers.GetRouteManager()
}

// GetVersionConfig 获取版本配置
func (g *Gateway) GetVersionConfig() *middleware.VersionConfig {
	return g.versionConfig
}

// NewGateway 创建网关实例
func NewGateway(cfg *config.Config) (*Gateway, error) {
	// 创建Gin路由器
	router := gin.New()

	// 创建网关结构（先创建一个空的结构）
	gw := &Gateway{
		config: cfg,
		router: router,
		done:   make(chan struct{}),
	}

	// 创建版本配置
	gw.versionConfig = middleware.NewVersionConfig()

	// 创建处理器（传入网关引用）
	handlers := NewHandlers(gw)

	// 设置其他字段
	gw.handlers = handlers

	// 设置中间件
	gw.setupMiddleware()

	// 设置路由
	gw.setupRoutes()

	// 启动后台任务
	go gw.backgroundTasks()

	return gw, nil
}

// setupMiddleware 设置中间件
func (g *Gateway) setupMiddleware() {
	// 恢复中间件
	g.router.Use(gin.Recovery())

	// 日志中间件
	g.router.Use(gin.Logger())

	// 安全响应头中间件（最先执行）
	securityHeadersConfig := &middleware.SecurityHeadersConfigExtended{
		XFrameOptions:             "SAMEORIGIN",
		XContentTypeOptions:       "nosniff",
		XXSSProtection:            "1; mode=block",
		StrictTransportSecurity:   "max-age=31536000; includeSubDomains",
		ContentSecurityPolicy:     "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'",
		ReferrerPolicy:            "strict-origin-when-cross-origin",
		PermissionsPolicy:         "geolocation=(), microphone=(), camera=()",
		CrossOriginOpenerPolicy:   "same-origin",
		CrossOriginResourcePolicy: "same-origin",
	}
	g.router.Use(middleware.SecurityHeadersMiddlewareExtended(securityHeadersConfig))

	// CORS中间件（使用新的安全配置）
	corsConfig := &middleware.CORSConfig{
		AllowedOrigins:   []string{"http://localhost:3000", "http://localhost:8080", "https://athena.example.com", "*"},
		AllowedMethods:   []string{"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"},
		AllowedHeaders:   []string{"Origin", "Content-Type", "Accept", "Authorization", "X-API-Key", "X-Request-ID"},
		ExposedHeaders:   []string{"Content-Length", "X-Total-Count", "X-Request-ID"},
		AllowCredentials: true,
		MaxAge:           3600,
	}
	g.router.Use(middleware.CORSMiddleware(corsConfig))

	// JWT认证中间件（可选认证，允许匿名访问）
	jwtSecret := os.Getenv("JWT_SECRET")
	if jwtSecret != "" {
		jwtConfig := &middleware.JWTConfig{
			Secret:           jwtSecret,
			Issuer:           "athena-gateway",
			Expiration:       24 * time.Hour,
			RefreshExpiration: 7 * 24 * time.Hour,
			CookieName:       "athena_token",
			UseCookie:        false,
			UseHeader:        true,
			HeaderName:       "Authorization",
			UseQuery:         false,
		}
		jwtManager := middleware.NewJWTManager(jwtConfig)
		g.router.Use(jwtManager.OptionalAuth())
	}

	// API密钥认证中间件
	apiKeyMiddleware := createAPIKeyMiddleware([]string{
		os.Getenv("API_KEY_1"),
		os.Getenv("API_KEY_2"),
	})
	g.router.Use(apiKeyMiddleware)

	// 请求ID中间件
	g.router.Use(requestIDMiddleware())

	// API版本管理中间件
	g.router.Use(g.versionConfig.VersionMiddleware())

	// 超时中间件
	g.router.Use(timeoutMiddleware(30 * time.Second))
}

// setupRoutes 设置路由
func (g *Gateway) setupRoutes() {
	// 根路径
	g.router.GET("/", func(c *gin.Context) {
		c.JSON(200, gin.H{
			"name":    "Athena Gateway Unified",
			"version": "1.0.0",
			"status":  "running",
		})
	})

	// 健康检查
	g.router.GET("/health", g.handlers.HealthCheck)
	g.router.GET("/ready", g.handlers.Ready)
	g.router.GET("/live", g.handlers.Live)

	// 创建版本管理处理器
	versionHandler := handlers.NewVersionHandler(g.versionConfig)

	// API路由组
	api := g.router.Group("/api")
	{
		// 服务管理
		api.POST("/services/batch_register", g.handlers.BatchRegister)
		api.GET("/services/instances", g.handlers.ListInstances)
		api.GET("/services/instances/:id", g.handlers.GetInstance)
		api.PUT("/services/instances/:id", g.handlers.UpdateInstance)
		api.DELETE("/services/instances/:id", g.handlers.DeleteInstance)

		// 路由管理
		api.GET("/routes", g.handlers.ListRoutes)
		api.POST("/routes", g.handlers.CreateRoute)
		api.PATCH("/routes/:id", g.handlers.UpdateRoute)
		api.DELETE("/routes/:id", g.handlers.DeleteRoute)

		// 依赖管理
		api.POST("/dependencies", g.handlers.SetDependencies)
		api.GET("/dependencies/:service", g.handlers.GetDependencies)

		// 配置管理
		api.POST("/config/load", g.handlers.LoadConfig)

		// 健康告警
		api.POST("/health/alerts", g.handlers.HealthAlert)

		// API版本管理
		api.GET("/versions", versionHandler.ListVersions)
		api.GET("/versions/:version", versionHandler.GetVersion)
		api.POST("/versions", versionHandler.RegisterVersion)
		api.PUT("/versions/:version", versionHandler.UpdateVersion)
		api.POST("/versions/:version/deprecate", versionHandler.DeprecateVersion)
		api.PUT("/versions/default", versionHandler.SetDefaultVersion)
	}

	// 代理路由 - 放在最后作为catch-all
	// 使用NoRoute来处理所有未匹配的路由
	g.router.NoRoute(g.handlers.ProxyRequest)
}

// GetRouter 获取路由器
func (g *Gateway) GetRouter() *gin.Engine {
	return g.router
}

// Close 关闭网关
func (g *Gateway) Close() error {
	g.mu.Lock()
	defer g.mu.Unlock()

	select {
	case <-g.done:
		// 已经关闭
		return nil
	default:
		close(g.done)
	}

	// 清理服务注册表资源
	if g.handlers != nil && g.handlers.serviceRegistry != nil {
		// 清理服务注册表
		instances := g.handlers.serviceRegistry.GetAll()
		for _, inst := range instances {
			g.handlers.serviceRegistry.Delete(inst.ID)
		}
	}

	// 清理路由管理器资源
	if g.handlers != nil && g.handlers.routeManager != nil {
		// TODO: 清理路由缓存（如果有）
	}

	return nil
}

// backgroundTasks 后台任务
func (g *Gateway) backgroundTasks() {
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			// 定期检查服务健康状态
			g.checkServiceHealth()

		case <-g.done:
			return
		}
	}
}

// checkServiceHealth 检查服务健康状态
func (g *Gateway) checkServiceHealth() {
	// TODO: 实现服务健康检查
	// 定期向注册的服务发送健康检查请求
	// 将不健康的服务标记为DOWN
}

// ServiceCall 服务调用（用于请求转发）
func (g *Gateway) ServiceCall(serviceName, path string, method string, headers map[string]string, body []byte) (*http.Response, error) {
	registry := g.GetRegistry()

	// 选择服务实例
	instance := registry.SelectInstance(serviceName)
	if instance == nil {
		return nil, fmt.Errorf("没有可用的服务实例: %s", serviceName)
	}

	// 构造目标URL
	url := fmt.Sprintf("http://%s:%d%s", instance.Host, instance.Port, path)

	// 创建请求体 Reader
	var bodyReader *bytes.Reader
	if body != nil {
		bodyReader = bytes.NewReader(body)
	}

	// 创建请求
	req, err := http.NewRequest(method, url, bodyReader)
	if err != nil {
		return nil, fmt.Errorf("创建请求失败: %w", err)
	}

	// 设置请求头
	for k, v := range headers {
		req.Header.Set(k, v)
	}

	// 如果有请求体，确保设置Content-Type
	if body != nil && req.Header.Get("Content-Type") == "" {
		req.Header.Set("Content-Type", "application/json")
	}

	// 添加转发标识头
	req.Header.Set("X-Forwarded-For", "Athena-Gateway")
	req.Header.Set("X-Forwarded-Proto", "http")
	req.Header.Set("X-Gateway-Service", serviceName)

	// 发送请求
	client := &http.Client{
		Timeout: 30 * time.Second,
		// 禁止自动跟随重定向
		CheckRedirect: func(req *http.Request, via []*http.Request) error {
			return http.ErrUseLastResponse
		},
	}

	resp, err := client.Do(req)
	if err != nil {
		// 标记实例为不健康
		registry.UpdateHeartbeat(instance.ID)
		return nil, fmt.Errorf("请求服务失败: %w", err)
	}

	// 更新心跳
	registry.UpdateHeartbeat(instance.ID)

	return resp, nil
}

// 辅助函数
// GenerateServiceID 生成服务实例ID（导出版本）
func GenerateServiceID(name, host string, port int, index int) string {
	return fmt.Sprintf("%s:%s:%d:%d", name, host, port, index)
}

func generateRouteID(path, targetService string) string {
	return fmt.Sprintf("%s:%s", path, targetService)
}

// 中间件
func requestIDMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		requestID := c.GetHeader("X-Request-ID")
		if requestID == "" {
			requestID = generateRequestID()
		}
		c.Set("request_id", requestID)
		c.Header("X-Request-ID", requestID)
		c.Next()
	}
}

func timeoutMiddleware(timeout time.Duration) gin.HandlerFunc {
	return func(c *gin.Context) {
		ctx, cancel := context.WithTimeout(c.Request.Context(), timeout)
		defer cancel()

		c.Request = c.Request.WithContext(ctx)
		c.Next()
	}
}

func generateRequestID() string {
	return fmt.Sprintf("%d-%d", time.Now().UnixNano(), time.Now().Unix())
}

// createAPIKeyMiddleware 创建API密钥认证中间件
func createAPIKeyMiddleware(validKeys []string) gin.HandlerFunc {
	// 创建密钥集合以便快速查找
	keySet := make(map[string]bool)
	for _, key := range validKeys {
		if key != "" {
			keySet[key] = true
		}
	}

	return func(c *gin.Context) {
		// 跳过健康检查和根路径
		if c.Request.URL.Path == "/" || c.Request.URL.Path == "/health" || c.Request.URL.Path == "/ready" || c.Request.URL.Path == "/live" {
			c.Next()
			return
		}

		// 检查JWT是否已认证
		if _, exists := c.Get("user_id"); exists {
			c.Next()
			return
		}

		// 检查API密钥
		apiKey := c.GetHeader("X-API-Key")
		if apiKey == "" {
			// 没有API密钥，继续（可选认证）
			c.Next()
			return
		}

		// 验证API密钥
		if !keySet[apiKey] {
			c.JSON(401, gin.H{
				"success": false,
				"error":   "Invalid API key",
			})
			c.Abort()
			return
		}

		// 设置认证信息
		c.Set("auth_method", "api_key")
		c.Set("api_key", apiKey)
		c.Next()
	}
}
