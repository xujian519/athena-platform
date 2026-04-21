# 智能体工具配置方案（基于实际能力）

> **版本**: 1.0 (Revised)
> **创建日期**: 2026-04-21
> **状态**: 基于平台实际能力的配置

---

## 📋 重要说明

本文档基于Athena平台**实际已实现的能力**，为每个智能体配置工具和技能。

### 实际约束

1. **专利检索**：目前只支持
   - ✅ 本地PostgreSQL的patent_db数据库检索
   - ✅ Google Patents在线检索
   - ❌ CNIPA、EPO、WIPO等暂未实现

2. **专利下载**：
   - ✅ Google Patents PDF下载

3. **技术分析**：
   - ✅ 要素提取（feature extraction）
   - ✅ 双图（附图）分析
   - ✅ 技术特征提取
   - ✅ 专利内容分析

---

## 1. 检索者（RetrieverAgent）

### 实际可用工具

| 工具名称 | 工具类型 | 文件位置 | 功能描述 | 状态 |
|---------|---------|---------|---------|------|
| `patent_retrieval` | 内置工具 | `core/tools/patent_retrieval.py` | 统一专利检索（本地PostgreSQL + Google Patents） | ✅ 已实现 |
| `patent_download` | 内置工具 | `core/tools/patent_download.py` | Google Patents PDF下载 | ✅ 已实现 |
| `patent_parse` | 内置工具 | `core/tools/` | 专利文本解析 | ✅ 已实现 |

### 检索渠道说明

```python
from core.tools.patent_retrieval import PatentRetrievalChannel

# 支持的检索渠道
CHANNELS = {
    "local_postgres": {
        "description": "本地PostgreSQL patent_db数据库",
        "database": "patent_db",
        "features": [
            "快速检索（已缓存）",
            "结构化数据",
            "支持复杂查询"
        ]
    },
    
    "google_patents": {
        "description": "Google Patents在线检索",
        "url": "https://patents.google.com",
        "features": [
            "全球专利检索",
            "实时数据",
            "PDF下载支持"
        ]
    }
}
```

### 工具配置（修正版）

```python
RETRIEVER_AGENT_TOOLS = {
    "agent_type": "retriever",
    "version": "1.0-revised",
    
    # 核心工具（必须可用）
    "required_tools": [
        {
            "name": "patent_retrieval",
            "class": "UnifiedPatentRetriever",
            "module": "core.tools.patent_retrieval",
            "channels": ["local_postgres", "google_patents"],
            "permission": "auto",
            "health_check": True,
            "timeout": 30.0,
            "description": "统一专利检索（本地PostgreSQL + Google Patents）"
        },
        {
            "name": "patent_download",
            "class": "UnifiedPatentDownloader",
            "module": "core.tools.patent_download",
            "permission": "auto",
            "health_check": True,
            "timeout": 60.0,
            "description": "Google Patents PDF下载"
        },
        {
            "name": "patent_parse",
            "class": "PatentParser",
            "module": "core.tools",
            "permission": "auto",
            "health_check": True,
            "timeout": 10.0,
            "description": "专利文本解析"
        }
    ],
    
    # 工具组（支持并行调用）
    "tool_groups": {
        "dual_channel_search": {
            "name": "双渠道检索",
            "tools": ["patent_retrieval:local_postgres", "patent_retrieval:google_patents"],
            "execution_mode": "parallel",  # 并行执行
            "merge_strategy": "union",  # 合并结果
            "deduplication": True,  # 去重
            "timeout": 30.0,
            "description": "同时检索本地和Google，合并去重"
        },
        
        "download_and_parse": {
            "name": "下载和解析",
            "tools": ["patent_download", "patent_parse"],
            "execution_mode": "sequential",  # 串行执行
            "timeout": 70.0,
            "description": "先下载专利，再解析内容"
        }
    },
    
    # 检索策略
    "search_strategies": {
        "default": {
            "channels": ["local_postgres", "google_patents"],
            "priority": "local_first",  # 优先使用本地
            "fallback": true,  # 本地失败时使用Google
            "description": "默认策略：本地优先，Google兜底"
        },
        
        "comprehensive": {
            "channels": ["local_postgres", "google_patents"],
            "priority": "parallel",  # 并行检索
            "fallback": false,
            "description": "全面检索：双渠道并行"
        },
        
        "realtime": {
            "channels": ["google_patents"],
            "priority": "google_only",
            "fallback": false,
            "description": "实时检索：仅使用Google Patents"
        }
    }
}
```

