# 云端模型快速启动指南

> **5分钟完成云端模型配置，成本降低99.9%**
> **难度**: ⭐☆☆☆☆ (非常简单)

---

## 🚀 快速开始 (3步)

### 步骤1: 获取API密钥 (2分钟)

**推荐使用DeepSeek** (最便宜 + 中文友好):

1. 访问: https://platform.deepseek.com/
2. 注册账号 (手机号或邮箱)
3. 进入"API Keys"页面
4. 点击"Create new key"
5. 复制API密钥 (格式: `sk-xxxxxxxx`)

### 步骤2: 配置环境变量 (1分钟)

**临时配置** (当前会话):
```bash
export DEEPSEEK_API_KEY="sk-your-api-key-here"
```

**永久配置** (推荐):
```bash
echo 'export DEEPSEEK_API_KEY="sk-your-api-key-here"' >> ~/.zshrc
source ~/.zshrc
```

**验证配置**:
```bash
echo $DEEPSEEK_API_KEY
```

### 步骤3: 测试连接 (2分钟)

**运行测试脚本**:
```bash
cd /Users/xujian/Athena工作平台
python tests/test_cloud_llm_integration.py
```

**预期输出**:
```
🌸 Athena平台 - 云端LLM集成测试
============================================================
📋 检查环境变量配置:
  ✅ DeepSeek        已配置

已配置服务: DeepSeek
============================================================
💰 成本优化策略测试
============================================================

⏳ 测试 deepseek (¥1/百万tokens - 推荐)...
✅ deepseek 可用

💡 推荐使用: deepseek（成本最低且可用）

============================================================
🔍 详细测试
============================================================

🧪 测试 DEEPSEEK - chat 模型
⏳ 正在初始化...
⏳ 测试简单生成...
✅ 生成成功
📝 结果: 专利法是保护发明创造权利的法律制度...
✅ DEEPSEEK 测试通过

============================================================
📊 最终测试报告
============================================================
DeepSeek        ✅ 通过

通过率: 1/1 (100.0%)

🎉 所有测试通过！云端LLM已准备就绪。
```

---

## 💰 成本对比

| 项目 | 本地模型 | 云端模型(DeepSeek) |
|------|---------|-------------------|
| 硬件成本 | ¥40,000 | ¥0 |
| 月度成本 | ¥3,083/月 | ¥2/月 |
| 年度成本 | ¥36,996/年 | ¥24/年 |
| **节省** | - | **99.9%** |

**每月1000次专利分析**:
- 本地模型: ¥3,083
- 云端模型: ¥2
- **年节省**: ¥36,972

---

## 📖 使用示例

### 1. Python代码中使用

#### 1.1 通用任务（聊天端点）

```python
import asyncio
from core.llm.adapters.cloud_adapter import CloudLLMAdapter

async def main():
    # 创建DeepSeek客户端
    adapter = CloudLLMAdapter(provider="deepseek", model="chat")
    await adapter.initialize()

    # 生成文本
    result = await adapter.generate(
        prompt="分析专利CN123456789A的创造性",
        temperature=0.7,
        max_tokens=2000
    )

    print(result)
    await adapter.close()

asyncio.run(main())
```

#### 1.2 编程任务（智谱GLM编程端点）

```python
import asyncio
from core.llm.adapters.cloud_adapter import CloudLLMAdapter

async def generate_code():
    # 使用智谱GLM编程端点
    adapter = CloudLLMAdapter(
        provider="zhipu",
        model="coding",
        endpoint_type="coding"  # 使用编程端点
    )
    await adapter.initialize()

    # 生成代码
    code = await adapter.generate(
        prompt="编写一个Python快速排序算法",
        temperature=0.3,  # 代码生成建议使用较低温度
        max_tokens=2000
    )

    print(code)
    await adapter.close()

asyncio.run(generate_code())
```

