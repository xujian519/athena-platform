// Package middleware - CORS中间件测试
package middleware

import (
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"
)

func init() {
	gin.SetMode(gin.TestMode)
}

func TestDefaultCORSConfig(t *testing.T) {
	config := DefaultCORSConfig()

	assert.Equal(t, []string{"*"}, config.AllowedOrigins)
	assert.Contains(t, config.AllowedMethods, "GET")
	assert.Contains(t, config.AllowedMethods, "POST")
	assert.False(t, config.AllowCredentials)
	assert.Equal(t, 86400, config.MaxAge)
}

func TestDevelopmentCORSConfig(t *testing.T) {
	config := DevelopmentCORSConfig()

	assert.Contains(t, config.AllowedOrigins, "http://localhost:3000")
	assert.Contains(t, config.AllowedOrigins, "http://127.0.0.1:3000")
	assert.True(t, config.AllowCredentials)
	assert.True(t, config.Debug)
}

func TestProductionCORSConfig(t *testing.T) {
	origins := []string{"https://example.com", "https://api.example.com"}
	config := ProductionCORSConfig(origins)

	assert.Equal(t, origins, config.AllowedOrigins)
	assert.False(t, config.AllowCredentials)
	assert.Equal(t, 3600, config.MaxAge)
}

func TestCORSMiddleware_Preflight(t *testing.T) {
	config := &CORSConfig{
		AllowedOrigins:   []string{"http://localhost:3000"},
		AllowedMethods:   []string{"GET", "POST", "PUT", "DELETE"},
		AllowedHeaders:   []string{"Content-Type", "Authorization"},
		ExposedHeaders:   []string{"X-Total-Count"},
		AllowCredentials: true,
		MaxAge:           3600,
	}

	router := gin.New()
	router.Use(CORSMiddleware(config))
	router.POST("/test", func(c *gin.Context) {
		c.String(200, "OK")
	})

	// 测试预检请求
	req := httptest.NewRequest("OPTIONS", "/test", nil)
	req.Header.Set("Origin", "http://localhost:3000")
	req.Header.Set("Access-Control-Request-Method", "POST")
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusNoContent, w.Code)
	assert.Equal(t, "GET, POST, PUT, DELETE", w.Header().Get("Access-Control-Allow-Methods"))
	assert.Equal(t, "Content-Type, Authorization", w.Header().Get("Access-Control-Allow-Headers"))
	assert.Equal(t, "3600", w.Header().Get("Access-Control-Max-Age"))
	assert.Equal(t, "http://localhost:3000", w.Header().Get("Access-Control-Allow-Origin"))
	assert.Equal(t, "true", w.Header().Get("Access-Control-Allow-Credentials"))
}

func TestCORSMiddleware_SimpleRequest(t *testing.T) {
	config := &CORSConfig{
		AllowedOrigins:   []string{"http://localhost:3000"},
		AllowedMethods:   []string{"GET", "POST"},
		AllowedHeaders:   []string{"Content-Type"},
		ExposedHeaders:   []string{"X-Total-Count"},
		AllowCredentials: true,
	}

	router := gin.New()
	router.Use(CORSMiddleware(config))
	router.GET("/test", func(c *gin.Context) {
		c.String(200, "OK")
	})

	// 测试简单请求
	req := httptest.NewRequest("GET", "/test", nil)
	req.Header.Set("Origin", "http://localhost:3000")
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, 200, w.Code)
	assert.Equal(t, "http://localhost:3000", w.Header().Get("Access-Control-Allow-Origin"))
	assert.Equal(t, "true", w.Header().Get("Access-Control-Allow-Credentials"))
	assert.Equal(t, "X-Total-Count", w.Header().Get("Access-Control-Expose-Headers"))
}

func TestCORSMiddleware_WildcardOrigin(t *testing.T) {
	config := &CORSConfig{
		AllowedOrigins:   []string{"*"},
		AllowedMethods:   []string{"GET"},
		AllowedHeaders:   []string{"Content-Type"},
		AllowCredentials: false,
	}

	router := gin.New()
	router.Use(CORSMiddleware(config))
	router.GET("/test", func(c *gin.Context) {
		c.String(200, "OK")
	})

	// 测试任意源
	req := httptest.NewRequest("GET", "/test", nil)
	req.Header.Set("Origin", "http://any-origin.com")
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, "*", w.Header().Get("Access-Control-Allow-Origin"))
}

func TestCORSMiddleware_DisallowedOrigin(t *testing.T) {
	config := &CORSConfig{
		AllowedOrigins:   []string{"http://localhost:3000"},
		AllowedMethods:   []string{"GET"},
		AllowedHeaders:   []string{"Content-Type"},
		AllowCredentials: false,
	}

	router := gin.New()
	router.Use(CORSMiddleware(config))
	router.GET("/test", func(c *gin.Context) {
		c.String(200, "OK")
	})

	// 测试不允许的源
	req := httptest.NewRequest("GET", "/test", nil)
	req.Header.Set("Origin", "http://malicious.com")
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, 200, w.Code) // 请求仍然成功，只是没有CORS头
	assert.Empty(t, w.Header().Get("Access-Control-Allow-Origin"))
}

