package gateway

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sync"
	"testing"
	"time"
)

// TestConfigManagerGetSet 测试配置的获取和设置
func TestConfigManagerGetSet(t *testing.T) {
	cm := NewConfigManager()
	defer cm.(*defaultConfigManager).Close()

	// 设置配置
	err := cm.Set("server.port", 8080)
	if err != nil {
		t.Errorf("设置配置失败: %v", err)
	}

	// 获取配置
	value, exists := cm.Get("server.port")
	if !exists {
		t.Error("配置应该存在")
	}

	if value != 8080 {
		t.Errorf("配置值不匹配: 期望 8080, 实际 %v", value)
	}

	// 获取不存在的配置
	_, exists = cm.Get("non.existent.key")
	if exists {
		t.Error("不存在的配置不应该存在")
	}
}

// TestConfigManagerWatch 测试配置监听
func TestConfigManagerWatch(t *testing.T) {
	cm := NewConfigManager()
	defer cm.(*defaultConfigManager).Close()

	receivedChanges := make([]ConfigChange, 0)
	var mu sync.Mutex

	// 注册监听器
	listener := func(change ConfigChange) {
		mu.Lock()
		defer mu.Unlock()
		receivedChanges = append(receivedChanges, change)
	}

	cm.Watch("test.key", listener)

	// 设置配置（应该触发监听器）
	cm.Set("test.key", "value1")
	cm.Set("test.key", "value2")

	// 等待异步通知
	time.Sleep(100 * time.Millisecond)

	mu.Lock()
	count := len(receivedChanges)
	mu.Unlock()

	if count < 2 {
		t.Errorf("应该收到2个配置变更, 实际收到 %d 个", count)
	}

	// 取消监听
	cm.Unwatch("test.key", listener)

	// 再次设置配置（不应该触发监听器）
	cm.Set("test.key", "value3")

	time.Sleep(100 * time.Millisecond)

	mu.Lock()
	count = len(receivedChanges)
	mu.Unlock()

	// 计数应该保持不变
	if count > 2 {
		t.Errorf("取消监听后不应再收到通知, 但收到了 %d 个", count)
	}
}

// TestConfigManagerLoadFromFile 测试从文件加载配置
func TestConfigManagerLoadFromFile(t *testing.T) {
	cm := NewConfigManager()
	defer cm.(*defaultConfigManager).Close()

	// 创建临时配置文件
	tmpDir := t.TempDir()
	configFile := filepath.Join(tmpDir, "config.json")

	config := map[string]interface{}{
		"server": map[string]interface{}{
			"port": 8080,
			"host": "localhost",
		},
		"database": map[string]interface{}{
			"driver":   "mysql",
			"timeout": 30,
		},
	}

	data, _ := json.MarshalIndent(config, "", "  ")
	os.WriteFile(configFile, data, 0644)

	// 从文件加载配置
	err := cm.LoadFromFile(configFile)
	if err != nil {
		t.Errorf("从文件加载配置失败: %v", err)
	}

	// 验证配置已加载
	value, exists := cm.Get("server.port")
	if !exists {
		t.Error("server.port 配置应该存在")
	}

	if value != float64(8080) { // JSON解析数字为float64
		t.Errorf("server.port 值不匹配: 期望 8080, 实际 %v", value)
	}

	value, exists = cm.Get("server.host")
	if !exists || value != "localhost" {
		t.Errorf("server.host 值不匹配")
	}

	value, exists = cm.Get("database.driver")
	if !exists || value != "mysql" {
		t.Errorf("database.driver 值不匹配")
	}

	value, exists = cm.Get("database.timeout")
	if !exists || value != float64(30) {
		t.Errorf("database.timeout 值不匹配")
	}
}

