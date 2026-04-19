package tracing

import "time"

type Config struct {
	// 服务配置
	ServiceName    string `yaml:"service_name" mapstructure:"service_name"`
	ServiceVersion string `yaml:"service_version" mapstructure:"service_version"`
	Environment    string `yaml:"environment" mapstructure:"environment"`

	// Jaeger配置
	Jaeger JaegerConfig `yaml:"jaeger" mapstructure:"jaeger"`

	// 采样配置
	Sampling SamplingConfig `yaml:"sampling" mapstructure:"sampling"`

	// 追踪配置
	Enabled            bool          `yaml:"enabled" mapstructure:"enabled"`
	BatchTimeout       time.Duration `yaml:"batch_timeout" mapstructure:"batch_timeout"`
	ExportTimeout      time.Duration `yaml:"export_timeout" mapstructure:"export_timeout"`
	MaxExportBatchSize int           `yaml:"max_export_batch_size" mapstructure:"max_export_batch_size"`
}

type JaegerConfig struct {
	Endpoint string `yaml:"endpoint" mapstructure:"endpoint"`
	Username string `yaml:"username" mapstructure:"username"`
	Password string `yaml:"password" mapstructure:"password"`
	Insecure bool   `yaml:"insecure" mapstructure:"insecure"`
}

type SamplingConfig struct {
	Type  string  `yaml:"type" mapstructure:"type"`
	Param float64 `yaml:"param" mapstructure:"param"`
}

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
