package gateway

import (
	"fmt"
	"io"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/athena-workspace/gateway-unified/internal/logging"
	"github.com/athena-workspace/gateway-unified/pkg/response"
)

// Handlers 包含Gateway的HTTP处理器
type Handlers struct {
	serviceRegistry *ServiceRegistry
	routeManager    *RouteManager
	gateway         *Gateway // 用于访问ServiceCall等方法
}

// NewHandlers 创建处理器集合
func NewHandlers(gw *Gateway) *Handlers {
	return &Handlers{
		serviceRegistry: NewServiceRegistry(),
		routeManager:    NewRouteManager(),
		gateway:         gw,
	}
}

// GetServiceRegistry 获取服务注册器
func (h *Handlers) GetServiceRegistry() *ServiceRegistry {
	return h.serviceRegistry
}

// GetRouteManager 获取路由管理器
func (h *Handlers) GetRouteManager() *RouteManager {
	return h.routeManager
}

// HealthCheck 健康检查
func (h *Handlers) HealthCheck(c *gin.Context) {
	status := gin.H{
		"status":    "UP",
		"instances": h.serviceRegistry.Count(),
		"routes":    h.routeManager.Count(),
		"timestamp": gin.H{},
	}

	// 检查依赖关系
	dependencies := h.serviceRegistry.GetAllDependencies()
	if len(dependencies) > 0 {
		status["dependencies"] = dependencies
	}

	response.Success(c, status)
}

// BatchRegister 批量注册服务
func (h *Handlers) BatchRegister(c *gin.Context) {
	var req BatchRegisterRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		response.BadRequest(c, err.Error())
		return
	}

	results := make([]*ServiceInstance, 0, len(req.Services))
	for i, svc := range req.Services {
		instance := &ServiceInstance{
			ID:          generateServiceID(svc.Name, svc.Host, svc.Port, i),
			ServiceName: svc.Name,
			Host:        svc.Host,
			Port:        svc.Port,
			Status:      "UP",
			Weight:      1,
			Metadata:    svc.Metadata,
		}

		h.serviceRegistry.Register(instance)
		results = append(results, instance)
	}

	response.Success(c, gin.H{
		"success": true,
		"data":    results,
		"count":   len(results),
	})
}

// ListInstances 查询服务实例
func (h *Handlers) ListInstances(c *gin.Context) {
	serviceName := c.Query("service")

	var instances []*ServiceInstance
	if serviceName != "" {
		instances = h.serviceRegistry.GetByService(serviceName)
	} else {
		instances = h.serviceRegistry.GetAll()
	}

	response.Success(c, gin.H{
		"success": true,
		"data":    instances,
		"count":   len(instances),
	})
}

// GetInstance 获取单个服务实例
func (h *Handlers) GetInstance(c *gin.Context) {
	instanceID := c.Param("id")

	instance := h.serviceRegistry.GetByID(instanceID)
	if instance == nil {
		response.NotFound(c, "实例不存在")
		return
	}

	response.Success(c, instance)
}

// UpdateInstance 更新服务实例
func (h *Handlers) UpdateInstance(c *gin.Context) {
	instanceID := c.Param("id")

	var req UpdateServiceInstanceRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		response.BadRequest(c, err.Error())
		return
	}

	instance := h.serviceRegistry.GetByID(instanceID)
	if instance == nil {
		response.NotFound(c, "实例不存在")
		return
	}

	// 更新字段
	if req.Weight > 0 {
		instance.Weight = req.Weight
	}
	if req.Host != "" {
		instance.Host = req.Host
	}
	if req.Port > 0 {
		instance.Port = req.Port
	}
	if req.Metadata != nil {
		if instance.Metadata == nil {
			instance.Metadata = make(map[string]interface{})
		}
		for k, v := range req.Metadata {
			instance.Metadata[k] = v
		}
	}

	// 更新心跳时间戳，确保服务保持健康状态
	h.serviceRegistry.UpdateHeartbeat(instanceID)

	response.Success(c, instance)
}

