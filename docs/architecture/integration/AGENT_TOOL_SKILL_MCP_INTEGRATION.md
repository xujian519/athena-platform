# 智能体工具与外部接口集成方案

> **版本**: 1.0
> **创建日期**: 2026-04-21
> **状态**: 详细设计

---

## 📋 问题陈述

用户提出的两个核心问题：

1. **所有智能体配置的工具是否应该讨论？**
   - 每个智能体应该配置哪些工具？
   - 工具的权限和调用规则？
   - 工具的健康检查和可用性验证？

2. **未来智能体外接skill和MCP等接口的问题是否应该一并讨论？**
   - 智能体如何调用外部skill？
   - 智能体如何调用MCP服务器？
   - 接口设计和集成方案？

---

## 🎯 设计目标

### 功能目标

| 目标 | 描述 | 优先级 |
|------|------|--------|
| **工具配置** | 为每个智能体配置合适的工具 | P0 |
| **权限控制** | 工具调用的权限和验证 | P0 |
| **健康检查** | 工具可用性验证和监控 | P1 |
| **Skill集成** | 智能体调用外部skill | P1 |
| **MCP集成** | 智能体调用MCP服务器 | P1 |
| **统一接口** | 统一的调用接口 | P2 |

---

### 性能目标

| 指标 | 目标 | 说明 |
|------|------|------|
| 工具调用延迟 | <100ms (P95) | 不包括工具执行时间 |
| 工具发现时间 | <50ms | 查找和选择工具 |
| 健康检查延迟 | <200ms | 验证工具可用性 |
| 并发调用支持 | >10 QPS | 同时调用多个工具 |

---

## 🏗️ 架构设计

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    智能体层 (Agents)                         │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌─────────┐  │
│  │ 检索者    │  │ 分析者    │  │ 创造性    │  │ 小诺   │  │
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └────┬────┘  │
└────────┼─────────────┼─────────────┼─────────────┼─────────┘
         │             │             │             │
┌────────┴─────────────┴─────────────┴─────────────┴─────────┐
│              统一工具调用层 (UnifiedToolCallLayer)          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ ToolSelector │  │ ToolCaller   │  │ HealthChecker│      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼──────────────────┼──────────────────┼──────────────┘
          │                  │                  │
┌─────────┴──────────────────┴──────────────────┴──────────────┐
│                    工具注册表 (ToolRegistry)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ 内置工具  │  │ Skill    │  │ MCP服务  │  │ 外部API  │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 1. 智能体工具配置

### 1.1 检索者（RetrieverAgent）

#### 工具清单

| 工具名称 | 工具类型 | 用途 | 优先级 | 权限 |
|---------|---------|------|--------|------|
| `patent_search_cnipa` | 内置工具 | 中国专利检索 | P0 | 读写 |
| `patent_search_google` | 内置工具 | Google Patents检索 | P0 | 读写 |
| `patent_search_epo` | 内置工具 | EPO专利检索 | P1 | 读写 |
| `patent_search_wipo` | 内置工具 | WIPO专利检索 | P1 | 读写 |
| `patent_download` | 内置工具 | 专利PDF下载 | P2 | 读写 |
| `patent_parse` | 内置工具 | 专利文本解析 | P0 | 读写 |
| `web_search` | MCP工具 | 网络搜索（补充） | P2 | 读写 |
| `web_scrape` | MCP工具 | 网页抓取（补充） | P2 | 读写 |

#### 工具配置

```python
RETRIEVER_AGENT_TOOLS = {
    "agent_type": "retriever",
    "default_tools": [
        "patent_search_cnipa",
        "patent_search_google",
        "patent_parse"
    ],
    "optional_tools": [
        "patent_search_epo",
        "patent_search_wipo",
        "patent_download",
        "web_search",
        "web_scrape"
    ],
    "tool_groups": {
        "patent_search": {
            "tools": ["patent_search_cnipa", "patent_search_google", "patent_search_epo", "patent_search_wipo"],
            "parallel": True,  # 支持并行调用
            "timeout": 30.0
        },
        "patent_processing": {
            "tools": ["patent_download", "patent_parse"],
            "parallel": False,  # 串行调用
            "timeout": 60.0
        }
    },
    "permissions": {
        "patent_search_cnipa": {
            "mode": "auto",  # 自动授权
            "rate_limit": "10/min"
        },
        "patent_search_google": {
            "mode": "auto",
            "rate_limit": "10/min"
        },
        "web_search": {
            "mode": "manual",  # 需要手动确认
            "rate_limit": "5/min"
        }
    }
}
```