### 使用示例

```python
# 示例1：双渠道并行检索
results = await agent.call_tool_group(
    group_name="dual_channel_search",
    params={
        "query": "自动驾驶 激光雷达",
        "limit": 10
    }
)

# 示例2：下载并解析专利
download_result = await agent.call_tool(
    tool_name="patent_download",
    params={"patent_number": "US12345678B2"}
)

if download_result.success:
    parse_result = await agent.call_tool(
        tool_name="patent_parse",
        params={
            "file_path": download_result.file_path,
            "parse_claims": True,
            "parse_description": True
        }
    )
```

---

## 2. 分析者（AnalyzerAgent）

### 实际可用工具和技能

| 工具/技能名称 | 类型 | 位置 | 功能描述 | 状态 |
|-------------|------|------|---------|------|
| `patent_analysis` | 内置工具 | `core/tools/patent_analysis_handler.py` | 专利内容分析 | ✅ 已实现 |
| `feature_extraction` | 内置工具 | `core/patent/` | 要素提取 | ✅ 已实现 |
| `drawing_analysis` | 内置工具 | `core/patent/drawing/` | 双图（附图）分析 | ✅ 已实现 |
| `vector_search` | 内置工具 | `core/tools/vector_search_handler.py` | 向量检索（相似专利） | ✅ 已实现 |
| `patent_similarity` | 内置工具 | `core/tools/patent_similarity.py` | 专利相似度分析 | ✅ 已实现 |
| `patent_translator` | 内置工具 | `core/tools/patent_translator.py` | 专利翻译（中英互译） | ✅ 已实现 |

### 工具配置（修正版）

```python
ANALYZER_AGENT_TOOLS = {
    "agent_type": "analyzer",
    "version": "1.0-revised",
    
    # 核心工具（必须可用）
    "required_tools": [
        {
            "name": "patent_analysis",
            "class": "patent_analysis_handler",
            "module": "core.tools.patent_analysis_handler",
            "permission": "auto",
            "health_check": True,
            "timeout": 30.0,
            "capabilities": [
                "basic_analysis",  # 基础分析（技术特征提取）
                "creativity_analysis",  # 创造性评估
                "novelty_analysis",  # 新颖性判断
                "comprehensive_analysis"  # 综合分析
            ],
            "description": "专利内容分析（技术特征提取、创造性评估、新颖性判断）"
        },
        {
            "name": "feature_extraction",
            "class": "FeatureExtractor",
            "module": "core.patent",
            "permission": "auto",
            "health_check": True,
            "timeout": 20.0,
            "description": "要素提取（技术特征、权利要求要素）"
        },
        {
            "name": "drawing_analysis",
            "class": "DrawingAnalyzer",
            "module": "core.patent.drawing",
            "permission": "auto",
            "health_check": True,
            "timeout": 15.0,
            "description": "双图（附图）分析"
        }
    ],
    
    # 辅助工具（可选）
    "optional_tools": [
        {
            "name": "vector_search",
            "class": "VectorSearchHandler",
            "module": "core.tools.vector_search_handler",
            "permission": "auto",
            "health_check": True,
            "timeout": 10.0,
            "description": "向量检索（相似专利）"
        },
        {
            "name": "patent_similarity",
            "class": "PatentSimilarity",
            "module": "core.tools.patent_similarity",
            "permission": "auto",
            "health_check": True,
            "timeout": 15.0,
            "description": "专利相似度分析"
        },
        {
            "name": "patent_translator",
            "class": "PatentTranslator",
            "module": "core.tools.patent_translator",
            "permission": "auto",
            "health_check": True,
            "timeout": 10.0,
            "description": "专利翻译（中英互译）"
        }
    ],
    
    # 工具组（支持并行调用）
    "tool_groups": {
        "technical_analysis": {
            "name": "技术分析",
            "tools": ["feature_extraction", "drawing_analysis"],
            "execution_mode": "parallel",  # 并行执行
            "timeout": 20.0,
            "description": "要素提取 + 双图分析"
        },
        
        "similarity_search": {
            "name": "相似度检索",
            "tools": ["vector_search", "patent_similarity"],
            "execution_mode": "parallel",  # 并行执行
            "timeout": 15.0,
            "description": "向量检索 + 相似度分析"
        },
        
        "comprehensive_analysis": {
            "name": "综合分析",
            "tools": [
                "patent_analysis:basic",
                "feature_extraction",
                "drawing_analysis",
                "vector_search"
            ],
            "execution_mode": "hybrid",  # 混合模式（部分并行）
            "timeout": 60.0,
            "description": "全面的专利技术分析"
        }
    }
}
```

