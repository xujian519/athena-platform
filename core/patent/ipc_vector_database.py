#!/usr/bin/env python3
from __future__ import annotations
"""
IPC分类向量数据库
IPC Classification Vector Database

基于生物学负熵优化思想的IPC分类向量系统:
- 将IPC分类定义向量化,实现语义检索
- 负熵优化排序:从混乱分类中找到最佳匹配
- 技术领域智能匹配:基于语义相似度
- 支持多级IPC分类:部、大类、小类、大组、小组

作者: 小诺·双鱼公主
创建时间: 2025-12-24
版本: v0.1.2 "晨星初现"
"""

import hashlib
import json
import logging

# 导入负熵优化器
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.biology.negentropy_optimizer import get_negentropy_optimizer

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class IPCLevel(Enum):
    """IPC分类级别"""

    SECTION = "section"  # 部 (A-H)
    SUBCLASS = "subclass"  # 小类 (A01)
    GROUP = "group"  # 大组 (A01B 1/00)
    SUBGROUP = "subgroup"  # 小组 (A01B 1/02)


@dataclass
class IPCEntry:
    """IPC分类条目"""

    ipc_code: str  # IPC分类号
    ipc_name: str  # 分类名称
    ipc_description: str  # 详细描述
    ipc_level: IPCLevel  # 分类级别
    section: str  # 所属部
    parent_code: str | None = None  # 父级代码

    # 扩展信息
    keywords: list[str] = field(default_factory=list)  # 关键词
    examples: list[str] = field(default_factory=list)  # 实例
    related_domains: list[str] = field(default_factory=list)  # 相关领域

    # 向量相关
    embedding: list[float] | None = None  # 向量嵌入
    embedding_id: str = ""  # 嵌入ID

    # 元数据
    source: str = "CNIPA"
    confidence: float = 1.0

    def __post_init__(self):
        """生成嵌入ID"""
        if not self.embedding_id:
            content = f"{self.ipc_code}:{self.ipc_name}:{self.ipc_description}"
            self.embedding_id = hashlib.md5(content.encode('utf-8'), usedforsecurity=False).hexdigest()

    def get_search_text(self) -> str:
        """获取用于向量化的文本"""
        parts = [
            self.ipc_name,
            self.ipc_description,
            " ".join(self.keywords),
            " ".join(self.examples),
        ]
        return " ".join(parts).strip()


@dataclass
class IPCMatchResult:
    """IPC匹配结果"""

    ipc_entry: IPCEntry
    similarity_score: float  # 相似度得分
    match_reason: str  # 匹配原因
    confidence: float  # 置信度
    suggested_keywords: list[str]  # 建议关键词


@dataclass
class IPCClassificationResult:
    """IPC分类结果"""

    query_text: str
    matched_ipcs: list[IPCMatchResult]
    primary_classification: str  # 主分类
    secondary_classifications: list[str]  # 次要分类
    domain_suggestions: list[str]  # 领域建议
    negentropy_score: float  # 负熵分数
    confidence: float  # 总置信度