// DeleteInstance 删除服务实例
func (h *Handlers) DeleteInstance(c *gin.Context) {
	instanceID := c.Param("id")

	if !h.serviceRegistry.Delete(instanceID) {
		response.NotFound(c, "实例不存在")
		return
	}

	response.Success(c, gin.H{
		"success": true,
		"data":    gin.H{"deleted": instanceID},
	})
}

// CreateRoute 创建路由
func (h *Handlers) CreateRoute(c *gin.Context) {
	var req RouteRule
	if err := c.ShouldBindJSON(&req); err != nil {
		response.BadRequest(c, err.Error())
		return
	}

	if req.ID == "" {
		req.ID = generateRouteID(req.Path, req.TargetService)
	}

	h.routeManager.Create(&req)

	response.Success(c, req)
}

// ListRoutes 查询路由
func (h *Handlers) ListRoutes(c *gin.Context) {
	routes := h.routeManager.GetAll()

	response.Success(c, gin.H{
		"success": true,
		"data":    routes,
		"count":   len(routes),
	})
}

// UpdateRoute 更新路由
func (h *Handlers) UpdateRoute(c *gin.Context) {
	routeID := c.Param("id")

	var req RouteRule
	if err := c.ShouldBindJSON(&req); err != nil {
		response.BadRequest(c, err.Error())
		return
	}

	route := h.routeManager.Get(routeID)
	if route == nil {
		response.NotFound(c, "路由不存在")
		return
	}

	// 更新路由
	rule := &req
	rule.ID = routeID // 保持ID不变

	h.routeManager.Update(rule)

	response.Success(c, rule)
}

// DeleteRoute 删除路由
func (h *Handlers) DeleteRoute(c *gin.Context) {
	routeID := c.Param("id")

	if !h.routeManager.Delete(routeID) {
		response.NotFound(c, "路由不存在")
		return
	}

	response.Success(c, gin.H{
		"success": true,
		"data":    gin.H{"deleted": routeID},
	})
}

// SetDependencies 设置服务依赖
func (h *Handlers) SetDependencies(c *gin.Context) {
	var req DependencySpec
	if err := c.ShouldBindJSON(&req); err != nil {
		response.BadRequest(c, err.Error())
		return
	}

	h.serviceRegistry.SetDependencies(req.Service, req.DependsOn)

	response.Success(c, gin.H{
		"success": true,
		"data": gin.H{
			"service":      req.Service,
			"dependencies": req.DependsOn,
		},
	})
}

// GetDependencies 查询服务依赖
func (h *Handlers) GetDependencies(c *gin.Context) {
	serviceName := c.Param("service")

	dependencies := h.serviceRegistry.GetDependencies(serviceName)

	response.Success(c, gin.H{
		"success": true,
		"data": gin.H{
			"service":      serviceName,
			"dependencies": dependencies,
		},
	})
}