---

### 1.2 分析者（AnalyzerAgent）

#### 工具清单

| 工具名称 | 工具类型 | 用途 | 优先级 | 权限 |
|---------|---------|------|--------|------|
| `text_parse` | 内置工具 | 文本解析 | P0 | 读写 |
| `feature_extract` | 内置工具 | 技术特征提取 | P0 | 读写 |
| `tech_summary` | 内置工具 | 技术总结生成 | P0 | 读写 |
| `knowledge_graph_query` | 内置工具 | 知识图谱查询 | P1 | 读写 |
| `vector_search` | 内置工具 | 向量检索 | P1 | 读写 |
| `legal_world_model_query` | 内置工具 | 法律世界模型查询 | P2 | 读写 |

#### 工具配置

```python
ANALYZER_AGENT_TOOLS = {
    "agent_type": "analyzer",
    "default_tools": [
        "text_parse",
        "feature_extract",
        "tech_summary"
    ],
    "optional_tools": [
        "knowledge_graph_query",
        "vector_search",
        "legal_world_model_query"
    ],
    "tool_groups": {
        "text_analysis": {
            "tools": ["text_parse", "feature_extract"],
            "parallel": False,
            "timeout": 30.0
        },
        "knowledge_query": {
            "tools": ["knowledge_graph_query", "vector_search", "legal_world_model_query"],
            "parallel": True,
            "timeout": 10.0
        }
    },
    "permissions": {
        "text_parse": {
            "mode": "auto",
            "rate_limit": "20/min"
        },
        "feature_extract": {
            "mode": "auto",
            "rate_limit": "20/min"
        },
        "knowledge_graph_query": {
            "mode": "auto",
            "rate_limit": "10/min"
        }
    }
}
```

---

### 1.3 创造性分析智能体（CreativityAnalyzerAgent）

#### 工具清单

| 工具名称 | 工具类型 | 用途 | 优先级 | 权限 |
|---------|---------|------|--------|------|
| `three_step_analysis` | 内置工具 | 三步法分析 | P0 | 读写 |
| `disclosure_analysis` | 内置工具 | 技术启示分析 | P0 | 读写 |
| `effect_analysis` | 内置工具 | 技术效果分析 | P0 | 读写 |
| `case_search` | Skill | 案例检索 | P1 | 读写 |
| `knowledge_query` | 内置工具 | 创造性知识查询 | P1 | 读写 |
| `academic_search` | MCP工具 | 学术论文检索 | P2 | 手动 |

#### 工具配置

```python
CREATIVITY_ANALYZER_AGENT_TOOLS = {
    "agent_type": "creativity_analyzer",
    "default_tools": [
        "three_step_analysis",
        "disclosure_analysis",
        "effect_analysis"
    ],
    "optional_tools": [
        "case_search",
        "knowledge_query",
        "academic_search"
    ],
    "tool_groups": {
        "creativity_analysis": {
            "tools": ["three_step_analysis", "disclosure_analysis", "effect_analysis"],
            "parallel": False,  # 串行执行（三步法）
            "timeout": 60.0
        },
        "evidence_collection": {
            "tools": ["case_search", "academic_search"],
            "parallel": True,
            "timeout": 30.0
        }
    },
    "permissions": {
        "three_step_analysis": {
            "mode": "auto",
            "rate_limit": "5/min"
        },
        "case_search": {
            "mode": "auto",
            "rate_limit": "10/min"
        },
        "academic_search": {
            "mode": "manual",  # 需要确认
            "rate_limit": "3/min"
        }
    }
}
```

---

### 1.4 新颖性分析智能体（NoveltyAnalyzerAgent）

#### 工具清单

| 工具名称 | 工具类型 | 用途 | 优先级 | 权限 |
|---------|---------|------|--------|------|
| `feature_compare` | 内置工具 | 特征逐一对比 | P0 | 读写 |
| `concept_hierarchy` | 内置工具 | 概念层级分析 | P0 | 读写 |
| `equivalent_substitution` | 内置工具 | 惯用手段置换判断 | P1 | 读写 |
| `prior_art_search` | Skill | 现有技术检索 | P0 | 读写 |
| `case_search` | Skill | 案例检索 | P2 | 读写 |

