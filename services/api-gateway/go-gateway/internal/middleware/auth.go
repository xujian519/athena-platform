package middleware

import (
	"net/http"
	"strings"
	"time"

	"athena-gateway/internal/config"
	"athena-gateway/pkg/logger"
	"athena-gateway/pkg/token"

	"github.com/gin-gonic/gin"
	"github.com/golang-jwt/jwt/v5"
	"go.uber.org/zap"
)

// Claims JWT声明结构
type Claims struct {
	UserID   string   `json:"user_id"`
	Username string   `json:"username"`
	Email    string   `json:"email"`
	Roles    []string `json:"roles"`
	jwt.RegisteredClaims
}

// AuthMiddleware 认证中间件
func Auth(jwtConfig config.JWTConfig) gin.HandlerFunc {
	return func(c *gin.Context) {
		// 从请求头获取Authorization
		authHeader := c.GetHeader("Authorization")
		if authHeader == "" {
			logger.Warn("缺少Authorization头", zap.String("path", c.Request.URL.Path))
			c.JSON(http.StatusUnauthorized, gin.H{
				"error": "缺少认证信息",
			})
			c.Abort()
			return
		}

		// 检查Bearer前缀
		const bearerPrefix = "Bearer "
		if !strings.HasPrefix(authHeader, bearerPrefix) {
			logger.Warn("Authorization格式错误", zap.String("header", authHeader))
			c.JSON(http.StatusUnauthorized, gin.H{
				"error": "认证信息格式错误",
			})
			c.Abort()
			return
		}

		// 提取token
		tokenString := authHeader[len(bearerPrefix):]

		// 解析和验证token
		claims, err := token.ParseJWT(tokenString, jwtConfig.Secret)
		if err != nil {
			logger.Error("Token验证失败",
				zap.String("path", c.Request.URL.Path),
				zap.Error(err),
			)
			c.JSON(http.StatusUnauthorized, gin.H{
				"error": "Token无效或已过期",
			})
			c.Abort()
			return
		}

		// 检查token是否过期
		if claims.ExpiresAt != nil && claims.ExpiresAt.Time.Before(time.Now()) {
			logger.Warn("Token已过期",
				zap.String("user_id", claims.UserID),
				zap.Time("expired_at", claims.ExpiresAt.Time),
			)
			c.JSON(http.StatusUnauthorized, gin.H{
				"error": "Token已过期",
			})
			c.Abort()
			return
		}

		// 将用户信息存入上下文
		c.Set("user_id", claims.UserID)
		c.Set("username", claims.Username)
		c.Set("email", claims.Email)
		c.Set("roles", claims.Roles)

		logger.Debug("用户认证成功",
			zap.String("user_id", claims.UserID),
			zap.String("path", c.Request.URL.Path),
		)

		c.Next()
	}
}

// AdminAuth 管理员认证中间件
func AdminAuth() gin.HandlerFunc {
	return func(c *gin.Context) {
		// 获取用户角色
		roles, exists := c.Get("roles")
		if !exists {
			logger.Error("无法获取用户角色")
			c.JSON(http.StatusForbidden, gin.H{
				"error": "权限不足",
			})
			c.Abort()
			return
		}

		// 检查是否包含管理员角色
		userRoles, ok := roles.([]string)
		if !ok {
			logger.Error("用户角色格式错误")
			c.JSON(http.StatusForbidden, gin.H{
				"error": "权限不足",
			})
			c.Abort()
			return
		}

		// 检查是否有管理员权限
		hasAdminRole := false
		for _, role := range userRoles {
			if role == "admin" || role == "super_admin" {
				hasAdminRole = true
				break
			}
		}

		if !hasAdminRole {
			logger.Warn("用户无管理员权限",
				zap.Strings("roles", userRoles),
				zap.String("path", c.Request.URL.Path),
			)
			c.JSON(http.StatusForbidden, gin.H{
				"error": "需要管理员权限",
			})
			c.Abort()
			return
		}

		c.Next()
	}
}