// LoadConfig 加载配置
func (h *Handlers) LoadConfig(c *gin.Context) {
	var config map[string]interface{}
	if err := c.ShouldBindJSON(&config); err != nil {
		response.BadRequest(c, err.Error())
		return
	}

	servicesAdded := 0
	routesAdded := 0

	// 处理服务实例配置
	if services, ok := config["services"].([]interface{}); ok {
		for _, svc := range services {
			if svcMap, ok := svc.(map[string]interface{}); ok {
				name, _ := svcMap["name"].(string)
				host, _ := svcMap["host"].(string)
				port := 8000 // 默认端口

				if p, ok := svcMap["port"].(float64); ok {
					port = int(p)
				}

				instance := &ServiceInstance{
					ID:          generateServiceID(name, host, port, servicesAdded),
					ServiceName: name,
					Host:        host,
					Port:        port,
					Status:      "UP",
					Weight:      1,
				}
				h.serviceRegistry.Register(instance)
				servicesAdded++
			}
		}
	}

	// 处理路由配置
	if routes, ok := config["routes"].([]interface{}); ok {
		for _, r := range routes {
			if rMap, ok := r.(map[string]interface{}); ok {
				path, _ := rMap["path"].(string)
				target, _ := rMap["target_service"].(string)

				route := &RouteRule{
					ID:            generateRouteID(path, target),
					Path:          path,
					TargetService: target,
					StripPrefix:   false,
				}

				if sp, ok := rMap["strip_prefix"].(bool); ok {
					route.StripPrefix = sp
				}

				if methods, ok := rMap["methods"].([]interface{}); ok {
					for _, m := range methods {
						if ms, ok := m.(string); ok {
							route.Methods = append(route.Methods, ms)
						}
					}
				}

				h.routeManager.Create(route)
				routesAdded++
			}
		}
	}

	logging.LogInfo("配置加载完成",
		logging.String("services_added", fmt.Sprint(servicesAdded)),
		logging.String("routes_added", fmt.Sprint(routesAdded)),
		logging.String("total_services", fmt.Sprint(h.serviceRegistry.Count())),
		logging.String("total_routes", fmt.Sprint(h.routeManager.Count())),
	)

	response.Success(c, gin.H{
		"success": true,
		"message": "配置加载成功",
		"data": gin.H{
			"services_added": servicesAdded,
			"routes_added":   routesAdded,
			"total_services": h.serviceRegistry.Count(),
			"total_routes":   h.routeManager.Count(),
		},
	})
}

// HealthAlertRequest 健康告警请求
type HealthAlertRequest struct {
	Service    string `json:"service"`
	AlertType  string `json:"alert_type"`  // error, warning, info
	Message    string `json:"message"`
	Severity   string `json:"severity"`    // critical, high, medium, low
	Metadata   map[string]interface{} `json:"metadata,omitempty"`
}

// HealthAlert 健康告警
func (h *Handlers) HealthAlert(c *gin.Context) {
	var req HealthAlertRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		response.BadRequest(c, err.Error())
		return
	}

	// 根据严重程度记录不同级别的日志
	switch req.Severity {
	case "critical", "high":
		logging.LogError("健康告警",
			logging.String("service", req.Service),
			logging.String("type", req.AlertType),
			logging.String("message", req.Message),
			logging.String("severity", req.Severity),
		)
	case "medium":
		logging.LogWarn("健康告警",
			logging.String("service", req.Service),
			logging.String("type", req.AlertType),
			logging.String("message", req.Message),
		)
	default:
		logging.LogInfo("健康告警",
			logging.String("service", req.Service),
			logging.String("type", req.AlertType),
			logging.String("message", req.Message),
		)
	}

	// TODO: 实现更复杂的告警逻辑
	// - 发送到外部告警系统 (如钉钉、企业微信、邮件)
	// - 记录到数据库
	// - 触发自动处理流程

	response.Success(c, gin.H{
		"alert_received": req.Message,
		"service":        req.Service,
		"severity":       req.Severity,
	})
}