#### 工具配置

```python
NOVELTY_ANALYZER_AGENT_TOOLS = {
    "agent_type": "novelty_analyzer",
    "default_tools": [
        "feature_compare",
        "concept_hierarchy",
        "prior_art_search"
    ],
    "optional_tools": [
        "equivalent_substitution",
        "case_search"
    ],
    "tool_groups": {
        "novelty_analysis": {
            "tools": ["feature_compare", "concept_hierarchy", "equivalent_substitution"],
            "parallel": False,  # 串行执行
            "timeout": 120.0  # ⚠️ 新颖性分析耗时较长
        },
        "evidence_collection": {
            "tools": ["prior_art_search", "case_search"],
            "parallel": True,
            "timeout": 60.0
        }
    },
    "permissions": {
        "feature_compare": {
            "mode": "auto",
            "rate_limit": "5/min"
        },
        "prior_art_search": {
            "mode": "manual",  # ⚠️ 需要确认
            "rate_limit": "3/min"
        }
    },
    "special_constraints": {
        "require_confirmation": True,  # ⚠️ 新颖性分析需要确认
        "min_confidence": 0.8  # 最低置信度要求
    }
}
```

---

### 1.5 侵权分析智能体（InfringementAnalyzerAgent）

#### 工具清单

| 工具名称 | 工具类型 | 用途 | 优先级 | 权限 |
|---------|---------|------|--------|------|
| `claim_parse` | 内置工具 | 权利要求解析 | P0 | 读写 |
| `product_analyze` | 内置工具 | 产品分析 | P0 | 读写 |
| `all_elements_test` | 内置工具 | 全面覆盖原则测试 | P0 | 读写 |
| `doctrine_of_equivalents` | 内置工具 | 等同原则测试 | P0 | 读写 |
| `defense_identify` | 内置工具 | 抗辩事由识别 | P1 | 读写 |
| `prior_art_search` | Skill | 现有技术检索 | P2 | 手动 |

#### 工具配置

```python
INFRINGEMENT_ANALYZER_AGENT_TOOLS = {
    "agent_type": "infringement_analyzer",
    "default_tools": [
        "claim_parse",
        "product_analyze",
        "all_elements_test",
        "doctrine_of_equivalents"
    ],
    "optional_tools": [
        "defense_identify",
        "prior_art_search"
    ],
    "tool_groups": {
        "infringement_analysis": {
            "tools": ["claim_parse", "product_analyze", "all_elements_test", "doctrine_of_equivalents"],
            "parallel": False,  # 串行执行
            "timeout": 90.0
        },
        "defense_analysis": {
            "tools": ["defense_identify", "prior_art_search"],
            "parallel": True,
            "timeout": 60.0
        }
    },
    "permissions": {
        "claim_parse": {
            "mode": "auto",
            "rate_limit": "10/min"
        },
        "all_elements_test": {
            "mode": "auto",
            "rate_limit": "5/min"
        },
        "prior_art_search": {
            "mode": "manual",
            "rate_limit": "3/min"
        }
    },
    "special_constraints": {
        "legal_disclaimer": True,  # ⚠️ 需要法律免责声明
        "min_confidence": 0.7
    }
}
```

---

## 2. 工具权限控制

### 2.1 权限模式

```python
from enum import Enum

class PermissionMode(Enum):
    """权限模式"""
    AUTO = "auto"          # 自动授权（默认）
    MANUAL = "manual"      # 手动确认
    BYPASS = "bypass"      # 绕过权限（仅系统工具）
    RESTRICTED = "restricted"  # 受限（需要特殊授权）
```

---

### 2.2 权限规则

```python
PERMISSION_RULES = {
    # 规则ID: 权限规则定义
    "patent_search_auto": {
        "pattern": "patent_search_*",
        "mode": PermissionMode.AUTO,
        "rate_limit": "10/min",
        "description": "专利检索工具自动授权"
    },
    
    "web_search_manual": {
        "pattern": "web_search",
        "mode": PermissionMode.MANUAL,
        "rate_limit": "5/min",
        "description": "网络搜索需要手动确认"
    },
    
    "system_tools_bypass": {
        "pattern": "system_*",
        "mode": PermissionMode.BYPASS,
        "description": "系统工具绕过权限检查"
    },
    
    "dangerous_tools_restricted": {
        "pattern": "*delete*",
        "mode": PermissionMode.RESTRICTED,
        "description": "危险工具需要特殊授权"
    }
}
```

