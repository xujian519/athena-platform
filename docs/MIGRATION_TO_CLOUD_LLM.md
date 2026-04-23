# 本地模型 → 云端模型迁移指南

> **目标**: 降低成本、简化运维、提升扩展性  
> **难度**: ⭐⭐☆☆☆ (简单)  
> **预计时间**: 30-60分钟

---

## 📋 迁移步骤

### 步骤1: 获取API密钥

**DeepSeek** (推荐 - 最便宜) ⭐⭐⭐⭐⭐
1. 访问: https://platform.deepseek.com/
2. 注册账号
3. 进入"API Keys"页面
4. 创建新的API密钥
5. 设置环境变量:
   ```bash
   export DEEPSEEK_API_KEY="sk-xxxxxxxxxxxxxxxx"
   ```

**通义千问** (阿里云)
1. 访问: https://dashscope.aliyuncs.com/
2. 登录阿里云账号
3. 开通DashScope服务
4. 创建API-KEY
5. 设置环境变量:
   ```bash
   export DASHSCOPE_API_KEY="sk-xxxxxxxxxxxxxxxx"
   ```

**智谱GLM**
1. 访问: https://open.bigmodel.cn/
2. 注册账号
3. 申请API Key
4. 设置环境变量:
   ```bash
   export ZHIPU_API_KEY="xxxxxxxxxxxxxxxx"
   ```

---

### 步骤2: 安装依赖

```bash
cd /Users/xujian/Athena工作平台

# 安装OpenAI SDK (云端API必需)
pip install openai

# 或使用Poetry
poetry add openai
```

---

### 步骤3: 配置环境变量

**临时设置** (当前会话):
```bash
export DEEPSEEK_API_KEY="sk-your-api-key"
export DASHSCOPE_API_KEY="sk-your-api-key"
export ZHIPU_API_KEY="your-api-key"
```

**永久设置** (添加到 ~/.zshrc):
```bash
echo 'export DEEPSEEK_API_KEY="sk-your-api-key"' >> ~/.zshrc
echo 'export DASHSCOPE_API_KEY="sk-your-api-key"' >> ~/.zshrc
echo 'export ZHIPU_API_KEY="your-api-key"' >> ~/.zshrc
source ~/.zshrc
```

---

### 步骤4: 测试云端API

**快速测试脚本**:

```python
# test_cloud_api.py
import asyncio
from core.llm.adapters.cloud_adapter import CloudLLMAdapter

async def test_cloud_api():
    """测试云端API"""
    
    print("🧪 测试云端LLM服务\n")
    
    # 测试DeepSeek
    print("1️⃣ 测试DeepSeek...")
    try:
        deepseek = CloudLLMAdapter(provider="deepseek", model="chat")
        await deepseek.initialize()
        result = await deepseek.generate("简单介绍一下专利法")
        print(f"✅ DeepSeek测试成功")
        print(f"   回复: {result[:100]}...")
        await deepseek.close()
    except Exception as e:
        print(f"❌ DeepSeek测试失败: {e}\n")
    
    # 测试通义千问
    print("\n2️⃣ 测试通义千问...")
    try:
        qwen = CloudLLMAdapter(provider="qwen", model="turbo")
        await qwen.initialize()
        result = await qwen.generate("简单介绍一下专利法")
        print(f"✅ 通义千问测试成功")
        print(f"   回复: {result[:100]}...")
        await qwen.close()
    except Exception as e:
        print(f"❌ 通义千问测试失败: {e}\n")
    
    # 测试智谱GLM
    print("\n3️⃣ 测试智谱GLM...")
    try:
        zhipu = CloudLLMAdapter(provider="zhipu", model="flash")
        await zhipu.initialize()
        result = await zhipu.generate("简单介绍一下专利法")
        print(f"✅ 智谱GLM测试成功")
        print(f"   回复: {result[:100]}...")
        await zhipu.close()
    except Exception as e:
        print(f"❌ 智谱GLM测试失败: {e}\n")

if __name__ == "__main__":
    asyncio.run(test_cloud_api())
```

运行测试:
```bash
cd /Users/xujian/Athena工作平台
python test_cloud_api.py
```

---

### 步骤5: 修改现有代码

**修改前** (本地模型):
```python
from core.llm.adapters.qwen_adapter import QwenAdapter

# 使用本地模型
adapter = QwenAdapter(model_id="qwen2.5-72b")
await adapter.initialize()
result = await adapter.generate("分析专利...")
```

**修改后** (云端模型):
```python
from core.llm.adapters.cloud_adapter import CloudLLMAdapter

# 使用云端模型
adapter = CloudLLMAdapter(provider="deepseek", model="chat")
await adapter.initialize()
result = await adapter.generate("分析专利...")
```

**无需修改** (如果使用统一LLM管理器):
```python
from core.llm.unified_llm_manager import UnifiedLLMManager

# 统一管理器会自动选择模型
manager = UnifiedLLMManager()
result = await manager.generate("分析专利...")
```

---

## 🎯 推荐配置方案

### 方案A: 纯云端架构 (推荐新手) ⭐⭐⭐⭐⭐

