package auth

import (
	"testing"
	"time"

	"athena-gateway/internal/config"
	"athena-gateway/internal/logging"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestJWTManager(t *testing.T) {
	// 设置测试配置
	testConfig := &config.Config{
		Auth: config.AuthConfig{
			JWTSecret:       "test-secret-key-for-jwt-testing",
			AccessTokenExp:  60,
			RefreshTokenExp: 24,
			Issuer:          "test-gateway",
		},
	}

	// 设置全局配置
	config.AppConfig = testConfig

	// 创建JWT管理器
	jwtManager, err := NewJWTManager()
	require.NoError(t, err)
	require.NotNil(t, jwtManager)
}

func TestGenerateTokenPair(t *testing.T) {
	// 设置测试配置
	testConfig := &config.Config{
		Auth: config.AuthConfig{
			JWTSecret:       "test-secret-key-for-jwt-testing",
			AccessTokenExp:  60,
			RefreshTokenExp: 24,
			Issuer:          "test-gateway",
		},
	}
	config.AppConfig = testConfig

	jwtManager, err := NewJWTManager()
	require.NoError(t, err)

	// 创建测试用户
	user := &UserInfo{
		UserID:   "test-user-123",
		Username: "testuser",
		Email:    "testuser@example.com",
		Role:     "user",
	}

	// 生成令牌对
	tokenPair, err := jwtManager.GenerateTokenPair(user)
	require.NoError(t, err)
	require.NotNil(t, tokenPair)

	// 验证令牌对
	assert.NotEmpty(t, tokenPair.AccessToken)
	assert.NotEmpty(t, tokenPair.RefreshToken)
	assert.Greater(t, tokenPair.ExpiresIn, int64(0))
	assert.Greater(t, tokenPair.RefreshExp, int64(0))
}

func TestValidateToken(t *testing.T) {
	// 设置测试配置
	testConfig := &config.Config{
		Auth: config.AuthConfig{
			JWTSecret:       "test-secret-key-for-jwt-testing",
			AccessTokenExp:  60,
			RefreshTokenExp: 24,
			Issuer:          "test-gateway",
		},
	}
	config.AppConfig = testConfig

	jwtManager, err := NewJWTManager()
	require.NoError(t, err)

	// 创建测试用户和令牌
	user := &UserInfo{
		UserID:   "test-user-123",
		Username: "testuser",
		Email:    "testuser@example.com",
		Role:     "user",
	}

	tokenPair, err := jwtManager.GenerateTokenPair(user)
	require.NoError(t, err)

	// 验证访问令牌
	claims, err := jwtManager.ValidateToken(tokenPair.AccessToken)
	require.NoError(t, err)
	require.NotNil(t, claims)

	// 验证声明
	assert.Equal(t, user.UserID, claims.UserID)
	assert.Equal(t, user.Username, claims.Username)
	assert.Equal(t, user.Email, claims.Email)
	assert.Equal(t, user.Role, claims.Role)
	assert.Equal(t, AccessToken, claims.TokenType)
	assert.Equal(t, "test-gateway", claims.Issuer)
	assert.Equal(t, user.UserID, claims.Subject)
}

func TestValidateExpiredToken(t *testing.T) {
	// 设置测试配置
	testConfig := &config.Config{
		Auth: config.AuthConfig{
			JWTSecret:       "test-secret-key-for-jwt-testing",
			AccessTokenExp:  1, // 1分钟过期
			RefreshTokenExp: 24,
			Issuer:          "test-gateway",
		},
	}
	config.AppConfig = testConfig

	jwtManager, err := NewJWTManager()
	require.NoError(t, err)

	// 创建测试用户
	user := &UserInfo{
		UserID:   "test-user-123",
		Username: "testuser",
		Email:    "testuser@example.com",
		Role:     "user",
	}

	// 生成令牌对
	tokenPair, err := jwtManager.GenerateTokenPair(user)
	require.NoError(t, err)

	// 等待令牌过期
	time.Sleep(2 * time.Second)

	// 验证过期令牌
	_, err = jwtManager.ValidateToken(tokenPair.AccessToken)
	assert.Error(t, err)
	assert.Equal(t, logging.ErrTokenExpired, err)
}

func TestValidateInvalidToken(t *testing.T) {
	// 设置测试配置
	testConfig := &config.Config{
		Auth: config.AuthConfig{
			JWTSecret:       "test-secret-key-for-jwt-testing",
			AccessTokenExp:  60,
			RefreshTokenExp: 24,
			Issuer:          "test-gateway",
		},
	}
	config.AppConfig = testConfig

	jwtManager, err := NewJWTManager()
	require.NoError(t, err)

	// 测试无效令牌
	invalidTokens := []string{
		"",                     // 空令牌
		"invalid.token.format", // 无效格式
		"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid", // 不完整令牌
	}

	for _, token := range invalidTokens {
		_, err := jwtManager.ValidateToken(token)
		assert.Error(t, err)
		assert.Equal(t, logging.ErrInvalidToken, err)
	}
}

func TestRefreshToken(t *testing.T) {
	// 设置测试配置
	testConfig := &config.Config{
		Auth: config.AuthConfig{
			JWTSecret:       "test-secret-key-for-jwt-testing",
			AccessTokenExp:  60,
			RefreshTokenExp: 24,
			Issuer:          "test-gateway",
		},
	}
	config.AppConfig = testConfig

	jwtManager, err := NewJWTManager()
	require.NoError(t, err)

	// 创建测试用户
	user := &UserInfo{
		UserID:   "test-user-123",
		Username: "testuser",
		Email:    "testuser@example.com",
		Role:     "user",
	}

	// 生成令牌对
	tokenPair, err := jwtManager.GenerateTokenPair(user)
	require.NoError(t, err)

	// 使用刷新令牌获取新令牌对
	newTokenPair, err := jwtManager.RefreshToken(tokenPair.RefreshToken)
	require.NoError(t, err)
	require.NotNil(t, newTokenPair)

	// 验证新令牌
	assert.NotEmpty(t, newTokenPair.AccessToken)
	assert.NotEmpty(t, newTokenPair.RefreshToken)
	assert.NotEqual(t, tokenPair.AccessToken, newTokenPair.AccessToken)
	assert.NotEqual(t, tokenPair.RefreshToken, newTokenPair.RefreshToken)
}

func TestRefreshTokenWithAccessToken(t *testing.T) {
	// 设置测试配置
	testConfig := &config.Config{
		Auth: config.AuthConfig{
			JWTSecret:       "test-secret-key-for-jwt-testing",
			AccessTokenExp:  60,
			RefreshTokenExp: 24,
			Issuer:          "test-gateway",
		},
	}
	config.AppConfig = testConfig

	jwtManager, err := NewJWTManager()
	require.NoError(t, err)

	// 创建测试用户
	user := &UserInfo{
		UserID:   "test-user-123",
		Username: "testuser",
		Email:    "testuser@example.com",
		Role:     "user",
	}

	// 生成令牌对
	tokenPair, err := jwtManager.GenerateTokenPair(user)
	require.NoError(t, err)

	// 尝试用访问令牌刷新
	_, err = jwtManager.RefreshToken(tokenPair.AccessToken)
	assert.Error(t, err)
	assert.Equal(t, logging.ErrInvalidToken, err)
}

func TestExtractTokenFromHeader(t *testing.T) {
	tests := []struct {
		name       string
		authHeader string
		wantToken  string
		wantErr    bool
	}{
		{
			name:       "valid bearer token",
			authHeader: "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
			wantToken:  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
			wantErr:    false,
		},
		{
			name:       "empty header",
			authHeader: "",
			wantToken:  "",
			wantErr:    true,
		},
		{
			name:       "invalid format",
			authHeader: "Basic dGVzdDp0ZXN0",
			wantToken:  "",
			wantErr:    true,
		},
		{
			name:       "only bearer",
			authHeader: "Bearer",
			wantToken:  "",
			wantErr:    true,
		},
		{
			name:       "bearer with empty token",
			authHeader: "Bearer ",
			wantToken:  "",
			wantErr:    true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			token, err := ExtractTokenFromHeader(tt.authHeader)
			if tt.wantErr {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
				assert.Equal(t, tt.wantToken, token)
			}
		})
	}
}

