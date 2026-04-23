# PatentDraftingProxy API文档

> **⚠️ 废弃通知 (2026-04-23)**
>
> 此文档已废弃。PatentDraftingProxy和WriterAgent已合并为**UnifiedPatentWriter**。
>
> 请使用新的统一API:
> ```python
> from core.agents.xiaona.unified_patent_writer import UnifiedPatentWriter
> writer = UnifiedPatentWriter()
> ```
>
> 本文档保留用于历史参考。

---

> **版本**: v1.0.0
> **最后更新**: 2026-04-23
> **代码质量**: 90/100（优秀）
> **生产状态**: ⚠️ 已废弃，请使用UnifiedPatentWriter

---

## 📖 概述

PatentDraftingProxy是Athena平台的专利撰写智能体，提供完整的专利申请文件撰写能力。它继承自BaseXiaonaComponent，集成在xiaona模块中。

### 核心特性

- ✅ **7个核心能力** - 覆盖专利撰写全流程
- ✅ **LLM三层降级** - DeepSeek → 本地8009 → 规则引擎
- ✅ **类型安全** - Mypy 0错误，完全类型保护
- ✅ **生产就绪** - 代码质量90分，测试95%通过

---

## 🚀 快速开始

### 安装和导入

```python
from core.agents.xiaona import PatentDraftingProxy

# 创建实例
proxy = PatentDraftingProxy()

# 可选：传入配置
config = {
    "llm_model": "deepseek-chat",
    "enable_rules_fallback": True,
    "log_level": "INFO"
}
proxy = PatentDraftingProxy(config=config)
```

### 基本使用

```python
# 准备技术交底书数据
disclosure = {
    "title": "一种智能包装机",
    "technical_field": "机械制造",
    "background_art": "现有包装机存在...",
    "invention_summary": "本发明提供...",
    "technical_problem": "现有技术存在...",
    "technical_solution": "本发明通过...",
    "beneficial_effects": ["提高效率", "降低成本"],
}

# 评估可专利性
result = await proxy.assess_patentability(disclosure)
print(f"新颖性: {result['novelty']}")
print(f"创造性: {result['inventiveness']}")
print(f"实用性: {result['utility']}")
```

---

## ⚡ API能力列表

### 1. analyze_disclosure - 分析技术交底书

**功能**: 提取技术交底书中的关键信息

**输入参数**:
```python
{
    "content": str,              # 文档内容（可选）
    "file_path": str,            # 文件路径（可选）
    "title": str,                # 发明名称（可选）
    "technical_field": str,      # 技术领域（可选）
    "background_art": str,       # 背景技术（可选）
    "invention_summary": str,    # 发明概述（可选）
    "technical_problem": str,    # 技术问题（可选）
    "technical_solution": str,   # 技术方案（可选）
    "beneficial_effects": list,  # 有益效果（可选）
}
```

**返回结果**:
```python
{
    "发明名称": str,
    "技术领域": {
        "技术领域": str,
        "IPC分类": list[str],
        "关键词": list[str]
    },
    "背景技术": {...},
    "发明内容": {...},
    "具体实施方式": {...},
    "权利要求": {...},
    "extracted_at": str
}
```

**使用示例**:
```python
result = await proxy.analyze_disclosure(disclosure)
print(f"发明名称: {result['发明名称']}")
print(f"技术领域: {result['技术领域']['技术领域']}")
print(f"IPC分类: {result['技术领域']['IPC分类']}")
```

**预计耗时**: 10秒

---

### 2. assess_patentability - 评估可专利性

**功能**: 评估专利的新颖性、创造性和实用性

**输入参数**:
```python
{
    # 与analyze_disclosure相同的输入格式
}
```

**返回结果**:
```python
{
    "novelty": str,              # 新颖性评估
    "inventiveness": str,         # 创造性评估
    "utility": str,               # 实用性评估
    "overall_assessment": str,    # 综合评估
    "recommendations": list[str], # 建议
    "assessed_at": str            # 评估时间
}
```

**使用示例**:
```python
result = await proxy.assess_patentability(disclosure)

if result['overall_assessment'] == '具有可专利性':
    print("✅ 该发明具有可专利性")
    print(f"新颖性: {result['novelty']}")
    print(f"创造性: {result['inventiveness']}")
    print(f"实用性: {result['utility']}")
else:
    print("⚠️ 需要进一步改进")
    print("建议:", result['recommendations'])
```

**预计耗时**: 15秒

---

### 3. draft_specification - 撰写说明书

**功能**: 生成完整的专利说明书

