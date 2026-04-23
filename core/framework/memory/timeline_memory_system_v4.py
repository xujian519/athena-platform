#!/usr/bin/env python3

"""
时间线记忆系统 v4.0 - 维特根斯坦版
Timeline Memory System v4.0 - Wittgenstein Edition

基于维特根斯坦《逻辑哲学论》的"事实总和"原理:
- 世界是事实的总和,而不是事物的总和
- 记忆应该记录事实及其逻辑关系,而不是孤立的事物
- 每个事实都有其确定性和边界

v4.0核心特性:
1. 事实关系映射 - 记录事实之间的逻辑关系
2. 不确定性标注 - 每个事实都有置信度
3. 逻辑结构提取 - 从事实中提取逻辑命题
4. 边界识别 - 明确知识的边界(不可说领域)

作者: 小诺·双鱼公主 v4.0
创建时间: 2025-12-25
版本: v4.0.0 "逻辑之光"
"""

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

sys.path.append(str(Path(__file__).parent.parent))

# 导入v4.0模块
from v4.uncertainty_quantifier import Confidence, UncertaintyQuantifier


class MemoryType(Enum):
    """记忆类型"""

    EPISODIC = "episodic"  # 情节记忆 - 事件、对话、经历
    SEMANTIC = "semantic"  # 语义记忆 - 事实、偏好、知识
    PROCEDURAL = "procedural"  # 程序记忆 - 技能、习惯、流程
    FACT_RELATION = "fact_relation"  # v4.0新增:事实关系


class FactRelationType(Enum):
    """v4.0新增:事实关系类型"""

    CAUSATION = "causation"  # 因果关系
    CORRELATION = "correlation"  # 相关关系
    TEMPORAL = "temporal"  # 时序关系
    LOGICAL = "logical"  # 逻辑关系
    HIERARCHICAL = "hierarchical"  # 层级关系
    CONTRADICTION = "contradiction"  # 矛盾关系


class FactBoundary(Enum):
    """v4.0新增:事实边界(基于维特根斯坦)"""

    SAYABLE = "sayable"  # 可说:逻辑和经验范围
    UNSAYABLE = "unsayable"  # 不可说:价值、伦理、美学
    UNCERTAIN = "uncertain"  # 不确定:边界模糊区域


@dataclass
class FactV4:
    """
    v4.0事实 - 基于维特根斯坦原则

    世界是事实的总和,不是事物的总和
    每个事实都有:
    - 确定性(置信度)
    - 逻辑关系(与其他事实的关系)
    - 边界(是否可说)
    """

    id: str
    type: MemoryType
    content: str
    confidence: Confidence  # v4.0:使用完整的置信度对象
    relations: list[dict]  # v4.0:与其他事实的关系
    boundary: FactBoundary  # v4.0:事实边界
    logical_structure: Optional[str] = None  # v4.0:逻辑结构(命题形式)
    created_at: datetime = field(default_factory=datetime.now)


