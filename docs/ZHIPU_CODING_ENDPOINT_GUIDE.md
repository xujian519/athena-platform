# 智谱GLM编程端点使用指南

> **端点地址**: https://open.bigmodel.cn/api/coding/paas/v4
> **专门优化**: 代码生成、代码分析、编程辅助

---

## 🔌 两个端点对比

### 智谱GLM提供两个API端点

| 端点类型 | URL | 用途 | 模型 |
|---------|-----|------|------|
| **聊天端点** | `https://open.bigmodel.cn/api/paas/v4` | 通用对话、文本生成 | glm-4-flash/plus/air |
| **编程端点** ⭐ | `https://open.bigmodel.cn/api/coding/paas/v4` | 代码生成、编程辅助 | glm-4-flash |

---

## 📊 端点选择指南

### 使用聊天端点 (`endpoint_type="chat"`)

**适用场景**:
- ✅ 专利分析
- ✅ 法律推理
- ✅ 文本摘要
- ✅ 通用对话
- ✅ 文档撰写

**示例**:
```python
adapter = CloudLLMAdapter(
    provider="zhipu",
    model="flash",
    endpoint_type="chat"  # 默认值
)

result = await adapter.generate("分析专利CN123456789A的创造性")
```

### 使用编程端点 (`endpoint_type="coding"`)

**适用场景**:
- ✅ 代码生成
- ✅ 代码分析
- ✅ 代码优化
- ✅ 调试辅助
- ✅ 技术问题解答

**示例**:
```python
adapter = CloudLLMAdapter(
    provider="zhipu",
    model="coding",
    endpoint_type="coding"  # 使用编程端点
)

result = await adapter.generate("编写一个快速排序算法")
```

---

## 🚀 快速开始

### 步骤1: 配置API密钥

```bash
export ZHIPU_API_KEY="your-api-key-here"
```

### 步骤2: 测试编程端点

```bash
cd /Users/xujian/Athena工作平台

# 运行编程端点测试
python tests/test_zhipu_coding.py

# 对比聊天端点和编程端点
python tests/test_zhipu_coding.py --compare
```

### 步骤3: 在代码中使用

**方法1: 生成代码**
```python
import asyncio
from core.llm.adapters.cloud_adapter import CloudLLMAdapter

async def generate_code():
    adapter = CloudLLMAdapter(
        provider="zhipu",
        model="coding",
        endpoint_type="coding"
    )

    await adapter.initialize()

    code = await adapter.generate(
        prompt="编写一个Python函数计算斐波那契数列",
        temperature=0.3,
        max_tokens=2000
    )

    print(code)
    await adapter.close()

asyncio.run(generate_code())
```

**方法2: 分析代码**
```python
async def analyze_code():
    adapter = CloudLLMAdapter(
        provider="zhipu",
        model="coding",
        endpoint_type="coding"
    )

    await adapter.initialize()

    analysis = await adapter.generate(
        prompt="""分析以下代码的时间复杂度:

        def find_duplicates(arr):
            seen = set()
            duplicates = []
            for item in arr:
                if item in seen:
                    duplicates.append(item)
                else:
                    seen.add(item)
            return duplicates
        """,
        temperature=0.5,
        max_tokens=1000
    )

    print(analysis)
    await adapter.close()

asyncio.run(analyze_code())
```

---

## 💡 实际应用场景

### 场景1: 专利分析工具开发

**任务**: 编写一个专利检索脚本

```python
adapter = CloudLLMAdapter(
    provider="zhipu",
    model="coding",
    endpoint_type="coding"
)

await adapter.initialize()

prompt = """
编写一个Python函数，用于从专利数据库检索专利。
要求：
1. 使用asyncio异步请求
2. 支持多个关键词查询
3. 返回JSON格式结果
4. 包含错误处理
"""

code = await adapter.generate(prompt, temperature=0.3)
print(code)
```

### 场景2: 代码审查

**任务**: 审查现有代码质量

```python
adapter = CloudLLMAdapter(
    provider="zhipu",
    model="coding",
    endpoint_type="coding"
)

await adapter.initialize()

prompt = """
请审查以下Python代码的质量，指出潜在问题：
1. 性能问题
2. 安全漏洞
3. 代码风格
4. 最佳实践

代码：
[你的代码]
"""

review = await adapter.generate(prompt, temperature=0.5)
print(review)
```

### 场景3: 算法优化

**任务**: 优化算法性能

```python
adapter = CloudLLMAdapter(
    provider="zhipu",
    model="coding",
    endpoint_type="coding"
)

await adapter.initialize()

prompt = """
优化以下Python代码的性能：
[你的低效代码]

要求：
1. 降低时间复杂度
2. 保持功能不变
3. 添加注释说明优化思路
"""

optimized = await adapter.generate(prompt, temperature=0.4)
print(optimized)
```

---

## 📈 性能对比

### 代码生成质量

| 任务类型 | 聊天端点 | 编程端点 | 推荐 |
|---------|---------|---------|------|
| 生成简单函数 | 良好 | 优秀 | 编程端点 |
| 生成复杂算法 | 一般 | 优秀 | 编程端点 |
| 代码调试 | 一般 | 优秀 | 编程端点 |
| 代码审查 | 一般 | 优秀 | 编程端点 |
| 非编程任务 | 优秀 | 不适用 | 聊天端点 |

