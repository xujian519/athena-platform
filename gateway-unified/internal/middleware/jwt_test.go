// Package middleware - JWT中间件测试
package middleware

import (
	"net/http/httptest"
	"testing"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"
)

func init() {
	gin.SetMode(gin.TestMode)
}

func TestDefaultJWTConfig(t *testing.T) {
	config := DefaultJWTConfig()

	assert.NotEmpty(t, config.Secret, "密钥不应为空")
	assert.Equal(t, "athena-gateway", config.Issuer)
	assert.Equal(t, 24*time.Hour, config.Expiration)
	assert.Equal(t, 7*24*time.Hour, config.RefreshExpiration)
	assert.True(t, config.UseCookie)
	assert.True(t, config.UseHeader)
	assert.False(t, config.UseQuery)
}

func TestNewJWTManager(t *testing.T) {
	config := &JWTConfig{
		Secret:     "test-secret",
		Issuer:     "test-issuer",
		Expiration: 1 * time.Hour,
	}

	manager := NewJWTManager(config)

	assert.NotNil(t, manager)
	assert.Equal(t, config, manager.config)
}

func TestNewJWTManager_NilConfig(t *testing.T) {
	manager := NewJWTManager(nil)

	assert.NotNil(t, manager)
	assert.NotNil(t, manager.config)
	assert.NotEmpty(t, manager.config.Secret)
}

func TestJWTManager_GenerateToken(t *testing.T) {
	manager := NewJWTManager(&JWTConfig{
		Secret:     "test-secret",
		Issuer:     "test-issuer",
		Expiration: 1 * time.Hour,
	})

	userID := "user123"
	username := "testuser"
	roles := []string{"admin", "user"}
	metadata := map[string]interface{}{
		"department": "engineering",
	}

	tokenPair, err := manager.GenerateToken(userID, username, roles, metadata)

	assert.NoError(t, err)
	assert.NotEmpty(t, tokenPair.AccessToken)
	assert.NotEmpty(t, tokenPair.RefreshToken)
	assert.True(t, tokenPair.ExpiresAt.After(time.Now()))
}

func TestJWTManager_ValidateToken(t *testing.T) {
	manager := NewJWTManager(&JWTConfig{
		Secret:     "test-secret",
		Issuer:     "test-issuer",
		Expiration: 1 * time.Hour,
	})

	// 生成Token
	tokenPair, err := manager.GenerateToken("user123", "testuser", []string{"admin"}, nil)
	assert.NoError(t, err)

	// 验证Token
	claims, err := manager.ValidateToken(tokenPair.AccessToken)

	assert.NoError(t, err)
	assert.Equal(t, "user123", claims.UserID)
	assert.Equal(t, "testuser", claims.Username)
	assert.Equal(t, "test-issuer", claims.Issuer)
}

func TestJWTManager_ValidateToken_Invalid(t *testing.T) {
	manager := NewJWTManager(&JWTConfig{
		Secret: "test-secret",
	})

	// 测试无效Token
	_, err := manager.ValidateToken("invalid-token")

	assert.Error(t, err)
}

func TestJWTManager_ValidateToken_WrongSecret(t *testing.T) {
	manager1 := NewJWTManager(&JWTConfig{
		Secret: "secret1",
	})

	manager2 := NewJWTManager(&JWTConfig{
		Secret: "secret2",
	})

	// 用manager1生成Token
	tokenPair, err := manager1.GenerateToken("user123", "testuser", []string{}, nil)
	assert.NoError(t, err)

	// 用manager2验证（应该失败）
	_, err = manager2.ValidateToken(tokenPair.AccessToken)

	assert.Error(t, err)
}

