package main

import (
	"context"
	"fmt"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"athena-gateway/internal/config"
	"athena-gateway/internal/gateway"
	"athena-gateway/internal/middleware"
	"athena-gateway/pkg/token"

	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
	"github.com/stretchr/testify/require"
	"github.com/stretchr/testify/suite"
)

// TestMain 测试主入口
func TestMain(m *testing.M) {
	// 设置测试模式
	gin.SetMode(gin.TestMode)

	// 运行测试
	m.Run()
}

// GatewayTestSuite 网关测试套件
type GatewayTestSuite struct {
	suite.Suite
	gw    *gateway.Gateway
	cfg   *config.Config
	token string
}

// SetupSuite 设置测试套件
func (suite *GatewayTestSuite) SetupSuite() {
	// 创建测试配置
	suite.cfg = &config.Config{
		Server: config.ServerConfig{
			Port:         8080,
			Host:         "localhost",
			Mode:         "test",
			ReadTimeout:  30,
			WriteTimeout: 30,
			IdleTimeout:  60,
		},
		Database: config.DatabaseConfig{
			Host:         "localhost",
			Port:         5432,
			User:         "test",
			Password:     "test",
			DBName:       "test_gateway",
			SSLMode:      "disable",
			MaxIdleConns: 5,
			MaxOpenConns: 20,
			MaxLifetime:  300,
		},
		Redis: config.RedisConfig{
			Host:     "localhost",
			Port:     6379,
			Password: "",
			DB:       1,
			PoolSize: 10,
		},
		JWT: config.JWTConfig{
			Secret:         "test-secret-key-at-least-32-characters-long",
			ExpirationTime: 3600,
			RefreshTime:    86400,
			Issuer:         "athena-gateway-test",
		},
		RateLimit: config.RateLimitConfig{
			Enabled:           true,
			RequestsPerMinute: 100,
			BurstSize:         200,
			WhitelistEnabled:  false,
			Whitelist:         []string{},
		},
		Services: config.ServicesConfig{
			Auth: config.ServiceConfig{
				URL:           "http://localhost:9001",
				Timeout:       30,
				RetryAttempts: 3,
				CircuitBreaker: config.CircuitBreakerConfig{
					Enabled:      true,
					Threshold:    5,
					Timeout:      60,
					ResetTimeout: 300,
					FailureRate:  0.5,
				},
			},
		},
		Monitoring: config.MonitoringConfig{
			Enabled: false,
			Port:    9090,
			Path:    "/metrics",
		},
		Logging: config.LoggingConfig{
			Level:  "debug",
			Format: "text",
			Output: "stdout",
		},
	}

	// 创建测试token
	tokenManager := token.NewTokenManager(
		suite.cfg.JWT.Secret,
		time.Duration(suite.cfg.JWT.ExpirationTime)*time.Second,
		time.Duration(suite.cfg.JWT.RefreshTime)*time.Second,
		suite.cfg.JWT.Issuer,
	)

	var err error
	suite.token, _, err = tokenManager.GenerateTokens(
		"test-user-123",
		"testuser",
		"test@example.com",
		[]string{"user", "admin"},
	)
	suite.Require().NoError(err)

	// 创建网关实例（实际测试中可能需要mock数据库连接）
	// 这里先跳过实际创建，在具体测试中mock
}

// TearDownSuite 清理测试套件
func (suite *GatewayTestSuite) TearDownSuite() {
	// 清理测试资源
}

// TestHealthCheck 测试健康检查
func (suite *GatewayTestSuite) TestHealthCheck() {
	// 创建测试路由
	router := gin.New()
	router.GET("/health", func(c *gin.Context) {
		c.JSON(200, gin.H{
			"status":    "healthy",
			"timestamp": time.Now().UTC(),
			"version":   "1.0.0",
		})
	})

	// 创建测试请求
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/health", nil)

	// 执行请求
	router.ServeHTTP(w, req)

	// 验证响应
	suite.Equal(200, w.Code)

	var response map[string]interface{}
	err := json.Unmarshal(w.Body.Bytes(), &response)
	suite.NoError(err)
	suite.Equal("healthy", response["status"])
}

