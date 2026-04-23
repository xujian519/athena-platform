#!/usr/bin/env python3
"""
知识库管理器
Knowledge Base Manager

增强的知识库与工具管理系统

作者: 小娜·天秤女神
创建时间: 2024年12月15日
"""

import asyncio
import hashlib
import json
import logging
import pickle
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)

class KnowledgeType(Enum):
    """知识类型"""
    LEGAL_RULE = "legal_rule"
    CASE_LAW = "case_law"
    PROCEDURE = "procedure"
    TEMPLATE = "template"
    REGULATION = "regulation"
    BEST_PRACTICE = "best_practice"
    EXPERT_INSIGHT = "expert_insight"
    TECHNICAL_GUIDE = "technical_guide"

class ToolType(Enum):
    """工具类型"""
    SEARCH = "search"
    ANALYSIS = "analysis"
    GENERATION = "generation"
    VALIDATION = "validation"
    CALCULATION = "calculation"
    TRANSLATION = "translation"
    CONVERSION = "conversion"

@dataclass
class KnowledgeItem:
    """知识条目"""
    item_id: str
    type: KnowledgeType
    title: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    source: str = ""
    confidence: float = 1.0
    last_updated: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    rating: float = 0.0

@dataclass
class Tool:
    """工具"""
    tool_id: str
    name: str
    type: ToolType
    description: str
    function: Callable
    parameters: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    usage_count: int = 0