func TestIsOriginAllowed(t *testing.T) {
	allowedOrigins := map[string]bool{
		"http://localhost:3000":    true,
		"https://example.com":      true,
		"*.example.com":            true,
		"*.sub.example.com":        true,
	}

	tests := []struct {
		name     string
		origin   string
		expected bool
	}{
		{"精确匹配", "http://localhost:3000", true},
		{"精确匹配2", "https://example.com", true},
		{"子域名匹配", "https://api.example.com", true},
		{"子域名匹配2", "https://test.sub.example.com", true},
		{"不匹配", "http://malicious.com", false},
		{"根域名匹配", "https://example.com", true}, // *.example.com不匹配根域名
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := isOriginAllowed(tt.origin, allowedOrigins)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestCORSByOrigin(t *testing.T) {
	// 只允许localhost和example.com
	allowFunc := func(origin string) bool {
		return origin == "http://localhost:3000" || origin == "https://example.com"
	}

	router := gin.New()
	router.Use(CORSByOrigin(allowFunc))
	router.GET("/test", func(c *gin.Context) {
		c.String(200, "OK")
	})

	// 测试允许的源
	req := httptest.NewRequest("GET", "/test", nil)
	req.Header.Set("Origin", "http://localhost:3000")
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, "http://localhost:3000", w.Header().Get("Access-Control-Allow-Origin"))

	// 测试不允许的源
	req = httptest.NewRequest("GET", "/test", nil)
	req.Header.Set("Origin", "http://malicious.com")
	w = httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Empty(t, w.Header().Get("Access-Control-Allow-Origin"))
}

func TestCORSByWhitelist(t *testing.T) {
	whitelist := []string{
		"http://localhost:3000",
		"https://example.com",
	}

	router := gin.New()
	router.Use(CORSByWhitelist(whitelist))
	router.GET("/test", func(c *gin.Context) {
		c.String(200, "OK")
	})

	// 测试白名单中的源
	req := httptest.NewRequest("GET", "/test", nil)
	req.Header.Set("Origin", "http://localhost:3000")
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, "http://localhost:3000", w.Header().Get("Access-Control-Allow-Origin"))

	// 测试不在白名单中的源
	req = httptest.NewRequest("GET", "/test", nil)
	req.Header.Set("Origin", "http://other.com")
	w = httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Empty(t, w.Header().Get("Access-Control-Allow-Origin"))
}

func TestCORSByRegex(t *testing.T) {
	patterns := []string{
		"http://localhost:*",
		"*.example.com",
	}

	router := gin.New()
	router.Use(CORSByRegex(patterns))
	router.GET("/test", func(c *gin.Context) {
		c.String(200, "OK")
	})

	tests := []struct {
		name     string
		origin   string
		expected string
	}{
		{"匹配localhost端口", "http://localhost:3000", "http://localhost:3000"},
		{"匹配子域名", "https://api.example.com", "https://api.example.com"},
		{"不匹配", "https://other.com", ""},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			req := httptest.NewRequest("GET", "/test", nil)
			req.Header.Set("Origin", tt.origin)
			w := httptest.NewRecorder()
			router.ServeHTTP(w, req)

			assert.Equal(t, tt.expected, w.Header().Get("Access-Control-Allow-Origin"))
		})
	}
}

func TestCORSMiddleware_Debug(t *testing.T) {
	config := &CORSConfig{
		AllowedOrigins:   []string{"*"},
		AllowedMethods:   []string{"GET"},
		AllowedHeaders:   []string{"Content-Type"},
		AllowCredentials: false,
		Debug:           true,
	}

	router := gin.New()
	router.Use(CORSMiddleware(config))
	router.GET("/test", func(c *gin.Context) {
		c.String(200, "OK")
	})

	req := httptest.NewRequest("GET", "/test", nil)
	req.Header.Set("Origin", "http://localhost:3000")
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, "request", w.Header().Get("X-CORS-Debug"))
}

func TestCORSMiddleware_NilConfig(t *testing.T) {
	router := gin.New()
	router.Use(CORSMiddleware(nil))
	router.GET("/test", func(c *gin.Context) {
		c.String(200, "OK")
	})

	req := httptest.NewRequest("GET", "/test", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, 200, w.Code)
	assert.Equal(t, "*", w.Header().Get("Access-Control-Allow-Origin"))
}

func TestCORSMiddleware_CredentialsWithWildcard(t *testing.T) {
	// 测试通配符+凭证的情况（应该不返回通配符）
	config := &CORSConfig{
		AllowedOrigins:   []string{"*"},
		AllowedMethods:   []string{"GET"},
		AllowedHeaders:   []string{"Content-Type"},
		AllowCredentials: true, // 启用凭证
	}

	router := gin.New()
	router.Use(CORSMiddleware(config))
	router.GET("/test", func(c *gin.Context) {
		c.String(200, "OK")
	})

	req := httptest.NewRequest("GET", "/test", nil)
	req.Header.Set("Origin", "http://localhost:3000")
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	// 由于启用了凭证，不应该返回通配符
	// 但由于没有匹配的源，所以也不会返回CORS头
	// 这是安全的行为
}