**输入参数**:
```python
{
    # 技术交底书数据
}
```

**返回结果**:
```python
{
    "技术领域": str,
    "背景技术": str,
    "发明内容": str,
    "具体实施方式": str,
    "附图说明": str,  # 如果提供附图
    "specification_parts": {
        "title": str,
        "technical_field": str,
        "background": str,
        "summary": str,
        "detailed_description": str,
        "drawings": str
    },
    "drafted_at": str
}
```

**使用示例**:
```python
result = await proxy.draft_specification(disclosure)

# 获取完整说明书
full_specification = (
    f"技术领域：\n{result['技术领域']}\n\n"
    f"背景技术：\n{result['背景技术']}\n\n"
    f"发明内容：\n{result['发明内容']}\n\n"
    f"具体实施方式：\n{result['具体实施方式']}"
)

# 保存到文件
with open('specification.txt', 'w', encoding='utf-8') as f:
    f.write(full_specification)
```

**预计耗时**: 25秒

---

### 4. draft_claims - 撰写权利要求书

**功能**: 生成独立权利要求和从属权利要求

**输入参数**:
```python
{
    # 技术交底书数据
    "specification": str,  # 可选：已撰写的说明书
}
```

**返回结果**:
```python
{
    "independent_claims": list[str],  # 独立权利要求
    "dependent_claims": list[str],    # 从属权利要求
    "claims_count": int,               # 权利要求数量
    "drafted_at": str
}
```

**使用示例**:
```python
result = await proxy.draft_claims(disclosure)

print(f"独立权利要求数量: {len(result['independent_claims'])}")
print(f"从属权利要求数量: {len(result['dependent_claims'])}")

# 获取第一条独立权利要求
print("\n权利要求1:")
print(result['independent_claims'][0])

# 组合所有权利要求
all_claims = result['independent_claims'] + result['dependent_claims']
claims_text = "\n\n".join([f"{i+1}. {claim}" for i, claim in enumerate(all_claims)])
```

**预计耗时**: 20秒

---

### 5. optimize_protection_scope - 优化保护范围

**功能**: 分析和优化权利要求的保护范围

**输入参数**:
```python
{
    "specification": str,
    "claims": str,
    "prior_art": str  # 可选：现有技术
}
```

**返回结果**:
```python
{
    "current_scope": str,           # 当前保护范围评估
    "optimization_suggestions": [   # 优化建议
        {
            "claim_number": int,
            "issue": str,
            "suggestion": str,
            "priority": str  # high/medium/low
        }
    ],
    "risk_assessment": {
        "too_broad": bool,
        "too_narrow": bool,
        "clarity_issues": list[str]
    },
    "optimized_at": str
}
```

**使用示例**:
```python
result = await proxy.optimize_protection_scope({
    "specification": specification,
    "claims": claims
})

print("保护范围评估:", result['current_scope'])

for suggestion in result['optimization_suggestions']:
    if suggestion['priority'] == 'high':
        print(f"⚠️  权利要求{suggestion['claim_number']}: {suggestion['suggestion']}")

print("\n风险评估:")
print(f"过宽风险: {result['risk_assessment']['too_broad']}")
print(f"过窄风险: {result['risk_assessment']['too_narrow']}")
```

**预计耗时**: 20秒

---

### 6. review_adequacy - 审查充分公开

**功能**: 检查说明书是否充分公开技术方案

**输入参数**:
```python
{
    "specification": str,
    "claims": str
}
```

**返回结果**:
```python
{
    "adequacy_score": float,        # 充分性评分（0-1）
    "completeness": {
        "technical_problem": bool,   # 技术问题是否清楚
        "technical_solution": bool,   # 技术方案是否完整
        "beneficial_effects": bool,   # 有益效果是否说明
        "examples": bool,             # 实施例是否充分
        "parameters": bool            # 参数是否公开
    },
    "issues": list[str],             # 发现的问题
    "recommendations": list[str],    # 改进建议
    "reviewed_at": str
}
```

**使用示例**:
```python
result = await proxy.review_adequacy({
    "specification": specification,
    "claims": claims
})

print(f"充分性评分: {result['adequacy_score']:.2f}")

print("\n完整性检查:")
for key, value in result['completeness'].items():
    status = "✅" if value else "❌"
    print(f"{status} {key}")

if result['issues']:
    print("\n发现的问题:")
    for issue in result['issues']:
        print(f"• {issue}")

if result['recommendations']:
    print("\n改进建议:")
    for rec in result['recommendations']:
        print(f"• {rec}")
```

**预计耗时**: 15秒

