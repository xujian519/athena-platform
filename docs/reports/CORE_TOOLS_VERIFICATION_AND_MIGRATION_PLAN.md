# 核心工具验证和迁移计划

> 生成日期: 2026-04-19
> 目的: 在迁移前验证核心工具的完整可用性

---

## 一、工具清单

### 1.1 已迁移工具（4个）

| 工具名称 | 文件位置 | 优先级 | 状态 | 验证 |
|---------|---------|--------|------|------|
| local_web_search | core/tools/real_tool_implementations.py | P0 | ✅ 已迁移 | ✅ 已验证 |
| enhanced_document_parser | core/tools/enhanced_document_parser.py | P0 | ✅ 已迁移 | ✅ 已验证 |
| patent_search | core/tools/patent_retrieval.py | P0 | ✅ 已迁移 | ✅ 已验证 |
| patent_download | core/tools/patent_download.py | P0 | ✅ 已迁移 | ✅ 已验证 |

### 1.2 待迁移工具（9个）

| 工具名称 | 文件位置 | 优先级 | 文件存在 | 可导入 | 有Handler |
|---------|---------|--------|----------|--------|----------|
| **vector_search** | core/vector/intelligent_vector_manager.py | **P0** | ✅ | ✅ | ❌ |
| academic_search | core/search/tools/google_scholar_tool.py | P1 | ✅ | ❌ | ❌ |
| legal_analysis | core/legal/legal_vector_retrieval_service.py | P1 | ✅ | ❌ | ❌ |
| semantic_analysis | core/nlp/semantic_analyzer.py | P1 | ❌ | ❌ | ❌ |
| patent_analysis | core/patent/patent_analyzer.py | P1 | ❌ | ❌ | ❌ |
| knowledge_graph_search | core/knowledge_graph/graph_manager.py | P2 | ❌ | ❌ | ❌ |
| browser_automation | core/tools/browser_automation_tool.py | P2 | ✅ | ✅ | ❌ |
| cache_management | core/cache/unified_cache.py | P1 | ✅ | ✅ | ❌ |
| data_transformation | core/data/transformation.py | P2 | ❌ | ❌ | ❌ |

---

## 二、P0工具详细分析

### 2.1 vector_search（向量语义搜索）

**功能描述**:
> 基于BGE-M3嵌入模型的向量语义搜索系统，支持法律和专利知识图谱的向量存储、检索和优化。

**核心功能**:
1. **向量存储**: 使用Qdrant向量数据库存储嵌入向量
2. **语义检索**: 基于余弦相似度的语义搜索
3. **多集合管理**: 支持多个向量集合（法律、专利等）
4. **性能优化**: 查询缓存、批量处理、性能统计
5. **混合检索**: 结合关键词和向量检索

**技术栈**:
- 向量数据库: Qdrant (localhost:6333)
- 嵌入模型: BGE-M3 (768维)
- 缓存: 内存缓存（1000条限制）
- 配置: JSON配置文件

**文件位置**: `core/vector/intelligent_vector_manager.py`

**主要类**: `IntelligentVectorManager`

**关键方法**:
- `__init__()`: 初始化向量管理器
- `search_vector()`: 向量搜索
- `search_hybrid()`: 混合搜索
- `add_documents()`: 添加文档
- `optimize_collection()`: 优化集合

**依赖项**:
```python
qdrant-client
sentence-transformers
numpy
```

**验证测试**:

```python
# 测试1: 检查依赖
try:
    from qdrant_client import QdrantClient
    from sentence_transformers import SentenceTransformer
    print("✅ 依赖项已安装")
except ImportError as e:
    print(f"❌ 依赖项缺失: {e}")

# 测试2: 检查Qdrant服务
import requests
try:
    response = requests.get("http://localhost:6333/collections")
    if response.status_code == 200:
        print("✅ Qdrant服务运行中")
    else:
        print("❌ Qdrant服务未运行")
except Exception as e:
    print(f"❌ Qdrant连接失败: {e}")

# 测试3: 加载嵌入模型
try:
    model = SentenceTransformer('BAAI/bge-m3')
    print(f"✅ BGE-M3模型加载成功 (维度: {model.get_sentence_embedding_dimension()})")
except Exception as e:
    print(f"❌ 模型加载失败: {e}")
```

**迁移建议**:

1. **创建Handler包装器**:
```python
@tool(
    name="vector_search",
    category="vector_search",
    description="向量语义搜索（基于BGE-M3模型）",
    priority="high",
    tags=["search", "vector", "semantic", "bge-m3"]
)
async def vector_search_handler(
    query: str,
    collection: str = "legal_main",
    top_k: int = 10,
    threshold: float = 0.7
) -> dict:
    """向量语义搜索Handler"""
    from core.vector.intelligent_vector_manager import IntelligentVectorManager
    
    manager = IntelligentVectorManager()
    results = await manager.search_vector(
        query=query,
        collection_name=collection,
        limit=top_k,
        score_threshold=threshold
    )
    
    return {
        "success": True,
        "query": query,
        "collection": collection,
        "total_results": len(results),
        "results": results
    }
```

