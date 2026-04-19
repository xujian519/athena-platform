package config

import (
	"os"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestLoadConfig(t *testing.T) {
	// 创建测试配置文件
	testConfig := `
server:
  host: "127.0.0.1"
  port: 9090
  read_timeout: 10
  write_timeout: 10
  idle_timeout: 30
  grace_timeout: 15

auth:
  jwt_secret: "test-secret-key"
  access_token_exp: 30
  refresh_token_exp: 12
  issuer: "test-gateway"
  skip_auth_paths:
    - "/health"
    - "/test"
  admin_users:
    - "test-admin"

logging:
  level: "debug"
  format: "json"
  output: "stdout"
  max_size: 50
  max_backups: 2
  max_age: 7
  compress: false

upstream:
  timeout: 15
  services:
    test_service:
      url: "http://test:8080"
      weight: 1
      headers:
        X-Test: "true"
`

	// 写入临时配置文件
	tmpFile, err := os.CreateTemp("", "test-config-*.yaml")
	require.NoError(t, err)
	defer os.Remove(tmpFile.Name())

	_, err = tmpFile.WriteString(testConfig)
	require.NoError(t, err)
	tmpFile.Close()

	// 加载配置
	config, err := LoadConfig(tmpFile.Name())
	require.NoError(t, err)
	require.NotNil(t, config)

	// 验证服务器配置
	assert.Equal(t, "127.0.0.1", config.Server.Host)
	assert.Equal(t, 9090, config.Server.Port)
	assert.Equal(t, 10, config.Server.ReadTimeout)
	assert.Equal(t, 10, config.Server.WriteTimeout)
	assert.Equal(t, 30, config.Server.IdleTimeout)
	assert.Equal(t, 15, config.Server.GraceTimeout)

	// 验证认证配置
	assert.Equal(t, "test-secret-key", config.Auth.JWTSecret)
	assert.Equal(t, 30, config.Auth.AccessTokenExp)
	assert.Equal(t, 12, config.Auth.RefreshTokenExp)
	assert.Equal(t, "test-gateway", config.Auth.Issuer)
	assert.Contains(t, config.Auth.SkipAuthPaths, "/health")
	assert.Contains(t, config.Auth.SkipAuthPaths, "/test")
	assert.Contains(t, config.Auth.AdminUsers, "test-admin")

	// 验证日志配置
	assert.Equal(t, "debug", config.Logging.Level)
	assert.Equal(t, "json", config.Logging.Format)
	assert.Equal(t, "stdout", config.Logging.Output)
	assert.Equal(t, 50, config.Logging.MaxSize)
	assert.Equal(t, 2, config.Logging.MaxBackups)
	assert.Equal(t, 7, config.Logging.MaxAge)
	assert.False(t, config.Logging.Compress)

	// 验证上游服务配置
	assert.Equal(t, 15, config.Upstream.Timeout)
	assert.Contains(t, config.Upstream.Services, "test_service")
	assert.Equal(t, "http://test:8080", config.Upstream.Services["test_service"].URL)
	assert.Equal(t, 1, config.Upstream.Services["test_service"].Weight)
	assert.Equal(t, "true", config.Upstream.Services["test_service"].Headers["X-Test"])
}

func TestLoadConfigWithDefaults(t *testing.T) {
	// 测试使用默认配置
	config, err := LoadConfig("")
	require.NoError(t, err)
	require.NotNil(t, config)

	// 验证默认值
	assert.Equal(t, "0.0.0.0", config.Server.Host)
	assert.Equal(t, 8080, config.Server.Port)
	assert.Equal(t, 30, config.Server.ReadTimeout)
	assert.Equal(t, "info", config.Logging.Level)
	assert.Equal(t, "json", config.Logging.Format)
	assert.Equal(t, "stdout", config.Logging.Output)
}

func TestConfigValidation(t *testing.T) {
	tests := []struct {
		name    string
		config  string
		wantErr bool
	}{
		{
			name: "valid config",
			config: `
server:
  port: 8080
  read_timeout: 30
  write_timeout: 30
auth:
  jwt_secret: "valid-secret"
  access_token_exp: 60
  refresh_token_exp: 24
logging:
  level: "info"
  format: "json"
  output: "stdout"
upstream:
  timeout: 30
`,
			wantErr: false,
		},
		{
			name: "invalid port",
			config: `
server:
  port: -1
auth:
  jwt_secret: "valid-secret"
  access_token_exp: 60
  refresh_token_exp: 24
`,
			wantErr: true,
		},
		{
			name: "empty jwt secret",
			config: `
server:
  port: 8080
auth:
  jwt_secret: ""
  access_token_exp: 60
  refresh_token_exp: 24
`,
			wantErr: true,
		},
		{
			name: "invalid log level",
			config: `
server:
  port: 8080
auth:
  jwt_secret: "valid-secret"
  access_token_exp: 60
  refresh_token_exp: 24
logging:
  level: "invalid"
  format: "json"
  output: "stdout"
upstream:
  timeout: 30
`,
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			tmpFile, err := os.CreateTemp("", "test-config-*.yaml")
			require.NoError(t, err)
			defer os.Remove(tmpFile.Name())

			_, err = tmpFile.WriteString(tt.config)
			require.NoError(t, err)
			tmpFile.Close()

			_, err = LoadConfig(tmpFile.Name())
			if tt.wantErr {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
			}
		})
	}
}

func TestGetServerAddr(t *testing.T) {
	config := &Config{
		Server: ServerConfig{
			Host: "127.0.0.1",
			Port: 9090,
		},
	}

	addr := config.GetServerAddr()
	assert.Equal(t, "127.0.0.1:9090", addr)
}

func TestIsDevelopment(t *testing.T) {
	// 测试开发环境
	config := &Config{}

	// 设置开发环境
	t.Setenv("ATHENA_GATEWAY_ENV", "development")
	assert.True(t, config.IsDevelopment())
	assert.False(t, config.IsProduction())

	// 设置生产环境
	t.Setenv("ATHENA_GATEWAY_ENV", "production")
	assert.False(t, config.IsDevelopment())
	assert.True(t, config.IsProduction())

	// 清除环境变量
	t.Setenv("ATHENA_GATEWAY_ENV", "")
	assert.False(t, config.IsDevelopment())
	assert.False(t, config.IsProduction())
}

func TestIsProduction(t *testing.T) {
	config := &Config{}

	// 使用GO_ENV
	t.Setenv("GO_ENV", "production")
	assert.True(t, config.IsProduction())

	// 使用ATHENA_GATEWAY_ENV
	t.Setenv("GO_ENV", "")
	t.Setenv("ATHENA_GATEWAY_ENV", "production")
	assert.True(t, config.IsProduction())
}
