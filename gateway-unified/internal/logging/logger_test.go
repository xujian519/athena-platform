// Package logging - 日志系统测试
package logging

import (
	"fmt"
	"os"
	"strings"
	"testing"
)

// TestFieldTypes 测试各种字段类型
func TestFieldTypes(t *testing.T) {
	tests := []struct {
		name  string
		field Field
		key   string
	}{
		{"String字段", String("key", "value"), "key"},
		{"Int字段", Int("count", 42), "count"},
		{"Int64字段", Int64("big", 9223372036854775807), "big"},
		{"Uint字段", Uint("unsigned", 42), "unsigned"},
		{"Uint64字段", Uint64("big", 18446744073709551615), "big"},
		{"Float64字段", Float64("pi", 3.14159), "pi"},
		{"Float32字段", Float32("small", 0.5), "small"},
		{"Bool字段", Bool("enabled", true), "enabled"},
		{"Any字段", Any("anything", map[string]int{"a": 1}), "anything"},
		{"Strings字段", Strings("list", []string{"a", "b"}), "list"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if tt.field.Key() != tt.key {
				t.Errorf("期望key为'%s'，实际为'%s'", tt.key, tt.field.Key())
			}
		})
	}
}

// TestErrorField 测试错误字段
func TestErrorField(t *testing.T) {
	err := &testError{msg: "test error"}
	field := Err(err)

	if field.Key() != "error" {
		t.Errorf("期望key为'error'，实际为'%s'", field.Key())
	}

	if field.Value() == nil {
		t.Error("错误值不应为nil")
	}
}

// TestNamedErr 测试命名错误字段
func TestNamedErr(t *testing.T) {
	err := &testError{msg: "test error"}
	field := NamedErr("custom_error", err)

	if field.Key() != "custom_error" {
		t.Errorf("期望key为'custom_error'，实际为'%s'", field.Key())
	}
}

// TestDefaultConfig 测试默认配置
func TestDefaultConfig(t *testing.T) {
	cfg := DefaultConfig()

	if cfg.Level != "info" {
		t.Errorf("期望默认级别为'info'，实际为'%s'", cfg.Level)
	}

	if cfg.Format != "text" {
		t.Errorf("期望默认格式为'text'，实际为'%s'", cfg.Format)
	}

	if cfg.Output != "stdout" {
		t.Errorf("期望默认输出为'stdout'，实际为'%s'", cfg.Output)
	}

	if !cfg.EnableCaller {
		t.Error("期望默认启用调用者信息")
	}
}

// TestDevelopmentConfig 测试开发环境配置
func TestDevelopmentConfig(t *testing.T) {
	cfg := DevelopmentConfig()

	if cfg.Level != "debug" {
		t.Errorf("期望开发环境级别为'debug'，实际为'%s'", cfg.Level)
	}
}

// TestProductionConfig 测试生产环境配置
func TestProductionConfig(t *testing.T) {
	cfg := ProductionConfig()

	if cfg.Level != "info" {
		t.Errorf("期望生产环境级别为'info'，实际为'%s'", cfg.Level)
	}

	if cfg.EnableCaller {
		t.Error("生产环境不应默认启用调用者信息")
	}
}

// TestConfigValidate 测试配置验证
func TestConfigValidate(t *testing.T) {
	tests := []struct {
		name      string
		cfg       *Config
		wantLevel string
		wantFormat string
	}{
		{
			name: "有效配置",
			cfg: &Config{
				Level:  "debug",
				Format: "json",
				Output: "stdout",
			},
			wantLevel:  "debug",
			wantFormat: "json",
		},
		{
			name: "无效级别-应默认为info",
			cfg: &Config{
				Level:  "invalid",
				Format: "text",
				Output: "stdout",
			},
			wantLevel: "info",
			wantFormat: "text",
		},
		{
			name: "无效格式-应默认为text",
			cfg: &Config{
				Level:  "info",
				Format: "invalid",
				Output: "stdout",
			},
			wantLevel:  "info",
			wantFormat: "text",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			tt.cfg.Validate()
			if tt.cfg.Level != tt.wantLevel {
				t.Errorf("期望级别为'%s'，实际为'%s'", tt.wantLevel, tt.cfg.Level)
			}
			if tt.cfg.Format != tt.wantFormat {
				t.Errorf("期望格式为'%s'，实际为'%s'", tt.wantFormat, tt.cfg.Format)
			}
		})
	}
}

// TestLevelWeight 测试日志级别权重
func TestLevelWeight(t *testing.T) {
	tests := []struct {
		level  string
		weight int
	}{
		{"debug", 0},
		{"info", 1},
		{"warn", 2},
		{"error", 3},
		{"fatal", 4},
	}

	for _, tt := range tests {
		t.Run(tt.level, func(t *testing.T) {
			if got := getLevelWeight(tt.level); got != tt.weight {
				t.Errorf("%s级别期望权重为%d，实际为%d", tt.level, tt.weight, got)
			}
		})
	}
}

