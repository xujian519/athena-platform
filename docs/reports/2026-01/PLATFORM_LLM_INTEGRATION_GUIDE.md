# 平台LLM层集成 - 专利执行器完整指南

## 📋 概述

本文档说明如何使用Athena平台的统一LLM层进行专利分析。

**版本**: v2.1.0
**日期**: 2025-12-14
**作者**: Athena AI系统

---

## 🎯 集成架构

```
┌─────────────────────────────────────────────────────────┐
│               专利执行器（平台LLM层集成）                   │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  PatentAnalysisExecutor                                 │
│  ├─ PlatformLLMService (平台LLM客户端)                   │
│  ├─ CacheService (缓存服务)                             │
│  └─ DatabaseService (数据库服务)                        │
│                                                          │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│          Athena平台统一LLM层                               │
├─────────────────────────────────────────────────────────┤
│  UnifiedLLMManager (统一LLM管理器)                        │
│  ├─ ModelCapabilityRegistry (模型注册表)                 │
│  ├─ IntelligentModelSelector (智能模型选择器)            │
│  ├─ ResponseCache (响应缓存)                            │
│  └─ CostMonitor (成本监控)                              │
│                                                          │
│  模型适配器:                                             │
│  ├─ GLMAdapter (glm-4-plus, glm-4-flash)               │
│  ├─ DeepSeekAdapter (deepseek-chat, deepseek-reasoner)  │
│  ├─ QwenAdapter (qwen-plus, qwen-max)                  │
│  └─ LocalLLMAdapter (qwen2.5-7b-instruct-gguf)         │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 快速开始

### 1. 环境准备

```bash
# 确保平台LLM层已配置
cd /Users/xujian/Athena工作平台

# 检查配置文件
cat config/llm_model_registry.json

# 检查环境变量
env | grep LLM
```

### 2. 基础使用

```python
import asyncio
from patent_executors_platform_llm import (
    PatentExecutorFactory,
    PatentTask,
    TaskPriority
)

async def main():
    # 创建工厂
    factory = PatentExecutorFactory()

    # 创建任务
    task = PatentTask(
        id='task_001',
        task_type='patent_analysis',
        parameters={
            'patent_data': {
                'title': '基于深度学习的智能图像识别系统',
                'abstract': '本发明公开了一种基于深度学习的智能图像识别系统...',
                'claims': '1. 一种基于深度学习的智能图像识别系统...',
                'description': '本发明涉及人工智能技术领域...'
            },
            'analysis_type': 'novelty'
        },
        priority=TaskPriority.HIGH
    )

    # 执行任务
    result = await factory.execute_with_executor('patent_analysis', task)

    # 查看结果
    if result.is_success():
        print(f"✅ 分析完成")
        print(f"模型: {result.data['model_used']}")
        print(f"置信度: {result.confidence}")
    else:
        print(f"❌ 失败: {result.error}")

asyncio.run(main())
```

### 3. 运行演示

```bash
# 运行集成演示
python3 patent-platform/workspace/src/action/test_platform_llm_integration.py

# 运行单元测试
python3 patent-platform/workspace/src/action/patent_executors_platform_llm.py
```

---

## 📊 可用的LLM模型

### 云端模型

| 模型ID | 类型 | 上下文 | 延迟 | 质量 | 适用任务 |
|--------|------|--------|------|------|----------|
| glm-4-plus | 推理 | 128K | 1500ms | 0.95 | 新颖性、创造性分析 |
| glm-4-flash | 推理 | 200K | 800ms | 0.85 | 快速分析、文档生成 |
| deepseek-chat | 通用 | 32K | 1000ms | 0.88 | 综合分析 |
| deepseek-reasoner | 推理 | 64K | 2000ms | 0.92 | 复杂推理 |
| qwen-plus | 通用 | 128K | 1200ms | 0.90 | 通用分析 |
| qwen-max | 高级 | 32K | 1800ms | 0.93 | 高质量分析 |

### 本地模型

| 模型ID | 类型 | 上下文 | 延迟 | 质量 | 说明 |
|--------|------|--------|------|------|------|
| qwen2.5-7b-instruct-gguf | 通用 | 32K | 3000ms | 0.75 | 本地运行，离线可用 |

### 模型选择策略

执行器会根据分析类型自动选择最佳模型：

```python
# 代码中的模型选择逻辑
model_preferences = {
    'novelty': ['glm-4-plus', 'deepseek-chat'],           # 新颖性需要高质量推理
    'inventiveness': ['glm-4-plus', 'deepseek-reasoner'], # 创造性需要深度推理
    'comprehensive': ['glm-4-plus', 'deepseek-reasoner'], # 综合分析需要全面能力
    'technical_analysis': ['glm-4-flash', 'glm-4-plus'],  # 技术分析可以快速处理
    'legal_analysis': ['glm-4-plus', 'deepseek-chat'],    # 法律分析需要准确理解
    'industrial_applicability': ['glm-4-flash', 'glm-4-plus']  # 实用性分析相对简单
}
```

---

## 🔧 配置说明

### 模型注册表配置

**文件路径**: `config/llm_model_registry.json`

```json
{
  "models": [
    {
      "model_id": "glm-4-plus",
      "model_type": "reasoning",
      "deployment": "cloud",
      "max_context": 128000,
      "supports_streaming": true,
      "supports_function_call": true,
      "supports_thinking": true,
      "avg_latency_ms": 1500,
      "throughput_tps": 80,
      "cost_per_1k_tokens": 0.05,
      "quality_score": 0.95,
      "suitable_tasks": [
        "novelty_analysis",
        "creativity_analysis",
        "complex_analysis"
      ]
    }
  ]
}
```

### 环境变量配置

```bash
# GLM API配置
export GLM_API_KEY="your-glm-api-key"
export GLM_API_BASE="https://open.bigmodel.cn/api/paas/v4/"

