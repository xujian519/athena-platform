package handlers

import (
	"time"

	"athena-gateway/internal/auth"
	"athena-gateway/internal/logging"
	"athena-gateway/pkg/response"
	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
)

// HealthHandler 健康检查处理器
type HealthHandler struct {
	startTime time.Time
	version   string
}

// NewHealthHandler 创建健康检查处理器
func NewHealthHandler(version string) *HealthHandler {
	return &HealthHandler{
		startTime: time.Now(),
		version:   version,
	}
}

// BasicHealth 基本健康检查
func (h *HealthHandler) BasicHealth(c *gin.Context) {
	response.Success(c, gin.H{
		"status":    "healthy",
		"timestamp": time.Now().Unix(),
		"uptime":    time.Since(h.startTime).String(),
	})
}

// Readiness 就绪检查
func (h *HealthHandler) Readiness(c *gin.Context) {
	// 这里可以添加对依赖服务的检查
	// 例如：数据库连接、Redis连接等

	ready := true
	checks := gin.H{
		"database": "ok",
		"redis":    "ok",
		"config":   "ok",
	}

	response.SuccessWithMessage(c, "服务就绪", gin.H{
		"ready":  ready,
		"checks": checks,
	})
}

// Liveness 存活检查
func (h *HealthHandler) Liveness(c *gin.Context) {
	// 检查服务是否还在运行
	response.SuccessWithMessage(c, "服务存活", gin.H{
		"uptime": time.Since(h.startTime).String(),
	})
}

// AuthHandler 认证处理器
type AuthHandler struct {
	jwtManager *auth.JWTManager
}

// NewAuthHandler 创建认证处理器
func NewAuthHandler(jwtManager *auth.JWTManager) *AuthHandler {
	return &AuthHandler{
		jwtManager: jwtManager,
	}
}

// LoginRequest 登录请求
type LoginRequest struct {
	Username string `json:"username" binding:"required"`
	Password string `json:"password" binding:"required"`
}

// LoginResponse 登录响应
type LoginResponse struct {
	UserInfo  auth.UserInfo  `json:"user_info"`
	TokenPair auth.TokenPair `json:"token_pair"`
}

// Login 用户登录
func (h *AuthHandler) Login(c *gin.Context) {
	var req LoginRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		logging.LogError(err, "登录请求参数解析失败")
		response.BadRequest(c, "请求参数错误")
		return
	}

	// TODO: 实现真实的用户认证逻辑
	// 这里只是演示，实际应该查询数据库验证用户凭据
	if !h.validateCredentials(req.Username, req.Password) {
		logging.LogWarn("用户登录失败",
			zap.String("username", req.Username),
			zap.String("client_ip", c.ClientIP()),
		)
		response.Unauthorized(c, "用户名或密码错误")
		return
	}

	// 创建用户信息
	userInfo := auth.UserInfo{
		UserID:   "user_" + req.Username,
		Username: req.Username,
		Email:    req.Username + "@example.com",
		Role:     "user",
	}

	// 生成令牌对
	tokenPair, err := h.jwtManager.GenerateTokenPair(&userInfo)
	if err != nil {
		logging.LogError(err, "令牌生成失败", zap.String("username", req.Username))
		response.InternalServerError(c, "令牌生成失败")
		return
	}

	// 记录登录成功日志
	logging.LogInfo("用户登录成功",
		zap.String("user_id", userInfo.UserID),
		zap.String("username", userInfo.Username),
		zap.String("client_ip", c.ClientIP()),
	)

	response.Created(c, "登录成功", LoginResponse{
		UserInfo:  userInfo,
		TokenPair: *tokenPair,
	})
}

// RefreshRequest 刷新令牌请求
type RefreshRequest struct {
	RefreshToken string `json:"refresh_token" binding:"required"`
}

// RefreshToken 刷新访问令牌
func (h *AuthHandler) RefreshToken(c *gin.Context) {
	var req RefreshRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		logging.LogError(err, "刷新令牌请求参数解析失败")
		response.BadRequest(c, "请求参数错误")
		return
	}

	// 刷新令牌
	tokenPair, err := h.jwtManager.RefreshToken(req.RefreshToken)
	if err != nil {
		logging.LogError(err, "令牌刷新失败")
		response.Unauthorized(c, "令牌刷新失败")
		return
	}

	logging.LogInfo("令牌刷新成功", zap.String("client_ip", c.ClientIP()))

	response.Success(c, tokenPair)
}

// Logout 用户登出
func (h *AuthHandler) Logout(c *gin.Context) {
	// TODO: 实现令牌黑名单机制
	// 这里只是演示，实际应该将令牌加入黑名单

	userID, _ := c.Get("user_id")
	username, _ := c.Get("username")

	logging.LogInfo("用户登出",
		zap.String("user_id", userID.(string)),
		zap.String("username", username.(string)),
		zap.String("client_ip", c.ClientIP()),
	)

	response.SuccessWithMessage(c, "登出成功", nil)
}

// validateCredentials 验证用户凭据（演示用）
func (h *AuthHandler) validateCredentials(username, password string) bool {
	// 这里只是演示，实际应该查询数据库验证
	// 为了演示，只允许admin/admin和user/user登录
	if (username == "admin" && password == "admin123") ||
		(username == "user" && password == "user123") {
		return true
	}
	return false
}

// AdminHandler 管理处理器
type AdminHandler struct {
	version string
}

// NewAdminHandler 创建管理处理器
func NewAdminHandler(version string) *AdminHandler {
	return &AdminHandler{
		version: version,
	}
}

// Status 获取系统状态
func (h *AdminHandler) Status(c *gin.Context) {
	userID, _ := c.Get("user_id")
	username, _ := c.Get("username")

	status := gin.H{
		"version":   h.version,
		"timestamp": time.Now().Unix(),
		"uptime":    time.Since(time.Now()).String(), // 这里应该记录启动时间
		"current_user": gin.H{
			"user_id":  userID,
			"username": username,
		},
		"system_info": gin.H{
			"go_version":  "go1.21+",
			"gin_version": gin.Version,
		},
	}

	response.Success(c, status)
}

// Metrics 获取系统指标
func (h *AdminHandler) Metrics(c *gin.Context) {
	// TODO: 实现真实的指标收集
	metrics := gin.H{
		"requests_total":     1000,
		"requests_success":   950,
		"requests_error":     50,
		"avg_response_time":  "150ms",
		"active_connections": 25,
		"memory_usage":       "45MB",
		"cpu_usage":          "12%",
	}

	response.Success(c, metrics)
}