### 使用示例

```python
# 示例1：技术分析（并行）
results = await agent.call_tool_group(
    group_name="technical_analysis",
    params={
        "patent_id": "CN123456789A",
        "patent_content": "..."
    }
)

# 返回：
# {
#     "feature_extraction": {...},
#     "drawing_analysis": {...}
# }

# 示例2：综合分析
results = await agent.call_tool_group(
    group_name="comprehensive_analysis",
    params={
        "patent_id": "CN123456789A",
        "analysis_depth": "deep"
    }
)
```

---

## 3. 创造性分析智能体（CreativityAnalyzerAgent）

### 实际可用工具和技能

| 工具/技能名称 | 类型 | 位置 | 功能描述 | 状态 |
|-------------|------|------|---------|------|
| `patent_analysis:creativity` | 内置工具 | `core/tools/patent_analysis_handler.py` | 创造性评估 | ✅ 已实现 |
| `knowledge_graph_query` | 内置工具 | `core/tools/knowledge_graph_handler.py` | 知识图谱查询 | ✅ 已实现 |
| `case_search` | Skill | `skills/legal-world-model/` | 案例检索 | ✅ 已实现 |
| `academic_search` | MCP工具 | `academic-search` | 学术论文检索 | ✅ 已实现 |

### 工具配置（修正版）

```python
CREATIVITY_ANALYZER_AGENT_TOOLS = {
    "agent_type": "creativity_analyzer",
    "version": "1.0-revised",
    
    # 核心工具（必须可用）
    "required_tools": [
        {
            "name": "patent_analysis",
            "capability": "creativity_analysis",
            "permission": "auto",
            "health_check": True,
            "timeout": 60.0,
            "description": "创造性评估（三步法）"
        },
        {
            "name": "knowledge_graph_query",
            "class": "KnowledgeGraphHandler",
            "module": "core.tools.knowledge_graph_handler",
            "permission": "auto",
            "health_check": True,
            "timeout": 10.0,
            "description": "知识图谱查询（案例、法条）"
        }
    ],
    
    # 辅助工具（可选）
    "optional_tools": [
        {
            "name": "case_search",
            "type": "skill",
            "skill_path": "skills/legal-world-model/",
            "permission": "auto",
            "health_check": True,
            "timeout": 30.0,
            "description": "案例检索（无效决定、审查决定）"
        },
        {
            "name": "academic_search",
            "type": "mcp",
            "mcp_server": "academic-search",
            "permission": "manual",  # 需要确认
            "health_check": True,
            "timeout": 30.0,
            "description": "学术论文检索（补充证据）"
        }
    ],
    
    # 工具组
    "tool_groups": {
        "three_step_analysis": {
            "name": "三步法分析",
            "tools": [
                "patent_analysis:creativity",
                "knowledge_graph_query"
            ],
            "execution_mode": "sequential",  # 串行执行（三步法）
            "timeout": 60.0,
            "description": "第一步：最接近现有技术 → 第二步：区别特征 → 第三步：技术启示"
        },
        
        "evidence_collection": {
            "name": "证据收集",
            "tools": ["case_search", "academic_search"],
            "execution_mode": "parallel",  # 并行执行
            "timeout": 30.0,
            "description": "案例检索 + 学术论文检索"
        }
    }
}
```

