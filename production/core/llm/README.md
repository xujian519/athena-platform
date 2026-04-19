# Athena统一LLM层 - API文档

**版本**: 1.0.0
**作者**: Claude Code
**最后更新**: 2026-01-23

---

## 📋 目录

- [概述](#概述)
- [快速开始](#快速开始)
- [核心API](#核心api)
- [高级功能](#高级功能)
- [配置说明](#配置说明)
- [监控和运维](#监控和运维)
- [故障排查](#故障排查)
- [最佳实践](#最佳实践)

---

## 概述

Athena统一LLM层是一个企业级的大语言模型统一调用框架，提供：

- 🤖 **多模型支持**: GLM、DeepSeek、Qwen、本地模型
- 🎯 **智能选择**: 根据任务类型自动选择最优模型
- 💰 **成本优化**: 实时成本追踪和预算控制
- ⚡ **高性能**: 响应缓存、并发处理、资源池管理
- 🔒 **安全可靠**: API密钥脱敏、异常处理、线程安全

**架构层次**:
```
应用层
  ↓
统一LLM管理器
  ↓
智能模型选择器 + 模型能力注册表
  ↓
模型适配器 (GLM/DeepSeek/Qwen/Local)
  ↓
基础设施 (缓存/监控/安全)
```

---

## 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install prometheus-client

# 配置环境变量（.env文件）
ZHIPUAI_API_KEY=your_zhipuai_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
DASHSCOPE_API_KEY=your_dashscope_api_key
LOCAL_MODEL_PATH=/path/to/models
```

### 2. 基础使用

```python
import asyncio
from core.llm.unified_llm_manager import get_unified_llm_manager

async def main():
    # 获取管理器实例
    manager = await get_unified_llm_manager()

    # 生成响应
    response = await manager.generate(
        message="请分析专利202311060998.X的创造性",
        task_type="creativity_analysis",
        enable_thinking=True
    )

    print(f"响应: {response.content}")
    print(f"使用模型: {response.model_used}")
    print(f"耗时: {response.processing_time:.2f}秒")
    print(f"成本: ¥{response.cost:.4f}")

if __name__ == '__main__':
    asyncio.run(main())
```

### 3. 高级用法

```python
# 自定义参数
response = await manager.generate(
    message="分析这段代码的性能瓶颈",
    task_type="tech_analysis",

    # LLM参数
    temperature=0.7,
    max_tokens=2000,

    # 上下文信息
    context={
        'system_prompt': '你是一位资深软件架构师',
        'code_language': 'Python'
    },

    # 功能开关
    enable_thinking=False,
    stream=False
)
```

---

## 核心API

### UnifiedLLMManager

统一LLM管理器，是主要的调用入口。

#### 初始化

```python
from core.llm.unified_llm_manager import get_unified_llm_manager

# 获取单例实例（自动初始化）
manager = await get_unified_llm_manager()

# 或手动初始化（带参数）
manager = UnifiedLLMManager(registry=custom_registry)
await manager.initialize(
    enable_cache_warmup=True,  # 启用缓存预热
    warmup_cache=False         # 是否预热响应缓存
)
```

#### generate方法

**核心生成接口**

```python
async def generate(
    message: str,              # 用户消息
    task_type: str,            # 任务类型
    context: Dict = None,      # 上下文信息
    **kwargs                   # 其他参数
) -> LLMResponse:
    """生成LLM响应"""
```

**参数说明**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| message | str | ✅ | 用户消息内容 |
| task_type | str | ✅ | 任务类型（见下表） |
| context | Dict | ❌ | 上下文信息 |
| temperature | float | ❌ | 温度参数（0-1），默认0.7 |
| max_tokens | int | ❌ | 最大token数，默认2000 |
| enable_thinking | bool | ❌ | 是否启用思维链，默认False |
| stream | bool | ❌ | 是否流式输出，默认False |

**任务类型**:

```python
# 对话类
'simple_chat'      # 简单对话
'general_chat'     # 通用对话
'simple_qa'        # 简单问答

# 专利分析类
'patent_search'     # 专利检索
'tech_analysis'     # 技术分析
'novelty_analysis'  # 新颖性分析
'creativity_analysis'  # 创造性分析
'invalidation_analysis'  # 无效性分析
'oa_response'       # OA答复

# 推理类
'reasoning'         # 通用推理
'complex_analysis'  # 复杂分析
'math_reasoning'    # 数学推理
```

**返回值**:

```python
@dataclass
class LLMResponse:
    content: str                    # 响应内容
    model_used: str                 # 使用的模型
    tokens_used: int                # 使用token数
    processing_time: float          # 处理时间（秒）
    cost: float                     # 成本（元）
    quality_score: float            # 质量评分（0-1）
    from_cache: bool                # 是否来自缓存
    reasoning_content: str          # 推理过程（部分模型支持）
```

**示例**:

```python
# 示例1：简单对话
response = await manager.generate(
    message="你好，请介绍一下你自己",
    task_type="simple_chat"
)

# 示例2：专利创造性分析
response = await manager.generate(
    message="请分析专利202311060998.X的创造性",
    task_type="creativity_analysis",
    enable_thinking=True,
    max_tokens=5000
)

# 示例3：带上下文的请求
response = await manager.generate(
    message="根据以下代码分析性能瓶颈",
    task_type="tech_analysis",
    context={
        'system_prompt': '你是一位资深性能优化专家',
        'code': 'def process(items): ...',
        'language': 'Python'
    }
)
```

---

## 高级功能

### 1. 模型选择策略

```python
from core.llm.model_selector import SelectionStrategy

# 获取管理器后修改选择策略
manager.selector.strategy = SelectionStrategy.COST_OPTIMIZED  # 成本优化
manager.selector.strategy = SelectionStrategy.QUALITY_OPTIMIZED  # 质量优化
manager.selector.strategy = SelectionStrategy.BALANCED  # 平衡策略
```

**策略对比**:

| 策略 | 说明 | 适用场景 |
|------|------|----------|
| COST_OPTIMIZED | 优先使用低成本模型 | 批量处理、测试 |
| QUALITY_OPTIMIZED | 优先使用高质量模型 | 关键决策、复杂分析 |
| BALANCED | 综合考虑成本和质量 | 日常使用 |
| FAST_RESPONSE | 优先使用快速响应模型 | 实时交互 |

### 2. 成本监控

```python
# 获取成本报告
report = manager.get_cost_report(time_window="today")
print(report)

# 获取预算状态
budget_status = manager.get_budget_status()
print(f"预算使用率: {budget_status['budget_utilization']:.1%}")
print(f"剩余预算: ¥{budget_status['remaining_budget']:.2f}")

# 获取最近告警
alerts = manager.get_recent_alerts(limit=5)
for alert in alerts:
    print(f"[{alert['level']}] {alert['message']}")
```

### 3. Prometheus监控

```python
# 导出metrics（用于Prometheus采集）
metrics_data, content_type = manager.export_metrics()

# 获取metrics摘要
summary = manager.get_metrics_summary()
print(f"启用的metrics数量: {summary['metrics_count']}")
print(f"Metrics列表: {summary['metrics_list']}")
```

**FastAPI集成示例**:

```python
from fastapi import FastAPI
from core.llm.unified_llm_manager import get_unified_llm_manager

app = FastAPI()
manager = None

@app.on_event("startup")
async def startup():
    global manager
    manager = await get_unified_llm_manager()

@app.get("/metrics")
async def metrics():
    """Prometheus metrics端点"""
    data, content_type = manager.export_metrics()
    from fastapi.responses import Response
    return Response(content=data, media_type=content_type)
```

### 4. 缓存管理

```python
# 获取缓存报告
cache_report = manager.response_cache.get_report()
print(cache_report)

# 清空缓存
manager.response_cache.clear()

# 配置任务类型的缓存设置
manager.response_cache.configure_task_type(
    task_type="patent_search",
    cacheable=True,
    ttl=7200  # 2小时
)
```

### 5. 健康检查

```python
# 检查所有模型健康状态
health_status = await manager.health_check()

for model_id, is_healthy in health_status.items():
    status_icon = "✅" if is_healthy else "❌"
    print(f"{status_icon} {model_id}: {'健康' if is_healthy else '不健康'}")

# 获取可用模型列表
available_models = manager.get_available_models()
print(f"可用模型: {', '.join(available_models)}")
```

---

## 配置说明

### 环境变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| ZHIPUAI_API_KEY | 智谱AI API密钥 | sk-xxx |
| DEEPSEEK_API_KEY | DeepSeek API密钥 | sk-xxx |
| DASHSCOPE_API_KEY | 阿里云API密钥 | sk-xxx |
| LOCAL_MODEL_PATH | 本地模型路径 | /path/to/models |
| LLM_MODEL_REGISTRY_PATH | 模型配置文件路径 | /path/to/config.json |

### 模型配置文件

**config/llm_model_registry.json**:

```json
{
  "version": "1.0.0",
  "last_updated": "2026-01-23T00:00:00",
  "total_models": 5,
  "models": [
    {
      "model_id": "glm-4-plus",
      "model_type": "reasoning",
      "deployment": "cloud",
      "max_context": 128000,
      "supports_streaming": true,
      "supports_function_call": true,
      "supports_thinking": true,
      "cost_per_1k_tokens": 0.05,
      "quality_score": 0.95,
      "suitable_tasks": [
        "novelty_analysis",
        "creativity_analysis"
      ]
    }
  ]
}
```

---

## 监控和运维

### 关键指标

| 指标 | 说明 | 告警阈值 |
|------|------|----------|
| request_total | 请求总数 | - |
| request_duration_seconds | 请求耗时 | P95 > 5s |
| tokens_total | Token使用量 | - |
| cost_yuan | 总成本（元） | 日预算超限 |
| cache_hits_total | 缓存命中数 | - |
| cache_misses_total | 缓存未命中数 | - |

### 日志示例

```python
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 敏感数据自动脱敏
logger.info("API密钥: sk-1234567890abcdef")
# 输出: API密钥: sk-1234****bcdef
```

---

## 故障排查

### 常见问题

**问题1: 模型初始化失败**

```python
# 原因: API密钥未配置
# 解决: 检查环境变量
import os
print(f"ZHIPUAI_API_KEY: {os.getenv('ZHIPUAI_API_KEY')}")
```

**问题2: 请求超时**

```python
# 原因: 网络问题或模型响应慢
# 解决: 增加超时时间
response = await manager.generate(
    message="...",
    task_type="simple_chat",
    timeout=60  # 60秒超时
)
```

**问题3: 成本超预算**

```python
# 原因: 频繁调用高成本模型
# 解决: 切换到成本优化策略
manager.selector.strategy = SelectionStrategy.COST_OPTIMIZED
```

---

## 最佳实践

### 1. 选择合适的任务类型

```python
# ✅ 好的做法
response = await manager.generate(
    message="分析专利创造性",
    task_type="creativity_analysis",  # 明确指定任务类型
    enable_thinking=True
)

# ❌ 不好的做法
response = await manager.generate(
    message="分析专利创造性",
    task_type="simple_chat",  # 任务类型不匹配
    enable_thinking=False
)
```

### 2. 合理设置参数

```python
# ✅ 好的做法
response = await manager.generate(
    message="简单问候",
    task_type="simple_chat",
    temperature=0.7,      # 适当的随机性
    max_tokens=500        # 限制输出长度
)

# ❌ 不好的做法
response = await manager.generate(
    message="简单问候",
    task_type="simple_chat",
    temperature=1.0,      # 过高随机性
    max_tokens=10000      # 浪费token
)
```

### 3. 利用缓存

```python
# ✅ 好的做法
# 相同问题直接从缓存获取
for question in repeated_questions:
    response = await manager.generate(
        message=question,
        task_type="simple_qa"  # 可缓存的任务类型
    )

# ❌ 不好的做法
# 每次都重新调用LLM
for question in repeated_questions:
    response = await manager.generate(
        message=question,
        task_type="creativity_analysis"  # 不缓存
    )
```

### 4. 错误处理

```python
# ✅ 好的做法
try:
    response = await manager.generate(
        message="...",
        task_type="simple_chat"
    )
    if not response.content:
        raise ValueError("空响应")
except Exception as e:
    logger.error(f"生成失败: {e}")
    # 降级处理
    return get_fallback_response()

# ❌ 不好的做法
response = await manager.generate(
    message="...",
    task_type="simple_chat"
)
# 没有错误处理
```

---

## 完整示例

### 示例1：专利分析流程

```python
import asyncio
from core.llm.unified_llm_manager import get_unified_llm_manager

async def analyze_patent(patent_id: str):
    """完整的专利分析流程"""
    manager = await get_unified_llm_manager()

    # 步骤1: 检索专利信息
    search_response = await manager.generate(
        message=f"检索专利{patent_id}的信息",
        task_type="patent_search"
    )
    print(f"检索结果: {search_response.content}")

    # 步骤2: 新颖性分析
    novelty_response = await manager.generate(
        message=f"分析专利{patent_id}的新颖性",
        task_type="novelty_analysis",
        context={'patent_data': search_response.content}
    )
    print(f"新颖性分析: {novelty_response.content}")

    # 步骤3: 创造性分析
    creativity_response = await manager.generate(
        message=f"分析专利{patent_id}的创造性",
        task_type="creativity_analysis",
        enable_thinking=True,
        max_tokens=5000
    )
    print(f"创造性分析: {creativity_response.content}")

    # 步骤4: 生成成本报告
    cost_report = manager.get_cost_report()
    print(f"\n成本报告:\n{cost_report}")

if __name__ == '__main__':
    asyncio.run(analyze_patent("202311060998.X"))
```

### 示例2：批量处理

```python
import asyncio
from typing import List

async def batch_analyze(questions: List[str]):
    """批量分析问题"""
    manager = await get_unified_llm_manager()

    # 切换到成本优化策略
    manager.selector.strategy = SelectionStrategy.COST_OPTIMIZED

    results = []
    for i, question in enumerate(questions):
        print(f"处理问题 {i+1}/{len(questions)}")

        response = await manager.generate(
            message=question,
            task_type="simple_qa",
            temperature=0.3,  # 降低随机性
            max_tokens=500     # 限制输出
        )

        results.append({
            'question': question,
            'answer': response.content,
            'model': response.model_used,
            'cost': response.cost
        })

        # 打印进度
        if (i + 1) % 10 == 0:
            stats = manager.get_stats()
            print(f"进度: {i+1}/{len(questions)}, "
                  f"成功率: {stats['success_rate']:.1%}, "
                  f"总成本: ¥{stats['total_cost']:.2f}")

    return results

if __name__ == '__main__':
    questions = ["问题1", "问题2", "问题3"]  # 您的问题列表
    results = asyncio.run(batch_analyze(questions))
```

---

## 更多资源

- [单元测试](../../tests/unit/test_unified_llm.py)
- [模型适配器](../adapters/)
- [安全工具](security_utils.py)
- [成本监控](cost_monitor.py)
- [响应缓存](response_cache.py)

---

**更新日志**:

- **v1.0.0** (2026-01-23): 初始版本
  - ✅ 核心功能实现
  - ✅ Prometheus监控集成
  - ✅ 缓存预热机制
  - ✅ 完整单元测试覆盖

---

**许可证**: MIT

**联系方式**: 如有问题，请提交Issue或联系维护团队。
