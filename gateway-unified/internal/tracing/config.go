// Package tracing 提供OpenTelemetry分布式追踪功能
// 支持Jaeger导出器，多种采样策略，完整的追踪配置
package tracing

import "time"

// Config 追踪器配置
type Config struct {
	// 服务配置
	ServiceName    string `yaml:"service_name" mapstructure:"service_name" json:"service_name"`
	ServiceVersion string `yaml:"service_version" mapstructure:"service_version" json:"service_version"`
	Environment    string `yaml:"environment" mapstructure:"environment" json:"environment"`

	// Jaeger配置
	Jaeger JaegerConfig `yaml:"jaeger" mapstructure:"jaeger" json:"jaeger"`

	// 采样配置
	Sampling SamplingConfig `yaml:"sampling" mapstructure:"sampling" json:"sampling"`

	// 追踪配置
	Enabled            bool          `yaml:"enabled" mapstructure:"enabled" json:"enabled"`
	BatchTimeout       time.Duration `yaml:"batch_timeout" mapstructure:"batch_timeout" json:"batch_timeout"`
	ExportTimeout      time.Duration `yaml:"export_timeout" mapstructure:"export_timeout" json:"export_timeout"`
	MaxExportBatchSize int           `yaml:"max_export_batch_size" mapstructure:"max_export_batch_size" json:"max_export_batch_size"`
}

// JaegerConfig Jaeger导出器配置
type JaegerConfig struct {
	Endpoint string `yaml:"endpoint" mapstructure:"endpoint" json:"endpoint"`
	Username string `yaml:"username" mapstructure:"username" json:"username"`
	Password string `yaml:"password" mapstructure:"password" json:"password"`
	Insecure bool   `yaml:"insecure" mapstructure:"insecure" json:"insecure"`
}

// SamplingConfig 采样策略配置
type SamplingConfig struct {
	Type  string  `yaml:"type" mapstructure:"type" json:"type"`           // 采样类型: always_on, always_off, probabilistic, parentbased_*
	Param float64 `yaml:"param" mapstructure:"param" json:"param"`       // 采样参数（用于probabilistic）
}

// DefaultConfig 返回默认配置
func DefaultConfig() Config {
	return Config{
		ServiceName:    "athena-gateway",
		ServiceVersion: "1.0.0",
		Environment:    "development",
		Jaeger: JaegerConfig{
			Endpoint: "http://localhost:14268/api/traces",
			Insecure: true,
		},
		Sampling: SamplingConfig{
			Type:  "probabilistic",
			Param: 0.1, // 10%采样率
		},
		Enabled:            true,
		BatchTimeout:       5 * time.Second,
		ExportTimeout:      30 * time.Second,
		MaxExportBatchSize: 512,
	}
}

// DevelopmentConfig 返回开发环境配置（更高采样率）
func DevelopmentConfig() Config {
	cfg := DefaultConfig()
	cfg.Environment = "development"
	cfg.Sampling.Param = 1.0 // 100%采样
	return cfg
}

// ProductionConfig 返回生产环境配置（较低采样率）
func ProductionConfig() Config {
	cfg := DefaultConfig()
	cfg.Environment = "production"
	cfg.Sampling.Param = 0.1 // 10%采样
	cfg.Jaeger.Endpoint = "http://jaeger:14268/api/traces"
	return cfg
}
