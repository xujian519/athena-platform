package middleware

import (
	"net/http/httptest"
	"testing"

	"github.com/gin-gonic/gin"
)

func setupTestAuth() *AuthConfig {
	config := NewAuthConfig()

	// 添加测试数据
	config.AddAPIKey("test-api-key-123")
	config.AddBearerToken("test-bearer-token-456")
	config.AddBasicAuthUser("admin", "password123")
	config.AddIPToWhitelist("127.0.0.1")
	config.AddIPToWhitelist("::1")

	return config
}

func TestAPIKeyAuth(t *testing.T) {
	config := setupTestAuth()
	config.EnableAPIKey = true

	router := gin.New()
	router.Use(config.AuthMiddleware())
	router.GET("/test", func(c *gin.Context) {
		c.JSON(200, gin.H{"message": "success"})
	})

	// 测试有效的API Key
	req := httptest.NewRequest("GET", "/test", nil)
	req.Header.Set("X-API-Key", "test-api-key-123")
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != 200 {
		t.Errorf("有效API Key返回状态 %d, want 200", w.Code)
	}

	// 测试无效的API Key
	req = httptest.NewRequest("GET", "/test", nil)
	req.Header.Set("X-API-Key", "invalid-key")
	w = httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != 401 {
		t.Errorf("无效API Key返回状态 %d, want 401", w.Code)
	}
}

func TestBearerTokenAuth(t *testing.T) {
	config := setupTestAuth()
	config.EnableBearer = true

	router := gin.New()
	router.Use(config.AuthMiddleware())
	router.GET("/test", func(c *gin.Context) {
		c.JSON(200, gin.H{"message": "success"})
	})

	// 测试有效的Bearer Token
	req := httptest.NewRequest("GET", "/test", nil)
	req.Header.Set("Authorization", "Bearer test-bearer-token-456")
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != 200 {
		t.Errorf("有效Bearer Token返回状态 %d, want 200", w.Code)
	}

	// 测试无效的Bearer Token
	req = httptest.NewRequest("GET", "/test", nil)
	req.Header.Set("Authorization", "Bearer invalid-token")
	w = httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != 401 {
		t.Errorf("无效Bearer Token返回状态 %d, want 401", w.Code)
	}

	// 测试没有Bearer前缀
	req = httptest.NewRequest("GET", "/test", nil)
	req.Header.Set("Authorization", "test-bearer-token-456")
	w = httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != 401 {
		t.Errorf("没有Bearer前缀返回状态 %d, want 401", w.Code)
	}
}

func TestBasicAuth(t *testing.T) {
	config := setupTestAuth()
	config.EnableBasicAuth = true

	router := gin.New()
	router.Use(config.AuthMiddleware())
	router.GET("/test", func(c *gin.Context) {
		c.JSON(200, gin.H{"message": "success"})
	})

	// 测试有效的基本认证
	req := httptest.NewRequest("GET", "/test", nil)
	req.SetBasicAuth("admin", "password123")
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != 200 {
		t.Errorf("有效基本认证返回状态 %d, want 200", w.Code)
	}

	// 测试无效的基本认证
	req = httptest.NewRequest("GET", "/test", nil)
	req.SetBasicAuth("admin", "wrong-password")
	w = httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != 401 {
		t.Errorf("无效基本认证返回状态 %d, want 401", w.Code)
	}
}

func TestIPWhitelist(t *testing.T) {
	config := setupTestAuth()
	config.EnableIPWhitelist = true

	router := gin.New()
	router.Use(config.AuthMiddleware())
	router.GET("/test", func(c *gin.Context) {
		c.JSON(200, gin.H{"message": "success"})
	})

	// 测试白名单IP
	req := httptest.NewRequest("GET", "/test", nil)
	req.RemoteAddr = "127.0.0.1:12345"
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != 200 {
		t.Errorf("白名单IP返回状态 %d, want 200", w.Code)
	}

	// 测试非白名单IP
	config.RemoveIPFromWhitelist("127.0.0.1")
	config.RemoveIPFromWhitelist("::1")

	req = httptest.NewRequest("GET", "/test", nil)
	req.RemoteAddr = "192.168.1.100:12345"
	w = httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != 403 {
		t.Errorf("非白名单IP返回状态 %d, want 403", w.Code)
	}
}

func TestNoAuth(t *testing.T) {
	config := NewAuthConfig()
	// 不启用任何认证

	router := gin.New()
	router.Use(config.AuthMiddleware())
	router.GET("/test", func(c *gin.Context) {
		c.JSON(200, gin.H{"message": "success"})
	})

	req := httptest.NewRequest("GET", "/test", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != 200 {
		t.Errorf("未启用认证时应返回 200, got %d", w.Code)
	}
}

func TestLoadAuthFromConfig(t *testing.T) {
	config := NewAuthConfig()

	configData := map[string]interface{}{
		"api_keys": []interface{}{"key1", "key2"},
		"bearer_tokens": []interface{}{"token1", "token2"},
		"basic_auth": map[string]interface{}{
			"user1": "pass1",
			"user2": "pass2",
		},
		"ip_whitelist": []interface{}{"192.168.1.1", "10.0.0.1"},
	}

	config.LoadAuthFromConfig(configData)

	// 验证API Keys
	if !config.APIKeys["key1"] || !config.APIKeys["key2"] {
		t.Error("API Keys未正确加载")
	}

	// 验证Bearer Tokens
	if !config.BearerTokens["token1"] || !config.BearerTokens["token2"] {
		t.Error("Bearer Tokens未正确加载")
	}

	// 验证基本认证
	if config.BasicAuth["user1"] != "pass1" {
		t.Error("基本认证未正确加载")
	}

	// 验证IP白名单
	if !config.IPWhitelist["192.168.1.1"] {
		t.Error("IP白名单未正确加载")
	}

	// 验证认证已启用
	if !config.EnableAPIKey || !config.EnableBearer || !config.EnableBasicAuth || !config.EnableIPWhitelist {
		t.Error("认证未正确启用")
	}
}

func TestRemoveAPIKey(t *testing.T) {
	config := NewAuthConfig()
	config.AddAPIKey("test-key")

	if !config.APIKeys["test-key"] {
		t.Fatal("API Key未添加")
	}

	config.RemoveAPIKey("test-key")

	if config.APIKeys["test-key"] {
		t.Error("API Key未移除")
	}
}
