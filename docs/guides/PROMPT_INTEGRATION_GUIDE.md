# 提示词系统集成指南

> 版本: v3.0 | 日期: 2026-04-05

## 一、快速集成

### 1.1 最简单的方式（推荐）

```python
from production.services.unified_prompt_loader_v3 import get_prompt

# 获取提示词 - 自动使用渐进式加载
prompt = get_prompt(
    task_type="patent_writing",  # 任务类型
    complexity="medium",          # 复杂度
    load_mode="progressive",      # 加载模式
)
```

### 1.2 使用加载器实例

```python
from production.services.unified_prompt_loader_v3 import (
    UnifiedPromptLoader,
    PromptConfig,
    LoadMode,
)

# 配置
config = PromptConfig(
    load_mode=LoadMode.PROGRESSIVE,  # 渐进式加载
    compression_ratio=0.4,           # 压缩到40%
    enable_cache=True,               # 启用缓存
)

# 创建加载器
loader = UnifiedPromptLoader(
    prompts_dir="/path/to/prompts",
    config=config,
)

# 加载提示词
loaded = loader.load("patent_writing", "medium")
prompt = loaded.get_content()

# 查看统计
print(f"Tokens: ~{loaded.total_tokens:,}")
print(f"缓存命中: {loaded.cache_hit}")
```

## 二、集成到现有代码

### 2.1 替换现有加载器

**旧代码：**
```python
from production.services.xiaona_prompt_loader import XiaonaPromptLoader

loader = XiaonaPromptLoader()
loader.load_all()
prompt = loader.get_full_prompt()
```

**新代码（向后兼容）：**
```python
from production.services.unified_prompt_loader_v3 import XiaonaPromptLoader

loader = XiaonaPromptLoader()
loader.load_all()
prompt = loader.get_full_prompt()  # 完全兼容
```

### 2.2 推荐的新方式

```python
from production.services.unified_prompt_loader_v3 import get_prompt

# 根据任务类型动态加载
def get_system_prompt(task_type: str) -> str:
    return get_prompt(
        task_type=task_type,
        complexity="medium" if task_type == "general" else "complex",
        load_mode="progressive",
    )
```

## 三、LLM服务集成

### 3.1 集成到LLM调用

```python
from production.services.unified_prompt_loader_v3 import UnifiedPromptLoader, PromptConfig

# 初始化加载器（全局一次）
prompt_loader = UnifiedPromptLoader(
    prompts_dir="/Users/xujian/Athena工作平台/prompts",
    config=PromptConfig(load_mode=LoadMode.PROGRESSIVE),
)

async def call_llm(task_type: str, user_message: str):
    # 加载提示词
    loaded = prompt_loader.load(task_type, "medium")
    system_prompt = loaded.get_content()
    
    # 调用LLM
    response = await llm_client.chat.completions.create(
        model="claude-3-sonnet",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )
    
    return response.choices[0].message.content
```

### 3.2 分阶段加载（推荐）

```python
from production.services.unified_prompt_loader_v3 import get_minimal_prompt, get_prompt

class ChatService:
    def __init__(self):
        # 初始只加载最小上下文
        self.minimal_prompt = get_minimal_prompt()
    
    def get_system_prompt(self, task_type: str = "general") -> str:
        """根据任务类型动态加载"""
        if task_type == "general":
            # 简单对话用最小上下文
            return self.minimal_prompt
        else:
            # 复杂任务加载完整提示词
            return get_prompt(task_type, "complex", "progressive")
```

## 四、配置选项

### 4.1 加载模式

| 模式 | Tokens | 适用场景 |
|------|--------|----------|
| `minimal` | ~1.7K | 简单对话、初始交互 |
| `progressive` | ~15-30K | 复杂任务（推荐） |
| `full` | ~125K | 需要完整上下文 |

### 4.2 配置参数

```python
config = PromptConfig(
    load_mode=LoadMode.PROGRESSIVE,  # 加载模式
    compression_ratio=0.4,           # 压缩比例
    cache_ttl=3600,                  # 缓存TTL（秒）
    cache_dir="/tmp/prompt_cache",   # 缓存目录
    enable_compression=True,         # 启用压缩
    enable_cache=True,               # 启用缓存
    verbose=False,                   # 详细日志
)
```

## 五、性能监控

### 5.1 获取统计

```python
stats = loader.get_stats()

print(f"缓存统计: {stats['cache_stats']}")
print(f"核心缓存大小: {stats['core_cache_size']}")
```

### 5.2 加载详情

```python
loaded = loader.load("patent_writing", "medium")

print(f"Tokens: ~{loaded.total_tokens:,}")
print(f"字符: {loaded.total_chars:,}")
print(f"加载时间: {loaded.load_time_ms:.1f}ms")
print(f"缓存命中: {loaded.cache_hit}")
print(f"压缩: {loaded.compressed}")

# 各片段详情
for segment in loaded.segments:
    print(f"  {segment.name}: ~{segment.token_count:,} tokens")
```

## 六、常见问题

### Q1: 如何验证优化效果？

```python
# 对比测试
from production.services.unified_prompt_loader_v3 import UnifiedPromptLoader, PromptConfig, LoadMode

# 原始（不压缩）
config_old = PromptConfig(load_mode=LoadMode.FULL, enable_compression=False)
loader_old = UnifiedPromptLoader("prompts", config_old)
old = loader_old.load("patent_writing", "medium")

# 优化后
config_new = PromptConfig(load_mode=LoadMode.PROGRESSIVE, enable_compression=True)
loader_new = UnifiedPromptLoader("prompts", config_new)
new = loader_new.load("patent_writing", "medium")

print(f"原始: ~{old.total_tokens:,} tokens")
print(f"优化: ~{new.total_tokens:,} tokens")
print(f"节省: {(1 - new.total_tokens/old.total_tokens)*100:.1f}%")
```

### Q2: 如何清除缓存？

```python
loader.clear_cache()
```

### Q3: 如何禁用压缩？

```python
config = PromptConfig(enable_compression=False)
```

## 七、最佳实践

1. **使用渐进式加载** - 初始只加载最小上下文，按需加载更多
2. **启用缓存** - 避免重复加载相同提示词
3. **监控Token消耗** - 定期检查 `loaded.total_tokens`
4. **根据任务类型选择复杂度** - 简单任务用 simple，复杂任务用 complex

---

*最后更新: 2026-04-05*