func TestJWTManager_RefreshToken(t *testing.T) {
	manager := NewJWTManager(&JWTConfig{
		Secret:            "test-secret",
		Expiration:        1 * time.Hour,
		RefreshExpiration: 24 * time.Hour,
	})

	// 生成初始Token
	tokenPair, err := manager.GenerateToken("user123", "testuser", []string{"admin"}, nil)
	assert.NoError(t, err)

	// 刷新Token
	newTokenPair, err := manager.RefreshToken(tokenPair.RefreshToken)

	assert.NoError(t, err)
	assert.NotEmpty(t, newTokenPair.AccessToken)
	assert.NotEmpty(t, newTokenPair.RefreshToken)
	// 注意：由于时间戳不同，Token内容会不同，但都有效
	// 只验证新Token有效即可
	claims, err := manager.ValidateToken(newTokenPair.AccessToken)
	assert.NoError(t, err)
	assert.Equal(t, "user123", claims.UserID)
}

func TestJWTManager_ExtractToken_FromHeader(t *testing.T) {
	config := &JWTConfig{
		Secret:     "test-secret",
		UseHeader:  true,
		HeaderName: "Authorization",
	}
	manager := NewJWTManager(config)

	// 创建测试路由
	router := gin.New()
	router.Use(func(c *gin.Context) {
		token := manager.ExtractToken(c)
		c.Set("token", token)
		c.Next()
	})
	router.GET("/test", func(c *gin.Context) {
		token, _ := c.Get("token")
		c.String(200, token.(string))
	})

	// 测试Bearer格式
	req := httptest.NewRequest("GET", "/test", nil)
	req.Header.Set("Authorization", "Bearer test-token-123")
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, "test-token-123", w.Body.String())

	// 测试直接Token格式
	req = httptest.NewRequest("GET", "/test", nil)
	req.Header.Set("Authorization", "test-token-456")
	w = httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, "test-token-456", w.Body.String())
}

func TestJWTManager_AuthMiddleware_Success(t *testing.T) {
	config := &JWTConfig{
		Secret:     "test-secret",
		UseHeader:  true,
		HeaderName: "Authorization",
	}
	manager := NewJWTManager(config)

	// 生成有效Token
	tokenPair, err := manager.GenerateToken("user123", "testuser", []string{"admin"}, nil)
	assert.NoError(t, err)

	// 创建测试路由
	router := gin.New()
	router.Use(manager.AuthMiddleware())
	router.GET("/protected", func(c *gin.Context) {
		userID, _ := c.Get("user_id")
		username, _ := c.Get("username")
		c.JSON(200, gin.H{
			"user_id":  userID,
			"username": username,
		})
	})

	// 测试有效Token
	req := httptest.NewRequest("GET", "/protected", nil)
	req.Header.Set("Authorization", "Bearer "+tokenPair.AccessToken)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, 200, w.Code)
}

func TestJWTManager_AuthMiddleware_NoToken(t *testing.T) {
	config := &JWTConfig{
		Secret:     "test-secret",
		UseHeader:  true,
		HeaderName: "Authorization",
	}
	manager := NewJWTManager(config)

	// 创建测试路由
	router := gin.New()
	router.Use(manager.AuthMiddleware())
	router.GET("/protected", func(c *gin.Context) {
		c.String(200, "OK")
	})

	// 测试无Token
	req := httptest.NewRequest("GET", "/protected", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, 401, w.Code)
}

func TestJWTManager_AuthMiddleware_InvalidToken(t *testing.T) {
	config := &JWTConfig{
		Secret:     "test-secret",
		UseHeader:  true,
		HeaderName: "Authorization",
	}
	manager := NewJWTManager(config)

	// 创建测试路由
	router := gin.New()
	router.Use(manager.AuthMiddleware())
	router.GET("/protected", func(c *gin.Context) {
		c.String(200, "OK")
	})

	// 测试无效Token
	req := httptest.NewRequest("GET", "/protected", nil)
	req.Header.Set("Authorization", "Bearer invalid-token")
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, 401, w.Code)
}

