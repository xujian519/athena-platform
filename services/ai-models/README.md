# AI Models Service

AI模型服务统一网关，提供所有AI模型的统一访问接口和智能路由功能。

## 🚀 功能特性

### 核心功能
- **统一接口** - 提供所有AI模型的标准访问接口
- **智能路由** - 根据任务类型自动选择最适合的模型
- **负载均衡** - 支持多种负载均衡策略
- **健康检查** - 实时监控所有模型服务状态
- **批量处理** - 支持批量推理请求
- **容错机制** - 自动处理服务故障和降级

### 支持的模型

#### DeepSeek Integration
- **端口**: 8088
- **能力**: 代码生成（12种语言）、专利代码生成
- **特点**: 高性能代码生成，专业优化

#### GLM Full Suite
- **端口**: 8090
- **能力**:
  - GLM-4.6（通用模型）
  - GLM-4.6-Code（代码模型）
  - GLM-4V-Plus（视觉模型）
  - CogVideoX（视频生成）
  - CogView-4（图像生成）
- **特点**: 全模态覆盖

#### GLM Integration
- **端口**: 8091
- **能力**: 智能体协调、专利深度分析、长文本处理
- **特点**: 增强GLM能力

#### Dual Model Integration
- **端口**: 8092
- **能力**: DeepSeek + GLM智能调度
- **特点**: 双模型协同，成本优化

## 📁 项目结构

```
ai-models/
├── main.py                     # 统一网关主入口
├── requirements.txt            # Python依赖
├── README.md                  # 项目文档
├── .env.example              # 环境变量示例
├── deepseek-integration/      # DeepSeek集成
├── dual-model-integration/    # 双模型集成
├── glm-full-suite/           # GLM全系列
└── glm-integration/          # GLM专用集成
```

## 🛠️ 安装和运行

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置环境变量
```bash
cp .env.example .env
# 编辑.env文件，配置各服务地址
```

### 3. 启动服务
```bash
# 开发模式
python main.py

# 生产模式
uvicorn main:app --host 0.0.0.0 --port 9000
```

## 📚 API文档

### 基础端点

#### GET /
获取服务基本信息

```json
{
  "service": "AI Models Service Gateway",
  "version": "1.0.0",
  "status": "running",
  "models": ["deepseek", "glm", "glm_code", ...]
}
```

#### GET /health
获取所有服务健康状态

```json
{
  "status": "healthy",
  "total_models": 6,
  "healthy_models": 5,
  "services": {
    "deepseek": {
      "status": "healthy",
      "load": 2,
      "url": "http://localhost:8088"
    }
  }
}
```

#### GET /models
列出所有可用模型

```json
{
  "models": [
    {
      "name": "deepseek",
      "capabilities": ["code_generation", "patent_analysis"],
      "status": "healthy",
      "load": 2
    }
  ]
}
```

### 推理端点

#### POST /api/v1/inference
单次推理请求

**请求体**:
```json
{
  "task_type": "code_generation",
  "model_type": null,  // null表示自动选择
  "input": {
    "language": "python",
    "prompt": "创建一个FastAPI服务"
  },
  "priority": 1,
  "timeout": 60
}
```

**响应**:
```json
{
  "task_id": "uuid",
  "model_used": "deepseek",
  "result": {
    "code": "import fastapi\n..."
  },
  "metadata": {
    "task_type": "code_generation",
    "processing_time": 1.5
  }
}
```

#### POST /api/v1/batch
批量推理请求

**请求体**:
```json
[
  {
    "task_type": "code_generation",
    "input": {...}
  },
  {
    "task_type": "patent_analysis",
    "input": {...}
  }
]
```

### 任务类型

| 任务类型 | 说明 | 推荐模型 |
|---------|------|---------|
| code_generation | 代码生成 | deepseek, glm_code |
| text_analysis | 文本分析 | glm, glm_code |
| patent_analysis | 专利分析 | deepseek, glm |
| multimodal | 多模态处理 | glm_vision, glm_image |
| general | 通用任务 | glm |

### 模型类型

| 模型类型 | 服务地址 | 主要能力 |
|---------|---------|---------|
| deepseek | :8088 | 代码生成 |
| glm | :8089 | 通用分析 |
| glm_code | :8091 | 代码处理 |
| glm_vision | :8090 | 视觉理解 |
| glm_video | :8090 | 视频生成 |
| glm_image | :8090 | 图像生成 |

## ⚙️ 配置说明

### 环境变量

```bash
# 服务配置
APP_NAME=AI Models Service Gateway
PORT=9000
DEBUG=false

# 模型服务地址
DEEPSEEK_URL=http://localhost:8088
DUAL_ORCHESTRATOR_URL=http://localhost:8089
GLM_FULL_SUITE_URL=http://localhost:8090
GLM_INTEGRATION_URL=http://localhost:8091

# 路由策略
ENABLE_SMART_ROUTING=true
LOAD_BALANCE_STRATEGY=round_robin  # round_robin, least_busy, priority
```

### 负载均衡策略

1. **round_robin** - 轮询分配
2. **least_busy** - 选择负载最低的服务
3. **priority** - 按预设优先级选择

## 🔧 开发指南

### 添加新模型服务

1. 在ModelServiceManager中注册新服务
2. 定义模型类型和任务类型
3. 实现对应的端点映射
4. 更新文档

### 自定义路由逻辑

```python
def custom_model_selector(task_type: TaskType, input_data: Dict) -> ModelType:
    # 自定义选择逻辑
    if "complex" in input_data.get("description", ""):
        return ModelType.GLM
    return ModelType.DEEPSEEK

# 在service_manager中设置
service_manager.set_custom_selector(custom_model_selector)
```

## 📊 监控和统计

### GET /api/v1/stats
获取服务统计信息

```json
{
  "gateway": {
    "uptime": "2h 30m 15s",
    "total_requests": 1523,
    "active_tasks": 3
  },
  "models": {
    "deepseek": {
      "status": "healthy",
      "load": 5,
      "success_rate": 98.5
    }
  }
}
```

## 🚨 故障处理

### 服务不可用
- 自动跳过不健康的服务
- 记录错误日志
- 返回降级响应

### 超时处理
- 设置合理的超时时间
- 支持任务取消
- 释放资源

### 负载过高
- 动态调整路由策略
- 实现请求队列
- 返回重试建议

## 🔄 更新日志

### v1.0.0 (2025-12-13)
- 初始版本发布
- 统一网关实现
- 支持6种模型类型
- 智能路由功能
- 批量处理支持

## 🤝 贡献指南

1. Fork项目
2. 创建特性分支
3. 提交更改
4. 发起Pull Request

## 📄 许可证

MIT License

---

**维护团队**: Athena AI Team
**最后更新**: 2025-12-13