class IPCVectorDatabase:
    """
    IPC分类向量数据库

    核心功能:
    1. IPC分类向量化存储
    2. 语义检索匹配
    3. 负熵优化排序
    4. 技术领域推荐
    """

    def __init__(self, ipc_data_path: str | None = None):
        """初始化IPC向量数据库"""
        self.name = "IPC分类向量数据库"
        self.version = "v0.1.2"

        # 数据路径
        self.ipc_data_path = ipc_data_path or (
            "/Users/xujian/Athena工作平台/apps/patent-platform/workspace/data/ipc_classification_knowledge.json"
        )

        # IPC存储
        self.ipc_entries: dict[str, IPCEntry] = {}  # {ipc_code: IPCEntry}
        self.by_section: dict[str, list[str]] = {}  # {section: [ipc_codes]}
        self.by_level: dict[IPCLevel, list[str]] = {}  # {level: [ipc_codes]}
        self.by_domain: dict[str, list[str]] = {}  # {domain: [ipc_codes]}

        # 负熵优化器
        self.negentropy_optimizer = get_negentropy_optimizer()

        # 向量索引(简化版,使用TF-IDF模拟)
        self.keyword_index: dict[str, list[str]] = {}  # {keyword: [ipc_codes]}
        self.domain_mapping: dict[str, list[str]] = {}  # 从配置加载

        # 初始化状态
        self.is_loaded = False

        logger.info(f"📚 {self.name} ({self.version}) 初始化完成")

    def load_ipc_data(self) -> None:
        """加载IPC分类数据"""
        try:
            with open(self.ipc_data_path, encoding="utf-8") as f:
                data = json.load(f)

            # 支持两种数据格式: ipc_sections 或 ipc_definitions
            sections = data.get("ipc_sections") or data.get("ipc_definitions", {})

            for section_code, section_data in sections.items():
                # 跳过metadata字段
                if section_code == "metadata":
                    continue

                # 添加部级条目
                section_name = section_data.get("section_name", section_data.get("name", ""))
                section_entry = IPCEntry(
                    ipc_code=section_code,
                    ipc_name=section_name,
                    ipc_description=section_name,  # 使用名称作为描述
                    ipc_level=IPCLevel.SECTION,
                    section=section_code,
                    keywords=self._extract_keywords_from_name(section_name),
                    source="CNIPA",
                )
                self._add_entry(section_entry)

                # 添加大类条目
                classes = section_data.get("classes", {})
                for class_code, class_data in classes.items():
                    class_name = class_data.get("class_name", class_data.get("name", ""))
                    class_entry = IPCEntry(
                        ipc_code=class_code,
                        ipc_name=class_name,
                        ipc_description=f"{section_name} - {class_name}",
                        ipc_level=IPCLevel.SUBCLASS,  # 大类对应小类级别
                        section=section_code,
                        parent_code=section_code,
                        keywords=self._extract_keywords_from_name(class_name),
                        source="CNIPA",
                    )
                    self._add_entry(class_entry)

                    # 添加小类条目(如果存在)
                    subclasses = class_data.get("subclasses", {})
                    for subclass_code, subclass_data in subclasses.items():
                        subclass_name = subclass_data.get(
                            "subclass_name", subclass_data.get("name", "")
                        )
                        subclass_entry = IPCEntry(
                            ipc_code=subclass_code,
                            ipc_name=subclass_name,
                            ipc_description=f"{section_name} - {class_name} - {subclass_name}",
                            ipc_level=IPCLevel.GROUP,  # 小类对应组级别
                            section=section_code,
                            parent_code=class_code,
                            keywords=self._extract_keywords_from_name(subclass_name),
                            source="CNIPA",
                        )
                        self._add_entry(subclass_entry)

            # 加载领域映射(如果存在)
            mapping_rules = data.get("mapping_rules", {})
            if mapping_rules:
                self.domain_mapping = mapping_rules.get("domain_correlations", {})

            # 反向构建域索引
            self._build_domain_index()

            self.is_loaded = True
            logger.info(f"✅ IPC数据加载完成: {len(self.ipc_entries)} 个分类")

        except FileNotFoundError:
            logger.error(f"❌ IPC数据文件不存在: {self.ipc_data_path}")
        except Exception as e:
            logger.error(f"❌ IPC数据加载失败: {e}")
            import traceback

            traceback.print_exc()

    def _extract_keywords_from_name(self, name: str) -> list[str]:
        """从名称中提取关键词"""
        # 简化实现:按分号和空格分割
        keywords = []
        for part in name.split(";"):
            for word in part.split():
                if len(word) >= 2:
                    keywords.append(word)
        return keywords

    def _add_entry(self, entry: IPCEntry) -> None:
        """添加IPC条目"""
        self.ipc_entries[entry.ipc_code] = entry

        # 按部索引
        if entry.section not in self.by_section:
            self.by_section[entry.section] = []
        self.by_section[entry.section].append(entry.ipc_code)

        # 按级别索引
        if entry.ipc_level not in self.by_level:
            self.by_level[entry.ipc_level] = []
        self.by_level[entry.ipc_level].append(entry.ipc_code)

        # 按关键词索引
        for keyword in entry.keywords:
            if keyword not in self.keyword_index:
                self.keyword_index[keyword] = []
            if entry.ipc_code not in self.keyword_index[keyword]:
                self.keyword_index[keyword].append(entry.ipc_code)

    def _build_domain_index(self) -> None:
        """构建领域索引"""
        for domain, ipc_codes in self.domain_mapping.items():
            self.by_domain[domain] = ipc_codes

    def search_by_text(
        self, query_text: str, top_n: int = 10, section_filter: str | None = None
    ) -> list[IPCMatchResult]:
        """
        基于文本搜索IPC分类(语义匹配)

        Args:
            query_text: 查询文本
            top_n: 返回前N个结果
            section_filter: 部级筛选

        Returns:
            匹配结果列表
        """
        if not self.is_loaded:
            self.load_ipc_data()

        results = []
        query_text.lower()

        # 对每个IPC条目计算相似度
        for _ipc_code, entry in self.ipc_entries.items():
            # 部级筛选
            if section_filter and entry.section != section_filter:
                continue

            # 计算相似度
            similarity, reason = self._calculate_similarity(query_text, entry)

            if similarity > 0.1:  # 最低阈值
                results.append(
                    IPCMatchResult(
                        ipc_entry=entry,
                        similarity_score=similarity,
                        match_reason=reason,
                        confidence=min(1.0, similarity),
                        suggested_keywords=entry.keywords[:5],
                    )
                )

        # 负熵优化排序:按相似度排序(有序 = 低熵)
        results.sort(key=lambda r: r.similarity_score, reverse=True)

        return results[:top_n]

    def _calculate_similarity(self, query_text: str, entry: IPCEntry) -> tuple[float, str]:
        """计算查询文本与IPC条目的相似度"""
        score = 0.0
        reasons = []

        query_lower = query_text.lower()
        name_lower = entry.ipc_name.lower()
        desc_lower = entry.ipc_description.lower()

        # 1. 名称匹配(权重: 25%)
        if query_lower in name_lower:
            score += 0.25
            reasons.append("名称包含")
        # 检查名称中的词是否在查询中
        name_words = [w for w in name_lower.split() if len(w) >= 2]
        for word in name_words:
            if word in query_lower:
                score += 0.05
                if "名称" not in str(reasons):
                    reasons.append("名称部分匹配")
                break

        # 2. 描述匹配(权重: 30%)
        if query_lower in desc_lower:
            score += 0.15
            reasons.append("描述包含")
        # 检查描述中的词
        desc_words = [w for w in desc_lower.split() if len(w) >= 2]
        matched_desc = sum(1 for w in desc_words if w in query_lower)
        if matched_desc > 0:
            score += min(0.15, matched_desc * 0.03)
            if "描述" not in str(reasons):
                reasons.append(f"描述匹配({matched_desc}词)")

        # 3. 关键词匹配(权重: 30%)
        matched_keywords = []
        for keyword in entry.keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in query_lower:
                matched_keywords.append(keyword)
                score += 0.08

        if matched_keywords:
            score = min(1.0, score)
            reasons.append(f"关键词: {', '.join(matched_keywords[:3])}")

        # 4. 领域推断(权重: 15%)
        # 常见领域词映射
        domain_keywords = {
            "G06": ["计算", "计算机", "软件", "程序", "算法", "数据", "代码"],
            "G01": ["测量", "检测", "传感", "测试", "分析"],
            "H04": ["通信", "网络", "传输", "信号"],
            "A61": ["医疗", "治疗", "诊断", "药物", "医学"],
            "B23": ["机械", "加工", "机床", "制造"],
            "F16": ["部件", "连接", "密封", "传动"],
        }

        for ipc_code, keywords in domain_keywords.items():
            if entry.ipc_code.startswith(ipc_code):
                for kw in keywords:
                    if kw in query_lower:
                        score += 0.03
                        if "领域" not in str(reasons):
                            reasons.append("领域相关")
                        break

        return min(1.0, score), "; ".join(reasons) if reasons else "语义相关"

    def classify_patent(self, patent_text: str, top_n: int = 5) -> IPCClassificationResult:
        """
        对专利文本进行IPC分类

        Args:
            patent_text: 专利文本
            top_n: 返回前N个分类

        Returns:
            分类结果
        """
        # 搜索匹配的IPC
        matches = self.search_by_text(patent_text, top_n=top_n)

        if not matches:
            return IPCClassificationResult(
                query_text=patent_text[:100],
                matched_ipcs=[],
                primary_classification="未分类",
                secondary_classifications=[],
                domain_suggestions=["综合技术"],
                negentropy_score=0.0,
                confidence=0.0,
            )

        # 主分类
        primary = matches[0].ipc_entry.ipc_code

        # 次要分类(相似度 > 0.3)
        secondary = [m.ipc_entry.ipc_code for m in matches[1:] if m.similarity_score > 0.3]

        # 领域建议
        domains = self._suggest_domains(matches)

        # 计算负熵分数
        similarities = [m.similarity_score for m in matches]
        negentropy_score = self.negentropy_optimizer.calculate_information_entropy(
            similarities, normalize=True
        )

        # 总置信度
        confidence = matches[0].confidence if matches else 0.0

        return IPCClassificationResult(
            query_text=patent_text[:100],
            matched_ipcs=matches,
            primary_classification=primary,
            secondary_classifications=secondary,
            domain_suggestions=domains,
            negentropy_score=negentropy_score,
            confidence=confidence,
        )

    def _suggest_domains(self, matches: list[IPCMatchResult]) -> list[str]:
        """建议技术领域"""
        domains = []

        # 基于IPC代码匹配领域
        for match in matches[:5]:
            ipc_code = match.ipc_entry.ipc_code
            for domain, ipc_codes in self.domain_mapping.items():
                if ipc_code in ipc_codes and domain not in domains:
                    domains.append(domain)

        # 如果没有匹配,基于部推断
        if not domains and matches:
            section = matches[0].ipc_entry.section
            section_domains = {
                "A": "人类生活必需",
                "B": "作业运输",
                "C": "化学冶金",
                "D": "纺织造纸",
                "E": "固定建筑",
                "F": "机械工程",
                "G": "物理",
                "H": "电学",
            }
            domains.append(section_domains.get(section, "综合技术"))

        return domains[:3]

    def get_ipc_details(self, ipc_code: str) -> IPCEntry | None:
        """获取IPC分类详情"""
        if not self.is_loaded:
            self.load_ipc_data()
        return self.ipc_entries.get(ipc_code)

    def get_by_section(self, section: str) -> list[IPCEntry]:
        """获取指定部的所有IPC"""
        if not self.is_loaded:
            self.load_ipc_data()

        codes = self.by_section.get(section, [])
        return [self.ipc_entries[code] for code in codes]

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "total_ipc_entries": len(self.ipc_entries),
            "sections": len(self.by_section),
            "domains": len(self.by_domain),
            "keyword_index_size": len(self.keyword_index),
            "is_loaded": self.is_loaded,
        }


