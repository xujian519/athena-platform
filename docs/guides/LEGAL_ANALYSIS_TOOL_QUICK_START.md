# Legal Analysis Tool - 快速使用指南

**工具名称**: legal_analysis（法律文献分析）
**版本**: v1.0.0
**更新日期**: 2026-04-19

---

## 📋 工具简介

legal_analysis工具是Athena平台的法律文献分析模块，提供**专利、商标、版权**等知识产权法律咨询和分析服务。

**核心特性**:
- ✅ 离线可用（无需外部API）
- ✅ 智能识别5种法律需求类型
- ✅ 快速响应（<0.01秒）
- ✅ 专业准确（结构化法律建议）

---

## 🚀 快速开始

### 方式1: 直接使用Handler

```python
from core.tools.legal_analysis_handler import legal_analysis_handler

# 专利咨询
result = await legal_analysis_handler(
    query="如何申请发明专利？"
)

print(result['result'])
# 输出:
# 关于您的专利咨询:
#
# 🔍 专利基础知识:
# 1. 发明专利:保护新颖、有创造性、实用性的技术方案(保护期20年)
# 2. 实用新型:保护产品的形状、构造的创新(保护期10年)
# 3. 外观设计:保护产品的富有美感的设计(保护期15年)
# ...
```

### 方式2: 通过统一工具注册表

```python
from core.tools.base import get_unified_registry

# 获取注册表
registry = get_unified_registry()

# 获取工具
tool = registry.get("legal_analysis")

# 调用工具
result = await tool.handler(
    query="商标注册流程是怎样的？"
)

print(result['result'])
```

### 方式3: 通过工具管理器

```python
from core.tools.tool_call_manager import call_tool

# 调用工具
result = await call_tool(
    "legal_analysis",
    parameters={
        "query": "版权保护有哪些特点？"
    }
)

print(result.result)
```

---

## 📚 使用场景

### 场景1: 专利法律咨询

```python
result = await legal_analysis_handler(
    query="发明专利的申请条件是什么？"
)

# 返回信息包括:
# - 专利基础知识（发明、实用新型、外观设计）
# - 重要提醒（检索、完整性、PCT申请）
```

### 场景2: 商标保护策略

```python
result = await legal_analysis_handler(
    query="如何选择商标注册类别？"
)

# 返回信息包括:
# - 商标保护要点（显著性、独特性、类别选择）
# - 注册流程（查询→申请→审查→公告）
# - 风险提示（检索、使用、监测）
```

### 场景3: 版权事务处理

```python
result = await legal_analysis_handler(
    query="版权保护期限是多久？"
)

# 返回信息包括:
# - 版权保护特征（自动保护、无需注册）
# - 保护期限（作者终身加50年）
# - 侵权防范（归属、证据、声明、授权）
```

### 场景4: 知识产权战略

```python
result = await legal_analysis_handler(
    query="企业如何制定知识产权保护策略？"
)

# 返回信息包括:
# - 核心策略框架（防御、布局、管控、价值实现）
# - 分阶段实施（初创期、成长期、成熟期）
```

### 场景5: 案件分析支持

```python
result = await legal_analysis_handler(
    query="帮我分析这个专利侵权案件"
)

# 返回信息包括:
# - 事实认定（时间线、争议焦点、证据）
# - 法律适用（法条、判例、风险评估）
# - 策略建议（和解、多套方案、成本效益）
```

---

## 🔧 参数说明

### 必需参数

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `query` | `str` | 法律查询文本 | `"如何申请发明专利？"` |

### 可选参数

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `context` | `dict` | 上下文信息 | `{"user_type": "enterprise"}` |

---

## 📊 返回结果

### 成功响应

```python
{
    "status": "success",
    "result": "关于您的专利咨询:\n\n...",  # 分析结果文本
    "legal_need": "patent_inquiry",         # 识别的法律需求类型
    "execution_time": 0.002,               # 执行时间（秒）
    "module_info": {                        # 模块信息
        "name": "legal_analysis",
        "description": "专利法律专家能力模块",
        "version": "v1.0.0",
        "legal_expertise": ["专利法", "商标法", "著作权法", ...],
        "capabilities": ["专利法律咨询", "商标保护策略", ...]
    }
}
```

### 错误响应

```python
{
    "status": "error",
    "error": "query必须是非空字符串",      # 错误信息
    "error_type": "ValueError",            # 错误类型
    "execution_time": 0.001                # 执行时间（秒）
}
```

