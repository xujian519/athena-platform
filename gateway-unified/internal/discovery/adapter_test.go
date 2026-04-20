// Package discovery - 服务发现测试
package discovery

import (
	"testing"
	"time"

	"github.com/athena-workspace/gateway-unified/internal/gateway"
)

// TestServiceDiscoveryAdapter 测试服务发现适配器
func TestServiceDiscoveryAdapter(t *testing.T) {
	// 创建Gateway注册表
	gwRegistry := gateway.NewServiceRegistry()

	// 创建适配器
	registry := NewGatewayRegistryAdapter(gwRegistry)

	// 创建适配器配置
	config := &ServiceDiscoveryConfig{
		ConfigPath:   "../../../config/service_discovery.json",
		ScanInterval: 5 * time.Second,
		AutoRegister: true,
		HealthCheck:  false, // 测试时禁用健康检查
	}

	// 创建适配器
	adapter := NewAdapter(config, registry)

	// 测试加载配置
	t.Run("LoadConfig", func(t *testing.T) {
		err := adapter.LoadConfig()
		if err != nil {
			t.Fatalf("加载配置失败: %v", err)
		}

		if adapter.configData == nil {
			t.Fatal("配置数据为空")
		}

		if len(adapter.configData.Services) == 0 {
			t.Log("配置文件中没有服务")
		}
	})

	// 测试同步服务
	t.Run("SyncServices", func(t *testing.T) {
		err := adapter.SyncServices()
		if err != nil {
			t.Fatalf("同步服务失败: %v", err)
		}

		// 验证服务已注册
		services := registry.GetAll()
		if len(services) == 0 {
			t.Fatal("没有注册任何服务")
		}

		t.Logf("已注册 %d 个服务", len(services))

		// 验证服务属性
		for _, svc := range services {
			if svc.ID == "" {
				t.Errorf("服务ID为空: %s", svc.ServiceName)
			}
			if svc.ServiceName == "" {
				t.Error("服务名称为空")
			}
			if svc.Host == "" {
				t.Errorf("服务主机为空: %s", svc.ServiceName)
			}
			if svc.Port <= 0 {
				t.Errorf("服务端口无效: %s -> %d", svc.ServiceName, svc.Port)
			}
		}
	})

	// 测试重复同步
	t.Run("SyncServicesTwice", func(t *testing.T) {
		// 第一次同步
		err := adapter.SyncServices()
		if err != nil {
			t.Fatalf("第一次同步失败: %v", err)
		}

		firstCount := registry.Count()

		// 第二次同步
		err = adapter.SyncServices()
		if err != nil {
			t.Fatalf("第二次同步失败: %v", err)
		}

		secondCount := registry.Count()

		// 服务数量应该保持一致
		if firstCount != secondCount {
			t.Errorf("重复同步后服务数量不一致: %d != %d", firstCount, secondCount)
		}
	})
}

// TestHealthChecker 测试健康检查器
func TestHealthChecker(t *testing.T) {
	checker := NewHealthChecker(&ServiceDiscoveryConfig{})

	// 测试超时设置
	t.Run("SetTimeout", func(t *testing.T) {
		checker.SetTimeout(10 * time.Second)
		if checker.GetTimeout() != 10*time.Second {
			t.Errorf("超时设置失败: 期望 10s, 实际 %v", checker.GetTimeout())
		}
	})

	// 测试健康检查 (假设Gateway正在运行)
	t.Run("CheckGateway", func(t *testing.T) {
		instance := &ServiceInstance{
			ID:          "test:127.0.0.1:8005:0",
			ServiceName: "test",
			Host:        "127.0.0.1",
			Port:        8005,
			Status:      "UP",
		}

		healthy := checker.Check(instance)
		t.Logf("Gateway健康检查结果: %v", healthy)

		// 测试带重试的健康检查
		healthyWithRetry := checker.CheckWithRetry(instance, 3)
		t.Logf("Gateway健康检查结果(带重试): %v", healthyWithRetry)
	})
}