class TimelineMemoryV4:
    """
    时间线记忆系统 v4.0 - 基于维特根斯坦原则

    核心改变:
    1. 从"记录事件"到"记录事实关系"
    2. 从"确定存储"到"标注不确定性"
    3. 从"孤立事物"到"逻辑网络"
    4. 从"无限扩展"到"明确边界"
    """

    def __init__(self, base_path: Optional[str] = None):
        """初始化记忆系统"""
        if base_path is None:
            base_path = "/Users/xujian/Athena工作平台/core/modules/memory/modules/memory/timeline_memories_v4"

        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

        # v4.0核心组件
        self.uncertainty_quantifier = UncertaintyQuantifier()

        # 记忆文件路径
        self.facts_file = self.base_path / "facts.jsonl"  # v4.0:事实存储
        self.relations_file = self.base_path / "relations.jsonl"  # v4.0:关系存储
        self.timeline_file = self.base_path / "complete_timeline.jsonl"
        self.index_file = self.base_path / "memory_index_v4.json"
        self.logical_graph_file = self.base_path / "logical_graph.json"  # v4.0:逻辑图谱

        # 初始化索引
        self._load_index()

        # 加载事实关系图谱
        self.fact_graph = self._load_fact_graph()

    def _load_index(self) -> Any:
        """加载记忆索引 - v4.0版本"""
        if self.index_file.exists():
            with open(self.index_file, encoding="utf-8") as f:
                self.index = json.load(f)
        else:
            self.index = {
                "total_facts": 0,
                "fact_types": {},
                "relations_count": 0,
                "average_confidence": 0.0,
                "boundary_distribution": {"sayable": 0, "unsayable": 0, "uncertain": 0},
                "date_range": {"earliest": None, "latest": None},
                "key_facts": [],
                "logical_structure_types": {},
                "last_updated": None,
            }
            self._save_index()

    def _save_index(self) -> Any:
        """保存索引 - v4.0版本"""
        self.index["last_updated"] = datetime.now().isoformat()
        with open(self.index_file, "w", encoding="utf-8") as f:
            json.dump(self.index, f, ensure_ascii=False, indent=2)

    def _load_fact_graph(self) -> dict:
        """加载事实关系图谱 - v4.0新增"""
        if self.logical_graph_file.exists():
            with open(self.logical_graph_file, encoding="utf-8") as f:
                return json.load(f)
        else:
            return {
                "nodes": {},  # 事实节点
                "edges": [],  # 关系边
                "logical_clusters": {},  # 逻辑聚类
            }

    def _save_fact_graph(self) -> Any:
        """保存事实关系图谱 - v4.0新增"""
        with open(self.logical_graph_file, "w", encoding="utf-8") as f:
            json.dump(self.fact_graph, f, ensure_ascii=False, indent=2)

    def add_fact(
        self,
        content: str,
        fact_type: MemoryType,
        evidence: Optional[list[str]] = None,
        confidence: float = 0.5,
        boundary: FactBoundary = FactBoundary.SAYABLE,
        source: Optional[str] = None,
        tags: Optional[list[str]] = None,
        related_facts: Optional[list[str]] = None,
    ) -> str:
        """
        v4.0新增:添加事实(而非事物)

        维特根斯坦原则:世界是事实的总和,不是事物的总和

        Args:
            content: 事实内容(命题形式)
            fact_type: 事实类型
            evidence: 支持证据
            confidence: 初始置信度
            boundary: 事实边界
            source: 来源
            tags: 标签
            related_facts: 相关事实ID列表

        Returns:
            事实ID
        """
        # v4.0:量化不确定性
        quantified_confidence = self.uncertainty_quantifier.quantify(
            claim=content, evidence=evidence or [], information_completeness=confidence
        )
        quantified_confidence.value = confidence

        fact_id = f"fact_{datetime.now().timestamp()}"

        fact = {
            "id": fact_id,
            "type": fact_type.value,
            "content": content,
            "confidence": {
                "value": quantified_confidence.value,
                "level": quantified_confidence.level.value,
                "evidence": quantified_confidence.evidence,
                "limitations": quantified_confidence.limitations,
            },
            "boundary": boundary.value,
            "logical_structure": self._extract_logical_structure(content),  # v4.0:提取逻辑结构
            "source": source,
            "tags": tags or [],
            "created_at": datetime.now().isoformat(),
            "relations": [],  # 将通过add_fact_relation添加
        }

        # 写入事实文件
        with open(self.facts_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(fact, ensure_ascii=False) + "\n")

        # 添加到图谱
        self.fact_graph["nodes"][fact_id] = fact

        # v4.0:建立事实关系
        if related_facts:
            for related_id in related_facts:
                self.add_fact_relation(
                    fact_id, related_id, FactRelationType.LOGICAL, confidence=0.7
                )

        # 更新索引
        self._update_index_for_fact(fact)

        self._save_index()
        self._save_fact_graph()

        return fact_id

    def _extract_logical_structure(self, content: str) -> Optional[str]:
        """
        v4.0新增:提取逻辑结构

        维特根斯坦:命题是现实的图像
        """
        content.lower()

        # 因果结构
        if any(word in content for word in ["因为", "由于", "导致", "所以"]):
            return "causation"

        # 条件结构
        if any(word in content for word in ["如果", "只要", "那么", "则"]):
            return "conditional"

        # 层级结构
        if any(word in content for word in ["包含", "属于", "是"]):
            return "hierarchical"

        # 对比结构
        if any(word in content for word in ["但是", "然而", "相反", "而"]):
            return "contrast"

        # 序列结构
        if any(word in content for word in ["首先", "然后", "最后", "接着"]):
            return "sequence"

        # 默认:原子命题
        return "atomic"

    def add_fact_relation(
        self,
        fact_id_1: str,
        fact_id_2: str,
        relation_type: FactRelationType,
        confidence: float = 0.7,
        evidence: Optional[list[str]] = None,
    ) -> str:
        """
        v4.0新增:添加事实关系

        维特根斯坦:事实之间有逻辑关系,形成逻辑网络
        """
        relation_id = f"rel_{fact_id_1}_{fact_id_2}_{relation_type.value}"

        relation = {
            "id": relation_id,
            "from_fact": fact_id_1,
            "to_fact": fact_id_2,
            "type": relation_type.value,
            "confidence": confidence,
            "evidence": evidence or [],
            "created_at": datetime.now().isoformat(),
        }

        # 写入关系文件
        with open(self.relations_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(relation, ensure_ascii=False) + "\n")

        # 添加到图谱
        self.fact_graph["edges"].append(relation)

        # 更新索引
        self.index["relations_count"] += 1

        self._save_index()
        self._save_fact_graph()

        return relation_id

    def _update_index_for_fact(self, fact: dict) -> Any:
        """更新索引 - v4.0版本"""
        self.index["total_facts"] += 1

        # 更新类型统计
        fact_type = fact["type"]
        self.index["fact_types"][fact_type] = self.index["fact_types"].get(fact_type, 0) + 1

        # 更新平均置信度
        current_avg = self.index["average_confidence"]
        current_count = self.index["total_facts"]
        fact_confidence = fact["confidence"]["value"]
        self.index["average_confidence"] = (
            current_avg * (current_count - 1) + fact_confidence
        ) / current_count

        # 更新边界分布
        boundary = fact["boundary"]
        self.index["boundary_distribution"][boundary] = (
            self.index["boundary_distribution"].get(boundary, 0) + 1
        )

        # 更新逻辑结构类型
        logical_structure = fact.get("logical_structure", "unknown")
        self.index["logical_structure_types"][logical_structure] = (
            self.index["logical_structure_types"].get(logical_structure, 0) + 1
        )

    def add_episodic_memory(
        self,
        title: str,
        content: str,
        event_date: Optional[str] = None,
        participants: Optional[list[str]] = None,
        tags: Optional[list[str]] = None,
        emotional_weight: float = 0.5,
        key_event: bool = False,
        confidence: float = 0.8,  # v4.0新增
    ) -> str:
        """
        添加情节记忆 - v4.0版本

        v4.0改变:情节记忆也作为事实存储,包含置信度
        """
        if event_date is None:
            event_date = datetime.now().isoformat()
        if participants is None:
            participants = ["徐健"]
        if tags is None:
            tags = []

        # v4.0:将情节记忆转化为事实
        fact_content = f"事件:{title}。{content}"

        # 判断边界
        boundary = FactBoundary.SAYABLE
        if any(keyword in content.lower() for keyword in ["感受", "体验", "情感", "心情", "情绪"]):
            boundary = FactBoundary.UNSAYABLE

        fact_id = self.add_fact(
            content=fact_content,
            fact_type=MemoryType.EPISODIC,
            evidence=[f"参与者: {', '.join(participants)}"],
            confidence=confidence,
            boundary=boundary,
            source=f"情节记忆: {title}",
            tags=[*tags, "episodic"],
        )

        # 额外保存情节特定的信息
        episodic_data = {
            "fact_id": fact_id,
            "title": title,
            "event_date": event_date,
            "participants": participants,
            "emotional_weight": emotional_weight,
            "key_event": key_event,
        }

        # 写入时间线
        with open(self.timeline_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(episodic_data, ensure_ascii=False) + "\n")

        if key_event:
            self.index["key_facts"].append({"id": fact_id, "title": title, "date": event_date})

        return fact_id

    def add_semantic_memory(
        self,
        category: str,
        key: str,
        value: Any,
        confidence: float = 1.0,
        source: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> str:
        """
        添加语义记忆 - v4.0版本

        v4.0改变:语义记忆作为命题式事实存储
        """
        if tags is None:
            tags = []

        # v4.0:将语义记忆转化为命题式事实
        fact_content = f"{category}:{key} = {value}"

        # 判断边界
        boundary = FactBoundary.SAYABLE
        if category in ["偏好", "感受", "体验", "价值"]:
            boundary = FactBoundary.UNSAYABLE
        elif confidence < 0.5:
            boundary = FactBoundary.UNCERTAIN

        fact_id = self.add_fact(
            content=fact_content,
            fact_type=MemoryType.SEMANTIC,
            evidence=[f"来源: {source}"] if source else [],
            confidence=confidence,
            boundary=boundary,
            source=source,
            tags=[*tags, "semantic", category],
        )

        return fact_id

    def query_facts(
        self,
        query: str,
        min_confidence: float = 0.0,
        boundary: Optional[FactBoundary] = None,
        fact_type: Optional[MemoryType] = None,
    ) -> list[dict]:
        """
        v4.0新增:查询事实

        支持按置信度、边界、类型过滤
        """
        results = []

        if not self.facts_file.exists():
            return results

        with open(self.facts_file, encoding="utf-8") as f:
            for line in f:
                fact = json.loads(line)

                # 置信度过滤
                if fact["confidence"]["value"] < min_confidence:
                    continue

                # 边界过滤
                if boundary and fact["boundary"] != boundary.value:
                    continue

                # 类型过滤
                if fact_type and fact["type"] != fact_type.value:
                    continue

                # 内容匹配
                if query.lower() in fact["content"].lower():
                    results.append(fact)

        # 按置信度排序
        results.sort(key=lambda x: x["confidence"]["value"], reverse=True)

        return results

    def get_fact_relations(self, fact_id: str) -> list[dict]:
        """
        v4.0新增:获取事实的关系网络
        """
        relations = []

        for edge in self.fact_graph["edges"]:
            if edge["from_fact"] == fact_id or edge["to_fact"] == fact_id:
                relations.append(edge)

        return relations

    def explain_uncertainty(self, fact_id: str) -> str:
        """
        v4.0新增:解释事实的不确定性

        这是v4.0的核心特性:诚实标注不确定性
        """
        if not self.facts_file.exists():
            return "❌ 事实不存在"

        with open(self.facts_file, encoding="utf-8") as f:
            for line in f:
                fact = json.loads(line)
                if fact["id"] == fact_id:
                    confidence_value = fact["confidence"]["value"]
                    confidence_level = fact["confidence"]["level"]
                    evidence = fact["confidence"]["evidence"]
                    limitations = fact["confidence"]["limitations"]
                    boundary = fact["boundary"]

                    explanation = f"📊 事实:{fact['content']}\n\n"
                    explanation += f"📈 置信度:{confidence_value:.1%} ({confidence_level})\n"

                    if evidence:
                        explanation += "📋 支持证据:\n"
                        for i, ev in enumerate(evidence, 1):
                            explanation += f"  {i}. {ev}\n"

                    if limitations:
                        explanation += "\n⚠️ 局限性:\n"
                        for lim in limitations:
                            explanation += f"  • {lim}\n"

                    explanation += f"\n🔒 边界:{self._get_boundary_description(boundary)}"

                    return explanation

        return "❌ 事实不存在"

    def _get_boundary_description(self, boundary: str) -> str:
        """获取边界描述"""
        descriptions = {
            "sayable": "✅ 可说:在逻辑和经验范围内",
            "unsayable": "🔒 不可说:超出逻辑范围,需要主观体验",
            "uncertain": "❓ 不确定:边界模糊,需要更多信息",
        }
        return descriptions.get(boundary, boundary)

    def analyze_logical_structure(self) -> dict:
        """
        v4.0新增:分析记忆系统的逻辑结构

        维特根斯坦:理解事实的逻辑结构
        """
        analysis = {
            "total_facts": self.index["total_facts"],
            "logical_distribution": self.index["logical_structure_types"],
            "boundary_distribution": self.index["boundary_distribution"],
            "average_confidence": self.index["average_confidence"],
            "relation_types": {},
            "logical_clusters": len(self.fact_graph.get("logical_clusters", {})),
            "insights": [],
        }

        # 分析关系类型分布
        for edge in self.fact_graph["edges"]:
            rel_type = edge["type"]
            analysis["relation_types"][rel_type] = analysis["relation_types"].get(rel_type, 0) + 1

        # 生成洞察
        if analysis["average_confidence"] < 0.6:
            analysis["insights"].append("⚠️ 平均置信度较低,建议验证和更新事实")

        unsayable_ratio = (
            analysis["boundary_distribution"]["unsayable"] / analysis["total_facts"]
            if analysis["total_facts"] > 0
            else 0
        )
        if unsayable_ratio > 0.3:
            analysis["insights"].append(f"ℹ️ 不可说领域占{unsayable_ratio:.1%},这些需要保持敬畏")

        return analysis

    def export_memory_report(self) -> str:
        """
        v4.0新增:导出记忆报告

        包含事实关系分析和逻辑结构
        """
        report = "=" * 80 + "\n"
        report += "📊 v4.0记忆系统报告\n"
        report += "基于维特根斯坦《逻辑哲学论》\n"
        report += "=" * 80 + "\n\n"

        # 基础统计
        report += "📈 基础统计:\n"
        report += f"  • 事实总数: {self.index['total_facts']}\n"
        report += f"  • 关系数: {self.index['relations_count']}\n"
        report += f"  • 平均置信度: {self.index['average_confidence']:.1%}\n\n"

        # 类型分布
        report += "📋 事实类型分布:\n"
        for fact_type, count in self.index["fact_types"].items():
            report += f"  • {fact_type}: {count}\n"
        report += "\n"

        # 边界分布
        report += "🔒 边界分布:\n"
        for boundary, count in self.index["boundary_distribution"].items():
            report += f"  • {boundary}: {count}\n"
        report += "\n"

        # 逻辑结构
        analysis = self.analyze_logical_structure()
        report += "🧠 逻辑结构:\n"
        for structure, count in analysis["logical_distribution"].items():
            report += f"  • {structure}: {count}\n"
        report += "\n"

        # 洞察
        if analysis["insights"]:
            report += "💡 洞察:\n"
            for insight in analysis["insights"]:
                report += f"  {insight}\n"
            report += "\n"

        report += "=" * 80 + "\n"
        report += f"报告生成时间: {datetime.now().isoformat()}\n"

        return report


# 便捷函数
def get_memory_system_v4() -> TimelineMemoryV4:
    """获取v4.0记忆系统实例"""
    return TimelineMemoryV4()


# 使用示例
if __name__ == "__main__":
    print("🧠 测试v4.0记忆系统(维特根斯坦版)...")

    memory = TimelineMemoryV4()

    # 示例1:添加事实(可说)
    fact_id_1 = memory.add_fact(
        content="Python的列表是可变的数据结构",
        fact_type=MemoryType.SEMANTIC,
        evidence=["官方文档", "语言规范", "实际测试"],
        confidence=0.95,
        boundary=FactBoundary.SAYABLE,
        source="技术知识",
        tags=["python", "编程"],
    )
    print(f"✅ 添加事实1: {fact_id_1}")

    # 示例2:添加事实(不可说)
    fact_id_2 = memory.add_fact(
        content="爸爸喜欢和小诺一起读书",
        fact_type=MemoryType.EPISODIC,
        evidence=["多次共同读书经历"],
        confidence=0.85,
        boundary=FactBoundary.UNSAYABLE,  # 这是情感领域,不可说
        source="观察",
        tags=["家庭", "阅读"],
    )
    print(f"✅ 添加事实2: {fact_id_2}")

    # 示例3:添加事实关系
    relation_id = memory.add_fact_relation(
        fact_id_1, fact_id_2, FactRelationType.LOGICAL, confidence=0.6
    )
    print(f"✅ 添加关系: {relation_id}")

    # 示例4:查询事实
    results = memory.query_facts("python", min_confidence=0.8)
    print(f"\n🔍 查询结果: {len(results)} 个")
    for result in results:
        print(f"  • {result['content'][:50]}... (置信度: {result['confidence']['value']:.1%})")

    # 示例5:解释不确定性
    print("\n📊 不确定性解释:")
    print(memory.explain_uncertainty(fact_id_1))

    # 示例6:导出报告
    print("\n📋 记忆报告:")
    print(memory.export_memory_report())

    print("\n🎉 v4.0记忆系统测试完成!")
    print("✨ 核心特性:事实关系、不确定性标注、逻辑结构、边界识别")