---

### 7. detect_common_errors - 检测常见错误

**功能**: 检测专利申请文件中的常见错误

**输入参数**:
```python
{
    "specification": str,
    "claims": str
}
```

**返回结果**:
```python
{
    "language_errors": [           # 语言错误
        {
            "type": str,            # 错误类型
            "location": str,         # 位置
            "issue": str,            # 问题描述
            "suggestion": str        # 修改建议
        }
    ],
    "logic_errors": [              # 逻辑错误
        {
            "type": str,
            "location": str,
            "issue": str,
            "suggestion": str
        }
    ],
    "format_errors": [             # 格式错误
        {
            "type": str,
            "location": str,
            "issue": str,
            "suggestion": str
        }
    ],
    "error_count": int,
    "detected_at": str
}
```

**使用示例**:
```python
result = await proxy.detect_common_errors({
    "specification": specification,
    "claims": claims
})

print(f"发现错误总数: {result['error_count']}")

if result['language_errors']:
    print("\n语言错误:")
    for error in result['language_errors']:
        print(f"• {error['location']}: {error['issue']}")
        print(f"  建议: {error['suggestion']}")

if result['logic_errors']:
    print("\n逻辑错误:")
    for error in result['logic_errors']:
        print(f"• {error['location']}: {error['issue']}")

if result['format_errors']:
    print("\n格式错误:")
    for error in result['format_errors']:
        print(f"• {error['location']}: {error['issue']}")
```

**预计耗时**: 10秒

---

## 🔄 完整工作流示例

### 专利撰写完整流程

```python
from core.agents.xiaona import PatentDraftingProxy
import asyncio

async def draft_patent_application(disclosure_data):
    """完整的专利撰写流程"""
    
    # 1. 创建代理实例
    proxy = PatentDraftingProxy()
    
    # 2. 分析技术交底书
    print("📄 分析技术交底书...")
    analysis = await proxy.analyze_disclosure(disclosure_data)
    print(f"✅ 发明名称: {analysis['发明名称']}")
    
    # 3. 评估可专利性
    print("\n🔍 评估可专利性...")
    patentability = await proxy.assess_patentability(disclosure_data)
    print(f"✅ 综合评估: {patentability['overall_assessment']}")
    
    # 如果可专利性不足，返回建议
    if patentability['overall_assessment'] != '具有可专利性':
        print("⚠️ 建议:", patentability['recommendations'])
        return None
    
    # 4. 撰写说明书
    print("\n📝 撰写说明书...")
    specification = await proxy.draft_specification(disclosure_data)
    full_spec = specification['技术领域'] + "\n\n" + \
                specification['背景技术'] + "\n\n" + \
                specification['发明内容'] + "\n\n" + \
                specification['具体实施方式']
    print("✅ 说明书撰写完成")
    
    # 5. 撰写权利要求书
    print("\n⚖️  撰写权利要求书...")
    claims_result = await proxy.draft_claims(disclosure_data)
    all_claims = claims_result['independent_claims'] + \
                  claims_result['dependent_claims']
    claims_text = "\n\n".join([f"{i+1}. {claim}" for i, claim in enumerate(all_claims)])
    print(f"✅ 权利要求书撰写完成（{len(all_claims)}条）")
    
    # 6. 优化保护范围
    print("\n🎯 优化保护范围...")
    optimization = await proxy.optimize_protection_scope({
        "specification": full_spec,
        "claims": claims_text
    })
    print(f"✅ 保护范围: {optimization['current_scope']}")
    
    # 7. 审查充分公开
    print("\n🔍 审查充分公开...")
    adequacy = await proxy.review_adequacy({
        "specification": full_spec,
        "claims": claims_text
    })
    print(f"✅ 充分性评分: {adequacy['adequacy_score']:.2f}")
    
    # 8. 检测常见错误
    print("\n🐛 检测常见错误...")
    errors = await proxy.detect_common_errors({
        "specification": full_spec,
        "claims": claims_text
    })
    print(f"✅ 发现错误: {errors['error_count']}个")
    
    # 返回完整申请文件
    return {
        "specification": full_spec,
        "claims": claims_text,
        "analysis": analysis,
        "patentability": patentability,
        "optimization": optimization,
        "adequacy": adequacy,
        "errors": errors
    }

# 使用示例
disclosure = {
    "title": "一种智能包装机",
    "technical_field": "机械制造",
    "background_art": "现有包装机存在...",
    "invention_summary": "本发明提供...",
    "technical_problem": "现有技术存在...",
    "technical_solution": "本发明通过...",
    "beneficial_effects": ["提高效率", "降低成本"],
}

# 执行完整流程
result = asyncio.run(draft_patent_application(disclosure))

if result:
    print("\n🎉 专利申请文件撰写完成！")
    
    # 保存到文件
    with open('patent_application.txt', 'w', encoding='utf-8') as f:
        f.write(f"说明书：\n\n{result['specification']}\n\n")
        f.write(f"权利要求书：\n\n{result['claims']}")
    print("✅ 已保存到 patent_application.txt")
```

