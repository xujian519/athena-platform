package gateway

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/athena-workspace/gateway-unified/internal/config"
)

// ExtendedGateway 扩展的网关结构，包含所有模块化组件
type ExtendedGateway struct {
	config                 *config.Config
	router                 *gin.Engine
	handlers               *Handlers

	// 新增的模块化组件
	loadBalancer           LoadBalancer
	circuitBreakerManager  *CircuitBreakerManager
	degradationManager     *DegradationManager
	pluginManager          *PluginManager
	configManager          ConfigManager

	done                   chan struct{}
}

// NewExtendedGateway 创建扩展的网关实例
func NewExtendedGateway(cfg *config.Config) (*ExtendedGateway, error) {
	// 创建Gin路由器
	router := gin.New()

	// 创建扩展网关结构
	gw := &ExtendedGateway{
		config: cfg,
		router: router,
		done:   make(chan struct{}),
	}

	// 创建处理器
	handlers := NewHandlers(&Gateway{config: cfg, router: router, done: make(chan struct{})})
	gw.handlers = handlers

	// 初始化模块化组件
	if err := gw.initModularComponents(); err != nil {
		return nil, err
	}

	// 设置中间件（包含插件系统）
	gw.setupExtendedMiddleware()

	// 设置路由
	gw.setupRoutes()

	// 启动后台任务
	go gw.backgroundTasks()

	return gw, nil
}

// initModularComponents 初始化模块化组件
func (g *ExtendedGateway) initModularComponents() error {
	// 1. 初始化负载均衡器
	lbConfig := LoadBalancerConfig{
		Strategy:          WeightedRoundRobin,
		PerformanceAware:  true,
		ResponseTimeWindow: 5 * time.Minute,
	}
	g.loadBalancer = NewLoadBalancer(lbConfig)

	// 2. 初始化熔断器管理器
	g.circuitBreakerManager = NewCircuitBreakerManager()

	// 3. 初始化降级管理器
	g.degradationManager = NewDegradationManager()

	// 4. 初始化插件管理器
	g.pluginManager = NewPluginManager()
	g.registerDefaultPlugins()

	// 5. 初始化配置管理器
	g.configManager = NewConfigManager()

	return nil
}

// registerDefaultPlugins 注册默认插件
func (g *ExtendedGateway) registerDefaultPlugins() {
	// 注册日志插件
	loggingPlugin := NewLoggingPlugin()
	g.pluginManager.Register(loggingPlugin)

	// 注册监控插件
	metricsPlugin := NewMetricsPlugin()
	g.pluginManager.Register(metricsPlugin)

	// 注册认证插件（可选）
	authPlugin := NewAuthPlugin()
	authConfig := map[string]interface{}{
		"enabled": true,
	}
	authPlugin.Init(authConfig)
	g.pluginManager.Register(authPlugin)

	// 注册限流插件（可选）
	rateLimitPlugin := NewRateLimitPlugin(100) // 每个IP每分钟100次请求
	rateLimitConfig := map[string]interface{}{
		"max_requests": 100,
	}
	rateLimitPlugin.Init(rateLimitConfig)
	g.pluginManager.Register(rateLimitPlugin)

	// 注册CORS插件
	corsPlugin := NewCORSPlugin()
	corsConfig := map[string]interface{}{
		"allowed_origins":   []string{"*"},
		"allowed_methods":   []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
		"allowed_headers":   []string{"Content-Type", "Authorization"},
		"allow_credentials": false,
	}
	corsPlugin.Init(corsConfig)
	g.pluginManager.Register(corsPlugin)
}

// setupExtendedMiddleware 设置扩展的中间件（包含插件系统）
func (g *ExtendedGateway) setupExtendedMiddleware() {
	// 基础中间件
	g.router.Use(gin.Recovery())
	g.router.Use(gin.Logger())

	// 请求ID中间件
	g.router.Use(requestIDMiddleware())

	// 超时中间件
	g.router.Use(timeoutMiddleware(30 * time.Second))

	// 插件中间件
	g.router.Use(func(c *gin.Context) {
		ctx := c.Request.Context()
		pluginCtx := &PluginContext{
			RequestID:   c.GetHeader("X-Request-ID"),
			ServiceName: c.Param("service"),
			Method:      c.Request.Method,
			Path:        c.Request.URL.Path,
			Metadata: map[string]interface{}{
				"client_ip":    c.ClientIP(),
				"user_agent":   c.Request.UserAgent(),
				"authorization": c.GetHeader("Authorization"),
			},
		}

		// 执行请求前插件
		if err := g.pluginManager.ExecutePhase(ctx, PhaseBeforeRequest, pluginCtx); err != nil {
			// 如果插件返回错误，终止请求
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			c.Abort()
			return
		}

		// 继续处理请求
		c.Next()

		// 执行请求后插件
		g.pluginManager.ExecutePhase(ctx, PhaseAfterRequest, pluginCtx)
	})
}

