// Package middleware - JWT认证中间件
package middleware

import (
	"crypto/rand"
	"encoding/base64"
	"errors"
	"fmt"
	"net/http"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/golang-jwt/jwt/v5"
)

// JWTConfig JWT配置
type JWTConfig struct {
	// JWT密钥（必须配置）
	Secret string

	// 签发者
	Issuer string

	// Token有效期（默认24小时）
	Expiration time.Duration

	// Refresh Token有效期（默认7天）
	RefreshExpiration time.Duration

	// Cookie名称
	CookieName string

	// 是否使用Cookie传输Token
	UseCookie bool

	// 是否允许通过Header传输Token
	UseHeader bool

	// Header名称
	HeaderName string

	// 是否允许通过Query传输Token
	UseQuery bool

	// Query参数名称
	QueryName string
}

// DefaultJWTConfig 默认JWT配置
func DefaultJWTConfig() *JWTConfig {
	// 生成随机密钥（仅用于开发环境）
	secret := generateRandomKey(32)

	return &JWTConfig{
		Secret:           secret,
		Issuer:           "athena-gateway",
		Expiration:       24 * time.Hour,
		RefreshExpiration: 7 * 24 * time.Hour,
		CookieName:       "jwt_token",
		UseCookie:        true,
		UseHeader:        true,
		HeaderName:       "Authorization",
		UseQuery:         false,
		QueryName:        "token",
	}
}

// Claims JWT声明
type Claims struct {
	UserID   string                 `json:"user_id"`
	Username string                 `json:"username"`
	Roles    []string               `json:"roles"`
	Metadata map[string]interface{} `json:"metadata"`
	jwt.RegisteredClaims
}

// TokenPair Token对（访问令牌 + 刷新令牌）
type TokenPair struct {
	AccessToken  string    `json:"access_token"`
	RefreshToken string    `json:"refresh_token"`
	ExpiresAt    time.Time `json:"expires_at"`
}

// JWTManager JWT管理器
type JWTManager struct {
	config *JWTConfig
}

// NewJWTManager 创建JWT管理器
func NewJWTManager(config *JWTConfig) *JWTManager {
	if config == nil {
		config = DefaultJWTConfig()
	}

	// 设置默认值
	if config.Issuer == "" {
		config.Issuer = "athena-gateway"
	}
	if config.Expiration == 0 {
		config.Expiration = 24 * time.Hour
	}
	if config.RefreshExpiration == 0 {
		config.RefreshExpiration = 7 * 24 * time.Hour
	}
	if config.CookieName == "" {
		config.CookieName = "jwt_token"
	}
	if config.HeaderName == "" {
		config.HeaderName = "Authorization"
	}
	if config.QueryName == "" {
		config.QueryName = "token"
	}

	return &JWTManager{
		config: config,
	}
}

// GenerateToken 生成Token对
func (j *JWTManager) GenerateToken(userID, username string, roles []string, metadata map[string]interface{}) (*TokenPair, error) {
	now := time.Now()

	// 创建访问令牌声明
	accessClaims := &Claims{
		UserID:   userID,
		Username: username,
		Roles:    roles,
		Metadata: metadata,
		RegisteredClaims: jwt.RegisteredClaims{
			Issuer:    j.config.Issuer,
			Subject:   userID,
			ExpiresAt: jwt.NewNumericDate(now.Add(j.config.Expiration)),
			IssuedAt:  jwt.NewNumericDate(now),
			NotBefore: jwt.NewNumericDate(now),
		},
	}

	// 创建刷新令牌声明
	refreshClaims := &Claims{
		UserID:   userID,
		Username: username,
		Roles:    roles,
		Metadata: metadata,
		RegisteredClaims: jwt.RegisteredClaims{
			Issuer:    j.config.Issuer,
			Subject:   userID,
			ExpiresAt: jwt.NewNumericDate(now.Add(j.config.RefreshExpiration)),
			IssuedAt:  jwt.NewNumericDate(now),
			NotBefore: jwt.NewNumericDate(now),
		},
	}

	// 生成访问令牌
	accessToken, err := jwt.NewWithClaims(jwt.SigningMethodHS256, accessClaims).SignedString([]byte(j.config.Secret))
	if err != nil {
		return nil, fmt.Errorf("生成访问令牌失败: %w", err)
	}

	// 生成刷新令牌
	refreshToken, err := jwt.NewWithClaims(jwt.SigningMethodHS256, refreshClaims).SignedString([]byte(j.config.Secret))
	if err != nil {
		return nil, fmt.Errorf("生成刷新令牌失败: %w", err)
	}

	return &TokenPair{
		AccessToken:   accessToken,
		RefreshToken:  refreshToken,
		ExpiresAt:     now.Add(j.config.Expiration),
	}, nil
}

// ValidateToken 验证Token
func (j *JWTManager) ValidateToken(tokenString string) (*Claims, error) {
	token, err := jwt.ParseWithClaims(tokenString, &Claims{}, func(token *jwt.Token) (interface{}, error) {
		// 验证签名算法
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, fmt.Errorf("意外的签名方法: %v", token.Header["alg"])
		}
		return []byte(j.config.Secret), nil
	})

	if err != nil {
		return nil, err
	}

	if claims, ok := token.Claims.(*Claims); ok && token.Valid {
		return claims, nil
	}

	return nil, errors.New("无效的令牌")
}

