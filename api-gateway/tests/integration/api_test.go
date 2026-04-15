package integration

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"athena-gateway/internal/auth"
	"athena-gateway/internal/config"
	"athena-gateway/internal/handlers"
	"athena-gateway/internal/middleware"
	"athena-gateway/pkg/response"
	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func setupTestRouter() (*gin.Engine, *handlers.AuthHandler) {
	gin.SetMode(gin.TestMode)

	// 创建测试配置
	testConfig := &config.Config{
		Auth: config.AuthConfig{
			JWTSecret:       "test-secret-key-for-integration-testing",
			AccessTokenExp:  60,
			RefreshTokenExp: 24,
			Issuer:          "test-gateway",
			SkipAuthPaths: []string{
				"/health",
				"/health/ready",
				"/health/live",
				"/api/v1/auth/login",
				"/api/v1/auth/refresh",
			},
			AdminUsers: []string{"admin"},
		},
	}
	config.AppConfig = testConfig

	// 创建JWT管理器
	jwtManager, _ := auth.NewJWTManager()

	// 创建处理器
	authHandler := handlers.NewAuthHandler(jwtManager)
	healthHandler := handlers.NewHealthHandler("1.0.0")

	// 创建路由器
	router := gin.New()

	// 添加中间件
	router.Use(middleware.RequestIDMiddleware())
	router.Use(middleware.LoggingMiddleware())

	// 设置路由
	router.GET("/health", healthHandler.BasicHealth)
	router.GET("/health/ready", healthHandler.Readiness)
	router.GET("/health/live", healthHandler.Liveness)

	v1 := router.Group("/api/v1")
	authGroup := v1.Group("/auth")
	{
		authGroup.POST("/login", authHandler.Login)
		authGroup.POST("/refresh", authHandler.RefreshToken)
	}

	protectedGroup := v1.Group("/")
	protectedGroup.Use(middleware.AuthMiddleware(jwtManager))
	{
		protectedGroup.POST("/auth/logout", authHandler.Logout)
	}

	return router, authHandler
}

func TestHealthEndpoints(t *testing.T) {
	router, _ := setupTestRouter()

	tests := []struct {
		name           string
		path           string
		expectedStatus int
	}{
		{"basic health", "/health", http.StatusOK},
		{"readiness check", "/health/ready", http.StatusOK},
		{"liveness check", "/health/live", http.StatusOK},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			req := httptest.NewRequest(http.MethodGet, tt.path, nil)
			w := httptest.NewRecorder()

			router.ServeHTTP(w, req)

			assert.Equal(t, tt.expectedStatus, w.Code)

			var response response.Response
			err := json.Unmarshal(w.Body.Bytes(), &response)
			require.NoError(t, err)
			assert.True(t, response.Success)
		})
	}
}

func TestLoginEndpoint(t *testing.T) {
	router, _ := setupTestRouter()

	tests := []struct {
		name           string
		requestBody    interface{}
		expectedStatus int
		expectedError  bool
	}{
		{
			name: "valid login",
			requestBody: map[string]string{
				"username": "admin",
				"password": "admin123",
			},
			expectedStatus: http.StatusCreated,
			expectedError:  false,
		},
		{
			name: "valid user login",
			requestBody: map[string]string{
				"username": "user",
				"password": "user123",
			},
			expectedStatus: http.StatusCreated,
			expectedError:  false,
		},
		{
			name: "invalid credentials",
			requestBody: map[string]string{
				"username": "admin",
				"password": "wrong-password",
			},
			expectedStatus: http.StatusUnauthorized,
			expectedError:  true,
		},
		{
			name: "missing username",
			requestBody: map[string]string{
				"password": "admin123",
			},
			expectedStatus: http.StatusBadRequest,
			expectedError:  true,
		},
		{
			name: "missing password",
			requestBody: map[string]string{
				"username": "admin",
			},
			expectedStatus: http.StatusBadRequest,
			expectedError:  true,
		},
		{
			name:           "empty body",
			requestBody:    nil,
			expectedStatus: http.StatusBadRequest,
			expectedError:  true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			var body []byte
			if tt.requestBody != nil {
				var err error
				body, err = json.Marshal(tt.requestBody)
				require.NoError(t, err)
			}

			req := httptest.NewRequest(http.MethodPost, "/api/v1/auth/login", bytes.NewBuffer(body))
			req.Header.Set("Content-Type", "application/json")
			w := httptest.NewRecorder()

			router.ServeHTTP(w, req)

			assert.Equal(t, tt.expectedStatus, w.Code)

			if tt.expectedError {
				var errorResp response.ErrorResponse
				err := json.Unmarshal(w.Body.Bytes(), &errorResp)
				require.NoError(t, err)
				assert.False(t, errorResp.Success)
			} else {
				var successResp response.Response
				err := json.Unmarshal(w.Body.Bytes(), &successResp)
				require.NoError(t, err)
				assert.True(t, successResp.Success)
				assert.NotNil(t, successResp.Data)
			}
		})
	}
}