// ServiceCallWithProtection 带保护的 服务调用（集成熔断器和负载均衡）
func (g *ExtendedGateway) ServiceCallWithProtection(serviceName, path string, method string, headers map[string]string, body []byte) (*http.Response, error) {
	registry := g.GetRegistry()

	// 1. 检查熔断器
	breakerConfig := CircuitBreakerConfig{
		MaxRequests: 1,
		Interval:    10 * time.Second,
		Timeout:     60 * time.Second,
		ReadyToTrip: func(counts Counts) bool {
			return counts.ConsecutiveFailures >= 5 ||
				   (counts.Requests >= 10 && float64(counts.TotalFailures)/float64(counts.Requests) > 0.5)
		},
	}
	breaker := g.circuitBreakerManager.GetOrCreate(serviceName, breakerConfig)

	if !breaker.Allow() {
		return nil, fmt.Errorf("服务 %s 熔断器已打开", serviceName)
	}

	// 2. 使用负载均衡器选择实例
	instances := registry.GetHealthyInstances(serviceName)
	if len(instances) == 0 {
		breaker.Failure()
		return nil, fmt.Errorf("没有可用的服务实例: %s", serviceName)
	}

	instance := g.loadBalancer.Select(instances)
	if instance == nil {
		breaker.Failure()
		return nil, fmt.Errorf("负载均衡器选择实例失败: %s", serviceName)
	}

	// 3. 发送请求
	startTime := time.Now()
	resp, err := g.sendRequest(instance, path, method, headers, body)
	duration := time.Since(startTime)

	// 4. 记录结果
	if err != nil {
		breaker.Failure()
		// 记录负载均衡器响应时间（即使失败也记录）
		g.loadBalancer.RecordResponse(serviceName, instance.ID, duration)
		return nil, fmt.Errorf("请求服务失败: %w", err)
	}

	breaker.Success()
	g.loadBalancer.RecordResponse(serviceName, instance.ID, duration)

	// 5. 更新心跳
	registry.UpdateHeartbeat(instance.ID)

	return resp, nil
}

// sendRequest 实际发送HTTP请求
func (g *ExtendedGateway) sendRequest(instance *ServiceInstance, path string, method string, headers map[string]string, body []byte) (*http.Response, error) {
	// 构造目标URL
	url := fmt.Sprintf("http://%s:%d%s", instance.Host, instance.Port, path)

	// 创建请求
	req, err := http.NewRequest(method, url, nil)
	if err != nil {
		return nil, err
	}

	// 设置请求头
	for k, v := range headers {
		req.Header.Set(k, v)
	}

	// 发送请求
	client := &http.Client{
		Timeout: 30 * time.Second,
		CheckRedirect: func(req *http.Request, via []*http.Request) error {
			return http.ErrUseLastResponse
		},
	}

	return client.Do(req)
}

// ProxyRequestWithDegradation 带降级保护的请求代理
func (g *ExtendedGateway) ProxyRequestWithDegradation(c *gin.Context) {
	requestPath := c.Request.URL.Path
	method := c.Request.Method

	// 查找路由规则
	route := g.GetRouteManager().FindByPath(requestPath, method)
	if route == nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "未找到匹配的路由规则"})
		return
	}

	targetService := route.TargetService

	// 使用降级管理器执行请求
	ctx := c.Request.Context()
	request := &ProxyRequest{
		Context: ctx,
		Route:   route,
		Gin:     c,
	}

	handler := func(ctx context.Context, req interface{}) (interface{}, error) {
		proxyReq := req.(*ProxyRequest)
		return g.doProxyRequest(proxyReq)
	}

	result, err := g.degradationManager.Execute(ctx, targetService, request, handler)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	// 返回结果
	c.JSON(http.StatusOK, result)
}