// RefreshToken 刷新Token
func (j *JWTManager) RefreshToken(refreshToken string) (*TokenPair, error) {
	// 验证刷新令牌
	claims, err := j.ValidateToken(refreshToken)
	if err != nil {
		return nil, fmt.Errorf("刷新令牌无效: %w", err)
	}

	// 生成新的Token对
	return j.GenerateToken(claims.UserID, claims.Username, claims.Roles, claims.Metadata)
}

// ExtractToken 从请求中提取Token
func (j *JWTManager) ExtractToken(c *gin.Context) string {
	var token string

	// 1. 尝试从Header获取
	if j.config.UseHeader {
		authHeader := c.GetHeader(j.config.HeaderName)
		if authHeader != "" {
			// 支持 "Bearer <token>" 格式
			if strings.HasPrefix(authHeader, "Bearer ") {
				token = strings.TrimPrefix(authHeader, "Bearer ")
			} else {
				token = authHeader
			}
			if token != "" {
				return token
			}
		}
	}

	// 2. 尝试从Cookie获取
	if j.config.UseCookie {
		if cookie, err := c.Cookie(j.config.CookieName); err == nil {
			return cookie
		}
	}

	// 3. 尝试从Query获取
	if j.config.UseQuery {
		if token = c.Query(j.config.QueryName); token != "" {
			return token
		}
	}

	return ""
}

// SetTokenCookie 设置Token Cookie
func (j *JWTManager) SetTokenCookie(c *gin.Context, token string) {
	if !j.config.UseCookie {
		return
	}

	// 设置Cookie（HttpOnly防止XSS）
	c.SetSameSite(http.SameSiteStrictMode)
	c.SetCookie(
		j.config.CookieName,
		token,
		int(j.config.Expiration.Seconds()),
		"/",
		"",
		false, // Secure（生产环境应设为true）
		true,  // HttpOnly
	)
}

// ClearTokenCookie 清除Token Cookie
func (j *JWTManager) ClearTokenCookie(c *gin.Context) {
	if !j.config.UseCookie {
		return
	}

	c.SetSameSite(http.SameSiteStrictMode)
	c.SetCookie(
		j.config.CookieName,
		"",
		-1,
		"/",
		"",
		false,
		true,
	)
}

// AuthMiddleware JWT认证中间件
func (j *JWTManager) AuthMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		// 提取Token
		token := j.ExtractToken(c)
		if token == "" {
			c.JSON(http.StatusUnauthorized, gin.H{
				"success": false,
				"error":   "未提供认证令牌",
			})
			c.Abort()
			return
		}

		// 验证Token
		claims, err := j.ValidateToken(token)
		if err != nil {
			c.JSON(http.StatusUnauthorized, gin.H{
				"success": false,
				"error":   "令牌无效或已过期",
			})
			c.Abort()
			return
		}

		// 将用户信息存入上下文
		c.Set("user_id", claims.UserID)
		c.Set("username", claims.Username)
		c.Set("roles", claims.Roles)
		c.Set("claims", claims)

		c.Next()
	}
}

// RequireRoles 角色验证中间件
func (j *JWTManager) RequireRoles(roles ...string) gin.HandlerFunc {
	return func(c *gin.Context) {
		// 获取用户角色
		userRoles, exists := c.Get("roles")
		if !exists {
			c.JSON(http.StatusForbidden, gin.H{
				"success": false,
				"error":   "无法获取用户角色",
			})
			c.Abort()
			return
		}

		userRoleList, ok := userRoles.([]string)
		if !ok {
			c.JSON(http.StatusForbidden, gin.H{
				"success": false,
				"error":   "无效的角色格式",
			})
			c.Abort()
			return
		}

		// 检查是否有任一所需角色
		hasRole := false
		for _, requiredRole := range roles {
			for _, userRole := range userRoleList {
				if userRole == requiredRole {
					hasRole = true
					break
				}
			}
			if hasRole {
				break
			}
		}

		if !hasRole {
			c.JSON(http.StatusForbidden, gin.H{
				"success": false,
				"error":   "权限不足",
			})
			c.Abort()
			return
		}

		c.Next()
	}
}

// OptionalAuth 可选认证中间件（允许匿名访问，但如果提供Token则验证）
func (j *JWTManager) OptionalAuth() gin.HandlerFunc {
	return func(c *gin.Context) {
		token := j.ExtractToken(c)
		if token != "" {
			// 尝试验证Token
			if claims, err := j.ValidateToken(token); err == nil {
				c.Set("user_id", claims.UserID)
				c.Set("username", claims.Username)
				c.Set("roles", claims.Roles)
				c.Set("claims", claims)
				c.Set("authenticated", true)
			}
		}

		c.Next()
	}
}

// generateRandomKey 生成随机密钥
func generateRandomKey(length int) string {
	bytes := make([]byte, length)
	if _, err := rand.Read(bytes); err != nil {
		// 如果随机数生成失败，使用时间戳作为后备
		return base64.StdEncoding.EncodeToString([]byte(fmt.Sprintf("%d", time.Now().UnixNano())))
	}
	return base64.StdEncoding.EncodeToString(bytes)
}