// TestAuthMiddleware 测试认证中间件
func (suite *GatewayTestSuite) TestAuthMiddleware() {
	// 创建测试路由
	router := gin.New()
	router.Use(middleware.Auth(suite.cfg.JWT))

	protectedRouter := router.Group("/protected")
	protectedRouter.GET("/test", func(c *gin.Context) {
		c.JSON(200, gin.H{"message": "access granted"})
	})

	// 测试无认证
	w1 := httptest.NewRecorder()
	req1, _ := http.NewRequest("GET", "/protected/test", nil)
	router.ServeHTTP(w1, req1)
	suite.Equal(401, w1.Code)

	// 测试有效token
	w2 := httptest.NewRecorder()
	req2, _ := http.NewRequest("GET", "/protected/test", nil)
	req2.Header.Set("Authorization", "Bearer "+suite.token)
	router.ServeHTTP(w2, req2)
	suite.Equal(200, w2.Code)

	// 测试无效token
	w3 := httptest.NewRecorder()
	req3, _ := http.NewRequest("GET", "/protected/test", nil)
	req3.Header.Set("Authorization", "Bearer invalid-token")
	router.ServeHTTP(w3, req3)
	suite.Equal(401, w3.Code)
}

// TestRateLimitMiddleware 测试限流中间件
func (suite *GatewayTestSuite) TestRateLimitMiddleware() {
	// 创建测试配置
	cfg := &config.Config{
		RateLimit: config.RateLimitConfig{
			Enabled:           true,
			RequestsPerMinute: 5,
			BurstSize:         10,
			WhitelistEnabled:  false,
		},
	}

	// 创建测试路由
	router := gin.New()
	router.Use(middleware.RateLimit(cfg))
	router.GET("/test", func(c *gin.Context) {
		c.JSON(200, gin.H{"message": "ok"})
	})

	// 发送多个请求
	for i := 0; i < 12; i++ {
		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/test", nil)
		req.Header.Set("X-Forwarded-For", "192.168.1.100")
		router.ServeHTTP(w, req)

		if i < 10 {
			suite.Equal(200, w.Code, fmt.Sprintf("Request %d should succeed", i+1))
		} else {
			suite.Equal(429, w.Code, fmt.Sprintf("Request %d should be rate limited", i+1))
		}
	}
}

// TestCORSMiddleware 测试CORS中间件
func (suite *GatewayTestSuite) TestCORSMiddleware() {
	// 创建测试路由
	router := gin.New()
	router.Use(middleware.CORS(suite.cfg))
	router.GET("/test", func(c *gin.Context) {
		c.JSON(200, gin.H{"message": "ok"})
	})

	// 创建预检请求
	w1 := httptest.NewRecorder()
	req1, _ := http.NewRequest("OPTIONS", "/test", nil)
	req1.Header.Set("Origin", "http://localhost:3000")
	req1.Header.Set("Access-Control-Request-Method", "GET")
	router.ServeHTTP(w1, req1)

	// 验证CORS头
	suite.Equal(204, w1.Code)
	suite.Equal("http://localhost:3000", w1.Header().Get("Access-Control-Allow-Origin"))
	suite.Equal("GET, POST, PUT, DELETE, OPTIONS, PATCH", w1.Header().Get("Access-Control-Allow-Methods"))
	suite.Equal("Origin, Content-Type, Accept, Authorization, X-Requested-With, X-Request-ID, X-API-Key", w1.Header().Get("Access-Control-Allow-Headers"))
}

// TestRequestIDMiddleware 测试请求ID中间件
func (suite *GatewayTestSuite) TestRequestIDMiddleware() {
	// 创建测试路由
	router := gin.New()
	router.Use(middleware.RequestID())
	router.GET("/test", func(c *gin.Context) {
		requestID := c.GetString("request_id")
		c.JSON(200, gin.H{"request_id": requestID})
	})

	// 测试自动生成请求ID
	w1 := httptest.NewRecorder()
	req1, _ := http.NewRequest("GET", "/test", nil)
	router.ServeHTTP(w1, req1)

	suite.Equal(200, w1.Code)

	var response1 map[string]interface{}
	err := json.Unmarshal(w1.Body.Bytes(), &response1)
	suite.NoError(err)
	suite.NotEmpty(response1["request_id"])
	suite.Equal(w1.Header().Get("X-Request-ID"), response1["request_id"])

	// 测试使用现有请求ID
	w2 := httptest.NewRecorder()
	req2, _ := http.NewRequest("GET", "/test", nil)
	req2.Header.Set("X-Request-ID", "test-request-id-123")
	router.ServeHTTP(w2, req2)

	suite.Equal(200, w2.Code)

	var response2 map[string]interface{}
	err = json.Unmarshal(w2.Body.Bytes(), &response2)
	suite.NoError(err)
	suite.Equal("test-request-id-123", response2["request_id"])
	suite.Equal("test-request-id-123", w2.Header().Get("X-Request-ID"))
}

