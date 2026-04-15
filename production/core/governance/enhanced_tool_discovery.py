#!/usr/bin/env python3
"""
增强工具发现模块
Enhanced Tool Discovery Module

提供智能工具发现功能,包括:
- 同义词扩展
- 模糊匹配
- 多关键词组合匹配
- 相关性评分

使用方法:
    from core.governance.enhanced_tool_discovery import EnhancedToolDiscovery

    discovery = EnhancedToolDiscovery(tool_metadata)
    results = await discovery.discover_tools("搜索专利", limit=10)
"""

from __future__ import annotations
import logging
import re
from collections import defaultdict
from difflib import SequenceMatcher
from typing import Any

logger = logging.getLogger(__name__)


# ================================
# 同义词词典
# ================================

SYNONYMS = {
    # 搜索相关
    "搜索": ["search", "query", "检索", "查找", "寻找", "searching", "find", "lookup", "retrieve"],
    "专利": ["patent", "知识产权", "ipr"],
    "法律": ["legal", "law", "法规", "条例", "司法"],
    "案例": ["case", "案例库", "判决", "裁定", "判决书"],
    "查找": ["search", "find", "query", "lookup", "locate"],
    "检索": ["search", "retrieve", "find", "lookup", "query"],
    "查询": ["search", "query", "find", "lookup", "retrieve"],
    # 分析相关
    "分析": ["analyze", "analysis", "研究", "评估", "evaluate", "examine", "investigate", "study"],
    "生成": ["generate", "create", "创建", "写作", "write", "produce", "make"],
    "处理": ["process", "handle", "执行", "execute", "do", "perform"],
    "评估": ["evaluate", "assess", "judge", "rate", "score"],
    "研究": ["research", "study", "investigate", "analyze"],
    # 数据相关
    "数据": ["data", "信息", "information"],
    "文档": ["document", "file", "文件"],
    "文本": ["text", "字符串", "string"],
    "内容": ["content", "内容物", "substance"],
    "信息": ["information", "info", "data", "消息"],
    # 服务相关
    "服务": ["service", "api", "接口"],
    "工具": ["tool", "utility", "函数", "function"],
    "模型": ["model", "算法", "algorithm"],
    "接口": ["interface", "api", "endpoint"],
    # 向量相关
    "向量": ["vector", "embedding", "嵌入"],
    "图谱": ["graph", "knowledge", "知识"],
    "语义": ["semantic", "meaning", "含义"],
    "嵌入": ["embedding", "vector", "向量"],
    # 智能体相关
    "智能体": ["agent", "智能", "ai", "bot"],
    "机器人": ["robot", "bot", "agent"],
    "助手": ["assistant", "helper", "aide"],
    # 任务相关
    "任务": ["task", "job", "work", "mission"],
    "工作": ["work", "job", "task"],
    "流程": ["process", "workflow", "pipeline"],
    # 系统相关
    "系统": ["system", "platform", "平台"],
    "平台": ["platform", "system"],
    "应用": ["application", "app", "程序"],
    # 网络相关
    "网络": ["network", "web", "internet"],
    "网页": ["webpage", "website", "page"],
    "爬虫": ["crawler", "spider", "scraper"],
    # 存储相关
    "存储": ["storage", "store", "save", "database", "db"],
    "数据库": ["database", "db", "datastore"],
    "缓存": ["cache", "buffer"],
    # 文件相关
    "文件": ["file", "document"],
    "读取": ["read", "load", "retrieve"],
    "写入": ["write", "save", "store"],
    # 通信相关
    "消息": ["message", "msg", "communication"],
    "通知": ["notification", "notify", "alert"],
    "发送": ["send", "transmit", "deliver"],
    # 配置相关
    "配置": ["config", "configuration", "setting", "settings"],
    "设置": ["setting", "configuration", "setup"],
    "参数": ["parameter", "param", "argument"],
    # 监控相关
    "监控": ["monitor", "watch", "track", "observe"],
    "日志": ["log", "logging", "record"],
    "统计": ["statistics", "stats", "metrics"],
    # 优化相关
    "优化": ["optimize", "optimization", "improve", "enhance"],
    "改进": ["improve", "enhance", "upgrade"],
    "提升": ["improve", "enhance", "boost"],
    # 测试相关
    "测试": ["test", "testing", "check", "verify"],
    "验证": ["verify", "validate", "confirm"],
    "检查": ["check", "inspect", "examine"],
    # 通用动词
    "运行": ["run", "execute", "start", "launch"],
    "停止": ["stop", "halt", "terminate"],
    "删除": ["delete", "remove", "erase"],
    "更新": ["update", "upgrade", "refresh"],
    "创建": ["create", "make", "build", "construct"],
    "获取": ["get", "obtain", "fetch", "retrieve"],
}