class KnowledgeBaseManager:
    """知识库管理器"""

    def __init__(self):
        """初始化管理器"""
        self.name = "小娜知识库管理器"
        self.version = "v2.0"

        # 存储路径
        self.knowledge_dir = Path("/Users/xujian/Athena工作平台/data/knowledge_base")
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)

        # 知识存储
        self.knowledge_store = {}
        self.knowledge_index = {}
        self.tool_registry = {}
        self.usage_logs = []

        # 数据文件
        self.knowledge_file = self.knowledge_dir / "knowledge_store.pkl"
        self.index_file = self.knowledge_dir / "knowledge_index.json"
        self.tools_file = self.knowledge_dir / "tools_registry.json"
        self.usage_file = self.knowledge_dir / "usage_logs.json"

        # 外部数据源
        self.external_sources = {
            "patent_law": {
                "url": "http://localhost:8002/query",
                "type": "vector_kg",
                "enabled": True
            },
            "legal_database": {
                "url": "http://localhost:8003/legal/search",
                "type": "api",
                "enabled": True
            }
        }

        # 缓存
        self.cache = {}
        self.cache_ttl = 3600  # 1小时

        self.initialized = False

    async def initialize(self):
        """初始化管理器"""
        try:
            # 加载知识库
            await self._load_knowledge_base()

            # 构建索引
            await self._build_index()

            # 加载工具
            await self._load_tools()

            # 初始化外部连接
            await self._initialize_external_connections()

            # 启动定期同步任务
            asyncio.create_task(self._periodic_sync())

            self.initialized = True
            logger.info("✅ 知识库管理器初始化完成")

        except Exception as e:
            logger.error(f"❌ 知识库管理器初始化失败: {str(e)}")
            self.initialized = True  # 使用默认配置

    async def add_knowledge(self, knowledge_data: dict[str, Any]) -> dict[str, Any]:
        """
        添加知识

        Args:
            knowledge_data: 知识数据
            {
                "type": "legal_rule|case_law|procedure|...",
                "title": "知识标题",
                "content": "知识内容",
                "metadata": {"author": "...", "version": "..."},
                "tags": ["标签1", "标签2"],
                "source": "来源",
                "confidence": 0.9
            }

        Returns:
            添加结果
        """
        try:
            # 创建知识条目
            item = KnowledgeItem(
                item_id=f"KB_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
                type=KnowledgeType(knowledge_data.get("type", "legal_rule")),
                title=knowledge_data.get("title", ""),
                content=knowledge_data.get("content", ""),
                metadata=knowledge_data.get("metadata", {}),
                tags=knowledge_data.get("tags", []),
                source=knowledge_data.get("source", "internal"),
                confidence=knowledge_data.get("confidence", 1.0)
            )

            # 存储知识
            self.knowledge_store[item.item_id] = item

            # 更新索引
            await self._update_index(item)

            # 保存到磁盘
            await self._save_knowledge_base()

            # 清除相关缓存
            await self._invalidate_cache(item.type)

            logger.info(f"✅ 知识已添加: {item.item_id}")

            return {
                "success": True,
                "item_id": item.item_id,
                "title": item.title,
                "type": item.type.value
            }

        except Exception as e:
            logger.error(f"❌ 添加知识失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def search_knowledge(self, query: str, knowledge_type: str | None = None,
                             filters: dict[str, Any] | None = None,
                             limit: int = 10) -> list[dict[str, Any]:
        """
        搜索知识

        Args:
            query: 搜索查询
            knowledge_type: 知识类型（可选）
            filters: 过滤条件（可选）
            limit: 返回数量限制

        Returns:
            搜索结果
        """
        try:
            # 检查缓存
            cache_key = await self._generate_cache_key(query, knowledge_type, filters)
            if cache_key in self.cache:
                cached_result = self.cache[cache_key]
                if (datetime.now() - cached_result["timestamp"]).seconds < self.cache_ttl:
                    return cached_result["results"]

            # 执行搜索
            results = await self._perform_search(query, knowledge_type, filters, limit)

            # 记录使用日志
            await self._log_usage("search", {
                "query": query,
                "type": knowledge_type,
                "filters": filters,
                "result_count": len(results)
            })

            # 缓存结果
            self.cache[cache_key] = {
                "results": results,
                "timestamp": datetime.now()
            }

            return results

        except Exception as e:
            logger.error(f"❌ 搜索知识失败: {str(e)}")
            return []

    async def _perform_search(self, query: str, knowledge_type: str | None,
                            filters: dict[str, Any] | None, limit: int) -> list[dict[str, Any]:
        """执行搜索"""
        results = []

        # 文本搜索
        text_results = await self._text_search(query, knowledge_type, filters)
        results.extend(text_results)

        # 语义搜索（如果配置了外部向量库）
        if self.external_sources.get("patent_law", {}).get("enabled"):
            semantic_results = await self._semantic_search(query, knowledge_type)
            # 合并并去重
            results = await self._merge_results(results, semantic_results)

        # 排序
        results = await self._rank_results(results, query)

        return results[:limit]

    async def _text_search(self, query: str, knowledge_type: str | None,
                         filters: dict[str, Any] | None) -> list[dict[str, Any]:
        """文本搜索"""
        results = []
        query_lower = query.lower()

        for item in self.knowledge_store.values():
            # 类型过滤
            if knowledge_type and item.type.value != knowledge_type:
                continue

            # 标签过滤
            if filters and "tags" in filters:
                if not any(tag in item.tags for tag in filters["tags"]):
                    continue

            # 内容匹配
            score = 0.0
            if query_lower in item.title.lower():
                score += 0.5
            if query_lower in item.content.lower():
                score += 0.3
            if any(query_lower in tag.lower() for tag in item.tags):
                score += 0.2

            if score > 0:
                results.append({
                    "item_id": item.item_id,
                    "type": item.type.value,
                    "title": item.title,
                    "content": item.content[:200] + "..." if len(item.content) > 200 else item.content,
                    "score": score,
                    "confidence": item.confidence,
                    "tags": item.tags,
                    "source": item.source
                })

        return results

    async def _semantic_search(self, query: str, knowledge_type: str | None) -> list[dict[str, Any]:
        """语义搜索"""
        try:
            # 调用外部向量库
            source = self.external_sources["patent_law"]
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    source["url"],
                    json={
                        "query": query,
                        "type": "semantic",
                        "domain": "patent"
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        # 转换格式
                        results = []
                        for item in data.get("results", []):
                            results.append({
                                "item_id": f"VEC_{item.get('id', '')}",
                                "type": "vector_search",
                                "title": item.get("title", ""),
                                "content": item.get("content", "")[:200] + "...",
                                "score": item.get("score", 0),
                                "confidence": item.get("confidence", 0.8),
                                "source": "vector_knowledge_base"
                            })
                        return results

        except Exception as e:
            logger.error(f"语义搜索失败: {str(e)}")

        return []

    async def _merge_results(self, results1: list[dict[str, Any],
                          results2: list[dict[str, Any]) -> list[dict[str, Any]:
        """合并搜索结果"""
        # 简单合并，实际应该去重
        return results1 + results2

    async def _rank_results(self, results: list[dict[str, Any], query: str) -> list[dict[str, Any]:
        """排序结果"""
        # 按分数和置信度综合排序
        for result in results:
            result["final_score"] = result["score"] * result["confidence"]

        return sorted(results, key=lambda x: x["final_score"], reverse=True)

    async def register_tool(self, tool_data: dict[str, Any]) -> dict[str, Any]:
        """
        注册工具

        Args:
            tool_data: 工具数据
            {
                "name": "工具名称",
                "type": "search|analysis|generation|...",
                "description": "工具描述",
                "function": callable,
                "parameters": {"param1": {...}}
            }

        Returns:
            注册结果
        """
        try:
            tool = Tool(
                tool_id=f"TOOL_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
                name=tool_data.get("name", ""),
                type=ToolType(tool_data.get("type", "search")),
                description=tool_data.get("description", ""),
                function=tool_data.get("function"),
                parameters=tool_data.get("parameters", {}),
                enabled=tool_data.get("enabled", True)
            )

            self.tool_registry[tool.tool_id] = tool

            # 保存工具注册表
            await self._save_tools()

            logger.info(f"✅ 工具已注册: {tool.name}")

            return {
                "success": True,
                "tool_id": tool.tool_id,
                "name": tool.name
            }

        except Exception as e:
            logger.error(f"❌ 注册工具失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def use_tool(self, tool_id: str, parameters: dict[str, Any]) -> dict[str, Any]:
        """
        使用工具

        Args:
            tool_id: 工具ID
            parameters: 参数

        Returns:
            使用结果
        """
        try:
            if tool_id not in self.tool_registry:
                return {
                    "success": False,
                    "error": f"工具不存在: {tool_id}"
                }

            tool = self.tool_registry[tool_id]
            if not tool.enabled:
                return {
                    "success": False,
                    "error": "工具已禁用"
                }

            # 执行工具
            result = await tool.function(parameters)

            # 更新使用统计
            tool.usage_count += 1

            # 记录使用日志
            await self._log_usage("tool", {
                "tool_id": tool_id,
                "tool_name": tool.name,
                "parameters": parameters,
                "success": True
            })

            # 保存更新
            await self._save_tools()

            return {
                "success": True,
                "result": result,
                "tool_name": tool.name
            }

        except Exception as e:
            logger.error(f"❌ 使用工具失败: {str(e)}")
            await self._log_usage("tool", {
                "tool_id": tool_id,
                "parameters": parameters,
                "success": False,
                "error": str(e)
            })
            return {
                "success": False,
                "error": str(e)
            }

    async def get_knowledge_statistics(self) -> dict[str, Any]:
        """获取知识库统计"""
        try:
            stats = {
                "total_items": len(self.knowledge_store),
                "by_type": {},
                "total_tools": len(self.tool_registry),
                "tool_usage": {},
                "cache_size": len(self.cache),
                "external_sources": len(self.external_sources)
            }

            # 按类型统计
            for item in self.knowledge_store.values():
                type_name = item.type.value
                stats["by_type"][type_name] = stats["by_type"].get(type_name, 0) + 1

            # 工具使用统计
            for tool in self.tool_registry.values():
                stats["tool_usage"][tool.name] = tool.usage_count

            return stats

        except Exception as e:
            logger.error(f"获取统计失败: {str(e)}")
            return {}

    async def update_knowledge(self, item_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        """更新知识"""
        try:
            if item_id not in self.knowledge_store:
                return {
                    "success": False,
                    "error": f"知识条目不存在: {item_id}"
                }

            item = self.knowledge_store[item_id]

            # 更新字段
            if "title" in updates:
                item.title = updates["title"]
            if "content" in updates:
                item.content = updates["content"]
            if "tags" in updates:
                item.tags = updates["tags"]
            if "metadata" in updates:
                item.metadata.update(updates["metadata"])
            if "confidence" in updates:
                item.confidence = updates["confidence"]

            item.last_updated = datetime.now()

            # 更新索引
            await self._update_index(item)

            # 保存
            await self._save_knowledge_base()

            return {
                "success": True,
                "item_id": item_id,
                "updated_at": item.last_updated.isoformat()
            }

        except Exception as e:
            logger.error(f"更新知识失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def delete_knowledge(self, item_id: str) -> dict[str, Any]:
        """删除知识"""
        try:
            if item_id not in self.knowledge_store:
                return {
                    "success": False,
                    "error": f"知识条目不存在: {item_id}"
                }

            item = self.knowledge_store[item_id]
            del self.knowledge_store[item_id]

            # 从索引中删除
            await self._remove_from_index(item_id)

            # 保存
            await self._save_knowledge_base()

            # 清除缓存
            await self._invalidate_cache(item.type)

            logger.info(f"✅ 知识已删除: {item_id}")

            return {
                "success": True,
                "item_id": item_id
            }

        except Exception as e:
            logger.error(f"删除知识失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _load_knowledge_base(self):
        """加载知识库"""
        try:
            if self.knowledge_file.exists():
                with open(self.knowledge_file, 'rb') as f:
                    self.knowledge_store = pickle.load(f)
                logger.info(f"✅ 加载了 {len(self.knowledge_store)} 条知识")

        except Exception as e:
            logger.warning(f"加载知识库失败: {str(e)}")
            self.knowledge_store = {}

    async def _save_knowledge_base(self):
        """保存知识库"""
        try:
            with open(self.knowledge_file, 'wb') as f:
                pickle.dump(self.knowledge_store, f)
        except Exception as e:
            logger.error(f"保存知识库失败: {str(e)}")

    async def _build_index(self):
        """构建索引"""
        try:
            if self.index_file.exists():
                with open(self.index_file, encoding='utf-8') as f:
                    self.knowledge_index = json.load(f)

            # 重建缺失的索引
            for item_id, item in self.knowledge_store.items():
                if item_id not in self.knowledge_index:
                    await self._update_index(item)

        except Exception as e:
            logger.warning(f"构建索引失败: {str(e)}")
            self.knowledge_index = {}

    async def _update_index(self, item: KnowledgeItem):
        """更新索引"""
        # 创建关键词索引
        keywords = await self._extract_keywords(item.title + " " + item.content)

        self.knowledge_index[item.item_id] = {
            "keywords": keywords,
            "type": item.type.value,
            "tags": item.tags,
            "last_updated": item.last_updated.isoformat()
        }

        # 保存索引
        await self._save_index()

    async def _remove_from_index(self, item_id: str):
        """从索引中删除"""
        if item_id in self.knowledge_index:
            del self.knowledge_index[item_id]
            await self._save_index()

    async def _save_index(self):
        """保存索引"""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.knowledge_index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存索引失败: {str(e)}")

    async def _load_tools(self):
        """加载工具"""
        try:
            if self.tools_file.exists():
                with open(self.tools_file, encoding='utf-8') as f:
                    tools_data = json.load(f)
                    # 注意：function 无法序列化，需要重新注册
                    logger.info(f"工具配置已加载，需重新注册 {len(tools_data)} 个工具")

            # 注册内置工具
            await self._register_builtin_tools()

        except Exception as e:
            logger.warning(f"加载工具失败: {str(e)}")
            await self._register_builtin_tools()

    async def _save_tools(self):
        """保存工具"""
        try:
            tools_data = {}
            for tool_id, tool in self.tool_registry.items():
                tools_data[tool_id] = {
                    "name": tool.name,
                    "type": tool.type.value,
                    "description": tool.description,
                    "parameters": tool.parameters,
                    "enabled": tool.enabled,
                    "usage_count": tool.usage_count
                }
            with open(self.tools_file, 'w', encoding='utf-8') as f:
                json.dump(tools_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存工具失败: {str(e)}")

    async def _register_builtin_tools(self):
        """注册内置工具"""
        # 文档生成工具
        await self.register_tool({
            "name": "文档生成器",
            "type": "generation",
            "description": "生成法律文档",
            "function": self._generate_document,
            "parameters": {
                "template": "文档模板",
                "data": "文档数据"
            }
        })

        # 日期计算工具
        await self.register_tool({
            "name": "日期计算器",
            "type": "calculation",
            "description": "计算法律期限",
            "function": self._calculate_legal_dates,
            "parameters": {
                "start_date": "开始日期",
                "duration": "期限"
            }
        })

        # 费用估算工具
        await self.register_tool({
            "name": "费用估算器",
            "type": "calculation",
            "description": "估算专利申请费用",
            "function": self._estimate_patent_costs,
            "parameters": {
                "patent_type": "专利类型",
                "complexity": "复杂度"
            }
        })

    async def _initialize_external_connections(self):
        """初始化外部连接"""
        # 测试外部连接
        for source_name, source in self.external_sources.items():
            if source.get("enabled"):
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(source["url"], timeout=5) as response:
                            if response.status == 200:
                                logger.info(f"✅ 外部数据源已连接: {source_name}")
                            else:
                                logger.warning(f"⚠️ 外部数据源响应异常: {source_name}")
                except Exception as e:
                    logger.warning(f"⚠️ 无法连接外部数据源: {source_name} - {str(e)}")

    async def _generate_document(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """生成文档（内置工具）"""
        template = parameters.get("template", "default")
        data = parameters.get("data", {})

        # 简化实现
        document = f"基于模板 {template} 生成的文档\n数据: {data}"

        return {
            "document": document,
            "format": "text"
        }

    async def _calculate_legal_dates(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """计算法律日期（内置工具）"""
        start_date = parameters.get("start_date", datetime.now().isoformat())
        duration = parameters.get("duration", 30)  # 天

        start = datetime.fromisoformat(start_date)
        end = start + timedelta(days=duration)

        return {
            "start_date": start_date,
            "end_date": end.isoformat(),
            "duration_days": duration
        }

    async def _estimate_patent_costs(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """估算专利费用（内置工具）"""
        patent_type = parameters.get("patent_type", "invention")
        complexity = parameters.get("complexity", "medium")

        base_costs = {
            "invention": {"low": 5000, "medium": 10000, "high": 20000},
            "utility_model": {"low": 2000, "medium": 4000, "high": 8000},
            "design": {"low": 1500, "medium": 3000, "high": 6000}
        }

        estimated_cost = base_costs.get(patent_type, {}).get(complexity, 10000)

        return {
            "estimated_cost": estimated_cost,
            "currency": "CNY",
            "patent_type": patent_type,
            "complexity": complexity
        }

    async def _extract_keywords(self, text: str) -> list[str]:
        """提取关键词"""
        # 简化的关键词提取
        stop_words = ["的", "了", "是", "在", "和", "与", "或"]
        words = text.split()
        keywords = []

        for word in words:
            if len(word) > 2 and word not in stop_words:
                keywords.append(word.lower())

        return list(set(keywords))

    async def _generate_cache_key(self, query: str, knowledge_type: str | None,
                                filters: dict[str, Any] | None) -> str:
        """生成缓存键"""
        key_data = f"{query}_{knowledge_type}_{filters or {}}"
        return hashlib.md5(key_data.encode(), usedforsecurity=False).hexdigest()

    async def _invalidate_cache(self, knowledge_type: KnowledgeType):
        """清除缓存"""
        keys_to_remove = []
        for key in self.cache:
            # 简化：清除所有缓存
            keys_to_remove.append(key)

        for key in keys_to_remove:
            del self.cache[key]

    async def _log_usage(self, usage_type: str, data: dict[str, Any]):
        """记录使用日志"""
        log_entry = {
            "type": usage_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        self.usage_logs.append(log_entry)

        # 限制日志大小
        if len(self.usage_logs) > 1000:
            self.usage_logs = self.usage_logs[-1000:]

        # 定期保存
        if len(self.usage_logs) % 100 == 0:
            await self._save_usage_logs()

    async def _save_usage_logs(self):
        """保存使用日志"""
        try:
            with open(self.usage_file, 'w', encoding='utf-8') as f:
                json.dump(self.usage_logs, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存使用日志失败: {str(e)}")

    async def _periodic_sync(self):
        """定期同步任务"""
        while True:
            try:
                # 每天执行一次
                await asyncio.sleep(86400)

                # 同步外部数据
                await self._sync_external_data()

                # 清理缓存
                await self._cleanup_cache()

                # 保存使用日志
                await self._save_usage_logs()

            except Exception as e:
                logger.error(f"定期同步失败: {str(e)}")

    async def _sync_external_data(self):
        """同步外部数据"""
        for source_name, source in self.external_sources.items():
            if source.get("enabled"):
                logger.info(f"同步外部数据源: {source_name}")
                # 实现同步逻辑

    async def _cleanup_cache(self):
        """清理缓存"""
        keys_to_remove = []
        current_time = datetime.now()

        for key, cached_item in self.cache.items():
            if (current_time - cached_item["timestamp"]).seconds > self.cache_ttl:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self.cache[key]

        logger.info(f"清理了 {len(keys_to_remove)} 个缓存项")

# 使用示例
async def main():
    """测试知识库管理器"""
    manager = KnowledgeBaseManager()
    await manager.initialize()

    # 添加知识
    result = await manager.add_knowledge({
        "type": "legal_rule",
        "title": "专利新颖性要求",
        "content": "专利的新颖性是指该发明不属于现有技术...",
        "tags": ["专利", "新颖性", "现有技术"],
        "source": "专利法",
        "confidence": 0.95
    })
    print(f"添加知识结果: {result}")

    # 搜索知识
    results = await manager.search_knowledge("专利新颖性", limit=5)
    print(f"搜索结果: {len(results)} 条")

    # 使用工具
    tool_result = await manager.use_tool(
        "TOOL_0001",  # 需要实际的工具ID
        {"template": "patent_application", "data": {"title": "测试专利"}}
    )
    print(f"工具使用结果: {tool_result}")

    # 获取统计
    stats = await manager.get_knowledge_statistics()
    print(f"知识库统计: {stats}")

# 入口点: @async_main装饰器已添加到main函数