# DeepSeek API配置
export DEEPSEEK_API_KEY="your-deepseek-api-key"

# 本地模型配置
export LOCAL_LLM_MODEL_PATH="/path/to/models"
export LOCAL_LLM_N_GPU_LAYERS="-1"

# 缓存配置
export ENABLE_RESPONSE_CACHE="true"
export CACHE_TTL="300"
```

---

## 📝 API参考

### PlatformLLMService

平台LLM服务客户端，封装了统一LLM层的调用。

#### analyze_patent()

使用平台LLM分析专利。

```python
async def analyze_patent(
    patent_data: Dict[str, Any],
    analysis_type: str = 'comprehensive'
) -> Dict[str, Any]
```

**参数**:
- `patent_data`: 专利数据字典
  - `title`: 专利标题
  - `abstract`: 专利摘要
  - `claims`: 权利要求
  - `description`: 说明书
- `analysis_type`: 分析类型
  - `novelty`: 新颖性分析
  - `inventiveness`: 创造性分析
  - `comprehensive`: 综合分析

**返回**:
```python
{
    'status': 'success',
    'analysis_result': {...},
    'provider': 'platform_llm',
    'model': 'glm-4-plus',
    'latency': 1.5,
    'tokens_used': 1234,
    'confidence': 0.85,
    'method': 'llm_analysis'
}
```

### PatentAnalysisExecutor

专利分析执行器，使用平台LLM层进行分析。

#### execute()

执行专利分析任务。

```python
async def execute(self, task: PatentTask) -> ExecutionResult
```

**返回**:
```python
ExecutionResult(
    status='success',
    data={
        'analysis_type': 'novelty',
        'analysis_result': {...},
        'report': {...},
        'recommendations': [...],
        'llm_provider': 'platform_llm',
        'model_used': 'glm-4-plus',
        'tokens_used': 1234
    },
    execution_time=1.5,
    confidence=0.85
)
```

---

## 🎨 使用示例

### 示例1: 新颖性分析

```python
from patent_executors_platform_llm import (
    PatentExecutorFactory,
    PatentTask
)

async def novelty_analysis():
    factory = PatentExecutorFactory()

    task = PatentTask(
        id='novelty_001',
        task_type='patent_analysis',
        parameters={
            'patent_data': {
                'title': '基于区块链的分布式数据存储系统',
                'abstract': '本发明提供一种基于区块链技术的分布式数据存储方案...',
                'claims': '1. 一种基于区块链的分布式数据存储系统...',
                'description': '本发明涉及区块链和分布式存储技术领域...'
            },
            'analysis_type': 'novelty'
        }
    )

    result = await factory.execute_with_executor('patent_analysis', task)

    # 查看新颖性评分
    if result.is_success():
        analysis = result.data['analysis_result']
        print(f"新颖性评分: {analysis.get('score')}")
        print(f"评估: {analysis.get('assessment')}")
```

### 示例2: 批量分析

```python
async def batch_analysis(patent_list):
    factory = PatentExecutorFactory()

    tasks = [
        PatentTask(
            id=f'task_{i}',
            task_type='patent_analysis',
            parameters={
                'patent_data': patent,
                'analysis_type': 'comprehensive'
            }
        )
        for i, patent in enumerate(patent_list)
    ]

    # 并发执行
    results = await asyncio.gather(*[
        factory.execute_with_executor('patent_analysis', task)
        for task in tasks
    ])

    return results