---

## 4. 新颖性分析智能体（NoveltyAnalyzerAgent）

### 实际可用工具和技能

| 工具/技能名称 | 类型 | 位置 | 功能描述 | 状态 |
|-------------|------|------|---------|------|
| `patent_analysis:novelty` | 内置工具 | `core/tools/patent_analysis_handler.py` | 新颖性判断 | ✅ 已实现 |
| `vector_search` | 内置工具 | `core/tools/vector_search_handler.py` | 向量检索（相似专利） | ✅ 已实现 |
| `patent_similarity` | 内置工具 | `core/tools/patent_similarity.py` | 专利相似度分析 | ✅ 已实现 |
| `patent_retrieval` | 内置工具 | `core/tools/patent_retrieval.py` | 专利检索（补充对比文献） | ✅ 已实现 |

### 工具配置（修正版）

```python
NOVELTY_ANALYZER_AGENT_TOOLS = {
    "agent_type": "novelty_analyzer",
    "version": "1.0-revised",
    
    # 核心工具（必须可用）
    "required_tools": [
        {
            "name": "patent_analysis",
            "capability": "novelty_analysis",
            "permission": "auto",
            "health_check": True,
            "timeout": 90.0,
            "description": "新颖性判断（单独对比原则）"
        },
        {
            "name": "vector_search",
            "permission": "auto",
            "health_check": True,
            "timeout": 10.0,
            "description": "向量检索（相似专利）"
        }
    ],
    
    # 辅助工具（可选）
    "optional_tools": [
        {
            "name": "patent_similarity",
            "permission": "auto",
            "health_check": True,
            "timeout": 15.0,
            "description": "专利相似度分析"
        },
        {
            "name": "patent_retrieval",
            "permission": "manual",  # ⚠️ 需要确认
            "health_check": True,
            "timeout": 30.0,
            "description": "专利检索（补充对比文献）"
        }
    ],
    
    # 工具组
    "tool_groups": {
        "novelty_analysis": {
            "name": "新颖性分析",
            "tools": [
                "patent_analysis:novelty",
                "vector_search",
                "patent_similarity"
            ],
            "execution_mode": "sequential",  # 串行执行
            "timeout": 120.0,
            "description": "单独对比原则 + 逐一特征对比"
        },
        
        "supplement_search": {
            "name": "补充检索",
            "tools": ["patent_retrieval"],
            "execution_mode": "sequential",
            "timeout": 30.0,
            "require_confirmation": True,  # ⚠️ 需要确认
            "description": "补充对比文献检索"
        }
    },
    
    # 特殊约束
    "special_constraints": {
        "require_confirmation": True,  # ⚠️ 新颖性分析需要确认
        "min_confidence": 0.8,
        "max_execution_time": 300.0  # 最长5分钟
    }
}
```

---

## 5. 侵权分析智能体（InfringementAnalyzerAgent）

### 实际可用工具和技能