---

### 2.3 权限检查流程

```python
async def check_tool_permission(
    agent_type: str,
    tool_name: str,
    params: Dict[str, Any]
) -> PermissionDecision:
    """
    检查工具调用权限
    
    Args:
        agent_type: 智能体类型
        tool_name: 工具名称
        params: 调用参数
    
    Returns:
        PermissionDecision: 权限决策
    """
    # 1. 查找匹配的权限规则
    rule = find_matching_rule(tool_name)
    
    # 2. 检查权限模式
    if rule.mode == PermissionMode.AUTO:
        return PermissionDecision(allowed=True, reason="自动授权")
    
    elif rule.mode == PermissionMode.MANUAL:
        # 请求用户确认
        return await request_user_confirmation(tool_name, params)
    
    elif rule.mode == PermissionMode.RESTRICTED:
        # 检查特殊授权
        if has_special_authorization(agent_type, tool_name):
            return PermissionDecision(allowed=True, reason="特殊授权")
        else:
            return PermissionDecision(allowed=False, reason="需要特殊授权")
    
    elif rule.mode == PermissionMode.BYPASS:
        return PermissionDecision(allowed=True, reason="系统工具")
```

---

## 3. 工具健康检查

### 3.1 健康检查机制

```python
class ToolHealthChecker:
    """工具健康检查器"""
    
    async def check_tool_health(self, tool_name: str) -> HealthStatus:
        """
        检查工具健康状态
        
        检查项：
        1. 工具是否已注册
        2. 工具元数据是否完整
        3. 工具处理器是否可用
        4. 工具响应时间是否正常
        """
        # 1. 检查工具注册
        if not self.registry.is_registered(tool_name):
            return HealthStatus(
                status="unhealthy",
                reason="工具未注册",
                suggestion="请先注册工具"
            )
        
        # 2. 检查元数据
        tool = self.registry.get(tool_name)
        if not tool.metadata_complete():
            return HealthStatus(
                status="warning",
                reason="工具元数据不完整",
                suggestion="请补充工具元数据"
            )
        
        # 3. 检查处理器
        if not tool.handler_available():
            return HealthStatus(
                status="unhealthy",
                reason="工具处理器不可用",
                suggestion="请检查工具实现"
            )
        
        # 4. 检查响应时间
        start_time = time.time()
        try:
            await tool.ping()
            response_time = time.time() - start_time
            
            if response_time > 1.0:  # 超过1秒
                return HealthStatus(
                    status="warning",
                    reason=f"响应时间过长: {response_time:.2f}s",
                    suggestion="建议优化工具性能"
                )
            
            return HealthStatus(
                status="healthy",
                reason="工具健康",
                response_time=response_time
            )
            
        except Exception as e:
            return HealthStatus(
                status="unhealthy",
                reason=f"工具异常: {str(e)}",
                suggestion="请检查工具实现"
            )
```

---

### 3.2 批量健康检查

```python
async def check_all_tools_health(
    agent_type: str
) -> Dict[str, HealthStatus]:
    """
    检查智能体的所有工具健康状态
    
    Args:
        agent_type: 智能体类型
    
    Returns:
        Dict[str, HealthStatus]: 工具名称 -> 健康状态
    """
    # 获取智能体的所有工具
    tools = get_agent_tools(agent_type)
    
    # 并行检查所有工具
    health_statuses = {}
    for tool in tools:
        status = await self.check_tool_health(tool)
        health_statuses[tool] = status
    
    return health_statuses
```

---

### 3.3 空闲时间验证（继承小诺设计）

