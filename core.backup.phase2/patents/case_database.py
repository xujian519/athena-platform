from __future__ import annotations

#!/usr/bin/env python3
"""
专利案例数据库
Patent Case Database

基于赫布定律和演化思想构建的专利案例库:
- 成功案例:高适应度基因,用于模式学习
- 失败案例:负反馈样本,用于避免重蹈覆辙
- 赫布学习:相似案例协同激活,强化连接
- 自然选择:筛选最佳案例用于参考

作者: 小诺·双鱼公主
创建时间: 2025-12-24
版本: v0.1.2 "晨星初现"
"""

import hashlib
import json
import logging
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class CaseType(Enum):
    """案例类型"""

    PATENT_DRAFTING = "patent_drafting"  # 专利撰写
    PATENT_ANALYSIS = "patent_analysis"  # 专利分析
    OFFICE_ACTION = "office_action"  # 意见答复


class CaseStatus(Enum):
    """案例状态"""

    SUCCESS = "success"  # 成功案例(高适应度)
    FAILURE = "failure"  # 失败案例(低适应度)
    PENDING = "pending"  # 待定案例


class TechnicalField(Enum):
    """技术领域"""

    MECHANICAL = "mechanical"  # 机械
    ELECTRICAL = "electrical"  # 电学
    CHEMICAL = "chemical"  # 化学
    SOFTWARE = "software"  # 软件
    BIOTECH = "biotech"  # 生物
    COMMUNICATION = "communication"  # 通信


@dataclass
class PatentCase:
    """专利案例"""

    case_id: str
    case_type: CaseType
    status: CaseStatus
    technical_field: TechnicalField

    # 核心内容
    title: str  # 案例标题
    description: str  # 案例描述
    input_data: dict[str, Any]  # 输入数据
    output_result: dict[str, Any]  # 输出结果
    solution: str  # 解决方案

    # 适应性指标
    fitness: float = 0.5  # 适应度(0-1)
    success_rate: float = 0.0  # 成功率
    confidence: float = 0.5  # 置信度

    # 元数据
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # 关联信息
    similar_cases: list[str] = field(default_factory=list)
    reference_count: int = 0  # 被引用次数

    def __post_init__(self):
        """生成案例ID"""
        if not self.case_id:
            content = f"{self.case_type.value}:{self.title}:{self.created_at}"
            self.case_id = hashlib.md5(content.encode('utf-8'), usedforsecurity=False).hexdigest()[:12]

    def calculate_similarity(self, other: PatentCase) -> float:
        """计算与其他案例的相似度"""
        similarity = 0.0

        # 类型相同(权重: 30%)
        if self.case_type == other.case_type:
            similarity += 0.3

        # 技术领域相同(权重: 20%)
        if self.technical_field == other.technical_field:
            similarity += 0.2

        # 标签重叠(权重: 20%)
        if self.tags and other.tags:
            overlap = len(set(self.tags) & set(other.tags))
            union = len(set(self.tags) | set(other.tags))
            similarity += 0.2 * (overlap / union if union > 0 else 0)

        # 描述相似度(简化:关键词重叠,权重: 30%)
        desc_words = set(self.description.lower().split())
        other_desc_words = set(other.description.lower().split())
        if desc_words and other_desc_words:
            overlap = len(desc_words & other_desc_words)
            union = len(desc_words | other_desc_words)
            similarity += 0.3 * (overlap / union if union > 0 else 0)

        return min(1.0, similarity)


@dataclass
class CaseRetrievalResult:
    """案例检索结果"""

    cases: list[PatentCase]
    total_count: int
    query_params: dict[str, Any]
    retrieval_time: float
    avg_similarity: float


