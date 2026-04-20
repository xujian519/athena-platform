// Package middleware - 版本管理中间件测试
package middleware

import (
	"net/http/httptest"
	"testing"

	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"
)

func init() {
	gin.SetMode(gin.TestMode)
}

func TestVersionExtraction(t *testing.T) {
	tests := []struct {
		name     string
		path     string
		expected string
	}{
		{"标准v1路径", "/api/v1/users", "v1"},
		{"标准v2路径", "/api/v2/users", "v2"},
		{"简写v1路径", "/v1/users", "v1"},
		{"简写v2路径", "/v2/users", "v2"},
		{"无版本路径", "/api/users", ""},
		{"根路径", "/", ""},
		{"嵌套路径", "/api/v1/legal/patents/search", "v1"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := extractVersionFromPath(tt.path)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestVersionConfig_RegisterVersion(t *testing.T) {
	config := NewVersionConfig()

	// 注册版本
	info := &APIVersion{
		Deprecated:    false,
		SunsetDate:    "",
		RemovedDate:   "",
		MigrationGuide: "",
	}
	config.RegisterVersion("v1", info)

	// 验证注册
	retrieved, exists := config.GetVersion("v1")
	assert.True(t, exists)
	assert.Equal(t, "v1", retrieved.Version)
	assert.False(t, retrieved.Deprecated)
}

func TestVersionConfig_UnregisterVersion(t *testing.T) {
	config := NewVersionConfig()

	// 注册然后注销
	info := &APIVersion{}
	config.RegisterVersion("v1", info)
	config.UnregisterVersion("v1")

	// 验证已注销
	_, exists := config.GetVersion("v1")
	assert.False(t, exists)
}

func TestVersionConfig_ListVersions(t *testing.T) {
	config := NewVersionConfig()

	// 注册多个版本
	config.RegisterVersion("v1", &APIVersion{})
	config.RegisterVersion("v2", &APIVersion{Deprecated: true})
	config.RegisterVersion("v3", &APIVersion{})

	// 列出版本
	versions := config.ListVersions()
	assert.Len(t, versions, 3)
}

func TestVersionConfig_DefaultVersion(t *testing.T) {
	config := NewVersionConfig()

	// 测试默认版本
	assert.Equal(t, "v1", config.GetDefaultVersion())

	// 设置新的默认版本
	config.SetDefaultVersion("v2")
	assert.Equal(t, "v2", config.GetDefaultVersion())
}

func TestVersionMiddleware_PathExtraction(t *testing.T) {
	config := NewVersionConfig()
	config.RegisterVersion("v1", &APIVersion{})
	config.RegisterVersion("v2", &APIVersion{})

	router := gin.New()
	router.Use(config.VersionMiddleware())
	router.GET("/api/v1/test", func(c *gin.Context) {
		version, _ := c.Get("api_version")
		c.JSON(200, gin.H{"version": version})
	})
	router.GET("/api/v2/test", func(c *gin.Context) {
		version, _ := c.Get("api_version")
		c.JSON(200, gin.H{"version": version})
	})

	// 测试v1路径
	req1 := httptest.NewRequest("GET", "/api/v1/test", nil)
	w1 := httptest.NewRecorder()
	router.ServeHTTP(w1, req1)
	assert.Equal(t, 200, w1.Code)
	assert.Contains(t, w1.Body.String(), "v1")

	// 测试v2路径
	req2 := httptest.NewRequest("GET", "/api/v2/test", nil)
	w2 := httptest.NewRecorder()
	router.ServeHTTP(w2, req2)
	assert.Equal(t, 200, w2.Code)
	assert.Contains(t, w2.Body.String(), "v2")
}

func TestVersionMiddleware_HeaderExtraction(t *testing.T) {
	config := NewVersionConfig()
	config.RegisterVersion("v1", &APIVersion{})
	config.RegisterVersion("v2", &APIVersion{})

	router := gin.New()
	router.Use(config.VersionMiddleware())
	router.GET("/api/test", func(c *gin.Context) {
		version, _ := c.Get("api_version")
		c.JSON(200, gin.H{"version": version})
	})

	// 测试从Header获取版本
	req := httptest.NewRequest("GET", "/api/test", nil)
	req.Header.Set("X-API-Version", "v2")
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, 200, w.Code)
	assert.Contains(t, w.Body.String(), "v2")
}

func TestVersionMiddleware_QueryExtraction(t *testing.T) {
	config := NewVersionConfig()
	config.RegisterVersion("v1", &APIVersion{})
	config.RegisterVersion("v2", &APIVersion{})

	router := gin.New()
	router.Use(config.VersionMiddleware())
	router.GET("/api/test", func(c *gin.Context) {
		version, _ := c.Get("api_version")
		c.JSON(200, gin.H{"version": version})
	})

	// 测试从查询参数获取版本
	req := httptest.NewRequest("GET", "/api/test?version=v2", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, 200, w.Code)
	assert.Contains(t, w.Body.String(), "v2")
}

func TestVersionMiddleware_InvalidVersion(t *testing.T) {
	config := NewVersionConfig()
	config.RegisterVersion("v1", &APIVersion{})
	// 不注册v2

	router := gin.New()
	router.Use(config.VersionMiddleware())
	router.GET("/api/v2/test", func(c *gin.Context) {
		c.JSON(200, gin.H{})
	})

	// 测试无效版本
	req := httptest.NewRequest("GET", "/api/v2/test", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, 400, w.Code)
	assert.Contains(t, w.Body.String(), "不支持的API版本")
}

func TestVersionMiddleware_DeprecatedVersion(t *testing.T) {
	config := NewVersionConfig()
	config.RegisterVersion("v1", &APIVersion{
		Deprecated:     true,
		SunsetDate:     "2026-12-31",
		RemovedDate:    "2027-01-01",
		MigrationGuide: "https://docs.example.com/migration-v1-to-v2",
	})

	router := gin.New()
	router.Use(config.VersionMiddleware())
	router.GET("/api/v1/test", func(c *gin.Context) {
		c.JSON(200, gin.H{})
	})

	// 测试废弃版本
	req := httptest.NewRequest("GET", "/api/v1/test", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, 200, w.Code)
	assert.Equal(t, "true", w.Header().Get("X-API-Deprecated"))
	assert.Equal(t, "v1", w.Header().Get("X-API-Deprecation-Version"))
	assert.Equal(t, "2026-12-31", w.Header().Get("Sunset"))
	assert.Equal(t, "2027-01-01", w.Header().Get("X-API-Removal-Date"))
	assert.Contains(t, w.Header().Get("Warning"), "deprecated")
}

func TestVersionMiddleware_VersionHeader(t *testing.T) {
	config := NewVersionConfig()
	config.IncludeVersionHeader = true
	config.RegisterVersion("v1", &APIVersion{})

	router := gin.New()
	router.Use(config.VersionMiddleware())
	router.GET("/api/v1/test", func(c *gin.Context) {
		c.JSON(200, gin.H{})
	})

	// 测试版本Header
	req := httptest.NewRequest("GET", "/api/v1/test", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, 200, w.Code)
	assert.Equal(t, "v1", w.Header().Get("X-API-Version"))
}

func TestRequireVersionMiddleware(t *testing.T) {
	config := NewVersionConfig()

	router := gin.New()
	router.GET("/api/test", config.RequireVersionMiddleware("v1"), func(c *gin.Context) {
		c.JSON(200, gin.H{"success": true})
	})

	// 测试正确版本
	req1 := httptest.NewRequest("GET", "/api/test", nil)
	req1.Header.Set("X-API-Version", "v1")
	w1 := httptest.NewRecorder()
	router.ServeHTTP(w1, req1)
	assert.Equal(t, 200, w1.Code)

	// 测试错误版本
	req2 := httptest.NewRequest("GET", "/api/test", nil)
	req2.Header.Set("X-API-Version", "v2")
	w2 := httptest.NewRecorder()
	router.ServeHTTP(w2, req2)
	assert.Equal(t, 400, w2.Code)
	assert.Contains(t, w2.Body.String(), "API版本不匹配")
}

func TestMinVersionMiddleware(t *testing.T) {
	config := NewVersionConfig()

	router := gin.New()
	router.GET("/api/test", config.MinVersionMiddleware("v2"), func(c *gin.Context) {
		c.JSON(200, gin.H{"success": true})
	})

	// 测试足够高的版本
	req1 := httptest.NewRequest("GET", "/api/test", nil)
	req1.Header.Set("X-API-Version", "v2")
	w1 := httptest.NewRecorder()
	router.ServeHTTP(w1, req1)
	assert.Equal(t, 200, w1.Code)

	// 测试版本过低
	req2 := httptest.NewRequest("GET", "/api/test", nil)
	req2.Header.Set("X-API-Version", "v1")
	w2 := httptest.NewRecorder()
	router.ServeHTTP(w2, req2)
	assert.Equal(t, 400, w2.Code)
	assert.Contains(t, w2.Body.String(), "API版本过低")
}

func TestCompareVersions(t *testing.T) {
	tests := []struct {
		name     string
		v1       string
		v2       string
		expected int
	}{
		{"v1 < v2", "v1", "v2", -1},
		{"v2 > v1", "v2", "v1", 1},
		{"v1 == v1", "v1", "v1", 0},
		{"v10 > v2", "v10", "v2", 1},  // 字符串比较，10 > 2
		{"无前缀比较", "1", "2", -1},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := compareVersions(tt.v1, tt.v2)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestLoadVersionsFromConfig(t *testing.T) {
	config := NewVersionConfig()

	// 模拟配置
	cfg := map[string]interface{}{
		"versions": []interface{}{
			map[string]interface{}{
				"version":   "v1",
				"deprecated": false,
			},
			map[string]interface{}{
				"version":        "v2",
				"deprecated":     true,
				"sunset_date":    "2026-12-31",
				"removed_date":   "2027-01-01",
				"migration_guide": "https://docs.example.com/migration",
			},
		},
		"default_version": "v2",
	}

	config.LoadVersionsFromConfig(cfg)

	// 验证加载结果
	v1, exists := config.GetVersion("v1")
	assert.True(t, exists)
	assert.False(t, v1.Deprecated)

	v2, exists := config.GetVersion("v2")
	assert.True(t, exists)
	assert.True(t, v2.Deprecated)
	assert.Equal(t, "2026-12-31", v2.SunsetDate)

	assert.Equal(t, "v2", config.GetDefaultVersion())
}