// RoleAuth 角色认证中间件
func RoleAuth(requiredRoles ...string) gin.HandlerFunc {
	return func(c *gin.Context) {
		// 获取用户角色
		roles, exists := c.Get("roles")
		if !exists {
			logger.Error("无法获取用户角色")
			c.JSON(http.StatusForbidden, gin.H{
				"error": "权限不足",
			})
			c.Abort()
			return
		}

		// 检查是否包含所需角色
		userRoles, ok := roles.([]string)
		if !ok {
			logger.Error("用户角色格式错误")
			c.JSON(http.StatusForbidden, gin.H{
				"error": "权限不足",
			})
			c.Abort()
			return
		}

		// 检查权限匹配
		hasPermission := false
		for _, requiredRole := range requiredRoles {
			for _, userRole := range userRoles {
				if userRole == requiredRole {
					hasPermission = true
					break
				}
			}
			if hasPermission {
				break
			}
		}

		if !hasPermission {
			logger.Warn("用户权限不足",
				zap.Strings("user_roles", userRoles),
				zap.Strings("required_roles", requiredRoles),
				zap.String("path", c.Request.URL.Path),
			)
			c.JSON(http.StatusForbidden, gin.H{
				"error": "权限不足",
			})
			c.Abort()
			return
		}

		c.Next()
	}
}

// OptionalAuth 可选认证中间件
func OptionalAuth(jwtConfig config.JWTConfig) gin.HandlerFunc {
	return func(c *gin.Context) {
		// 从请求头获取Authorization
		authHeader := c.GetHeader("Authorization")
		if authHeader == "" {
			// 没有认证信息，继续处理
			c.Next()
			return
		}

		// 检查Bearer前缀
		const bearerPrefix = "Bearer "
		if !strings.HasPrefix(authHeader, bearerPrefix) {
			// 格式错误，继续处理但不设置用户信息
			c.Next()
			return
		}

		// 提取token
		tokenString := authHeader[len(bearerPrefix):]

		// 解析和验证token
		claims, err := token.ParseJWT(tokenString, jwtConfig.Secret)
		if err != nil {
			// Token无效，继续处理但不设置用户信息
			c.Next()
			return
		}

		// 检查token是否过期
		if claims.ExpiresAt != nil && claims.ExpiresAt.Time.Before(time.Now()) {
			// Token过期，继续处理但不设置用户信息
			c.Next()
			return
		}

		// 将用户信息存入上下文
		c.Set("user_id", claims.UserID)
		c.Set("username", claims.Username)
		c.Set("email", claims.Email)
		c.Set("roles", claims.Roles)

		c.Next()
	}
}

// GetCurrentUser 获取当前用户信息
func GetCurrentUser(c *gin.Context) *Claims {
	userID, exists := c.Get("user_id")
	if !exists {
		return nil
	}

	username, _ := c.Get("username")
	email, _ := c.Get("email")
	roles, _ := c.Get("roles")

	userRoles, _ := roles.([]string)

	return &Claims{
		UserID:   userID.(string),
		Username: username.(string),
		Email:    email.(string),
		Roles:    userRoles,
	}
}

// IsAuthenticated 检查用户是否已认证
func IsAuthenticated(c *gin.Context) bool {
	_, exists := c.Get("user_id")
	return exists
}

// HasRole 检查用户是否具有指定角色
func HasRole(c *gin.Context, role string) bool {
	roles, exists := c.Get("roles")
	if !exists {
		return false
	}

	userRoles, ok := roles.([]string)
	if !ok {
		return false
	}

	for _, r := range userRoles {
		if r == role {
			return true
		}
	}

	return false
}

// HasAnyRole 检查用户是否具有任意一个指定角色
func HasAnyRole(c *gin.Context, requiredRoles ...string) bool {
	roles, exists := c.Get("roles")
	if !exists {
		return false
	}

	userRoles, ok := roles.([]string)
	if !ok {
		return false
	}

	for _, requiredRole := range requiredRoles {
		for _, userRole := range userRoles {
			if userRole == requiredRole {
				return true
			}
		}
	}

	return false
}