# ================================
# 增强工具发现器
# ================================


class EnhancedToolDiscovery:
    """增强工具发现器"""

    def __init__(self, tool_metadata: dict[str, Any]):
        """
        初始化增强工具发现器

        Args:
            tool_metadata: 工具元数据字典 {tool_id: ToolMetadata}
        """
        self.tool_metadata = tool_metadata

        # 加载中文标签
        self.tool_labels = self._load_chinese_labels()

        # 构建索引
        self._build_index()

    def _build_index(self) -> Any:
        """构建工具索引"""
        # 构建关键词索引
        self.keyword_index = defaultdict(list)

        for tool_id, metadata in self.tool_metadata.items():
            # 提取关键词
            keywords = self._extract_keywords(metadata)

            # 添加中文标签关键词
            if tool_id in self.tool_labels:
                keywords.update(self.tool_labels[tool_id])

            # 添加到索引
            for keyword in keywords:
                self.keyword_index[keyword].append(tool_id)

        logger.info(f"✅ 工具索引已构建,共 {len(self.keyword_index)} 个关键词")

    def _load_chinese_labels(self) -> dict[str, list[str]]:
        """
        加载中文工具标签

        Returns:
            工具ID到中文标签的映射
        """
        try:
            import importlib.util

            spec = importlib.util.spec_from_file_location(
                "tool_labels_zh", "core/governance/tool_labels_zh.py"
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            labels = module.TOOL_LABELS_ZH
            logger.info(f"✅ 已加载 {len(labels)} 个工具的中文标签")
            return labels
        except Exception as e:
            logger.warning(f"⚠️ 无法加载中文标签: {e}")
            return {}

    def _extract_keywords(self, metadata) -> set[str]:
        """
        从工具元数据中提取关键词

        Args:
            metadata: 工具元数据

        Returns:
            关键词集合
        """
        keywords = set()

        # 从名称提取
        if metadata.name:
            keywords.update(self._tokenize(metadata.name))

        # 从描述提取
        if metadata.description:
            keywords.update(self._tokenize(metadata.description))

        # 从能力提取
        for capability in metadata.capabilities:
            keywords.update(self._tokenize(capability))

        return keywords

    def _tokenize(self, text: str) -> set[str]:
        """
        分词并提取关键词

        Args:
            text: 输入文本

        Returns:
            关键词集合
        """
        # 转小写
        text = text.lower()

        # 移除特殊字符
        text = re.sub(r"[^\w\s\u4e00-\u9fff]", " ", text)

        # 分词
        words = text.split()

        # 过滤停用词
        stop_words = {"的", "是", "在", "和", "与", "或", "a", "an", "the", "of", "and", "or"}
        words = [w for w in words if len(w) > 1 and w not in stop_words]

        return set(words)

    def _expand_synonyms(self, query: str) -> set[str]:
        """
        同义词扩展

        Args:
            query: 查询文本

        Returns:
            扩展后的关键词集合
        """
        keywords = self._tokenize(query)
        expanded = set(keywords)

        # 添加同义词
        for keyword in keywords:
            if keyword in SYNONYMS:
                expanded.update(SYNONYMS[keyword])

            # 反向查找(查询可能是同义词)
            for main_word, synonyms in SYNONYMS.items():
                if keyword in synonyms:
                    expanded.add(main_word)
                    expanded.update(synonyms)

        return expanded

    def _fuzzy_match_score(self, text1: str, text2: str) -> float:
        """
        模糊匹配评分

        Args:
            text1: 文本1
            text2: 文本2

        Returns:
            相似度分数 (0.0 - 1.0)
        """
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

    async def discover_tools(
        self,
        query: str,
        limit: int = 10,
        category: str | None = None,
        enable_synonyms: bool = True,
        enable_fuzzy: bool = True,
    ) -> list[dict[str, Any]]:
        """
        智能工具发现

        Args:
            query: 查询描述
            limit: 返回数量限制
            category: 工具类别过滤
            enable_synonyms: 是否启用同义词扩展
            enable_fuzzy: 是否启用模糊匹配

        Returns:
            匹配的工具列表,按相关性排序
        """
        results = []

        # 同义词扩展(将中文查询扩展到英文关键词)
        keywords = self._expand_synonyms(query) if enable_synonyms else self._tokenize(query)

        logger.debug(f"查询: {query}, 扩展关键词: {keywords}")

        # 遍历所有工具
        for tool_id, metadata in self.tool_metadata.items():
            # 类别过滤
            if category and metadata.category.value != category:
                continue

            # 状态过滤
            if metadata.status.value != "available":
                continue

            # 计算相关性分数
            score = await self._calculate_relevance_score(query, keywords, metadata, enable_fuzzy)

            if score > 0:
                results.append(
                    {
                        "tool_id": tool_id,
                        "name": metadata.name,
                        "description": metadata.description,
                        "category": metadata.category.value,
                        "score": score,
                        "success_rate": metadata.success_rate,
                    }
                )

        # 按分数排序
        results.sort(key=lambda x: x["score"], reverse=True)

        logger.info(f"✅ 发现 {len(results)} 个相关工具(查询: {query})")

        return results[:limit]

    async def _calculate_relevance_score(
        self, query: str, keywords: set[str], metadata, enable_fuzzy: bool
    ) -> float:
        """
        计算相关性分数

        Args:
            query: 原始查询
            keywords: 扩展后的关键词
            metadata: 工具元数据
            enable_fuzzy: 是否启用模糊匹配

        Returns:
            相关性分数
        """
        score = 0.0
        tool_id = getattr(metadata, "tool_id", None)

        # 1. 精确关键词匹配(权重:0.5)
        for keyword in keywords:
            # 名称匹配
            if keyword in metadata.name.lower():
                score += 0.25

            # 描述匹配
            if keyword in metadata.description.lower():
                score += 0.15

            # 能力匹配
            for capability in metadata.capabilities:
                if keyword in capability.lower():
                    score += 0.1
                    break

            # 中文标签匹配(高优先级)
            if tool_id and tool_id in self.tool_labels:
                if keyword in self.tool_labels[tool_id]:
                    score += 0.3  # 中文标签匹配权重更高

        # 2. 模糊匹配(权重:0.3)
        if enable_fuzzy:
            query_lower = query.lower()

            # 与名称的模糊匹配
            fuzzy_name = self._fuzzy_match_score(query_lower, metadata.name.lower())
            if fuzzy_name > 0.6:  # 相似度阈值
                score += fuzzy_name * 0.15

            # 与描述的模糊匹配
            fuzzy_desc = self._fuzzy_match_score(query_lower, metadata.description.lower())
            if fuzzy_desc > 0.5:
                score += fuzzy_desc * 0.15

        # 3. 完整短语匹配(权重:0.2)
        if query.lower() in metadata.description.lower():
            score += 0.1

        # 4. 中文标签直接匹配(额外加分)
        if tool_id and tool_id in self.tool_labels:
            # 检查查询是否直接匹配中文标签
            query_lower = query.lower()
            for label in self.tool_labels[tool_id]:
                if query_lower in label.lower() or label.lower() in query_lower:
                    score += 0.5  # 直接匹配给予额外加分
                    break

        return score

    def get_discovery_stats(self) -> dict[str, Any]:
        """
        获取发现器统计信息

        Returns:
            统计信息字典
        """
        return {
            "total_tools": len(self.tool_metadata),
            "total_keywords": len(self.keyword_index),
            "avg_keywords_per_tool": (
                sum(len(v) for v in self.keyword_index.values()) / len(self.keyword_index)
                if self.keyword_index
                else 0
            ),
            "synonym_groups": len(SYNONYMS),
        }


# ================================
# 便捷函数
# ================================


async def discover_tools_enhanced(
    tool_metadata: dict[str, Any], query: str, limit: int = 10, **kwargs
) -> list[dict[str, Any]]:
    """
    增强工具发现的便捷函数

    Args:
        tool_metadata: 工具元数据字典
        query: 查询描述
        limit: 返回数量限制
        **kwargs: 其他参数

    Returns:
        匹配的工具列表
    """
    discovery = EnhancedToolDiscovery(tool_metadata)
    return await discovery.discover_tools(query, limit, **kwargs)