func TestProtectedEndpointWithoutAuth(t *testing.T) {
	router, _ := setupTestRouter()

	req := httptest.NewRequest(http.MethodPost, "/api/v1/auth/logout", nil)
	w := httptest.NewRecorder()

	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusUnauthorized, w.Code)

	var errorResp response.ErrorResponse
	err := json.Unmarshal(w.Body.Bytes(), &errorResp)
	require.NoError(t, err)
	assert.False(t, errorResp.Success)
	assert.Equal(t, "未授权访问", errorResp.Message)
}

func TestProtectedEndpointWithAuth(t *testing.T) {
	router, authHandler := setupTestRouter()

	// 首先登录获取token
	loginReq := map[string]string{
		"username": "admin",
		"password": "admin123",
	}

	body, _ := json.Marshal(loginReq)
	req := httptest.NewRequest(http.MethodPost, "/api/v1/auth/login", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusCreated, w.Code)

	var loginResp response.Response
	err := json.Unmarshal(w.Body.Bytes(), &loginResp)
	require.NoError(t, err)

	// 提取token
	data := loginResp.Data.(map[string]interface{})
	tokenPair := data["token_pair"].(map[string]interface{})
	accessToken := tokenPair["access_token"].(string)

	// 使用token访问受保护的端点
	logoutReq := httptest.NewRequest(http.MethodPost, "/api/v1/auth/logout", nil)
	logoutReq.Header.Set("Authorization", "Bearer "+accessToken)
	w2 := httptest.NewRecorder()

	router.ServeHTTP(w2, logoutReq)

	assert.Equal(t, http.StatusOK, w2.Code)

	var logoutResp response.Response
	err = json.Unmarshal(w2.Body.Bytes(), &logoutResp)
	require.NoError(t, err)
	assert.True(t, logoutResp.Success)
}

func TestProtectedEndpointWithInvalidToken(t *testing.T) {
	router, _ := setupTestRouter()

	// 使用无效token
	req := httptest.NewRequest(http.MethodPost, "/api/v1/auth/logout", nil)
	req.Header.Set("Authorization", "Bearer invalid-token")
	w := httptest.NewRecorder()

	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusUnauthorized, w.Code)

	var errorResp response.ErrorResponse
	err := json.Unmarshal(w.Body.Bytes(), &errorResp)
	require.NoError(t, err)
	assert.False(t, errorResp.Success)
}

func TestRefreshTokenEndpoint(t *testing.T) {
	router, _ := setupTestRouter()

	// 首先登录获取refresh token
	loginReq := map[string]string{
		"username": "admin",
		"password": "admin123",
	}

	body, _ := json.Marshal(loginReq)
	req := httptest.NewRequest(http.MethodPost, "/api/v1/auth/login", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusCreated, w.Code)

	var loginResp response.Response
	err := json.Unmarshal(w.Body.Bytes(), &loginResp)
	require.NoError(t, err)

	// 提取refresh token
	data := loginResp.Data.(map[string]interface{})
	tokenPair := data["token_pair"].(map[string]interface{})
	refreshToken := tokenPair["refresh_token"].(string)

	// 使用refresh token获取新的token对
	refreshReq := map[string]string{
		"refresh_token": refreshToken,
	}

	refreshBody, _ := json.Marshal(refreshReq)
	req2 := httptest.NewRequest(http.MethodPost, "/api/v1/auth/refresh", bytes.NewBuffer(refreshBody))
	req2.Header.Set("Content-Type", "application/json")
	w2 := httptest.NewRecorder()

	router.ServeHTTP(w2, req2)

	assert.Equal(t, http.StatusOK, w2.Code)

	var refreshResp response.Response
	err = json.Unmarshal(w2.Body.Bytes(), &refreshResp)
	require.NoError(t, err)
	assert.True(t, refreshResp.Success)
	assert.NotNil(t, refreshResp.Data)
}

func TestNotFoundEndpoint(t *testing.T) {
	router, _ := setupTestRouter()

	req := httptest.NewRequest(http.MethodGet, "/nonexistent", nil)
	w := httptest.NewRecorder()

	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusNotFound, w.Code)

	var errorResp response.ErrorResponse
	err := json.Unmarshal(w.Body.Bytes(), &errorResp)
	require.NoError(t, err)
	assert.False(t, errorResp.Success)
	assert.Equal(t, "请求的资源不存在", errorResp.Message)
}

func TestRequestIDMiddleware(t *testing.T) {
	router, _ := setupTestRouter()

	req := httptest.NewRequest(http.MethodGet, "/health", nil)
	w := httptest.NewRecorder()

	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	assert.NotEmpty(t, w.Header().Get("X-Request-ID"))
}
