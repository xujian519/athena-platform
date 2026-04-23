# 云端模型迁移检查清单

> **按顺序完成以下步骤，预计总时间: 30分钟**

---

## 📋 准备阶段 (10分钟)

### ✅ 步骤1: 选择服务商

**推荐**: DeepSeek (最便宜 + 中文友好)

| 服务商 | 成本 | 优势 | 推荐度 |
|--------|------|------|--------|
| **DeepSeek** | ¥1/百万tokens | 最便宜、中文好 | ⭐⭐⭐⭐⭐ |
| 通义千问 | ¥0.8/百万tokens | 阿里云生态 | ⭐⭐⭐⭐ |
| 智谱GLM | ¥0.5/百万tokens | 快速响应 | ⭐⭐⭐⭐ |
| Claude | ¥3-15/百万tokens | 质量最高 | ⭐⭐⭐ |

**决定**: 我将使用 [___] 服务商

---

### ✅ 步骤2: 注册账号

**DeepSeek**:
- [ ] 访问 https://platform.deepseek.com/
- [ ] 注册账号（手机号或邮箱）
- [ ] 验证邮箱/手机

**通义千问**:
- [ ] 访问 https://dashscope.aliyuncs.com/
- [ ] 登录阿里云账号
- [ ] 开通DashScope服务

**智谱GLM**:
- [ ] 访问 https://open.bigmodel.cn/
- [ ] 注册账号
- [ ] 实名认证

**完成时间**: _____ 分钟

---

### ✅ 步骤3: 获取API密钥

**DeepSeek**:
- [ ] 进入"API Keys"页面
- [ ] 点击"Create new key"
- [ ] 复制API密钥 (格式: `sk-xxxxxxxx`)
- [ ] 安全保存（不要泄露）

**通义千问**:
- [ ] 进入"API-KEY管理"
- [ ] 创建新的API-KEY
- [ ] 复制并保存

**智谱GLM**:
- [ ] 进入"API Key"页面
- [ ] 申请API Key
- [ ] 复制并保存

**API密钥**: `sk-_____________________________________________`

**完成时间**: _____ 分钟

---

## 🔧 配置阶段 (5分钟)

### ✅ 步骤4: 安装依赖

**检查OpenAI SDK**:
```bash
python -c "import openai; print(openai.__version__)"
```

如果报错，安装SDK:
```bash
# 使用Poetry
poetry add openai

# 或使用pip
pip install openai
```

- [ ] OpenAI SDK已安装

**完成时间**: _____ 分钟

---

### ✅ 步骤5: 配置环境变量

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

应该显示你的API密钥

- [ ] 环境变量已配置
- [ ] 验证成功

**完成时间**: _____ 分钟

---

## 🧪 测试阶段 (10分钟)

### ✅ 步骤6: 运行测试脚本

```bash
cd /Users/xujian/Athena工作平台
python tests/test_cloud_llm_integration.py
```

**预期输出**:
```
🌸 Athena平台 - 云端LLM集成测试
============================================================
✅ DEEPSEEK 测试通过
通过率: 1/1 (100.0%)
🎉 所有测试通过！云端LLM已准备就绪。
```

- [ ] 测试通过
- [ ] 看到成功消息

**完成时间**: _____ 分钟

---

### ✅ 步骤7: 验证功能

**快速测试** (Python):
```python
import asyncio
from core.llm.adapters.cloud_adapter import CloudLLMAdapter

async def test():
    adapter = CloudLLMAdapter(provider="deepseek", model="chat")
    await adapter.initialize()
    result = await adapter.generate("简单介绍一下专利法")
    print(result)
    await adapter.close()

asyncio.run(test())
```

- [ ] Python测试成功
- [ ] 可以正常生成文本

**完成时间**: _____ 分钟

---

## 📊 监控阶段 (5分钟)

### ✅ 步骤8: 设置成本监控

**生成演示数据**:
```bash
python scripts/monitor_cloud_llm_cost.py --demo
```

**查看今日成本**:
```bash
python scripts/monitor_cloud_llm_cost.py --period today
```

**预期输出**:
```
💰 云端LLM成本报告 - TODAY
============================================================
📈 总体统计:
  调用次数: 100
  总Token数: 175,000
  总成本: ¥0.1750
```

- [ ] 成本监控正常工作
- [ ] 看到成本报告

**完成时间**: _____ 分钟

---

### ✅ 步骤9: 导出首份报告

```bash
python scripts/monitor_cloud_llm_cost.py --export
```

- [ ] 报告已导出到 `reports/cost_report.json`
- [ ] 可以查看详细成本数据

**完成时间**: _____ 分钟

---

## ✅ 完成确认

### 总体检查清单

**准备阶段**:
- [ ] 已选择服务商
- [ ] 已注册账号
- [ ] 已获取API密钥

**配置阶段**:
- [ ] 已安装OpenAI SDK
- [ ] 已配置环境变量
- [ ] 已验证配置

**测试阶段**:
- [ ] 测试脚本通过
- [ ] Python测试成功
- [ ] 可以正常生成文本

**监控阶段**:
- [ ] 成本监控正常
- [ ] 已导出首份报告

### 总耗时

**准备阶段**: _____ 分钟
**配置阶段**: _____ 分钟
**测试阶段**: _____ 分钟
**监控阶段**: _____ 分钟

**总计**: _____ 分钟 (目标: <30分钟)

---

## 🎉 迁移完成

### 下一步建议

**1. 设置每日成本监控**:
```bash
# 添加到crontab
0 18 * * * cd /Users/xujian/Athena工作平台 && python scripts/monitor_cloud_llm_cost.py --period today --export
```

**2. 配置告警**:
- 在服务商后台设置用量告警
- 建议阈值: ¥10/天

**3. 定期审查**:
- 每周查看成本报告
- 每月评估服务商性价比

**4. 优化策略**:
- 简单任务 → 便宜模型（智谱GLM）
- 标准任务 → 平衡模型（DeepSeek）
- 复杂任务 → 高质量模型（通义千问Max）

---

## 📞 需要帮助？

### 常见问题

**Q: 测试失败怎么办？**
A: 检查以下几点：
1. API密钥是否正确
2. 网络连接是否正常
3. OpenAI SDK是否已安装

**Q: 成本太高怎么办？**
A: 尝试以下优化：
1. 使用更便宜的模型（智谱GLM）
2. 实现响应缓存
3. 减少max_tokens参数

**Q: 想切回本地模型怎么办？**
A: 随时可以切回：
```python
from core.llm.adapters.qwen_adapter import QwenAdapter
adapter = QwenAdapter(model_id="qwen2.5-72b")
```

### 联系支持

**维护者**: 徐健 (xujian519@gmail.com)
**项目位置**: `/Users/xujian/Athena工作平台/`

---

## 📚 相关文档

- **快速启动指南**: [QUICK_START_CLOUD_LLM.md](QUICK_START_CLOUD_LLM.md)
- **成本分析**: [CLOUD_LLM_COST_ANALYSIS.md](CLOUD_LLM_COST_ANALYSIS.md)
- **迁移指南**: [MIGRATION_TO_CLOUD_LLM.md](MIGRATION_TO_CLOUD_LLM.md)
- **文档索引**: [CLOUD_LLM_README.md](CLOUD_LLM_README.md)

---

**最后更新**: 2026-04-23
**版本**: v1.0

---

**🌸 Athena平台 - 云端模型，成本更低，性能更好！**