// doProxyRequest 实际执行代理请求
func (g *ExtendedGateway) doProxyRequest(req *ProxyRequest) (interface{}, error) {
	// 读取请求体
	body, _ := req.Gin.GetRawData()

	// 复制请求头
	headers := make(map[string]string)
	for k, v := range req.Gin.Request.Header {
		if len(v) > 0 {
			headers[k] = v[0]
		}
	}

	// 使用带保护的ServiceCall
	resp, err := g.ServiceCallWithProtection(
		req.Route.TargetService,
		req.Route.Path,
		req.Gin.Request.Method,
		headers,
		body,
	)

	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	// 返回响应
	return gin.H{
		"status": resp.StatusCode,
		"headers": resp.Header,
	}, nil
}

// ProxyRequest 代理请求结构
type ProxyRequest struct {
	Context context.Context
	Route   *RouteRule
	Gin     *gin.Context
}

// GetRegistry 获取服务注册表
func (g *ExtendedGateway) GetRegistry() *ServiceRegistry {
	return g.handlers.GetServiceRegistry()
}

// GetRouteManager 获取路由管理器
func (g *ExtendedGateway) GetRouteManager() *RouteManager {
	return g.handlers.GetRouteManager()
}

// GetRouter 获取路由器
func (g *ExtendedGateway) GetRouter() *gin.Engine {
	return g.router
}

// setupRoutes 设置路由
func (g *ExtendedGateway) setupRoutes() {
	// 根路径
	g.router.GET("/", func(c *gin.Context) {
		c.JSON(200, gin.H{
			"name":    "Athena Gateway Extended",
			"version": "2.0.0",
			"status":  "running",
		})
	})

	// 健康检查
	g.router.GET("/health", g.handlers.HealthCheck)

	// 原有的API路由
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
	}

	// 新增的模块化组件管理API
	modular := g.router.Group("/api/modular")
	{
		// 负载均衡器
		modular.GET("/loadbalancer/stats/:service", func(c *gin.Context) {
			serviceName := c.Param("service")
			stats := g.loadBalancer.GetStats(serviceName)
			c.JSON(200, stats)
		})

		// 熔断器
		modular.GET("/circuit_breaker/stats", func(c *gin.Context) {
			stats := g.circuitBreakerManager.GetStats()
			c.JSON(200, stats)
		})

		// 降级管理
		modular.GET("/degradation/status/:service", func(c *gin.Context) {
			serviceName := c.Param("service")
			status := g.degradationManager.GetStatus(serviceName)
			c.JSON(200, status)
		})
		modular.POST("/degradation/trigger/:service", func(c *gin.Context) {
			serviceName := c.Param("service")
			err := g.degradationManager.ManualTrigger(serviceName)
			if err != nil {
				c.JSON(500, gin.H{"error": err.Error()})
				return
			}
			c.JSON(200, gin.H{"success": true})
		})
		modular.POST("/degradation/recover/:service", func(c *gin.Context) {
			serviceName := c.Param("service")
			err := g.degradationManager.ManualRecover(serviceName)
			if err != nil {
				c.JSON(500, gin.H{"error": err.Error()})
				return
			}
			c.JSON(200, gin.H{"success": true})
		})

		// 插件管理
		modular.GET("/plugins", func(c *gin.Context) {
			plugins := g.pluginManager.GetAll()
			c.JSON(200, plugins)
		})

		// 配置管理
		modular.GET("/config", func(c *gin.Context) {
			configs := g.configManager.GetAll()
			c.JSON(200, configs)
		})
		modular.POST("/config", func(c *gin.Context) {
			var req struct {
				Key   string      `json:"key" binding:"required"`
				Value interface{} `json:"value" binding:"required"`
			}
			if err := c.ShouldBindJSON(&req); err != nil {
				c.JSON(400, gin.H{"error": err.Error()})
				return
			}
			err := g.configManager.Set(req.Key, req.Value)
			if err != nil {
				c.JSON(500, gin.H{"error": err.Error()})
				return
			}
			c.JSON(200, gin.H{"success": true})
		})
	}

	// 代理路由 - 使用带降级保护的代理
	g.router.NoRoute(g.ProxyRequestWithDegradation)
}

// Close 关闭网关
func (g *ExtendedGateway) Close() error {
	// 关闭插件管理器
	g.pluginManager.Shutdown()

	// 关闭配置管理器
	g.configManager.Close()

	// 关闭原有资源
	close(g.done)

	return nil
}

// backgroundTasks 后台任务
func (g *ExtendedGateway) backgroundTasks() {
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
func (g *ExtendedGateway) checkServiceHealth() {
	// TODO: 实现服务健康检查
}