// ProxyRequest 代理请求到目标服务
func (h *Handlers) ProxyRequest(c *gin.Context) {
	// 获取请求路径
	requestPath := c.Request.URL.Path
	method := c.Request.Method

	// 查找匹配的路由规则
	route := h.routeManager.FindByPath(requestPath, method)
	if route == nil {
		response.NotFound(c, "未找到匹配的路由规则")
		return
	}

	// 获取目标服务
	targetService := route.TargetService

	// 读取请求体
	var body []byte
	if c.Request.Body != nil {
		body, _ = io.ReadAll(c.Request.Body)
	}

	// 复制请求头
	headers := make(map[string]string)
	for k, v := range c.Request.Header {
		if len(v) > 0 {
			headers[k] = v[0]
		}
	}

	// 移除不需要转发的头
	delete(headers, "Host")
	delete(headers, "Content-Length")

	// 处理路径前缀
	targetPath := requestPath

	// 支持从metadata中指定目标路径
	if targetPathOverride, ok := route.Metadata["target_path"].(string); ok && targetPathOverride != "" {
		targetPath = targetPathOverride
	} else if route.StripPrefix {
		// 移除路由路径的前缀
		// 例如: /api/xiaona/patents -> /patents (当路由为 /api/xiaona/*)
		if len(route.Path) > 0 && route.Path != "/*" && route.Path != "/**" {
			// 对于 /api/xiaona/* 模式，移除 /api/xiaona 前缀
			prefix := route.Path
			if strings.HasSuffix(prefix, "/*") {
				prefix = strings.TrimSuffix(prefix, "/*")
			} else if strings.HasSuffix(prefix, "/**") {
				prefix = strings.TrimSuffix(prefix, "/**")
			}
			// 检查请求路径是否以前缀开头
			if requestPath == prefix || requestPath == prefix+"/" {
				targetPath = "/"
			} else if strings.HasPrefix(requestPath, prefix+"/") {
				targetPath = strings.TrimPrefix(requestPath, prefix+"/")
				// 确保路径以 / 开头
				if targetPath != "" && !strings.HasPrefix(targetPath, "/") {
					targetPath = "/" + targetPath
				}
			} else if requestPath == prefix+"/*" || requestPath == prefix+"/**" {
				// 对于通配符匹配的情况，也需要剥离前缀
				targetPath = "/"
			} else if strings.HasPrefix(requestPath, prefix) {
				// 请求路径完全匹配前缀（如 /api/legal-world-model/health 对于 /api/legal-world-model/*）
				// 移除前缀部分
				targetPath = strings.TrimPrefix(requestPath, prefix)
				if targetPath == "" {
					targetPath = "/"
				}
				// 确保路径以 / 开头
				if !strings.HasPrefix(targetPath, "/") {
					targetPath = "/" + targetPath
				}
			}
		}
	}

	// 调用服务
	startTime := time.Now()
	resp, err := h.gateway.ServiceCall(targetService, targetPath, method, headers, body)
	if err != nil {
		logging.LogError("服务调用失败",
			logging.String("service", targetService),
			logging.String("path", targetPath),
			logging.Err(err),
		)
		response.InternalError(c, fmt.Sprintf("服务调用失败: %v", err))
		return
	}
	defer resp.Body.Close()

	// 记录响应时间
	duration := time.Since(startTime)
	logging.LogInfo("服务调用完成",
		logging.String("service", targetService),
		logging.String("path", targetPath),
		logging.String("method", method),
		logging.String("duration", duration.String()),
		logging.String("status", fmt.Sprint(resp.StatusCode)),
	)

	// 复制响应头
	for k, v := range resp.Header {
		if len(v) > 0 {
			c.Header(k, v[0])
		}
	}

	// 读取响应体
	responseBody, err := io.ReadAll(resp.Body)
	if err != nil {
		logging.LogError("读取响应体失败", logging.Err(err))
		response.InternalError(c, "读取响应失败")
		return
	}

	// 设置状态码并返回响应
	c.Status(resp.StatusCode)
	c.Writer.Write(responseBody)
}

// Ready 就绪检查端点
func (h *Handlers) Ready(c *gin.Context) {
	// 检查是否有健康的服务实例
	instances := h.serviceRegistry.GetAll()
	healthyCount := 0
	for _, inst := range instances {
		if inst.Status == "UP" {
			healthyCount++
		}
	}

	if healthyCount == 0 {
		c.JSON(503, gin.H{
			"success": false,
			"error":   "No healthy instances",
		})
		return
	}

	c.JSON(200, gin.H{
		"success": true,
		"data": gin.H{
			"status": "ready",
		},
	})
}

// Live 存活检查端点
func (h *Handlers) Live(c *gin.Context) {
	// 简单的存活检查，如果服务能响应则认为是存活的
	c.JSON(200, gin.H{
		"success": true,
		"data": gin.H{
			"status": "alive",
		},
	})
}