class PatentCaseDatabase:
    """
    专利案例数据库

    核心功能:
    1. 案例存储和管理
    2. 相似案例检索(赫布学习)
    3. 适应度评估(自然选择)
    4. 模式提取和推荐
    """

    def __init__(self):
        """初始化案例数据库"""
        self.name = "专利案例数据库"
        self.version = "v0.1.2"

        # 案例存储
        self.cases: dict[str, PatentCase] = {}

        # 索引
        self.by_type: dict[CaseType, list[str]] = defaultdict(list)
        self.by_status: dict[CaseStatus, list[str]] = defaultdict(list)
        self.by_field: dict[TechnicalField, list[str]] = defaultdict(list)
        self.by_tags: dict[str, list[str]] = defaultdict(list)

        # 赫布学习:案例协同激活网络
        self.coactivation_network: dict[str, dict[str, float]] = defaultdict(
            lambda: defaultdict(float)
        )

        # 统计信息
        self.total_references = 0
        self.success_rate_history: list[tuple[str, float]] = []

        logger.info(f"📚 {self.name} ({self.version}) 初始化完成")

    def add_case(self, case: PatentCase) -> str:
        """
        添加案例

        Args:
            case: 专利案例

        Returns:
            案例ID
        """
        # 生成ID
        if not case.case_id:
            case.__post_init__()

        # 存储案例
        self.cases[case.case_id] = case

        # 更新索引
        self.by_type[case.case_type].append(case.case_id)
        self.by_status[case.status].append(case.case_id)
        self.by_field[case.technical_field].append(case.case_id)
        for tag in case.tags:
            self.by_tags[tag].append(case.case_id)

        logger.info(f"📚 添加案例: {case.title} [{case.status.value}]")

        return case.case_id

    def update_case_fitness(
        self, case_id: str, fitness: float, success: bool | None = None
    ) -> None:
        """
        更新案例适应度(自然选择)

        Args:
            case_id: 案例ID
            fitness: 新的适应度值
            success: 是否成功(可选)
        """
        if case_id not in self.cases:
            logger.warning(f"案例不存在: {case_id}")
            return

        case = self.cases[case_id]
        old_fitness = case.fitness
        case.fitness = max(0.0, min(1.0, fitness))

        # 更新状态
        if success is not None:
            case.status = CaseStatus.SUCCESS if success else CaseStatus.FAILURE

        # 更新成功率
        if case.success_rate == 0:
            case.success_rate = fitness
        else:
            # 指数移动平均
            case.success_rate = 0.7 * case.success_rate + 0.3 * fitness

        case.updated_at = datetime.now().isoformat()

        # 记录历史
        self.success_rate_history.append((case_id, case.success_rate))

        logger.info(f"📚 更新适应度: {case.title} " f"{old_fitness:.2f} → {case.fitness:.2f}")

    def record_coactivation(self, case_id1: str, case_id2: str) -> None:
        """
        记录案例协同激活(赫布学习)

        Args:
            case_id1: 案例1 ID
            case_id2: 案例2 ID
        """
        if case_id1 not in self.cases or case_id2 not in self.cases:
            return

        # 双向强化
        self.coactivation_network[case_id1][case_id2] += 0.1
        self.coactivation_network[case_id2][case_id1] += 0.1

        # 限制在[0, 1]
        self.coactivation_network[case_id1][case_id2] = min(
            1.0, self.coactivation_network[case_id1][case_id2]
        )
        self.coactivation_network[case_id2][case_id1] = min(
            1.0, self.coactivation_network[case_id2][case_id1]
        )

        logger.debug(f"📚 协同激活: {case_id1} <-> {case_id2}")

    def retrieve_similar_cases(
        self,
        query_case: PatentCase,
        top_n: int = 10,
        min_similarity: float = 0.3,
        case_type: CaseType = None,
        status: CaseStatus = None,
    ) -> CaseRetrievalResult:
        """
        检索相似案例

        Args:
            query_case: 查询案例
            top_n: 返回前N个
            min_similarity: 最小相似度
            case_type: 案例类型筛选
            status: 状态筛选

        Returns:
            检索结果
        """
        start_time = datetime.now()

        # 候选案例
        candidates = []

        for _case_id, case in self.cases.items():
            # 类型筛选
            if case_type and case.case_type != case_type:
                continue

            # 状态筛选
            if status and case.status != status:
                continue

            # 计算相似度
            similarity = query_case.calculate_similarity(case)

            if similarity >= min_similarity:
                candidates.append((similarity, case))

        # 排序:按相似度和适应度综合排序
        candidates.sort(key=lambda x: (x[0] * 0.7 + x[1].fitness * 0.3), reverse=True)

        # 取前N个
        top_cases = [case for _, case in candidates[:top_n]]

        # 更新引用计数
        for case in top_cases:
            case.reference_count += 1
            # 记录协同激活
            self.record_coactivation(query_case.case_id, case.case_id)

        retrieval_time = (datetime.now() - start_time).total_seconds()

        avg_similarity = (
            sum(s for s, _ in candidates[:top_n]) / len(candidates[:top_n])
            if candidates[:top_n]
            else 0.0
        )

        result = CaseRetrievalResult(
            cases=top_cases,
            total_count=len(candidates),
            query_params={
                "case_type": query_case.case_type.value,
                "technical_field": query_case.technical_field.value,
                "tags": query_case.tags,
            },
            retrieval_time=retrieval_time,
            avg_similarity=avg_similarity,
        )

        logger.info(f"📚 检索到 {len(top_cases)} 个相似案例 " f"(平均相似度: {avg_similarity:.2f})")

        return result

    def get_best_cases(
        self, case_type: CaseType, technical_field: TechnicalField = None, top_n: int = 5
    ) -> list[PatentCase]:
        """
        获取最佳案例(自然选择:高适应度)

        Args:
            case_type: 案例类型
            technical_field: 技术领域(可选)
            top_n: 返回前N个

        Returns:
            最佳案例列表
        """
        candidates = []

        for case_id in self.by_type[case_type]:
            case = self.cases[case_id]

            # 领域筛选
            if technical_field and case.technical_field != technical_field:
                continue

            # 只考虑成功案例
            if case.status != CaseStatus.SUCCESS:
                continue

            candidates.append(case)

        # 按适应度和成功率排序
        candidates.sort(key=lambda c: (c.fitness * 0.6 + c.success_rate * 0.4), reverse=True)

        return candidates[:top_n]

    def extract_patterns(self, case_type: CaseType, top_n: int = 10) -> list[dict[str, Any]]:
        """
        提取成功模式

        Args:
            case_type: 案例类型
            top_n: 返回前N个模式

        Returns:
            模式列表
        """
        # 获取成功案例
        success_cases = [
            self.cases[cid]
            for cid in self.by_type[case_type]
            if self.cases[cid].status == CaseStatus.SUCCESS
        ]

        if not success_cases:
            return []

        patterns = []

        # 1. 标签模式
        tag_counter = Counter()
        for case in success_cases:
            for tag in case.tags:
                tag_counter[tag] += case.fitness

        top_tags = [
            {"tag": tag, "weight": weight} for tag, weight in tag_counter.most_common(top_n)
        ]
        patterns.append({"pattern_type": "tags", "description": "高频标签模式", "data": top_tags})

        # 2. 技术领域分布
        field_counter = Counter(case.technical_field.value for case in success_cases)
        patterns.append(
            {
                "pattern_type": "technical_fields",
                "description": "技术领域分布",
                "data": [
                    {"field": field, "count": count} for field, count in field_counter.most_common()
                ],
            }
        )

        # 3. 平均适应度
        avg_fitness = sum(c.fitness for c in success_cases) / len(success_cases)
        avg_success_rate = sum(c.success_rate for c in success_cases) / len(success_cases)

        patterns.append(
            {
                "pattern_type": "quality_metrics",
                "description": "质量指标",
                "data": {
                    "avg_fitness": avg_fitness,
                    "avg_success_rate": avg_success_rate,
                    "total_cases": len(success_cases),
                },
            }
        )

        return patterns

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        total = len(self.cases)

        if total == 0:
            return {"message": "暂无案例"}

        success_count = len(self.by_status[CaseStatus.SUCCESS])
        failure_count = len(self.by_status[CaseStatus.FAILURE])

        # 按类型统计
        by_type = {case_type.value: len(case_ids) for case_type, case_ids in self.by_type.items()}

        # 按领域统计
        by_field = {field.value: len(case_ids) for field, case_ids in self.by_field.items()}

        # 平均适应度
        avg_fitness = sum(c.fitness for c in self.cases.values()) / total

        return {
            "total_cases": total,
            "success_cases": success_count,
            "failure_cases": failure_count,
            "success_rate": success_count / total if total > 0 else 0,
            "by_type": by_type,
            "by_technical_field": by_field,
            "average_fitness": avg_fitness,
            "total_references": sum(c.reference_count for c in self.cases.values()),
        }