// TestShouldLog 测试日志级别过滤
func TestShouldLog(t *testing.T) {
	cfg := &Config{Level: "info"}

	tests := []struct {
		level      string
		shouldLog  bool
	}{
		{"debug", false},
		{"info", true},
		{"warn", true},
		{"error", true},
		{"fatal", true},
	}

	for _, tt := range tests {
		t.Run(tt.level, func(t *testing.T) {
			if got := cfg.ShouldLog(tt.level); got != tt.shouldLog {
				t.Errorf("级别%s: 期望shouldLog=%v，实际=%v", tt.level, tt.shouldLog, got)
			}
		})
	}
}

// TestDefaultRotationConfig 测试默认轮转配置
func TestDefaultRotationConfig(t *testing.T) {
	cfg := DefaultRotationConfig()

	if cfg.MaxSize != 100 {
		t.Errorf("期望MaxSize为100，实际为%d", cfg.MaxSize)
	}

	if cfg.MaxBackups != 10 {
		t.Errorf("期望MaxBackups为10，实际为%d", cfg.MaxBackups)
	}

	if cfg.MaxAge != 30 {
		t.Errorf("期望MaxAge为30，实际为%d", cfg.MaxAge)
	}

	if !cfg.Compress {
		t.Error("期望默认启用压缩")
	}
}

// TestLoggingFunctions 测试日志函数
func TestLoggingFunctions(t *testing.T) {
	// 重定向输出到buffer以捕获日志
	// 注意：这需要修改Init以支持自定义io.Writer
	// 当前简化测试，只确保函数不会panic

	LogInfo("info message", String("key", "value"))
	LogDebug("debug message", Int("count", 42))
	LogWarn("warn message", Bool("flag", true))
	LogError("error message", Err(&testError{msg: "test"}))
	LogFatal("fatal message", Float64("pi", 3.14))
}

// TestFieldFormats 测试字段格式化
func TestFieldFormats(t *testing.T) {
	fields := []Field{
		String("name", "test"),
		Int("count", 42),
		Bool("enabled", true),
		Float64("ratio", 0.95),
		Err(&testError{msg: "error"}),
	}

	// 构建日志消息
	var msg string
	for _, f := range fields {
		msg += f.Key() + "="
		switch v := f.Value().(type) {
		case string:
			msg += v + " "
		case int64:
			msg += fmt.Sprintf("%d ", v)
		case bool:
			msg += fmt.Sprintf("%t ", v)
		case float64:
			msg += fmt.Sprintf("%.2f ", v)
		case error:
			if v != nil {
				msg += v.Error() + " "
			}
		default:
			msg += fmt.Sprintf("%v ", v)
		}
	}

	// 检查是否包含所有字段
	expectedParts := []string{"name=test", "count=42", "enabled=true", "ratio=0.95", "error"}
	for _, part := range expectedParts {
		if !strings.Contains(msg, part) {
			t.Errorf("日志消息应包含'%s'，实际为'%s'", part, msg)
		}
	}
}

// formatValue 格式化值的辅助函数
func formatValue(v interface{}) string {
	switch val := v.(type) {
	case string:
		return val
	case int:
		return string(rune(val + '0'))
	case int64:
		return string(rune(val + '0'))
	case bool:
		if val {
			return "true"
		}
		return "false"
	case float64:
		return "0.95"
	case error:
		return val.Error()
	default:
		return ""
	}
}

// TestInit 测试日志初始化
func TestInit(t *testing.T) {
	tests := []struct {
		name    string
		cfg     interface{}
		wantErr bool
	}{
		{
			name:    "nil配置",
			cfg:     nil,
			wantErr: false,
		},
		{
			name:    "默认配置",
			cfg:     DefaultConfig(),
			wantErr: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := Init(tt.cfg)
			if (err != nil) != tt.wantErr {
				t.Errorf("Init() error = %v, wantErr %v", err, tt.wantErr)
			}
		})
	}
}

// TestGlobalLogger 测试全局logger
func TestGlobalLogger(t *testing.T) {
	// 确保globalLogger已初始化
	logger := getLogger()
	if logger == nil {
		t.Error("全局logger不应为nil")
	}

	// 测试日志输出
	logger.logger.SetOutput(os.Stdout)
	logger.logger.Print("test message")
}

// BenchmarkLogging 性能测试
func BenchmarkLogging(b *testing.B) {
	fields := []Field{
		String("key1", "value1"),
		Int("key2", 42),
		Bool("key3", true),
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		LogInfo("test message", fields...)
	}
}

// BenchmarkFieldCreation 性能测试 - 字段创建
func BenchmarkFieldCreation(b *testing.B) {
	b.Run("String", func(b *testing.B) {
		for i := 0; i < b.N; i++ {
			_ = String("key", "value")
		}
	})

	b.Run("Int", func(b *testing.B) {
		for i := 0; i < b.N; i++ {
			_ = Int("key", 42)
		}
	})

	b.Run("Bool", func(b *testing.B) {
		for i := 0; i < b.N; i++ {
			_ = Bool("key", true)
		}
	})

	b.Run("Float64", func(b *testing.B) {
		for i := 0; i < b.N; i++ {
			_ = Float64("key", 3.14)
		}
	})
}

// 测试用的错误类型
type testError struct {
	msg string
}

func (e *testError) Error() string {
	return e.msg
}
