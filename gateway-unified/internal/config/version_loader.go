// Package config - 版本配置加载器
package config

import (
	"os"

	"gopkg.in/yaml.v3"
	"github.com/athena-workspace/gateway-unified/internal/middleware"
)

// VersionConfig 版本配置结构
type VersionConfig struct {
	Versions        []VersionInfo `yaml:"versions"`
	DefaultVersion  string        `yaml:"default_version"`
	VersionDetection VersionDetectionConfig `yaml:"version_detection"`
}

// VersionInfo 版本信息
type VersionInfo struct {
	Version        string `yaml:"version"`
	Deprecated     bool   `yaml:"deprecated"`
	SunsetDate     string `yaml:"sunset_date"`
	RemovedDate    string `yaml:"removed_date"`
	MigrationGuide string `yaml:"migration_guide"`
}

// VersionDetectionConfig 版本检测配置
type VersionDetectionConfig struct {
	Enabled               bool `yaml:"enabled"`
	IncludeVersionHeader  bool `yaml:"include_version_header"`
}

// VersionLoader 版本配置加载器
type VersionLoader struct {
	config *VersionConfig
}

// NewVersionLoader 创建版本配置加载器
func NewVersionLoader() *VersionLoader {
	return &VersionLoader{
		config: &VersionConfig{
			Versions: []VersionInfo{
				{
					Version:    "v1",
					Deprecated: false,
				},
			},
			DefaultVersion: "v1",
			VersionDetection: VersionDetectionConfig{
				Enabled:              true,
				IncludeVersionHeader: true,
			},
		},
	}
}

// LoadFromFile 从文件加载版本配置
func (l *VersionLoader) LoadFromFile(path string) error {
	data, err := os.ReadFile(path)
	if err != nil {
		return err
	}

	var config VersionConfig
	if err := yaml.Unmarshal(data, &config); err != nil {
		return err
	}

	l.config = &config
	return nil
}

// ApplyTo 将配置应用到版本管理中间件
func (l *VersionLoader) ApplyTo(versionConfig *middleware.VersionConfig) {
	// 应用版本检测配置
	versionConfig.EnableVersionDetection = l.config.VersionDetection.Enabled
	versionConfig.IncludeVersionHeader = l.config.VersionDetection.IncludeVersionHeader

	// 应用默认版本
	if l.config.DefaultVersion != "" {
		versionConfig.SetDefaultVersion(l.config.DefaultVersion)
	}

	// 注册所有版本
	for _, ver := range l.config.Versions {
		info := &middleware.APIVersion{
			Deprecated:     ver.Deprecated,
			SunsetDate:     ver.SunsetDate,
			RemovedDate:    ver.RemovedDate,
			MigrationGuide: ver.MigrationGuide,
		}
		versionConfig.RegisterVersion(ver.Version, info)
	}
}

// GetConfig 获取配置
func (l *VersionLoader) GetConfig() *VersionConfig {
	return l.config
}
