# Core Services

核心基础设施服务，为整个Athena平台提供基础支持。

## 服务列表

### 1. health-checker
健康检查服务
- 端口: 9001
- 功能: 监控所有服务健康状态
- 状态: ✅ 运行中

### 2. cache
缓存服务
- 端口: 9002
- 功能: 分布式缓存管理
- 状态: ✅ 运行中

### 3. platform-monitor
平台监控服务
- 端口: 9003
- 功能: 性能指标收集
- 状态: ✅ 运行中

## 快速启动

### 启动所有服务
```bash
./start_all.sh
```

### 停止所有服务
```bash
./stop_all.sh
```

### 查看服务状态
```bash
curl http://localhost:9001/health
```

## 配置

所有服务共享统一的配置文件 `config/settings.json`：

```json
{
  "services": {
    "health_checker": {
      "port": 9001,
      "check_interval": 30
    },
    "cache": {
      "port": 9002,
      "redis_url": "redis://localhost:6379"
    },
    "platform_monitor": {
      "port": 9003,
      "metrics_retention": "7d"
    }
  }
}
```

## 日志

日志文件位于 `logs/` 目录：
- health-checker.log
- cache.log
- platform-monitor.log

## 监控

访问监控仪表板：
- http://localhost:9003/dashboard

## 开发

每个服务都有独立的测试：
```bash
cd health-checker
pytest
```

## 负责人

- 团队：Athena基础设施团队
- 联系：infra@athena.com