2. **迁移步骤**:
   - 步骤1: 创建Handler包装器
   - 步骤2: 添加@tool装饰器
   - 步骤3: 测试验证
   - 步骤4: 更新调用方

3. **预计时间**: 2小时

**风险评估**:
- 🟡 **中等风险**: 依赖外部服务（Qdrant）
- 🟡 **中等风险**: 需要加载大型嵌入模型
- 🟢 **低风险**: 代码结构清晰，易于迁移

---

## 三、P1工具详细分析

### 3.1 academic_search（学术文献搜索）

**功能描述**:
> Google Scholar学术文献搜索工具，支持论文检索、引用分析、作者信息查询。

**文件位置**: `core/search/tools/google_scholar_tool.py`

**状态**: ❌ 不可导入（相对导入问题）

**问题分析**:
```python
# 错误: attempted relative import with no known parent package
# 原因: 模块使用了相对导入，但无法作为独立模块运行
```

**迁移建议**:
1. 修复导入问题
2. 创建Handler包装器
3. 测试验证

**预计时间**: 1.5小时

---

### 3.2 legal_analysis（法律文献分析）

**功能描述**:
> 法律文献向量检索和分析工具，支持法律条文、案例、法规的语义搜索。

**文件位置**: `core/legal/legal_vector_retrieval_service.py`

**状态**: ❌ 不可导入（NoneType错误）

**问题分析**:
```python
# 错误: 'NoneType' object has no attribute '__dict__'
# 原因: 可能是初始化时某个依赖为None
```

**迁移建议**:
1. 调试并修复初始化问题
2. 创建Handler包装器
3. 测试验证

**预计时间**: 2小时

---

### 3.3 semantic_analysis（语义分析）

**功能描述**:
> 文本语义分析和理解工具，支持语义相似度、情感分析、实体识别等。

**文件位置**: `core/nlp/semantic_analyzer.py`

**状态**: ❌ 文件不存在

**问题分析**:
该文件不存在，可能：
- 功能已集成到其他模块
- 需要重新创建
- 使用其他工具替代

**迁移建议**:
1. 确认该功能是否需要
2. 查找替代实现
3. 或创建新的语义分析工具

**预计时间**: 3小时（如需创建）

---

### 3.4 patent_analysis（专利分析）

**功能描述**:
> 专利内容分析和创造性评估工具，支持专利文本分析、权利要求分析、创造性评估。

**文件位置**: `core/patent/patent_analyzer.py`

**状态**: ❌ 文件不存在

**问题分析**:
该文件不存在，可能功能在其他模块中。

**迁移建议**:
1. 查找专利分析的实际实现位置
2. 确认是否需要迁移
3. 创建Handler包装器

**预计时间**: 2小时

---

### 3.5 cache_management（缓存管理）

**功能描述**:
> 统一缓存管理系统，支持多层缓存、缓存策略、性能监控。

**文件位置**: `core/cache/unified_cache.py`

**状态**: ✅ 文件存在，✅ 可导入，❌ 无Handler

**迁移建议**:
1. 创建Handler包装器
2. 添加@tool装饰器
3. 测试验证

**预计时间**: 1小时

---

## 四、P2工具分析

### 4.1 browser_automation（浏览器自动化）

**功能描述**:
> 基于Playwright的浏览器自动化工具，支持网页操作、数据抓取、截图等。

**文件位置**: `core/tools/browser_automation_tool.py`

**状态**: ✅ 文件存在，✅ 可导入，❌ 无Handler

**迁移建议**:
1. 创建Handler包装器
2. 添加@tool装饰器
3. 测试验证

**预计时间**: 1.5小时

---

### 4.2 knowledge_graph_search（知识图谱搜索）

**功能描述**:
> 知识图谱搜索和推理工具，支持图谱遍历、关系查询、智能推理。

**文件位置**: `core/knowledge_graph/graph_manager.py`

**状态**: ❌ 文件不存在

**问题分析**:
该文件不存在，需要查找实际实现。

**迁移建议**:
1. 查找知识图谱的实际实现位置
2. 确认是否需要迁移
3. 创建Handler包装器

**预计时间**: 2小时

---

### 4.3 data_transformation（数据转换）

**功能描述**:
> 数据转换和格式化工具，支持数据清洗、格式转换、类型转换。

**文件位置**: `core/data/transformation.py`

**状态**: ❌ 文件不存在

