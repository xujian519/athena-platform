package config

import (
	"os"
	"path/filepath"
	"testing"
)

// TestDefaultConfig 测试默认配置
func TestDefaultConfig(t *testing.T) {
	cfg := defaultConfig()

	if cfg.Server.Port != 8005 {
		t.Errorf("默认端口 = %d, want 8005", cfg.Server.Port)
	}
	if cfg.Server.Production {
		t.Error("默认生产模式应为 false")
	}
	if cfg.Logging.Level != "info" {
		t.Errorf("默认日志级别 = %s, want info", cfg.Logging.Level)
	}
}

// TestLoadWithFile 测试YAML文件加载
func TestLoadWithFile(t *testing.T) {
	// 创建临时配置文件
	tmpDir := t.TempDir()
	configFile := filepath.Join(tmpDir, "test-config.yaml")

	yamlContent := `
server:
  port: 9999
  production: true
logging:
  level: debug
  format: text
`

	if err := os.WriteFile(configFile, []byte(yamlContent), 0644); err != nil {
		t.Fatalf("创建配置文件失败: %v", err)
	}

	// 加载配置
	cfg, err := LoadWithFile(configFile)
	if err != nil {
		t.Fatalf("加载配置失败: %v", err)
	}

	// 验证YAML配置生效
	if cfg.Server.Port != 9999 {
		t.Errorf("Port = %d, want 9999", cfg.Server.Port)
	}
	if !cfg.Server.Production {
		t.Error("Production should be true")
	}
	if cfg.Logging.Level != "debug" {
		t.Errorf("LogLevel = %s, want debug", cfg.Logging.Level)
	}
}

// TestEnvOverrides 测试环境变量覆盖
func TestEnvOverrides(t *testing.T) {
	// 设置环境变量
	os.Setenv("GATEWAY_PORT", "7777")
	os.Setenv("GATEWAY_PRODUCTION", "true")
	os.Setenv("GATEWAY_LOG_LEVEL", "debug")
	defer func() {
		os.Unsetenv("GATEWAY_PORT")
		os.Unsetenv("GATEWAY_PRODUCTION")
		os.Unsetenv("GATEWAY_LOG_LEVEL")
	}()

	cfg := defaultConfig()
	applyEnvOverrides(cfg)

	if cfg.Server.Port != 7777 {
		t.Errorf("Port = %d, want 7777", cfg.Server.Port)
	}
	if !cfg.Server.Production {
		t.Error("Production should be true")
	}
	if cfg.Logging.Level != "debug" {
		t.Errorf("LogLevel = %s, want debug", cfg.Logging.Level)
	}
}

// TestEnvOverrideInvalidValues 测试无效环境变量值
func TestEnvOverrideInvalidValues(t *testing.T) {
	// 设置无效的环境变量
	os.Setenv("GATEWAY_PORT", "invalid")
	os.Setenv("GATEWAY_READ_TIMEOUT", "-1")
	defer func() {
		os.Unsetenv("GATEWAY_PORT")
		os.Unsetenv("GATEWAY_READ_TIMEOUT")
	}()

	cfg := defaultConfig()
	originalPort := cfg.Server.Port
	originalTimeout := cfg.Server.ReadTimeout

	applyEnvOverrides(cfg)

	// 无效值应该被忽略，保持默认值
	if cfg.Server.Port != originalPort {
		t.Errorf("无效端口不应更改默认值: got %d, want %d", cfg.Server.Port, originalPort)
	}
	if cfg.Server.ReadTimeout != originalTimeout {
		t.Errorf("无效超时不应更改默认值: got %d, want %d", cfg.Server.ReadTimeout, originalTimeout)
	}
}

// TestSaveConfig 测试保存配置
func TestSaveConfig(t *testing.T) {
	tmpDir := t.TempDir()
	configFile := filepath.Join(tmpDir, "saved-config.yaml")

	cfg := &Config{
		Server: ServerConfig{
			Port:       8888,
			Production: true,
		},
		Logging: LoggingConfig{
			Level: "debug",
		},
	}

	if err := SaveConfig(cfg, configFile); err != nil {
		t.Fatalf("保存配置失败: %v", err)
	}

	// 验证文件存在
	if _, err := os.Stat(configFile); os.IsNotExist(err) {
		t.Error("配置文件未创建")
	}

	// 重新加载验证内容
	loaded, err := LoadWithFile(configFile)
	if err != nil {
		t.Fatalf("重新加载配置失败: %v", err)
	}

	if loaded.Server.Port != 8888 {
		t.Errorf("重新加载后 Port = %d, want 8888", loaded.Server.Port)
	}
}

// TestConfigWatcher 测试配置观察者
func TestConfigWatcher(t *testing.T) {
	cfg1 := defaultConfig()
	cfg1.Server.Port = 1111

	watcher := NewConfigWatcher(cfg1)

	// 测试Get
	if watcher.Get().Server.Port != 1111 {
		t.Errorf("Get() Port = %d, want 1111", watcher.Get().Server.Port)
	}

	// 测试Watch
	ch := watcher.Watch()

	// 先更新配置
	cfg2 := defaultConfig()
	cfg2.Server.Port = 2222
	watcher.Update(cfg2)

	// 等待通知
	select {
	case newCfg := <-ch:
		if newCfg.Server.Port != 2222 {
			t.Errorf("通知的 Port = %d, want 2222", newCfg.Server.Port)
		}
	default:
		t.Error("未收到配置更新通知")
	}
}

// TestLoadWithNonExistentFile 测试加载不存在的文件
func TestLoadWithNonExistentFile(t *testing.T) {
	// 不存在的文件应该返回默认配置
	cfg, err := LoadWithFile("/non/existent/file.yaml")
	if err != nil {
		t.Errorf("不存在的文件应返回默认配置，但得到错误: %v", err)
	}
	if cfg == nil {
		t.Error("应该返回默认配置而不是 nil")
	}
}