| 工具/技能名称 | 类型 | 位置 | 功能描述 | 状态 |
|-------------|------|------|---------|------|
| `patent_analysis:claim_parse` | 内置工具 | `core/tools/` | 权利要求解析 | ✅ 已实现 |
| `vector_search` | 内置工具 | `core/tools/vector_search_handler.py` | 产品相似度检索 | ✅ 已实现 |
| `knowledge_graph_query` | 内置工具 | `core/tools/knowledge_graph_handler.py` | 法律案例查询 | ✅ 已实现 |
| `patent_retrieval` | 内置工具 | `core/tools/patent_retrieval.py` | 现有技术检索（抗辩） | ✅ 已实现 |

### 工具配置（修正版）

```python
INFRINGEMENT_ANALYZER_AGENT_TOOLS = {
    "agent_type": "infringement_analyzer",
    "version": "1.0-revised",
    
    # 核心工具（必须可用）
    "required_tools": [
        {
            "name": "patent_analysis",
            "capability": "claim_parse",
            "permission": "auto",
            "health_check": True,
            "timeout": 30.0,
            "description": "权利要求解析"
        },
        {
            "name": "vector_search",
            "permission": "auto",
            "health_check": True,
            "timeout": 15.0,
            "description": "产品相似度检索"
        }
    ],
    
    # 辅助工具（可选）
    "optional_tools": [
        {
            "name": "knowledge_graph_query",
            "permission": "auto",
            "health_check": True,
            "timeout": 10.0,
            "description": "法律案例查询"
        },
        {
            "name": "patent_retrieval",
            "permission": "manual",  # ⚠️ 需要确认
            "health_check": True,
            "timeout": 30.0,
            "description": "现有技术检索（抗辩）"
        }
    ],
    
    # 工具组
    "tool_groups": {
        "infringement_analysis": {
            "name": "侵权分析",
            "tools": [
                "patent_analysis:claim_parse",
                "vector_search"
            ],
            "execution_mode": "sequential",  # 串行执行
            "timeout": 60.0,
            "description": "全面覆盖原则 + 等同原则"
        },
        
        "defense_analysis": {
            "name": "抗辩分析",
            "tools": [
                "knowledge_graph_query",
                "patent_retrieval"
            ],
            "execution_mode": "parallel",  # 并行执行
            "timeout": 30.0,
            "require_confirmation": True,  # ⚠️ 需要确认
            "description": "现有技术抗辩 + 案例支持"
        }
    },
    
    # 特殊约束
    "special_constraints": {
        "legal_disclaimer": True,  # ⚠️ 需要法律免责声明
        "min_confidence": 0.7
    }
}
```

---

## 6. 工具健康检查配置

### 健康检查清单

```python
TOOL_HEALTH_CHECK_CONFIG = {
    # 检索者工具
    "retriever": {
        "tools": [
            {
                "name": "patent_retrieval",
                "checks": {
                    "local_postgres": {
                        "check_type": "database_connection",
                        "connection_string": "postgresql://user:pass@localhost/patent_db",
                        "timeout": 5.0,
                        "description": "检查PostgreSQL连接"
                    },
                    "google_patents": {
                        "check_type": "http_ping",
                        "url": "https://patents.google.com",
                        "timeout": 10.0,
                        "description": "检查Google Patents可用性"
                    }
                }
            },
            {
                "name": "patent_download",
                "checks": {
                    "download_capability": {
                        "check_type": "test_download",
                        "test_patent": "US1",  # 简单测试专利
                        "timeout": 30.0,
                        "description": "测试PDF下载能力"
                    }
                }
            }
        ],
        "idle_check_interval": 3600,  # 每小时检查一次
        "pre_demo_check": True,  # ⚠️ 演示前必须检查
        "blocking_on_failure": True  # ⚠️ 演示前检查失败时阻止演示
    },
    
    # 分析者工具
    "analyzer": {
        "tools": [
            {
                "name": "patent_analysis",
                "checks": {
                    "basic_analysis": {
                        "check_type": "test_execution",
                        "test_patent": "CN123456789A",
                        "test_capability": "basic_analysis",
                        "timeout": 30.0,
                        "description": "测试基础分析能力"
                    }
                }
            },
            {
                "name": "feature_extraction",
                "checks": {
                    "extraction_capability": {
                        "check_type": "test_execution",
                        "test_content": "测试专利内容",
                        "timeout": 20.0,
                        "description": "测试要素提取能力"
                    }
                }
            },
            {
                "name": "drawing_analysis",
                "checks": {
                    "drawing_capability": {
                        "check_type": "test_execution",
                        "test_drawing": "测试附图",
                        "timeout": 15.0,
                        "description": "测试双图分析能力"
                    }
                }
            }
        ],
        "idle_check_interval": 1800,  # 每30分钟检查一次
        "pre_demo_check": True,
        "blocking_on_failure": True
    }
}
```