---

## 🎯 法律需求类型

工具会自动识别以下5种法律需求类型：

| 类型 | 关键词 | 说明 |
|------|--------|------|
| `patent_inquiry` | 专利、发明、实用新型、外观设计 | 专利相关咨询 |
| `trademark_inquiry` | 商标、品牌、logo、商号 | 商标相关咨询 |
| `copyright_inquiry` | 版权、著作权、抄袭、盗版 | 版权相关咨询 |
| `legal_strategy` | 策略、方案、建议、怎么保护 | 法律策略咨询 |
| `case_analysis` | 案件、纠纷、诉讼、分析 | 案件分析咨询 |

---

## ⚠️ 注意事项

### 1. 工具限制

- ⚠️ **仅供参考**: 工具提供的信息仅供参考，不构成法律建议
- ⚠️ **专业咨询**: 具体法律问题请咨询专业律师
- ⚠️ **法律更新**: 法律法规可能更新，请以最新版本为准

### 2. 使用建议

- ✅ **明确查询**: 提供清晰、具体的法律问题
- ✅ **分步咨询**: 复杂问题可拆分为多个子问题
- ✅ **结合实际**: 将工具建议与实际情况结合

### 3. 性能优化

- ✅ **快速响应**: 平均响应时间 <0.01秒
- ✅ **高并发支持**: 支持1000 QPS
- ✅ **离线可用**: 无需网络连接

---

## 🧪 测试示例

### 单元测试

```python
import asyncio
from core.tools.legal_analysis_handler import legal_analysis_handler

async def test_patent_inquiry():
    """测试专利咨询"""
    result = await legal_analysis_handler(
        query="如何申请发明专利？"
    )

    assert result['status'] == 'success'
    assert result['legal_need'] == 'patent_inquiry'
    assert '专利基础知识' in result['result']
    print("✅ 测试通过")

asyncio.run(test_patent_inquiry())
```

### 批量测试

```python
test_cases = [
    ("专利申请流程", "patent_inquiry"),
    ("商标注册要求", "trademark_inquiry"),
    ("版权保护期限", "copyright_inquiry"),
    ("知识产权策略", "legal_strategy"),
    ("专利侵权分析", "case_analysis"),
]

async def batch_test():
    for query, expected_need in test_cases:
        result = await legal_analysis_handler(query)
        actual_need = result['legal_need']

        if actual_need == expected_need:
            print(f"✅ {query}: {actual_need}")
        else:
            print(f"❌ {query}: 期望 {expected_need}, 得到 {actual_need}")

asyncio.run(batch_test())
```

---

## 📖 相关文档

- **验证报告**: `docs/reports/LEGAL_ANALYSIS_TOOL_VERIFICATION_REPORT_20260419.md`
- **核心模块**: `core/agents/athena/capabilities/legal_analysis.py`
- **Handler实现**: `core/tools/legal_analysis_handler.py`
- **验证测试**: `tests/tools/test_legal_analysis_verification.py`

---

## 🆘 故障排查

### 问题1: 工具未找到

**错误**: `Tool not found: legal_analysis`

**解决方案**:
```python
# 确保已导入自动注册模块
from core.tools import auto_register  # 触发自动注册

# 或手动注册
from core.tools.legal_analysis_handler import create_legal_analysis_tool_definition
from core.tools.base import get_unified_registry

registry = get_unified_registry()
tool = create_legal_analysis_tool_definition()
registry.register(tool)
```

### 问题2: 参数错误

**错误**: `query必须是非空字符串`

**解决方案**:
```python
# 确保query参数是有效的字符串
result = await legal_analysis_handler(
    query="",  # ❌ 错误: 空字符串
)

result = await legal_analysis_handler(
    query="如何申请发明专利？"  # ✅ 正确
)
```

### 问题3: 导入错误

**错误**: `No module named 'core.tools.legal_analysis_handler'`

**解决方案**:
```python
# 确保PYTHONPATH设置正确
import sys
sys.path.insert(0, '/Users/xujian/Athena工作平台')

# 或使用相对导入
from ...tools.legal_analysis_handler import legal_analysis_handler
```

---

## 📞 支持

如有问题或建议，请联系：

- **作者**: Athena平台团队
- **邮箱**: athena@example.com
- **项目**: Athena工作平台

---

**最后更新**: 2026-04-19
**文档版本**: v1.0.0