**优势**:
- ✅ 零运维成本
- ✅ 按量付费
- ✅ 无需本地GPU
- ✅ 自动扩展

**配置**:
```json
{
  "default_provider": "deepseek",
  "fallback_providers": ["qwen", "zhipu"]
}
```

**成本估算** (1000次专利分析/月):
- DeepSeek: ¥1/百万tokens × 10万tokens = ¥10/月
- 通义千问: ¥0.8/百万tokens × 10万tokens = ¥8/月

---

### 方案B: 混合架构 (推荐专业用户) ⭐⭐⭐⭐

**策略**:
- 简单任务 → DeepSeek (云端)
- 复杂推理 → 通义千问Max (云端)
- 隐私敏感 → 本地模型
- 高并发 → 多云端负载均衡

**配置**:
```python
routing_rules = {
    "simple_task": "deepseek",      # 简单任务用DeepSeek
    "complex_reasoning": "qwen-max",  # 复杂推理用Qwen Max
    "sensitive_data": "local",      # 敏感数据用本地
    "high_volume": "round_robin"    # 高并发用轮询
}
```

---

## ⚠️ 注意事项

### 1. 数据隐私

**云端API风险**:
- 数据会发送到第三方服务器
- 需要审查服务提供商的隐私政策
- 专利数据可能包含敏感信息

**建议**:
- ✅ 非敏感数据使用云端
- ✅ 敏感数据使用本地模型
- ✅ 脱敏处理后再发送云端

### 2. 网络延迟

**云端API延迟**:
- API调用: 200-500ms
- 相比本地: 50-100ms

**影响**:
- 单次调用差异不大
- 批量调用会有累积延迟

**解决方案**:
- ✅ 使用异步并发
- ✅ 实现响应缓存
- ✅ 批量请求并行化

### 3. API限流

**常见限流**:
- DeepSeek: 10000次/分钟
- 通义千问: 10000次/分钟
- 智谱GLM: 5000次/分钟

**解决方案**:
```python
# 实现重试机制
max_retries = 3
retry_after = 60  # 秒

# 实现队列缓冲
request_queue = asyncio.Queue(maxsize=1000)
```

### 4. 成本监控

**建议**:
- 设置月度预算上限
- 监控API调用量
- 定期审查账单

---

## 📊 成本对比

### 场景: 1000次专利分析/月

| 服务商 | 模型 | 输入tokens | 输出tokens | 成本/月 |
|--------|------|-----------|-----------|---------|
| **DeepSeek** | deepseek-chat | 10万 | 10万 | **¥20** |
| **通义千问** | qwen-turbo | 10万 | 10万 | **¥16** |
| **智谱GLM** | glm-4-flash | 10万 | 10万 | **¥10** |
| **本地模型** | Qwen2.5-72B | - | - | **¥100** (电费) |

**结论**: 云端模型成本仅为本地模型的1/5-1/10

---

## ✅ 迁移检查清单

### 准备阶段
- [ ] 选择云端服务提供商
- [ ] 注册账号并获取API密钥
- [ ] 设置环境变量
- [ ] 安装OpenAI SDK
- [ ] 运行测试脚本验证

### 实施阶段
- [ ] 修改配置文件
- [ ] 更新代码中的模型调用
- [ ] 测试关键功能
- [ ] 监控API调用量

### 验证阶段
- [ ] 功能测试（对比本地模型结果）
- [ ] 性能测试（响应时间、吞吐量）
- [ ] 成本验证（检查API账单）
- [ ] 压力测试（并发、限流）

### 运维阶段
- [ ] 设置成本告警
- [ ] 配置API密钥轮换
- [ ] 建立监控仪表板
- [ ] 制定降级方案

---

## 🆘 故障排除

### 问题1: API密钥无效

**错误**: `AuthenticationError: Invalid API key`

**解决方案**:
1. 检查环境变量是否设置
2. 验证API密钥是否正确
3. 检查API密钥是否已激活

### 问题2: 网络连接失败

**错误**: `ConnectionError: Connection timeout`

**解决方案**:
1. 检查网络连接
2. 尝试访问其他网站
3. 检查防火墙设置
4. 使用代理（如果需要）

### 问题3: API限流

**错误**: `RateLimitError: Rate limit exceeded`

**解决方案**:
1. 实现重试机制（指数退避）
2. 添加请求队列
3. 升级到更高套餐
4. 使用多服务商负载均衡

---

## 📚 参考资源

### 官方文档
- DeepSeek: https://platform.deepseek.com/docs
- 通义千问: https://help.aliyun.com/zh/dashscope/
- 智谱GLM: https://open.bigmodel.cn/dev/api

### OpenAI SDK文档
- https://github.com/openai/openai-python

### Athena平台文档
- 统一LLM管理器: `/core/llm/unified_llm_manager.py`
- DeepSeek客户端: `/core/llm/deepseek_client.py`
- 云端适配器: `/core/llm/adapters/cloud_adapter.py`

---

**维护者**: 徐健 (xujian519@gmail.com)
**项目位置**: `/Users/xujian/Athena工作平台/`
**最后更新**: 2026-04-23

---

**🌸 Athena平台 - 使用云端模型，降低成本，简化运维！**