// TestConfigManagerLoadFromEnv 测试从环境变量加载配置
func TestConfigManagerLoadFromEnv(t *testing.T) {
	cm := NewConfigManager()
	defer cm.(*defaultConfigManager).Close()

	// 设置环境变量
	os.Setenv("APP_SERVER_PORT", "8080")
	os.Setenv("APP_SERVER_HOST", "localhost")
	os.Setenv("APP_DB_TIMEOUT", "30")
	defer func() {
		os.Unsetenv("APP_SERVER_PORT")
		os.Unsetenv("APP_SERVER_HOST")
		os.Unsetenv("APP_DB_TIMEOUT")
	}()

	// 从环境变量加载配置
	err := cm.LoadFromEnv("APP_")
	if err != nil {
		t.Errorf("从环境变量加载配置失败: %v", err)
	}

	// 验证配置
	value, exists := cm.Get("SERVER_PORT")
	if !exists || value != "8080" {
		t.Errorf("SERVER_PORT 配置不匹配: %v", value)
	}

	value, exists = cm.Get("SERVER_HOST")
	if !exists || value != "localhost" {
		t.Errorf("SERVER_HOST 配置不匹配")
	}

	value, exists = cm.Get("DB_TIMEOUT")
	if !exists || value != "30" {
		t.Errorf("DB_TIMEOUT 配置不匹配")
	}
}

// TestConfigManagerSaveToFile 测试保存配置到文件
func TestConfigManagerSaveToFile(t *testing.T) {
	cm := NewConfigManager()
	defer cm.(*defaultConfigManager).Close()

	// 设置一些配置
	cm.Set("server.port", 8080)
	cm.Set("server.host", "localhost")
	cm.Set("app.name", "test-app")

	// 保存到文件
	tmpDir := t.TempDir()
	configFile := filepath.Join(tmpDir, "output.json")

	err := cm.SaveToFile(configFile)
	if err != nil {
		t.Errorf("保存配置到文件失败: %v", err)
	}

	// 验证文件存在
	if _, err := os.Stat(configFile); os.IsNotExist(err) {
		t.Error("配置文件应该存在")
	}

	// 读取文件验证内容
	data, err := os.ReadFile(configFile)
	if err != nil {
		t.Errorf("读取配置文件失败: %v", err)
	}

	var savedConfig map[string]interface{}
	err = json.Unmarshal(data, &savedConfig)
	if err != nil {
		t.Errorf("解析保存的配置失败: %v", err)
	}

	// 验证配置值
	if savedConfig["server.port"] != float64(8080) {
		t.Errorf("保存的server.port不匹配")
	}

	if savedConfig["server.host"] != "localhost" {
		t.Errorf("保存的server.host不匹配")
	}

	if savedConfig["app.name"] != "test-app" {
		t.Errorf("保存的app.name不匹配")
	}
}

// TestConfigManagerGetAll 测试获取所有配置
func TestConfigManagerGetAll(t *testing.T) {
	cm := NewConfigManager()
	defer cm.(*defaultConfigManager).Close()

	// 设置多个配置
	cm.Set("key1", "value1")
	cm.Set("key2", "value2")
	cm.Set("key3", "value3")

	// 获取所有配置
	allConfigs := cm.GetAll()

	if len(allConfigs) != 3 {
		t.Errorf("应该有3个配置, 实际有 %d 个", len(allConfigs))
	}

	if allConfigs["key1"] != "value1" {
		t.Errorf("key1 值不匹配")
	}

	if allConfigs["key2"] != "value2" {
		t.Errorf("key2 值不匹配")
	}

	if allConfigs["key3"] != "value3" {
		t.Errorf("key3 值不匹配")
	}
}

// TestConfigValidator 测试配置验证器
func TestConfigValidator(t *testing.T) {
	cm := NewConfigManager()
	defer cm.(*defaultConfigManager).Close()

	dcm := cm.(*defaultConfigManager)

	// 注册验证器
	dcm.RegisterValidator("server.port", PortValidator)
	dcm.RegisterValidator("app.name", StringValidator)

	// 测试有效值
	err := cm.Set("server.port", 8080)
	if err != nil {
		t.Errorf("设置有效端口应该成功: %v", err)
	}

	err = cm.Set("app.name", "test-app")
	if err != nil {
		t.Errorf("设置有效应用名应该成功: %v", err)
	}

	// 测试无效值
	err = cm.Set("server.port", 70000)
	if err == nil {
		t.Error("设置无效端口应该失败")
	}

	err = cm.Set("app.name", 123)
	if err == nil {
		t.Error("设置非字符串应用名应该失败")
	}
}

// TestPositiveIntValidator 测试正整数验证器
func TestPositiveIntValidator(t *testing.T) {
	err := PositiveIntValidator("test", 10)
	if err != nil {
		t.Errorf("正整数应该通过验证: %v", err)
	}

	err = PositiveIntValidator("test", -1)
	if err == nil {
		t.Error("负数应该验证失败")
	}

	err = PositiveIntValidator("test", "not-a-number")
	if err == nil {
		t.Error("非数字应该验证失败")
	}
}