---

## 7. 工具调用权限配置

### 权限模式

```python
TOOL_PERMISSION_CONFIG = {
    # 自动授权的工具（默认）
    "auto_permission_tools": [
        "patent_retrieval",
        "patent_analysis",
        "feature_extraction",
        "drawing_analysis",
        "vector_search",
        "patent_similarity",
        "patent_translator",
        "knowledge_graph_query"
    ],
    
    # 需要手动确认的工具
    "manual_permission_tools": [
        "academic_search",  # MCP工具
        "web_search",  # MCP工具
        "patent_retrieval:novelty_supplement",  # 新颖性补充检索
        "patent_retrieval:infringement_supplement"  # 侵权补充检索
    ],
    
    # 受限工具（需要特殊授权）
    "restricted_tools": [
        "database_write",  # 数据库写入
        "system_modify"  # 系统修改
    ],
    
    # 速率限制
    "rate_limits": {
        "patent_retrieval": "10/min",
        "patent_download": "5/min",
        "patent_analysis": "5/min",
        "vector_search": "20/min",
        "academic_search": "3/min"
    }
}
```

---

## 8. 实施建议

### 阶段1：工具注册（1周）

**任务**:
1. 注册所有实际可用的工具
2. 配置工具权限和速率限制
3. 实现工具健康检查
4. 实现空闲时间验证

**产出**:
- 工具注册表
- 权限配置文件
- 健康检查系统

---

### 阶段2：智能体集成（1周）

**任务**:
1. 为每个智能体配置工具
2. 实现工具组调用
3. 实现并行调用支持
4. 编写调用示例

**产出**:
- 智能体工具配置文件
- 工具调用接口
- 使用文档

---

### 阶段3：测试与优化（1周）

**任务**:
1. 单元测试（每个工具）
2. 集成测试（工具组调用）
3. 性能测试（并行调用）
4. 文档完善

**产出**:
- 测试套件
- 性能报告
- 完整文档

---

## 9. 总结

### 关键修正

1. **检索者**：
   - ✅ 本地PostgreSQL + Google Patents
   - ✅ 专利下载（Google Patents PDF）
   - ❌ 移除CNIPA、EPO、WIPO（暂未实现）

2. **分析者**：
   - ✅ 专注于技术分析
   - ✅ 要素提取、双图分析
   - ✅ 专利内容分析、向量检索、相似度分析

3. **创造性分析**：
   - ✅ 三步法分析
   - ✅ 知识图谱查询
   - ✅ 案例检索、学术论文检索（MCP）

4. **新颖性分析**：
   - ✅ 单独对比原则
   - ✅ 向量检索、相似度分析
   - ✅ 补充检索（需确认）

5. **侵权分析**：
   - ✅ 权利要求解析
   - ✅ 产品相似度检索
   - ✅ 法律案例查询、现有技术检索（抗辩）

---

### 性能目标

| 指标 | 目标 |
|------|------|
| 双渠道检索延迟 | <2s (P95) |
| 专利下载时间 | <30s (P95) |
| 要素提取时间 | <10s (P95) |
| 双图分析时间 | <15s (P95) |
| 综合分析时间 | <60s (P95) |

---

**End of Document**