### 成本对比

两个端点价格相同:
- **输入**: ¥0.5/百万tokens
- **输出**: ¥0.5/百万tokens

**成本优势**: 使用编程端点获得更好的代码质量，但价格不变！

---

## 🔧 配置说明

### 端点配置 (`config/cloud_llm_config.json`)

```json
"zhipu": {
  "name": "智谱GLM",
  "api_key": "${ZHIPU_API_KEY}",
  "base_url": "https://open.bigmodel.cn/api/paas/v4",
  "coding_url": "https://open.bigmodel.cn/api/coding/paas/v4",
  "models": {
    "flash": "glm-4-flash",
    "plus": "glm-4-plus",
    "air": "glm-4-air",
    "coding": "glm-4-flash"
  }
}
```

### 适配器配置 (`core/llm/adapters/cloud_adapter.py`)

```python
DEFAULT_ENDPOINTS = {
    "zhipu": {
        "chat": {
            "base_url": "https://open.bigmodel.cn/api/paas/v4",
            "models": {
                "flash": "glm-4-flash",
                "plus": "glm-4-plus",
                "air": "glm-4-air"
            }
        },
        "coding": {
            "base_url": "https://open.bigmodel.cn/api/coding/paas/v4",
            "models": {
                "coding": "glm-4-flash"
            }
        }
    }
}
```

---

## ⚠️ 注意事项

### 1. 端点选择

**错误示例**:
```python
# ❌ 使用聊天端点生成代码
adapter = CloudLLMAdapter(
    provider="zhipu",
    model="flash",
    endpoint_type="chat"  # 默认
)
code = await adapter.generate("编写快速排序算法")
```

**正确示例**:
```python
# ✅ 使用编程端点生成代码
adapter = CloudLLMAdapter(
    provider="zhipu",
    model="coding",
    endpoint_type="coding"  # 明确指定
)
code = await adapter.generate("编写快速排序算法")
```

### 2. 温度参数

**代码生成建议使用较低温度**:
```python
# 代码生成 - 温度0.2-0.4
code = await adapter.generate(
    prompt="编写排序算法",
    temperature=0.3  # 代码需要确定性
)

# 代码分析 - 温度0.4-0.6
analysis = await adapter.generate(
    prompt="分析这段代码",
    temperature=0.5  # 允许一些变化
)

# 创意编程 - 温度0.6-0.8
creative = await adapter.generate(
    prompt="设计一个有趣的数据结构",
    temperature=0.7  # 需要创造性
)
```

### 3. 提示词工程

**好的代码生成提示词**:
```
编写一个[语言]函数来[任务描述]。

要求：
1. [具体要求1]
2. [具体要求2]
3. [具体要求3]

包含：
- 类型注解
- 文档字符串
- 示例代码
- 错误处理
```

---

## 🧪 测试脚本

### 运行测试

```bash
# 测试编程端点
python tests/test_zhipu_coding.py

# 对比两个端点
python tests/test_zhipu_coding.py --compare
```

### 预期输出

```
🧪 测试智谱GLM编程端点
============================================================
端点: https://open.bigmodel.cn/api/coding/paas/v4
============================================================

1️⃣ 创建编程端点适配器...
2️⃣ 初始化连接...
✅ 连接成功

3️⃣ 测试代码生成...
提示词: 编写一个Python函数计算斐波那契数列

✅ 代码生成成功

📝 生成的代码:
------------------------------------------------------------
def fibonacci(n: int) -> int:
    """
    计算斐波那契数列的第n项（递归实现）

    Args:
        n: 要计算的项数

    Returns:
        第n项的值

    Examples:
        >>> fibonacci(10)
        55
        >>> fibonacci(20)
        6765
    """
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
------------------------------------------------------------

🎉 所有测试通过！智�谱GLM编程端点工作正常
```

---

## 📚 相关文档

- **快速启动**: [QUICK_START_CLOUD_LLM.md](QUICK_START_CLOUD_LLM.md)
- **成本分析**: [CLOUD_LLM_COST_ANALYSIS.md](CLOUD_LLM_COST_ANALYSIS.md)
- **迁移指南**: [MIGRATION_TO_CLOUD_LLM.md](MIGRATION_TO_CLOUD_LLM.md)
- **文档索引**: [CLOUD_LLM_README.md](CLOUD_LLM_README.md)

---

## 🎯 总结

### 关键要点

1. **两个端点**:
   - 聊天端点: `/api/paas/v4` (通用)
   - 编程端点: `/api/coding/paas/v4` (编程专用)

2. **正确选择**:
   - 编程任务 → 使用 `endpoint_type="coding"`
   - 非编程任务 → 使用 `endpoint_type="chat"` (默认)

3. **成本相同**:
   - 两个端点价格都是 ¥0.5/百万tokens
   - 编程端点质量更好，但价格不变

4. **立即开始**:
   ```bash
   python tests/test_zhipu_coding.py
   ```

---

**维护者**: 徐健 (xujian519@gmail.com)
**项目位置**: `/Users/xujian/Athena工作平台/`
**最后更新**: 2026-04-23

---

**🌸 Athena平台 - 智谱GLM编程端点，代码生成更专业！**