**迁移建议**:
1. 确认该功能是否需要
2. 查找替代实现
3. 或创建新的数据转换工具

**预计时间**: 2小时（如需创建）

---

## 五、迁移优先级和时间估算

### 5.1 迁移顺序

| 优先级 | 工具名称 | 预计时间 | 累计时间 |
|--------|---------|---------|---------|
| P0 | vector_search | 2小时 | 2小时 |
| P1 | cache_management | 1小时 | 3小时 |
| P1 | academic_search | 1.5小时 | 4.5小时 |
| P1 | legal_analysis | 2小时 | 6.5小时 |
| P2 | browser_automation | 1.5小时 | 8小时 |
| P1 | patent_analysis | 2小时 | 10小时 |
| P2 | knowledge_graph_search | 2小时 | 12小时 |
| P2 | data_transformation | 2小时 | 14小时 |
| P1 | semantic_analysis | 3小时 | 17小时 |

**总计**: 约17小时（2-3个工作日）

### 5.2 迁移计划

**第1天**:
- vector_search（P0）- 2小时
- cache_management（P1）- 1小时
- academic_search（P1）- 1.5小时
- legal_analysis（P1）- 2小时

**第2天**:
- browser_automation（P2）- 1.5小时
- patent_analysis（P1）- 2小时
- knowledge_graph_search（P2）- 2小时

**第3天**:
- data_transformation（P2）- 2小时
- semantic_analysis（P1）- 3小时
- 测试和验证 - 2小时

---

## 六、验证测试模板

### 6.1 功能验证模板

```python
#!/usr/bin/env python3
"""
工具验证测试模板
"""

async def verify_tool(tool_name: str, handler_func):
    """验证工具功能"""
    
    print(f"验证工具: {tool_name}")
    
    # 1. 检查工具已注册
    from core.tools.unified_registry import get_unified_registry
    registry = get_unified_registry()
    
    tool = registry.get(tool_name)
    if not tool:
        print(f"❌ 工具未注册")
        return False
    
    print(f"✅ 工具已注册")
    
    # 2. 检查工具元数据
    assert tool.name == tool_name
    assert tool.category
    assert tool.description
    print(f"✅ 元数据完整")
    
    # 3. 测试工具功能
    try:
        # 基础参数测试
        test_params = get_test_params(tool_name)
        result = await tool.function(**test_params)
        
        assert result is not None
        assert "success" in result
        print(f"✅ 功能测试通过")
        
    except Exception as e:
        print(f"❌ 功能测试失败: {e}")
        return False
    
    # 4. 检查错误处理
    try:
        error_params = get_error_params(tool_name)
        result = await tool.function(**error_params)
        
        assert result["success"] is False
        print(f"✅ 错误处理正确")
        
    except Exception as e:
        print(f"❌ 错误处理失败: {e}")
        return False
    
    print(f"✅ 所有验证通过\n")
    return True


def get_test_params(tool_name: str) -> dict:
    """获取测试参数"""
    params = {
        "vector_search": {
            "query": "测试查询",
            "collection": "legal_main",
            "top_k": 5
        },
        "cache_management": {
            "action": "get_stats"
        },
        # ... 其他工具的测试参数
    }
    return params.get(tool_name, {})


def get_error_params(tool_name: str) -> dict:
    """获取错误测试参数"""
    params = {
        "vector_search": {
            "query": "",  # 空查询
            "collection": "invalid_collection"
        },
        # ... 其他工具的错误参数
    }
    return params.get(tool_name, {})
```

---

## 七、下一步行动

### 7.1 立即行动（今天）

1. **验证vector_search工具**
   - 运行依赖检查
   - 测试Qdrant连接
   - 测试嵌入模型加载
   - 创建Handler包装器

2. **创建验证测试脚本**
   - 提供统一的验证模板
   - 自动化测试流程

### 7.2 短期计划（本周）

1. **完成P0工具迁移**
   - vector_search
   - 验证和测试

2. **完成P1工具迁移**
   - cache_management
   - academic_search
   - legal_analysis

3. **测试和文档**
   - 单元测试
   - 集成测试
   - 更新文档

### 7.3 中期计划（下周）

1. **完成P2工具迁移**
   - browser_automation
   - patent_analysis
   - knowledge_graph_search
   - data_transformation
   - semantic_analysis

2. **持续优化**
   - 性能调优
   - 功能增强
   - 文档完善

---

**维护者**: 徐健 (xujian519@gmail.com)
**创建者**: Claude Code (Sonnet 4.6)
**最后更新**: 2026-04-19 22:00

---

## 总结

✅ **已完成核心工具识别和分析**
✅ **13个核心工具已分类（4个已迁移，9个待迁移）**
✅ **制定了详细的迁移计划和时间估算**

**下一步**: 从vector_search开始，逐个验证和迁移核心工具。