// TestTokenValidation 测试Token验证
func (suite *GatewayTestSuite) TestTokenValidation() {
	tokenManager := token.NewTokenManager(
		suite.cfg.JWT.Secret,
		time.Duration(suite.cfg.JWT.ExpirationTime)*time.Second,
		time.Duration(suite.cfg.JWT.RefreshTime)*time.Second,
		suite.cfg.JWT.Issuer,
	)

	// 测试有效token
	claims, err := tokenManager.ValidateToken(suite.token)
	suite.NoError(err)
	suite.Equal("test-user-123", claims.UserID)
	suite.Equal("testuser", claims.Username)
	suite.Equal("test@example.com", claims.Email)
	suite.Contains(claims.Roles, "admin")

	// 测试无效token
	_, err = tokenManager.ValidateToken("invalid.token.here")
	suite.Error(err)

	// 测试过期token
	expiredTokenManager := token.NewTokenManager(
		suite.cfg.JWT.Secret,
		-1*time.Second, // 立即过期
		time.Duration(suite.cfg.JWT.RefreshTime)*time.Second,
		suite.cfg.JWT.Issuer,
	)
	expiredToken, _, err := expiredTokenManager.GenerateTokens(
		"test-user-123",
		"testuser",
		"test@example.com",
		[]string{"user"},
	)
	suite.NoError(err)

	_, err = tokenManager.ValidateToken(expiredToken)
	suite.Error(err)
}

// TestPasswordHashing 测试密码哈希
func (suite *GatewayTestSuite) TestPasswordHashing() {
	password := "test-password-123"

	// 测试密码哈希
	hash, err := token.HashPassword(password)
	suite.NoError(err)
	suite.NotEmpty(hash)
	suite.NotEqual(password, hash)

	// 测试密码验证
	suite.True(token.CheckPassword(password, hash))
	suite.False(token.CheckPassword("wrong-password", hash))
}

// TestGatewayConfig 测试网关配置
func (suite *GatewayTestSuite) TestGatewayConfig() {
	// 验证配置结构
	suite.Equal(8080, suite.cfg.Server.Port)
	suite.Equal("localhost", suite.cfg.Server.Host)
	suite.Equal("test", suite.cfg.Server.Mode)
	suite.Equal("test-secret-key-at-least-32-characters-long", suite.cfg.JWT.Secret)
	suite.True(suite.cfg.RateLimit.Enabled)
	suite.Equal(100, suite.cfg.RateLimit.RequestsPerMinute)
	suite.Equal("http://localhost:9001", suite.cfg.Services.Auth.URL)
}

// RunTests 运行测试套件
func TestGatewaySuite(t *testing.T) {
	suite.Run(t, new(GatewayTestSuite))
}

// BenchmarkAuthMiddleware 认证中间件基准测试
func BenchmarkAuthMiddleware(b *testing.B) {
	cfg := &config.Config{
		JWT: config.JWTConfig{
			Secret: "benchmark-secret-key-at-least-32-characters-long",
		},
	}

	router := gin.New()
	router.Use(middleware.Auth(cfg.JWT))
	router.GET("/test", func(c *gin.Context) {
		c.JSON(200, gin.H{"message": "ok"})
	})

	// 生成有效的测试token
	tokenManager := token.NewTokenManager(
		cfg.JWT.Secret,
		3600*time.Second,
		86400*time.Second,
		"benchmark-test",
	)
	token, _, err := tokenManager.GenerateTokens(
		"benchmark-user",
		"benchmark",
		"benchmark@example.com",
		[]string{"user"},
	)
	if err != nil {
		b.Fatal(err)
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/test", nil)
		req.Header.Set("Authorization", "Bearer "+token)
		router.ServeHTTP(w, req)
	}
}