func TestJWTManager_RequireRoles_Success(t *testing.T) {
	config := &JWTConfig{
		Secret:     "test-secret",
		UseHeader:  true,
		HeaderName: "Authorization",
	}
	manager := NewJWTManager(config)

	// 生成带角色的Token
	tokenPair, err := manager.GenerateToken("user123", "testuser", []string{"admin", "user"}, nil)
	assert.NoError(t, err)

	// 创建测试路由
	router := gin.New()
	router.Use(manager.AuthMiddleware())
	router.GET("/admin", manager.RequireRoles("admin"), func(c *gin.Context) {
		c.String(200, "OK")
	})

	req := httptest.NewRequest("GET", "/admin", nil)
	req.Header.Set("Authorization", "Bearer "+tokenPair.AccessToken)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, 200, w.Code)
}

func TestJWTManager_RequireRoles_NoRole(t *testing.T) {
	config := &JWTConfig{
		Secret:     "test-secret",
		UseHeader:  true,
		HeaderName: "Authorization",
	}
	manager := NewJWTManager(config)

	// 生成不带admin角色的Token
	tokenPair, err := manager.GenerateToken("user123", "testuser", []string{"user"}, nil)
	assert.NoError(t, err)

	// 创建测试路由
	router := gin.New()
	router.Use(manager.AuthMiddleware())
	router.GET("/admin", manager.RequireRoles("admin"), func(c *gin.Context) {
		c.String(200, "OK")
	})

	req := httptest.NewRequest("GET", "/admin", nil)
	req.Header.Set("Authorization", "Bearer "+tokenPair.AccessToken)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, 403, w.Code)
}

func TestJWTManager_OptionalAuth(t *testing.T) {
	config := &JWTConfig{
		Secret:     "test-secret",
		UseHeader:  true,
		HeaderName: "Authorization",
	}
	manager := NewJWTManager(config)

	// 生成Token
	tokenPair, err := manager.GenerateToken("user123", "testuser", []string{"user"}, nil)
	assert.NoError(t, err)

	// 创建测试路由
	router := gin.New()
	router.Use(manager.OptionalAuth())
	router.GET("/public", func(c *gin.Context) {
		authenticated, _ := c.Get("authenticated")
		c.JSON(200, gin.H{
			"authenticated": authenticated,
		})
	})

	// 测试带Token的请求
	req := httptest.NewRequest("GET", "/public", nil)
	req.Header.Set("Authorization", "Bearer "+tokenPair.AccessToken)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, 200, w.Code)

	// 测试不带Token的请求
	req = httptest.NewRequest("GET", "/public", nil)
	w = httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, 200, w.Code)
}

func TestJWTManager_SetTokenCookie(t *testing.T) {
	config := &JWTConfig{
		Secret:     "test-secret",
		UseCookie:  true,
		CookieName: "jwt_token",
		Expiration: 1 * time.Hour,
	}
	manager := NewJWTManager(config)

	// 创建测试上下文
	router := gin.New()
	router.Use(func(c *gin.Context) {
		manager.SetTokenCookie(c, "test-token-123")
		c.Next()
	})
	router.GET("/test", func(c *gin.Context) {
		c.String(200, "OK")
	})

	req := httptest.NewRequest("GET", "/test", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	// 检查Cookie是否设置
	cookies := w.Result().Cookies()
	assert.Len(t, cookies, 1)
	assert.Equal(t, "jwt_token", cookies[0].Name)
	assert.Equal(t, "test-token-123", cookies[0].Value)
	assert.True(t, cookies[0].HttpOnly)
}

func TestJWTManager_ClearTokenCookie(t *testing.T) {
	config := &JWTConfig{
		Secret:     "test-secret",
		UseCookie:  true,
		CookieName: "jwt_token",
	}
	manager := NewJWTManager(config)

	// 创建测试上下文
	router := gin.New()
	router.Use(func(c *gin.Context) {
		manager.ClearTokenCookie(c)
		c.Next()
	})
	router.GET("/test", func(c *gin.Context) {
		c.String(200, "OK")
	})

	req := httptest.NewRequest("GET", "/test", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	// 检查Cookie是否清除
	cookies := w.Result().Cookies()
	assert.Len(t, cookies, 1)
	assert.Equal(t, "jwt_token", cookies[0].Name)
	assert.Empty(t, cookies[0].Value)
	assert.Equal(t, -1, cookies[0].MaxAge)
}
