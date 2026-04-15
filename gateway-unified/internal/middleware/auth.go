package middleware

import (
	"crypto/subtle"
	"encoding/base64"
	"net/http"
	"strings"
	"sync"

	"github.com/gin-gonic/gin"
)

// AuthConfig 认证配置
type AuthConfig struct {
	// API Keys列表
	APIKeys map[string]bool
	// API Keys 读写锁
	apiKeysMu sync.RWMutex

	// Bearer Tokens列表
	BearerTokens map[string]bool
	bearerTokensMu sync.RWMutex

	// 基本认证用户名密码
	BasicAuth map[string]string
	basicAuthMu sync.RWMutex

	// IP白名单
	IPWhitelist map[string]bool
	ipWhitelistMu sync.RWMutex

	// 是否启用认证
	EnableAPIKey    bool
	EnableBearer    bool
	EnableBasicAuth bool
	EnableIPWhitelist bool
}

// NewAuthConfig 创建认证配置
func NewAuthConfig() *AuthConfig {
	return &AuthConfig{
		APIKeys:       make(map[string]bool),
		BearerTokens:  make(map[string]bool),
		BasicAuth:     make(map[string]string),
		IPWhitelist:   make(map[string]bool),
	}
}

// AddAPIKey 添加API Key
func (a *AuthConfig) AddAPIKey(key string) {
	a.apiKeysMu.Lock()
	defer a.apiKeysMu.Unlock()
	a.APIKeys[key] = true
}

// RemoveAPIKey 移除API Key
func (a *AuthConfig) RemoveAPIKey(key string) {
	a.apiKeysMu.Lock()
	defer a.apiKeysMu.Unlock()
	delete(a.APIKeys, key)
}

// AddBearerToken 添加Bearer Token
func (a *AuthConfig) AddBearerToken(token string) {
	a.bearerTokensMu.Lock()
	defer a.bearerTokensMu.Unlock()
	a.BearerTokens[token] = true
}

// AddBasicAuthUser 添加基本认证用户
func (a *AuthConfig) AddBasicAuthUser(username, password string) {
	a.basicAuthMu.Lock()
	defer a.basicAuthMu.Unlock()
	a.BasicAuth[username] = password
}

// AddIPToWhitelist 添加IP到白名单
func (a *AuthConfig) AddIPToWhitelist(ip string) {
	a.ipWhitelistMu.Lock()
	defer a.ipWhitelistMu.Unlock()
	a.IPWhitelist[ip] = true
}

// RemoveIPFromWhitelist 从白名单移除IP
func (a *AuthConfig) RemoveIPFromWhitelist(ip string) {
	a.ipWhitelistMu.Lock()
	defer a.ipWhitelistMu.Unlock()
	delete(a.IPWhitelist, ip)
}

// AuthMiddleware 认证中间件
func (a *AuthConfig) AuthMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		// IP白名单检查
		if a.EnableIPWhitelist && !a.checkIPWhitelist(c) {
			c.JSON(http.StatusForbidden, gin.H{
				"success": false,
				"error":    "IP地址未在白名单中",
			})
			c.Abort()
			return
		}

		// 尝试各种认证方式
		authenticated := false

		// 1. 检查API Key
		if a.EnableAPIKey && a.checkAPIKey(c) {
			authenticated = true
		}

		// 2. 检查Bearer Token
		if !authenticated && a.EnableBearer && a.checkBearerToken(c) {
			authenticated = true
		}

		// 3. 检查基本认证
		if !authenticated && a.EnableBasicAuth && a.checkBasicAuth(c) {
			authenticated = true
		}

		if !authenticated && (a.EnableAPIKey || a.EnableBearer || a.EnableBasicAuth) {
			// 返回401未授权
			c.Header("WWW-Authenticate", `Bearer realm="Athena Gateway"`)
			c.JSON(http.StatusUnauthorized, gin.H{
				"success": false,
				"error":    "未授权访问",
			})
			c.Abort()
			return
		}

		c.Next()
	}
}

// checkAPIKey 检查API Key
func (a *AuthConfig) checkAPIKey(c *gin.Context) bool {
	apiKey := c.GetHeader("X-API-Key")
	if apiKey == "" {
		return false
	}

	a.apiKeysMu.RLock()
	defer a.apiKeysMu.RUnlock()

	return a.APIKeys[apiKey]
}

// checkBearerToken 检查Bearer Token
func (a *AuthConfig) checkBearerToken(c *gin.Context) bool {
	authHeader := c.GetHeader("Authorization")
	if authHeader == "" {
		return false
	}

	// 检查Bearer前缀
	if !strings.HasPrefix(authHeader, "Bearer ") {
		return false
	}

	token := strings.TrimPrefix(authHeader, "Bearer ")

	a.bearerTokensMu.RLock()
	defer a.bearerTokensMu.RUnlock()

	return a.BearerTokens[token]
}

// checkBasicAuth 检查基本认证
func (a *AuthConfig) checkBasicAuth(c *gin.Context) bool {
	username, password, ok := c.Request.BasicAuth()
	if !ok {
		return false
	}

	a.basicAuthMu.RLock()
	defer a.basicAuthMu.RUnlock()

	// 使用constant-time比较防止时序攻击
	storedPassword, exists := a.BasicAuth[username]
	if !exists {
		return false
	}

	return subtle.ConstantTimeCompare([]byte(password), []byte(storedPassword)) == 1
}

// checkIPWhitelist 检查IP白名单
func (a *AuthConfig) checkIPWhitelist(c *gin.Context) bool {
	clientIP := c.ClientIP()

	a.ipWhitelistMu.RLock()
	defer a.ipWhitelistMu.RUnlock()

	return a.IPWhitelist[clientIP]
}

// decodeBasicAuth 解码基本认证
func decodeBasicAuth(auth string) (username, password string, ok bool) {
	const prefix = "Basic "
	if !strings.HasPrefix(auth, prefix) {
		return
	}
	c, err := base64.StdEncoding.DecodeString(strings.TrimPrefix(auth, prefix))
	if err != nil {
		return
	}
	cs := string(c)
	s := strings.IndexByte(cs, ':')
	if s < 0 {
		return
	}
	return cs[:s], cs[s+1:], true
}

// LoadAuthFromConfig 从配置加载认证信息
func (a *AuthConfig) LoadAuthFromConfig(config map[string]interface{}) {
	// 加载API Keys
	if apiKeys, ok := config["api_keys"].([]interface{}); ok {
		for _, key := range apiKeys {
			if keyStr, ok := key.(string); ok {
				a.AddAPIKey(keyStr)
			}
		}
		a.EnableAPIKey = true
	}

	// 加载Bearer Tokens
	if bearerTokens, ok := config["bearer_tokens"].([]interface{}); ok {
		for _, token := range bearerTokens {
			if tokenStr, ok := token.(string); ok {
				a.AddBearerToken(tokenStr)
			}
		}
		a.EnableBearer = true
	}

	// 加载基本认证
	if basicAuth, ok := config["basic_auth"].(map[string]interface{}); ok {
		for username, password := range basicAuth {
			if passwordStr, ok := password.(string); ok {
				a.AddBasicAuthUser(username, passwordStr)
			}
		}
		a.EnableBasicAuth = true
	}

	// 加载IP白名单
	if ipWhitelist, ok := config["ip_whitelist"].([]interface{}); ok {
		for _, ip := range ipWhitelist {
			if ipStr, ok := ip.(string); ok {
				a.AddIPToWhitelist(ipStr)
			}
		}
		a.EnableIPWhitelist = true
	}
}