// TestRangeValidator 测试范围验证器
func TestRangeValidator(t *testing.T) {
	validator := RangeValidator(1, 100)

	err := validator("test", 50)
	if err != nil {
		t.Errorf("范围内的值应该通过验证: %v", err)
	}

	err = validator("test", 0)
	if err == nil {
		t.Error("小于最小值的应该验证失败")
	}

	err = validator("test", 101)
	if err == nil {
		t.Error("大于最大值的应该验证失败")
	}
}

// TestOneOfValidator 测试枚举验证器
func TestOneOfValidator(t *testing.T) {
	validator := OneOfValidator([]string{"option1", "option2", "option3"})

	err := validator("test", "option2")
	if err != nil {
		t.Errorf("枚举中的值应该通过验证: %v", err)
	}

	err = validator("test", "option4")
	if err == nil {
		t.Error("不在枚举中的值应该验证失败")
	}

	err = validator("test", 123)
	if err == nil {
		t.Error("非字符串值应该验证失败")
	}
}

// TestConfigChangeListener 测试配置变更监听器
func TestConfigChangeListener(t *testing.T) {
	cm := NewConfigManager()
	defer cm.(*defaultConfigManager).Close()

	changeReceived := false
	var receivedChange ConfigChange

	listener := func(change ConfigChange) {
		changeReceived = true
		receivedChange = change
	}

	cm.Watch("test.key", listener)

	// 触发变更
	cm.Set("test.key", "new-value")

	// 等待异步通知
	time.Sleep(100 * time.Millisecond)

	if !changeReceived {
		t.Error("应该收到配置变更通知")
	}

	if receivedChange.Key != "test.key" {
		t.Errorf("配置键不匹配: 期望 'test.key', 实际 %s", receivedChange.Key)
	}

	if receivedChange.NewValue != "new-value" {
		t.Errorf("新值不匹配: 期望 'new-value', 实际 %v", receivedChange.NewValue)
	}

	// 验证变更时间戳
	if receivedChange.Timestamp.IsZero() {
		t.Error("变更时间戳不应该为零")
	}
}

// TestConfigChangeOldValue 测试配置变更时的旧值
func TestConfigChangeOldValue(t *testing.T) {
	cm := NewConfigManager()
	defer cm.(*defaultConfigManager).Close()

	// 设置初始值
	cm.Set("test.key", "old-value")

	var receivedChange ConfigChange
	listener := func(change ConfigChange) {
		receivedChange = change
	}

	cm.Watch("test.key", listener)

	// 更新值
	cm.Set("test.key", "new-value")

	time.Sleep(100 * time.Millisecond)

	// 验证旧值
	if receivedChange.OldValue != "old-value" {
		t.Errorf("旧值不匹配: 期望 'old-value', 实际 %v", receivedChange.OldValue)
	}

	if receivedChange.NewValue != "new-value" {
		t.Errorf("新值不匹配: 期望 'new-value', 实际 %v", receivedChange.NewValue)
	}
}

// TestConfigManagerConcurrentAccess 测试并发访问
func TestConfigManagerConcurrentAccess(t *testing.T) {
	cm := NewConfigManager()
	defer cm.(*defaultConfigManager).Close()

	// 并发设置
	done := make(chan bool)
	for i := 0; i < 100; i++ {
		go func(idx int) {
			key := fmt.Sprintf("key%d", idx)
			cm.Set(key, idx)
			done <- true
		}(i)
	}

	// 等待所有设置完成
	for i := 0; i < 100; i++ {
		<-done
	}

	// 验证所有配置都已设置
	allConfigs := cm.GetAll()
	if len(allConfigs) != 100 {
		t.Errorf("应该有100个配置, 实际有 %d 个", len(allConfigs))
	}

	// 并发读取
	for i := 0; i < 100; i++ {
		go func(idx int) {
			key := fmt.Sprintf("key%d", idx)
			_, exists := cm.Get(key)
			if !exists {
				t.Errorf("配置 %s 应该存在", key)
			}
			done <- true
		}(i)
	}

	// 等待所有读取完成
	for i := 0; i < 100; i++ {
		<-done
	}
}