func TestIsAdminUser(t *testing.T) {
	// 设置测试配置
	testConfig := &config.Config{
		Auth: config.AuthConfig{
			AdminUsers: []string{"admin", "superuser", "root"},
		},
	}
	config.AppConfig = testConfig

	tests := []struct {
		username string
		expected bool
	}{
		{"admin", true},
		{"superuser", true},
		{"root", true},
		{"user", false},
		{"guest", false},
		{"", false},
	}

	for _, tt := range tests {
		t.Run(tt.username, func(t *testing.T) {
			result := IsAdminUser(tt.username)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestIsPathSkipAuth(t *testing.T) {
	// 设置测试配置
	testConfig := &config.Config{
		Auth: config.AuthConfig{
			SkipAuthPaths: []string{
				"/health",
				"/health/ready",
				"/api/v1/auth/login",
				"/api/v1/auth/refresh",
			},
		},
	}
	config.AppConfig = testConfig

	tests := []struct {
		path     string
		expected bool
	}{
		{"/health", true},
		{"/health/ready", true},
		{"/api/v1/auth/login", true},
		{"/api/v1/auth/refresh", true},
		{"/api/v1/users", false},
		{"/api/v1/admin/status", false},
		{"/", false},
	}

	for _, tt := range tests {
		t.Run(tt.path, func(t *testing.T) {
			result := IsPathSkipAuth(tt.path)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestGenerateRandomKey(t *testing.T) {
	key1, err := GenerateRandomKey(32)
	require.NoError(t, err)
	assert.NotEmpty(t, key1)
	assert.Equal(t, 44, len(key1)) // Base64编码后的长度

	key2, err := GenerateRandomKey(32)
	require.NoError(t, err)
	assert.NotEmpty(t, key2)
	assert.NotEqual(t, key1, key2) // 应该生成不同的密钥
}
