# 🛠️ Athena工作平台服务目录

这里是Athena工作平台的核心服务集合，经过精心重构，提供了统一、高效、可扩展的服务架构。

## 📁 目录结构

```
services_new/
├── 🔧 manage_services.py           # 统一服务管理器 (主要工具)
├── 📁 ai-services/                # AI服务模块
│   ├── 🤖 ai-models/              # AI模型服务
│   ├── 🧠 reasoning/              # 推理服务
│   └── 🎨 creative-generation/    # 创意生成服务
├── 📁 data-services/              # 数据服务模块
│   ├── 💾 storage/                # 存储服务
│   ├── 🔍 search/                 # 搜索服务
│   └── 📊 analytics/              # 分析服务
├── 📁 knowledge-services/         # 知识服务模块
│   ├── 🕸️ knowledge-graph/       # 知识图谱服务
│   ├── 📚 vector-database/        # 向量数据库
│   └── 🔍 semantic-search/        # 语义搜索服务
├── 📁 api-gateway/                # API网关模块
│   ├── 🌐 gateway/                # 主网关
│   ├── 🔐 auth/                   # 认证服务
│   └── ⚖️ rate-limiting/          # 限流服务
├── 📁 monitoring/                 # 监控服务模块
│   ├── 📊 metrics/                # 指标收集
│   ├── 📝 logging/                # 日志服务
│   └── 🚨 alerting/              # 告警服务
├── 📁 integration-services/       # 集成服务模块
│   ├── 🔌 external-apis/          # 外部API集成
│   ├── 📡 message-queue/          # 消息队列
│   └── 🔄 task-scheduler/         # 任务调度
├── 📁 common-utilities/           # 通用工具模块
│   ├── 🛡️ security/               # 安全工具
│   ├── 🔧 config/                 # 配置管理
│   └── 📋 utils/                  # 工具函数
└── 📖 README.md                   # 本文档
```

## 🚀 快速开始

### 1. 使用统一服务管理器

```bash
# 查看所有服务
python3 services_new/manage_services.py list

# 启动所有服务
python3 services_new/manage_services.py start

# 启动指定服务
python3 services_new/manage_services.py start ai_services

# 查看服务健康状态
python3 services_new/manage_services.py check

# 停止指定服务
python3 services_new/manage_services.py stop ai_services

# 重启所有服务
python3 services_new/manage_services.py restart
```

### 2. 服务配置

服务配置存储在 `config/services.json` 中：

```json
{
  "services": {
    "ai_services": {
      "name": "AI服务",
      "description": "AI模型和推理服务",
      "status": "stopped",
      "port": 9001,
      "script": "ai_services/start_ai_services.py"
    }
  }
}
```

## 🎯 服务模块详解

### 🤖 AI服务 (ai-services)

**功能**: 提供AI模型推理、自然语言处理、创意生成等AI能力

**主要组件**:
- **ai-models**: 各种AI模型服务（LLM、CV、语音等）
- **reasoning**: 逻辑推理和决策服务
- **creative-generation**: 文本、图像、音频生成服务

**端口范围**: 9001-9010

### 💾 数据服务 (data-services)

**功能**: 提供数据存储、检索、分析等数据管理能力

**主要组件**:
- **storage**: 分布式存储服务
- **search**: 全文搜索和向量搜索
- **analytics**: 数据分析和报表服务

**端口范围**: 9011-9020

### 🕸️ 知识服务 (knowledge-services)

**功能**: 提供知识图谱、语义搜索、知识管理等知识处理能力

**主要组件**:
- **knowledge-graph**: 知识图谱构建和查询
- **vector-database**: 向量数据库服务
- **semantic-search**: 语义搜索和理解

**端口范围**: 9021-9030

### 🌐 API网关 (api-gateway)

**功能**: 提供统一的API入口、认证、限流、路由等功能

**主要组件**:
- **gateway**: 主网关服务
- **auth**: 身份认证和授权
- **rate-limiting**: 访问频率控制

**端口范围**: 8080 (主网关)

### 📊 监控服务 (monitoring)

**功能**: 提供系统监控、日志管理、告警等运维能力

**主要组件**:
- **metrics**: 性能指标收集
- **logging**: 分布式日志服务
- **alerting**: 智能告警系统

**端口范围**: 9090-9100

## 🔧 开发指南

### 添加新服务

1. **创建服务目录**:
   ```bash
   mkdir services_new/your-service-category/your-new-service
   ```

2. **创建启动脚本**:
   ```python
   # services_new/your-service-category/your-new-service/start_service.py
   import sys
   import os
   from pathlib import Path

   def main():
       print("🚀 启动新服务...")
       # 你的服务启动逻辑

   if __name__ == "__main__":
       main()
   ```

3. **更新服务配置**:
   ```bash
   python3 services_new/manage_services.py list
   # 服务会自动发现新配置
   ```

### 服务开发规范

1. **命名规范**: 使用小写字母和连字符
2. **端口分配**: 避免端口冲突，使用分配的端口范围
3. **日志规范**: 使用统一的日志格式
4. **配置管理**: 使用环境变量和配置文件
5. **健康检查**: 提供 `/health` 端点

## 🔍 服务监控

### 健康检查

每个服务都应该提供健康检查端点：

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }
```

### 监控指标

服务应该暴露以下指标：
- 请求数量和响应时间
- 错误率和成功率
- 资源使用情况（CPU、内存）
- 业务相关指标

## 🛡️ 安全考虑

1. **认证授权**: 所有服务需要通过API网关认证
2. **网络安全**: 服务间通信使用TLS加密
3. **数据保护**: 敏感数据需要加密存储
4. **访问控制**: 实施最小权限原则

## 🚀 部署建议

### 开发环境
```bash
# 启动开发环境
python3 services_new/manage_services.py start

# 查看日志
tail -f documentation/logs/services/*.log
```

### 生产环境
```bash
# 使用systemd管理服务
sudo systemctl enable athena-services
sudo systemctl start athena-services

# 使用Docker部署
docker-compose up -d
```

## 🔧 故障排除

### 常见问题

1. **端口冲突**: 检查端口是否被占用
   ```bash
   lsof -i :8080
   ```

2. **服务启动失败**: 查看服务日志
   ```bash
   tail -f documentation/logs/services/your-service.log
   ```

3. **依赖缺失**: 检查Python依赖
   ```bash
   pip install -r requirements.txt
   ```

### 调试模式

```bash
# 启用调试模式
export DEBUG=true
python3 services_new/manage_services.py start
```

## 📞 技术支持

如果遇到问题：

1. 查看服务健康状态: `python3 services_new/manage_services.py check`
2. 检查系统日志: `tail -f documentation/logs/system.log`
3. 重启服务: `python3 services_new/manage_services.py restart`
4. 联系开发团队: 提交Issue到项目仓库

---

**🏛️ Athena AI系统**
*让智能服务为您的业务赋能！*