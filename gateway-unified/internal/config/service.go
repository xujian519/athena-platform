package config

import (
	"fmt"
	"os"

	"gopkg.in/yaml.v3"
)

// ServiceConfig 服务配置
type ServiceConfig struct {
	Name     string                 `yaml:"name"`
	Host     string                 `yaml:"host"`
	Port     int                    `yaml:"port"`
	Protocol string                 `yaml:"protocol"`
	Metadata map[string]interface{} `yaml:"metadata,omitempty"`
}

// ServicesConfig 服务配置列表
type ServicesConfig struct {
	Services []ServiceConfig `yaml:"services"`
}

// LoadServiceInstances 从文件加载服务实例配置
func LoadServiceInstances(path string) (*ServicesConfig, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("读取服务配置文件失败: %w", err)
	}

	var config ServicesConfig
	if err := yaml.Unmarshal(data, &config); err != nil {
		return nil, fmt.Errorf("解析服务配置文件失败: %w", err)
	}

	return &config, nil
}

// SaveServiceInstances 保存服务实例配置到文件
func SaveServiceInstances(path string, config *ServicesConfig) error {
	data, err := yaml.Marshal(config)
	if err != nil {
		return fmt.Errorf("序列化服务配置失败: %w", err)
	}

	if err := os.WriteFile(path, data, 0644); err != nil {
		return fmt.Errorf("写入服务配置文件失败: %w", err)
	}

	return nil
}