---

## ⚙️ 配置选项

### 初始化配置

```python
config = {
    # LLM配置
    "llm_model": "deepseek-chat",           # 首选LLM模型
    "enable_rules_fallback": True,         # 启用规则引擎降级
    "local_llm_url": "http://localhost:8009",  # 本地LLM地址
    
    # 日志配置
    "log_level": "INFO",                     # 日志级别
    "enable_detailed_logging": False,        # 详细日志
    
    # 性能配置
    "timeout": 30,                           # 超时时间（秒）
    "max_retries": 3,                        # 最大重试次数
    
    # 输出配置
    "output_format": "detailed",             # 输出格式: simple/detailed
    "include_confidence": True,              # 包含置信度
}

proxy = PatentDraftingProxy(config=config)
```

---

## 🔧 错误处理

### 异常类型

```python
try:
    result = await proxy.assess_patentability(disclosure)
except ValueError as e:
    # 输入数据验证失败
    print(f"输入错误: {e}")
except RuntimeError as e:
    # LLM调用失败
    print(f"运行时错误: {e}")
except Exception as e:
    # 其他错误
    print(f"未知错误: {e}")
```

### LLM降级机制

PatentDraftingProxy使用三层降级机制：

1. **DeepSeek云端模型**（首选）
   - 高质量输出
   - 需要API密钥

2. **本地8009端口模型**（备选）
   - 无需API密钥
   - 自动降级

3. **规则引擎**（兜底）
   - 保证始终有输出
   - 质量相对较低

---

## 📊 性能指标

### 响应时间

| 能力 | 预计耗时 | 说明 |
|-----|---------|------|
| analyze_disclosure | ~10秒 | 取决于文档长度 |
| assess_patentability | ~15秒 | LLM推理时间 |
| draft_specification | ~25秒 | 生成内容较长 |
| draft_claims | ~20秒 | 生成多条权利要求 |
| optimize_protection_scope | ~20秒 | 分析和优化 |
| review_adequacy | ~15秒 | 多项检查 |
| detect_common_errors | ~10秒 | 规则检查为主 |

### 资源消耗

- **内存**: ~200MB（包含LLM加载）
- **CPU**: 中等（LLM推理时）
- **网络**: 取决于LLM选择（云端/本地）

---

## 🧪 测试

### 运行测试

```bash
# 单元测试
poetry run pytest tests/agents/xiaona/test_patent_drafting_proxy.py -v

# 部署验证
poetry run python test_patent_drafting_deployment.py
```

### 测试覆盖率

- **单元测试**: 95% (38/40通过)
- **集成测试**: 通过
- **部署验证**: 100% (5/5通过)

---

## 📚 相关文档

- **部署报告**: `docs/reports/PATENT_DRAFTING_DEPLOYMENT_SUCCESS_20260423.md`
- **Mypy修复**: `docs/reports/PATENT_DRAFTING_MYPY_TYPE_FIX_COMPLETE_20260423.md`
- **集成分析**: `docs/reports/PATENT_DRAFTING_INTEGRATION_ANALYSIS_20260423.md`
- **代码质量**: `docs/reports/PATENT_DRAFTING_CODE_QUALITY_FIX_COMPLETE_20260423.md`

---

## 🆘 故障排除

### 常见问题

**Q: LLM调用失败怎么办？**

A: PatentDraftingProxy会自动降级到本地模型或规则引擎，保证始终有输出。

**Q: 如何提高输出质量？**

A: 
1. 提供详细的技术交底书
2. 配置DeepSeek API密钥
3. 使用"enable_rules_fallback=False"强制使用LLM

**Q: 处理时间过长？**

A: 
1. 检查输入文档长度
2. 调整timeout参数
3. 使用本地模型而非云端API

---

## 📞 支持

如有问题或建议，请：
- 查看文档：`docs/reports/`
- 运行测试：`test_patent_drafting_deployment.py`
- 提交Issue到项目仓库

---

**文档版本**: v1.0.0  
**最后更新**: 2026-04-23  
**维护者**: Athena平台团队