```

### 示例3: 自定义模型选择

```python
async def analysis_with_specific_model():
    from core.llm.unified_llm_manager import get_unified_llm_manager
    from core.llm.base import LLMRequest

    llm_manager = get_unified_llm_manager()
    await llm_manager.initialize()

    # 直接调用LLM管理器
    request = LLMRequest(
        message="请分析以下专利的新颖性...",
        context={'system_prompt': '你是一位专利分析专家'},
        temperature=0.7,
        max_tokens=2000
    )

    response = await llm_manager.generate(
        model_id='glm-4-plus',  # 指定模型
        request=request
    )

    print(f"响应: {response.content}")
    print(f"Token使用: {response.tokens_used}")
```

---

## 🔍 降级机制

当平台LLM层不可用时，系统会自动降级到规则引擎：

```python
# 降级逻辑
if not PLATFORM_LLM_AVAILABLE or not self.llm_manager:
    logger.warning("LLM不可用，使用规则引擎分析")
    return await self._rule_based_analysis(patent_data, analysis_type)
```

规则引擎特点：
- ✅ 无需外部依赖
- ✅ 基于规则的简单评分
- ⚠️ 分析精度有限
- ⚠️ 置信度较低(0.65)

---

## 📊 性能指标

### 执行时间对比

| 分析类型 | LLM分析 | 规则引擎 | 提升 |
|----------|---------|----------|------|
| 新颖性分析 | 1.5s | 0.1s | LLM质量更高 |
| 创造性分析 | 2.0s | 0.1s | LLM质量更高 |
| 综合分析 | 3.0s | 0.1s | LLM质量更高 |
| 缓存命中 | 0.1s | - | **95%提升** |

### 成本估算

| 模型 | 成本/1K tokens | 平均消耗 | 单次分析成本 |
|------|---------------|----------|-------------|
| glm-4-plus | ¥0.05 | 1500 tokens | ¥0.075 |
| glm-4-flash | ¥0.01 | 1200 tokens | ¥0.012 |
| deepseek-chat | ¥0.01 | 1800 tokens | ¥0.018 |
| 本地模型 | ¥0 | - | ¥0 |

---

## 🐛 故障排查

### 问题1: 平台LLM层不可用

```
错误: 无法导入平台LLM层
解决: 检查项目路径是否正确，确保core/llm目录存在
```

### 问题2: 模型加载失败

```
错误: ⚠️ GLM模型 glm-4-plus 适配器加载失败
解决:
1. 检查API密钥是否配置
2. 检查网络连接是否正常
3. 系统会自动降级到规则引擎
```

### 问题3: JSON解析失败

```
警告: JSON解析失败，返回原始文本
解决:
1. 这是正常情况，系统会返回原始文本
2. 不影响分析结果的使用
3. 可以尝试使用不同的模型
```

---

## 📈 监控和统计

### 获取LLM统计信息

```python
from core.llm.unified_llm_manager import get_unified_llm_manager

llm_manager = get_unified_llm_manager()
stats = llm_manager.stats

print(f"总请求数: {stats['total_requests']}")
print(f"成功率: {stats['successful_requests'] / stats['total_requests']:.2%}")
print(f"平均延迟: {stats['total_processing_time'] / stats['total_requests']:.2f}s")
print(f"总成本: ¥{stats['total_cost']:.2f}")
```

### 查看模型使用情况

```python
model_usage = stats['model_usage']
for model_id, count in model_usage.items():
    print(f"{model_id}: {count}次调用")
```

---

## 🚀 未来计划

### 短期 (1-2周)

- [ ] 添加更多分析类型
- [ ] 优化Prompt工程
- [ ] 支持流式响应
- [ ] 增加缓存预热

### 中期 (1-2月)

- [ ] 支持多模态分析（图片、表格）
- [ ] 集成知识图谱
- [ ] 添加分析历史
- [ ] 支持批量导出

### 长期 (3-6月)

- [ ] 自动优化模型选择
- [ ] 自定义分析模板
- [ ] 多语言支持
- [ ] 云端部署

---

## 📞 技术支持

### 相关文档

- 平台LLM层文档: `/core/llm/README.md`
- 模型注册表: `/config/llm_model_registry.json`
- 增强版执行器: `patent_executors_enhanced.py`
- 测试用例: `test_patent_executors_platform_llm.py`

### 联系方式

- 作者: Athena AI系统
- 创建日期: 2025-12-14
- 版本: v2.1.0

---

**更新日期**: 2025-12-14
**审核状态**: ✅ 已完成