```python
class IdleTimeVerifier:
    """空闲时间验证器"""
    
    async def verify_before_demonstration(self, agent_type: str):
        """
        ⚠️ 给客户展示前验证（关键功能）
        
        验证所有工具可用性，如有失败则阻止演示
        """
        health_statuses = await self.check_all_tools_health(agent_type)
        
        # 检查是否有不健康的工具
        unhealthy_tools = [
            tool for tool, status in health_statuses.items()
            if status.status != "healthy"
        ]
        
        if unhealthy_tools:
            raise DemonstrationBlockedError(
                f"以下工具不可用，无法进行演示：{', '.join(unhealthy_tools)}",
                unhealthy_tools=unhealthy_tools
            )
        
        return True
    
    async def verify_during_idle(self, agent_type: str):
        """
        空闲时间验证（后台任务）
        
        发现问题但不阻止运行，只记录日志
        """
        try:
            health_statuses = await self.check_all_tools_health(agent_type)
            
            # 记录不健康的工具
            for tool, status in health_statuses.items():
                if status.status != "healthy":
                    logger.warning(
                        f"工具 {tool} 健康检查失败: {status.reason}",
                        extra={"tool": tool, "status": status}
                    )
                    
                    # 尝试恢复
                    await self.attempt_recovery(tool)
                    
        except Exception as e:
            logger.error(f"空闲时间验证失败: {str(e)}")
```

---

## 4. Skill集成方案

### 4.1 Skill定义

**Skill**是封装了特定能力的可复用模块，类似于工具但更复杂。

**特点**:
- 可能包含多个工具
- 可能有自己的状态
- 可能需要初始化配置
- 可能需要生命周期管理

---