**注意**: 智谱GLM提供两个端点
- **聊天端点**: 通用对话、文本分析（默认）
- **编程端点**: 代码生成、代码分析（编程专用）

详见: [智谱GLM编程端点指南](ZHIPU_CODING_ENDPOINT_GUIDE.md)

### 2. 在Athena平台中使用

**统一LLM管理器会自动选择最优模型**:

```python
from core.llm.unified_llm_manager import get_llm_manager

# 获取管理器
manager = get_llm_manager()

# 自动使用云端模型（成本优化）
result = await manager.generate(
    prompt="分析专利...",
    provider_preference="cloud"  # 优先使用云端
)
```

### 3. 命令行使用

```bash
# 运行测试
python tests/test_cloud_llm_integration.py

# 查看成本分析
cat docs/CLOUD_LLM_COST_ANALYSIS.md

# 查看迁移指南
cat docs/MIGRATION_TO_CLOUD_LLM.md
```

---

## 🔧 故障排除

### 问题1: API密钥无效

**错误**: `AuthenticationError: Invalid API key`

**解决方案**:
1. 检查API密钥是否正确复制
2. 确认没有多余空格: `export DEEPSEEK_API_KEY="sk-xxx"` (不要有空格)
3. 验证环境变量: `echo $DEEPSEEK_API_KEY`

### 问题2: 网络连接失败

**错误**: `ConnectionError: Connection timeout`

**解决方案**:
1. 检查网络连接: `ping api.deepseek.com`
2. 尝试访问网站: `curl https://api.deepseek.com`
3. 检查防火墙设置

### 问题3: OpenAI SDK未安装

**错误**: `ModuleNotFoundError: No module named 'openai'`

**解决方案**:
```bash
# 使用Poetry
poetry add openai

# 或使用pip
pip install openai
```

---

## 🎯 推荐配置

### 个人用户 (推荐)

**服务商**: DeepSeek
**成本**: ¥2/月 (1000次分析)
**优势**:
- ✅ 最便宜的云端API
- ✅ 中文支持好
- ✅ 性能稳定

### 团队使用

**服务商**: DeepSeek + 通义千问
**成本**: ¥36/月 (10000次分析)
**优势**:
- ✅ 多服务商负载均衡
- ✅ 避免单点故障
- ✅ 中文优化

### 企业用户

**策略**: 混合架构
- 简单任务: 智谱GLM (¥0.5/百万tokens)
- 标准任务: DeepSeek (¥1/百万tokens)
- 复杂任务: 通义千问Max (¥2/百万tokens)
- 隐私数据: 本地模型

---

## 📚 更多资源

### 官方文档
- **DeepSeek**: https://platform.deepseek.com/docs
- **通义千问**: https://help.aliyun.com/zh/dashscope/
- **智谱GLM**: https://open.bigmodel.cn/dev/api

### Athena平台文档
- **成本分析**: `docs/CLOUD_LLM_COST_ANALYSIS.md`
- **迁移指南**: `docs/MIGRATION_TO_CLOUD_LLM.md`
- **API适配器**: `core/llm/adapters/cloud_adapter.py`
- **配置文件**: `config/cloud_llm_config.json`

### 测试脚本
- **集成测试**: `tests/test_cloud_llm_integration.py`
- **单元测试**: `tests/core/llm/test_cloud_adapter.py`

---

## ✅ 下一步

1. **运行测试**: `python tests/test_cloud_llm_integration.py`
2. **查看成本**: 阅读 `docs/CLOUD_LLM_COST_ANALYSIS.md`
3. **迁移代码**: 参考 `docs/MIGRATION_TO_CLOUD_LLM.md`
4. **监控使用**: 设置API使用量告警

---

**维护者**: 徐健 (xujian519@gmail.com)
**项目位置**: `/Users/xujian/Athena工作平台/`
**最后更新**: 2026-04-23

---

**🌸 Athena平台 - 云端模型，成本更低，性能更好！**