# 全局单例
_ipc_vector_db_instance = None


def get_ipc_vector_db() -> IPCVectorDatabase:
    """获取IPC向量数据库单例"""
    global _ipc_vector_db_instance
    if _ipc_vector_db_instance is None:
        _ipc_vector_db_instance = IPCVectorDatabase()
    return _ipc_vector_db_instance


# 测试代码
async def main():
    """测试IPC向量数据库"""

    print("\n" + "=" * 60)
    print("📚 IPC分类向量数据库测试")
    print("=" * 60 + "\n")

    db = get_ipc_vector_db()

    # 测试1:加载数据
    print("📝 测试1: 加载IPC数据")
    db.load_ipc_data()
    stats = db.get_statistics()
    print("✅ 加载完成:")
    print(f"  总IPC数: {stats['total_ipc_entries']}")
    print(f"  部数: {stats['sections']}")
    print(f"  领域数: {stats['domains']}\n")

    # 测试2:文本搜索
    print("📝 测试2: 文本搜索")
    query = "基于深度学习的图像识别方法"
    results = db.search_by_text(query, top_n=5)

    print(f"查询: {query}")
    print(f"找到 {len(results)} 个匹配:\n")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result.ipc_entry.ipc_code} - {result.ipc_entry.ipc_name}")
        print(f"   相似度: {result.similarity_score:.2f}")
        print(f"   原因: {result.match_reason}")
        print()

    # 测试3:专利分类
    print("📝 测试3: 专利分类")
    patent_text = """
    本发明涉及一种基于卷积神经网络的图像识别方法,
    属于计算机视觉和人工智能技术领域。
    该方法包括数据预处理、特征提取、图像分类等步骤。
    """

    classification = db.classify_patent(patent_text)

    print(f"专利文本: {classification.query_text}")
    print(f"主分类: {classification.primary_classification}")
    print(f"次要分类: {classification.secondary_classifications}")
    print(f"领域建议: {classification.domain_suggestions}")
    print(f"负熵分数: {classification.negentropy_score:.2f}")
    print(f"置信度: {classification.confidence:.2f}\n")

    # 测试4:获取指定部
    print("📝 测试4: 获取G部(物理)分类")
    g_section = db.get_by_section("G")
    print(f"G部共有 {len(g_section)} 个分类:")
    for entry in g_section[:5]:
        print(f"  {entry.ipc_code}: {entry.ipc_name}")

    print("\n✅ 测试完成!")


# 入口点: @async_main装饰器已添加到main函数