### 4.2 Skill接口设计

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseSkill(ABC):
    """Skill基类"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化Skill"""
        self.config = config or {}
        self.state = {}
    
    @abstractmethod
    async def initialize(self) -> bool:
        """初始化资源（如连接数据库）"""
        pass
    
    @abstractmethod
    async def execute(self, command: str, params: Dict[str, Any]) -> Any:
        """执行Skill命令"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> bool:
        """清理资源"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """返回Skill的能力列表"""
        pass
    
    async def health_check(self) -> bool:
        """健康检查"""
        return True
```

---

### 4.3 Skill示例

```python
class PatentRetrievalSkill(BaseSkill):
    """专利检索Skill"""
    
    async def initialize(self) -> bool:
        """初始化数据库连接"""
        self.db = await connect_to_database(self.config.get("db_url"))
        return self.db is not None
    
    async def execute(self, command: str, params: Dict[str, Any]) -> Any:
        """执行检索命令"""
        if command == "search":
            return await self._search_patents(params)
        elif command == "download":
            return await self._download_patent(params)
        else:
            raise ValueError(f"未知命令: {command}")
    
    async def cleanup(self) -> bool:
        """清理数据库连接"""
        if self.db:
            await self.db.close()
            return True
        return False
    
    def get_capabilities(self) -> List[str]:
        """返回能力列表"""
        return ["search", "download", "parse"]
    
    async def _search_patents(self, params: Dict[str, Any]) -> List[Dict]:
        """搜索专利"""
        query = params.get("query")
        limit = params.get("limit", 10)
        
        results = await self.db.execute(
            "SELECT * FROM patents WHERE text LIKE ? LIMIT ?",
            f"%{query}%", limit
        )
        
        return results
```

---

### 4.4 Skill注册与调用

```python
class SkillRegistry:
    """Skill注册表"""
    
    def __init__(self):
        self.skills: Dict[str, BaseSkill] = {}
    
    async def register_skill(
        self,
        name: str,
        skill_class: type,
        config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """注册Skill"""
        try:
            # 初始化Skill
            skill = skill_class(config)
            
            # 初始化资源
            if await skill.initialize():
                self.skills[name] = skill
                logger.info(f"Skill {name} 注册成功")
                return True
            else:
                logger.error(f"Skill {name} 初始化失败")
                return False
                
        except Exception as e:
            logger.error(f"Skill {name} 注册异常: {str(e)}")
            return False
    
    async def call_skill(
        self,
        name: str,
        command: str,
        params: Dict[str, Any]
    ) -> Any:
        """调用Skill"""
        if name not in self.skills:
            raise ValueError(f"Skill {name} 未注册")
        
        skill = self.skills[name]
        
        # 健康检查
        if not await skill.health_check():
            raise RuntimeError(f"Skill {name} 不健康")
        
        # 执行命令
        return await skill.execute(command, params)
    
    async def cleanup_all(self):
        """清理所有Skill"""
        for name, skill in self.skills.items():
            try:
                await skill.cleanup()
                logger.info(f"Skill {name} 清理成功")
            except Exception as e:
                logger.error(f"Skill {name} 清理失败: {str(e)}")
```

---

### 4.5 智能体调用Skill

```python
class AgentWithSkillSupport:
    """支持Skill的智能体基类"""
    
    def __init__(self, skill_registry: SkillRegistry):
        self.skill_registry = skill_registry
        self.available_skills: List[str] = []
    
    async def call_skill(
        self,
        skill_name: str,
        command: str,
        params: Dict[str, Any]
    ) -> Any:
        """
        调用Skill
        
        Args:
            skill_name: Skill名称
            command: 命令名称
            params: 命令参数
        
        Returns:
            执行结果
        """
        # 检查权限
        if skill_name not in self.available_skills:
            raise PermissionError(f"智能体无权限调用Skill: {skill_name}")
        
        # 调用Skill
        return await self.skill_registry.call_skill(
            skill_name, command, params
        )
    
    async def load_skill_dependencies(self, agent_type: str):
        """
        加载智能体依赖的Skill
        
        Args:
            agent_type: 智能体类型
        """
        # 获取智能体配置的Skill
        skill_configs = AGENT_SKILL_CONFIGS.get(agent_type, [])
        
        for skill_config in skill_configs:
            skill_name = skill_config["name"]
            skill_class = skill_config["class"]
            skill_config_params = skill_config.get("config", {})
            
            # 注册Skill
            success = await self.skill_registry.register_skill(
                skill_name, skill_class, skill_config_params
            )
            
            if success:
                self.available_skills.append(skill_name)
```

---

## 5. MCP集成方案

### 5.1 MCP服务器清单

| MCP服务器 | 功能 | 工具列表 | 状态 |
|----------|------|---------|------|
| `gaode-mcp-server` | 高德地图服务 | 地理编码、路径规划 | active |
| `academic-search` | 学术搜索 | 论文检索、Semantic Scholar | active |
| `jina-ai-mcp-server` | Jina AI服务 | 网页抓取、向量搜索、重排序 | active |
| `memory` | 知识图谱内存 | 实体、关系、观察 | active |
| `local-search-engine` | 本地搜索引擎 | 搜索+抓取 | active |

---

### 5.2 MCP工具映射

```python
MCP_TOOL_MAPPING = {
    # 学术搜索MCP
    "academic_search": {
        "mcp_server": "academic-search",
        "mcp_tools": [
            "search_papers",
            "get_paper_metadata",
            "get_citations"
        ],
        "agent_mapping": {
            "creativity_analyzer": ["search_papers"],
            "novelty_analyzer": ["search_papers"],
            "analyzer": ["search_papers"]
        }
    },
    
    # Jina AI MCP
    "jina_ai": {
        "mcp_server": "jina-ai-mcp-server",
        "mcp_tools": [
            "read_web",
            "web_search",
            "vector_search",
            "rerank"
        ],
        "agent_mapping": {
            "retriever": ["read_web", "web_search"],
            "analyzer": ["read_web", "vector_search"],
            "creativity_analyzer": ["web_search"]
        }
    },
    
    # Memory MCP
    "memory": {
        "mcp_server": "memory",
        "mcp_tools": [
            "create_entities",
            "create_relations",
            "search_nodes",
            "read_graph"
        ],
        "agent_mapping": {
            "xiaonuo": ["create_entities", "create_relations", "search_nodes"],
            "analyzer": ["search_nodes"]
        }
    },
    
    # 本地搜索引擎MCP
    "local_search_engine": {
        "mcp_server": "local-search-engine",
        "mcp_tools": [
            "web_search",
            "web_scrape",
            "web_search_and_scrape"
        ],
        "agent_mapping": {
            "retriever": ["web_search", "web_scrape"],
            "analyzer": ["web_search"]
        }
    }
}
```

---

### 5.3 MCP调用接口

```python
class MCPClient:
    """MCP客户端"""
    
    def __init__(self, mcp_server_url: str):
        self.mcp_server_url = mcp_server_url
        self.session = None
    
    async def connect(self):
        """连接MCP服务器"""
        self.session = aiohttp.ClientSession()
    
    async def call_tool(
        self,
        tool_name: str,
        params: Dict[str, Any]
    ) -> Any:
        """
        调用MCP工具
        
        Args:
            tool_name: 工具名称
            params: 工具参数
        
        Returns:
            执行结果
        """
        if not self.session:
            await self.connect()
        
        # 构造MCP请求
        mcp_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": params
            },
            "id": str(uuid.uuid4())
        }
        
        # 发送请求
        async with self.session.post(
            f"{self.mcp_server_url}/mcp",
            json=mcp_request
        ) as response:
            result = await response.json()
            
            if "error" in result:
                raise RuntimeError(result["error"])
            
            return result["result"]
    
    async def close(self):
        """关闭连接"""
        if self.session:
            await self.session.close()
```

---

### 5.4 智能体调用MCP工具

```python
class AgentWithMCPSupport:
    """支持MCP的智能体基类"""
    
    def __init__(self):
        self.mcp_clients: Dict[str, MCPClient] = {}
        self.available_mcp_tools: Dict[str, str] = {}  # tool_name -> mcp_server
    
    async def initialize_mcp_clients(self, agent_type: str):
        """
        初始化MCP客户端
        
        Args:
            agent_type: 智能体类型
        """
        # 获取智能体配置的MCP工具
        mcp_configs = AGENT_MCP_CONFIGS.get(agent_type, [])
        
        for mcp_config in mcp_configs:
            mcp_server = mcp_config["mcp_server"]
            mcp_tools = mcp_config["tools"]
            
            # 初始化MCP客户端
            client = MCPClient(mcp_config["url"])
            await client.connect()
            
            self.mcp_clients[mcp_server] = client
            
            # 注册可用工具
            for tool in mcp_tools:
                self.available_mcp_tools[tool] = mcp_server
    
    async def call_mcp_tool(
        self,
        tool_name: str,
        params: Dict[str, Any]
    ) -> Any:
        """
        调用MCP工具
        
        Args:
            tool_name: 工具名称
            params: 工具参数
        
        Returns:
            执行结果
        """
        if tool_name not in self.available_mcp_tools:
            raise ValueError(f"MCP工具 {tool_name} 不可用")
        
        mcp_server = self.available_mcp_tools[tool_name]
        client = self.mcp_clients[mcp_server]
        
        return await client.call_tool(tool_name, params)
```

---

## 6. 统一调用接口

### 6.1 统一工具调用器

```python
class UnifiedToolCaller:
    """统一工具调用器"""
    
    def __init__(
        self,
        tool_registry: ToolRegistry,
        skill_registry: SkillRegistry,
        mcp_clients: Dict[str, MCPClient]
    ):
        self.tool_registry = tool_registry
        self.skill_registry = skill_registry
        self.mcp_clients = mcp_clients
    
    async def call(
        self,
        agent_type: str,
        tool_type: str,  # "builtin", "skill", "mcp"
        tool_name: str,
        params: Dict[str, Any]
    ) -> Any:
        """
        统一调用接口
        
        Args:
            agent_type: 智能体类型
            tool_type: 工具类型（builtin/skill/mcp）
            tool_name: 工具名称
            params: 工具参数
        
        Returns:
            执行结果
        """
        # 1. 检查权限
        permission = await self.check_permission(
            agent_type, tool_type, tool_name, params
        )
        
        if not permission.allowed:
            raise PermissionError(permission.reason)
        
        # 2. 根据工具类型调用
        if tool_type == "builtin":
            return await self._call_builtin_tool(tool_name, params)
        
        elif tool_type == "skill":
            return await self._call_skill(tool_name, params)
        
        elif tool_type == "mcp":
            return await self._call_mcp_tool(tool_name, params)
        
        else:
            raise ValueError(f"未知工具类型: {tool_type}")
    
    async def _call_builtin_tool(
        self,
        tool_name: str,
        params: Dict[str, Any]
    ) -> Any:
        """调用内置工具"""
        tool = self.tool_registry.get(tool_name)
        return await tool.execute(params)
    
    async def _call_skill(
        self,
        skill_name: str,
        params: Dict[str, Any]
    ) -> Any:
        """调用Skill"""
        command = params.pop("command", "execute")
        return await self.skill_registry.call_skill(
            skill_name, command, params
        )
    
    async def _call_mcp_tool(
        self,
        tool_name: str,
        params: Dict[str, Any]
    ) -> Any:
        """调用MCP工具"""
        # 查找MCP服务器
        mcp_server = self._find_mcp_server(tool_name)
        client = self.mcp_clients[mcp_server]
        
        return await client.call_tool(tool_name, params)
```

---

### 6.2 并行调用支持

```python
class ParallelToolCaller:
    """并行工具调用器"""
    
    async def call_parallel(
        self,
        calls: List[Dict[str, Any]]
    ) -> List[Any]:
        """
        并行调用多个工具
        
        Args:
            calls: 调用列表
                [
                    {"tool_type": "builtin", "tool_name": "tool1", "params": {...}},
                    {"tool_type": "skill", "tool_name": "skill1", "params": {...}},
                    {"tool_type": "mcp", "tool_name": "mcp1", "params": {...}}
                ]
        
        Returns:
            List[Any]: 执行结果列表
        """
        # 创建异步任务
        tasks = [
            self.unified_call(
                call["tool_type"],
                call["tool_name"],
                call["params"]
            )
            for call in calls
        ]
        
        # 并行执行
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"工具调用失败: {calls[i]}")
                results[i] = None
        
        return results
```

---

## 7. 配置文件结构

### 7.1 智能体配置文件

```json
{
  "agent_type": "creativity_analyzer",
  "version": "1.0",
  "tools": {
    "builtin": [
      {
        "name": "three_step_analysis",
        "priority": "P0",
        "permission": "auto",
        "rate_limit": "5/min"
      },
      {
        "name": "disclosure_analysis",
        "priority": "P0",
        "permission": "auto",
        "rate_limit": "5/min"
      }
    ],
    "skills": [
      {
        "name": "case_search",
        "class": "CaseSearchSkill",
        "config": {
          "database_url": "postgresql://..."
        },
        "permission": "auto",
        "rate_limit": "10/min"
      }
    ],
    "mcp": [
      {
        "name": "academic_search",
        "mcp_server": "academic-search",
        "tools": ["search_papers", "get_paper_metadata"],
        "permission": "manual",
        "rate_limit": "3/min"
      }
    ]
  },
  "tool_groups": {
    "creativity_analysis": {
      "tools": ["three_step_analysis", "disclosure_analysis"],
      "parallel": false,
      "timeout": 60.0
    },
    "evidence_collection": {
      "tools": ["case_search", "academic_search"],
      "parallel": true,
      "timeout": 30.0
    }
  }
}
```

---

## 8. 实施计划

### 阶段1：工具配置（1周）

**任务**:
1. 定义每个智能体的工具清单
2. 实现工具权限控制
3. 实现工具健康检查
4. 实现空闲时间验证

**产出**:
- 智能体工具配置文件（JSON）
- 权限控制系统
- 健康检查系统

---

### 阶段2：Skill集成（1周）

**任务**:
1. 设计Skill接口
2. 实现Skill注册表
3. 实现智能体调用Skill
4. 实现Skill生命周期管理

**产出**:
- Skill基类和接口
- Skill注册表
- Skill调用示例

---

### 阶段3：MCP集成（1周）

**任务**:
1. 实现MCP客户端
2. 实现MCP工具映射
3. 实现智能体调用MCP工具
4. 实现MCP工具监控

**产出**:
- MCP客户端实现
- MCP工具映射配置
- MCP调用示例

---

### 阶段4：统一接口（1周）

**任务**:
1. 实现统一工具调用器
2. 实现并行调用支持
3. 实现调用监控和日志
4. 编写测试和文档

**产出**:
- 统一工具调用器
- 并行调用支持
- 测试套件和文档

---

## 9. 总结

### 关键设计要点

1. **工具配置**: 为每个智能体配置合适的工具
2. **权限控制**: 三种权限模式（auto/manual/restricted）
3. **健康检查**: 空闲时间验证和演示前验证
4. **Skill集成**: 统一的Skill接口和生命周期管理
5. **MCP集成**: 统一的MCP客户端和工具映射
6. **统一接口**: 统一的调用接口和并行支持

---

### 性能目标

| 指标 | 目标 |
|------|------|
| 工具调用延迟 | <100ms (P95) |
| 工具发现时间 | <50ms |
| 健康检查延迟 | <200ms |
| 并发调用支持 | >10 QPS |

---

### 下一步工作

1. ✅ 架构设计（本文档）
2. ⏳ 工具配置实施
3. ⏳ Skill集成实施
4. ⏳ MCP集成实施
5. ⏳ 统一接口实施
6. ⏳ 测试和文档

---

**End of Document**