// TestCreateInstance 测试创建服务实例
func TestCreateInstance(t *testing.T) {
	gwRegistry := gateway.NewServiceRegistry()
	registry := NewGatewayRegistryAdapter(gwRegistry)
	adapter := NewAdapter(&ServiceDiscoveryConfig{}, registry)

	svcInfo := ServiceInfo{
		Name:           "test-service",
		Type:           "test",
		Provider:       "test-provider",
		Protocol:       "http",
		Enabled:        true,
		Port:           8080,
		Description:    "测试服务",
		HealthEndpoint: "/custom-health",
		Metadata: map[string]interface{}{
			"version": "1.0.0",
		},
	}

	instance := adapter.createInstance(svcInfo)

	// 验证实例属性
	if instance.ServiceName != svcInfo.Name {
		t.Errorf("服务名称不匹配: 期望 %s, 实际 %s", svcInfo.Name, instance.ServiceName)
	}

	if instance.Host != "127.0.0.1" {
		t.Errorf("主机地址不匹配: 期望 127.0.0.1, 实际 %s", instance.Host)
	}

	if instance.Port != svcInfo.Port {
		t.Errorf("端口不匹配: 期望 %d, 实际 %d", svcInfo.Port, instance.Port)
	}

	if instance.Status != "UP" {
		t.Errorf("状态不匹配: 期望 UP, 实际 %s", instance.Status)
	}

	// 验证元数据
	if instance.Metadata == nil {
		t.Fatal("元数据为空")
	}

	if instance.Metadata["type"] != svcInfo.Type {
		t.Errorf("类型元数据不匹配: 期望 %s, 实际 %v", svcInfo.Type, instance.Metadata["type"])
	}

	if instance.Metadata["health_endpoint"] != svcInfo.HealthEndpoint {
		t.Errorf("健康检查端点不匹配: 期望 %s, 实际 %v", svcInfo.HealthEndpoint, instance.Metadata["health_endpoint"])
	}

	if instance.Metadata["version"] != "1.0.0" {
		t.Errorf("自定义元数据不匹配: 期望 1.0.0, 实际 %v", instance.Metadata["version"])
	}
}

// TestGatewayRegistryAdapter 测试Gateway注册表适配器
func TestGatewayRegistryAdapter(t *testing.T) {
	gwRegistry := gateway.NewServiceRegistry()
	adapter := NewGatewayRegistryAdapter(gwRegistry)

	// 测试注册服务
	t.Run("Register", func(t *testing.T) {
		instance := &ServiceInstance{
			ID:          "test:127.0.0.1:8080:0",
			ServiceName: "test-service",
			Host:        "127.0.0.1",
			Port:        8080,
			Status:      "UP",
			Weight:      1,
		}

		adapter.Register(instance)

		// 验证注册成功
		retrieved := adapter.GetByID(instance.ID)
		if retrieved == nil {
			t.Fatal("注册后无法获取服务")
		}

		if retrieved.ServiceName != instance.ServiceName {
			t.Errorf("服务名称不匹配: 期望 %s, 实际 %s", instance.ServiceName, retrieved.ServiceName)
		}
	})

	// 测试获取所有服务
	t.Run("GetAll", func(t *testing.T) {
		services := adapter.GetAll()
		if len(services) == 0 {
			t.Error("应该至少有一个服务")
		}
	})

	// 测试计数
	t.Run("Count", func(t *testing.T) {
		count := adapter.Count()
		if count != 1 {
			t.Errorf("服务数量应该为1, 实际为 %d", count)
		}
	})

	// 测试更新服务
	t.Run("Update", func(t *testing.T) {
		instance := adapter.GetByID("test:127.0.0.1:8080:0")
		if instance == nil {
			t.Fatal("服务不存在")
		}

		instance.Status = "DOWN"
		instance.Weight = 2

		success := adapter.Update(instance)
		if !success {
			t.Error("更新服务失败")
		}

		// 验证更新
		updated := adapter.GetByID("test:127.0.0.1:8080:0")
		if updated.Status != "DOWN" {
			t.Errorf("状态未更新: 期望 DOWN, 实际 %s", updated.Status)
		}
		if updated.Weight != 2 {
			t.Errorf("权重未更新: 期望 2, 实际 %d", updated.Weight)
		}
	})

	// 测试删除服务
	t.Run("Delete", func(t *testing.T) {
		success := adapter.Delete("test:127.0.0.1:8080:0")
		if !success {
			t.Error("删除服务失败")
		}

		// 验证删除
		deleted := adapter.GetByID("test:127.0.0.1:8080:0")
		if deleted != nil {
			t.Error("服务应该已被删除")
		}

		if adapter.Count() != 0 {
			t.Errorf("服务数量应该为0, 实际为 %d", adapter.Count())
		}
	})
}
