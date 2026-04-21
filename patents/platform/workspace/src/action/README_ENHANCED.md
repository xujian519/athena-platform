# 增强版专利执行器 - 快速启动指南

## 🚀 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install -r requirements.txt

# 或手动安装核心依赖
pip install aiohttp psycopg2-binary redis pytest pytest-asyncio
```

### 2. 配置环境变量

创建 `.env` 文件：

```bash
# AI服务（至少配置一个）
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."

# 数据库
export PG_HOST="localhost"
export PG_PORT="5432"
export PG_DATABASE="athena"
export PG_USER="postgres"
export PG_PASSWORD="..."

# 缓存
export REDIS_HOST="localhost"
export REDIS_PORT="6379"

# 执行器
export ENABLE_CACHE="true"
export CACHE_TTL="300"
```

### 3. 运行测试

```bash
# 运行所有测试
pytest tests/test_patent_executors_enhanced.py -v

# 运行增强版执行器自测
python patent-platform/workspace/src/action/patent_executors_enhanced.py
```

### 4. 使用示例

```python
import asyncio
from patent_executors_enhanced import (
    PatentExecutorFactory,
    PatentTask,
    TaskPriority,
    AnalysisType
)

async def main():
    # 创建工厂
    factory = PatentExecutorFactory()

    # 创建分析任务
    task = PatentTask(
        id='analysis_001',
        task_type='patent_analysis',
        parameters={
            'patent_data': {
                'title': '基于深度学习的智能图像识别系统',
                'abstract': '本发明公开了一种基于深度学习的智能图像识别系统...',
                'claims': '1. 一种基于深度学习的智能图像识别系统...'
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
        print(f"置信度: {result.confidence:.2f}")
        print(f"报告: {result.data['report']}")
        print(f"建议: {result.data['recommendations']}")
    else:
        print(f"❌ 执行失败: {result.error}")

if __name__ == '__main__':
    asyncio.run(main())
```

## 📋 API参考

### 执行器工厂

```python
factory = PatentExecutorFactory()

# 列出所有执行器
executors = factory.list_executors()

# 获取执行器
executor = factory.get_executor('patent_analysis')

# 执行任务
result = await factory.execute_with_executor('patent_analysis', task)
```

### 可用执行器

| 执行器名称 | 别名 | 功能 |
|-----------|------|------|
| patent_analysis | analysis, novelty_analysis | 专利分析 |
| patent_filing | filing, utility_filing | 专利申请 |
| patent_monitoring | monitoring | 专利监控 |
| patent_validation | validation | 专利验证 |

### 任务参数

#### 专利分析 (patent_analysis)

```python
parameters = {
    'patent_data': {
        'title': '专利标题',
        'abstract': '专利摘要',
        'claims': '权利要求',
        'description': '说明书'
    },
    'analysis_type': 'novelty',  # novelty, inventiveness, comprehensive
    'depth': 'standard'  # standard, detailed
}
```

#### 专利申请 (patent_filing)

```python
parameters = {
    'patent_data': {...},
    'filing_type': 'utility_model',  # invention_patent, utility_model, design_patent
    'jurisdiction': 'CN',  # 国家代码
    'expedited': False  # 是否加急
}
```

#### 专利监控 (patent_monitoring)

```python
parameters = {
    'patent_ids': ['CN202410001234.5', 'CN202410001235.2'],
    'monitoring_type': 'legal_status',  # legal_status, infringement, competitor
    'frequency': 'weekly',  # daily, weekly, monthly
    'alert_threshold': 0.8
}
```

#### 专利验证 (patent_validation)

```python
parameters = {
    'patent_data': {...},
    'validation_scope': 'comprehensive'  # comprehensive, formality, technical
}
```

## 🔧 高级用法

### 自定义配置

```python
import os
from patent_executors_enhanced import ExecutorConfig, PatentExecutorFactory

# 通过环境变量配置
os.environ['AI_PROVIDER'] = 'anthropic'
os.environ['CACHE_TTL'] = '600'

factory = PatentExecutorFactory()
```

### 批量执行

```python
async def batch_analysis(patent_list):
    factory = PatentExecutorFactory()

    tasks = [
        PatentTask(
            id=f'task_{i}',
            task_type='patent_analysis',
            parameters={'patent_data': patent, 'analysis_type': 'comprehensive'}
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

### 错误处理

```python
result = await factory.execute_with_executor('patent_analysis', task)

if result.is_failed():
    print(f"错误: {result.error}")
    print(f"执行时间: {result.execution_time:.2f}秒")
elif result.status == 'partial':
    print(f"部分成功")
    print(f"警告: {result.warnings}")
```

### 使用缓存

```python
# 启用缓存（通过环境变量）
export ENABLE_CACHE="true"
export CACHE_TTL="300"

# 或在代码中
config = ExecutorConfig()
config.enable_cache = True
config.cache_ttl = 300

factory = PatentExecutorFactory(config)
```

## 📊 性能优化建议

1. **启用缓存**: 对重复分析任务可提升95%性能
2. **调整并发**: 根据服务器资源调整MAX_CONCURRENT_TASKS
3. **选择合适的AI模型**: gpt-3.5-turbo速度更快，gpt-4质量更高
4. **使用批量处理**: 一次性处理多个任务

## 🐛 故障排查

### 问题1: AI服务不可用

```
错误: 无法导入ExternalAIManager
解决: 检查AI服务配置，系统会自动降级到规则引擎
```

### 问题2: 数据库连接失败

```
错误: 数据库连接失败
解决: 检查PostgreSQL是否运行，配置是否正确
```

### 问题3: 任务执行超时

```
错误: 任务执行超时
解决: 增加TASK_TIMEOUT环境变量值
```

## 📞 获取帮助

- 查看完整文档: `/docs/03-reports/2026-01/PATENT_EXECUTORS_ENHANCEMENT_REPORT.md`
- 查看测试用例: `/tests/test_patent_executors_enhanced.py`
- 查看源代码: `/patent-platform/workspace/src/action/patent_executors_enhanced.py`