# 全局单例
_patent_case_db_instance = None


def get_patent_case_db() -> PatentCaseDatabase:
    """获取专利案例数据库单例"""
    global _patent_case_db_instance
    if _patent_case_db_instance is None:
        _patent_case_db_instance = PatentCaseDatabase()
    return _patent_case_db_instance


# 测试代码
async def main():
    """测试专利案例数据库"""

    print("\n" + "=" * 60)
    print("📚 专利案例数据库测试")
    print("=" * 60 + "\n")

    db = get_patent_case_db()

    # 测试1:添加案例
    print("📝 测试1: 添加案例")

    # 成功案例
    success_case = PatentCase(
        case_id="",
        case_type=CaseType.PATENT_DRAFTING,
        status=CaseStatus.SUCCESS,
        technical_field=TechnicalField.SOFTWARE,
        title="AI算法专利撰写成功案例",
        description="基于深度学习的图像识别算法专利撰写",
        input_data={"invention": "深度学习图像识别", "claims": 10},
        output_result={"patent_id": "CN202310000001", "granted": True},
        solution="采用独立权利要求保护核心算法,从属权利要求保护具体实现",
        fitness=0.9,
        success_rate=0.85,
        confidence=0.9,
        tags=["AI", "深度学习", "图像识别", "算法"],
    )

    db.add_case(success_case)

    # 失败案例
    failure_case = PatentCase(
        case_id="",
        case_type=CaseType.OFFICE_ACTION,
        status=CaseStatus.FAILURE,
        technical_field=TechnicalField.SOFTWARE,
        title="意见答复失败案例",
        description="新颖性争辩失败",
        input_data={"rejection_type": "novelty", "prior_art": 5},
        output_result={"final_result": "rejected"},
        solution="未充分识别区别技术特征",
        fitness=0.2,
        success_rate=0.0,
        confidence=0.3,
        tags=["答复失败", "新颖性"],
    )

    db.add_case(failure_case)

    print("✅ 添加案例完成\n")

    # 测试2:相似案例检索
    print("📝 测试2: 相似案例检索")

    query = PatentCase(
        case_id="",
        case_type=CaseType.PATENT_DRAFTING,
        status=CaseStatus.SUCCESS,
        technical_field=TechnicalField.SOFTWARE,
        title="机器学习专利撰写",
        description="机器学习算法专利申请",
        input_data={},
        output_data={},
        solution="",
        tags=["AI", "机器学习", "算法"],
    )

    result = db.retrieve_similar_cases(query, top_n=5)

    print(f"检索到 {result.total_count} 个案例")
    print(f"平均相似度: {result.avg_similarity:.2f}")
    print(f"检索时间: {result.retrieval_time:.3f}秒\n")

    # 测试3:获取最佳案例
    print("📝 测试3: 获取最佳案例")

    best_cases = db.get_best_cases(case_type=CaseType.PATENT_DRAFTING, top_n=3)

    for i, case in enumerate(best_cases, 1):
        print(f"{i}. {case.title}")
        print(f"   适应度: {case.fitness:.2f}, 成功率: {case.success_rate:.2f}")
    print()

    # 测试4:模式提取
    print("📝 测试4: 提取成功模式")

    patterns = db.extract_patterns(CaseType.PATENT_DRAFTING)

    for pattern in patterns:
        print(f"• {pattern['description']}")
        print(f"  {json.dumps(pattern['data'], ensure_ascii=False, indent=4)}")
    print()

    # 测试5:统计信息
    print("📝 测试5: 统计信息")

    stats = db.get_statistics()
    print(json.dumps(stats, ensure_ascii=False, indent=2))

    print("\n✅ 测试完成!")


# 入口点: @async_main装饰器已添加到main函数
