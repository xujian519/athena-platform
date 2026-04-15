"""
服务能力知识图谱 (ServiceKG)
用于智能体精确匹配和调用微服务
"""

from __future__ import annotations
import json
from dataclasses import dataclass, field, fields
from enum import Enum
from pathlib import Path
from typing import Any

from loguru import logger


class ServiceCategory(Enum):
    """服务分类"""

    PATENT = "patent"  # 专利相关
    AGENT = "agent"  # 智能体
    BROWSER = "browser"  # 浏览器
    KNOWLEDGE = "knowledge"  # 知识图谱
    SEARCH = "search"  # 搜索
    ANALYSIS = "analysis"  # 分析
    CONTROL = "control"  # 控制
    STORAGE = "storage"  # 存储
    MONITORING = "monitoring"  # 监控
    UTILITY = "utility"  # 工具


@dataclass
class ServiceCapability:
    """服务能力描述"""

    # 基础信息
    service_id: str  # 服务唯一标识
    service_name: str  # 服务名称
    category: ServiceCategory  # 服务分类

    # 能力描述(多维度)
    description: str  # 自然语言描述
    keywords: list[str]  # 关键词列表
    semantic_tags: list[str]  # 语义标签

    # 功能能力
    capabilities: list[str]  # 具体能力列表
    input_types: list[str]  # 输入类型
    output_types: list[str]  # 输出类型

    # 性能指标
    avg_response_time: float = 0.0  # 平均响应时间(ms)
    success_rate: float = 1.0  # 成功率(0-1)
    load_capacity: int = 100  # 负载容量

    # 使用统计
    total_calls: int = 0  # 总调用次数
    successful_calls: int = 0  # 成功调用次数
    user_satisfaction: float = 0.0  # 用户满意度(0-1)

    # 置信度评分
    confidence_score: float = 0.0  # 综合置信度评分

    # 元数据
    metadata: dict[str, Any] = field(default_factory=dict)

    def calculate_confidence(self) -> float:
        """计算综合置信度评分"""
        # 性能评分 (40%)
        performance_score = min(1.0, 1000 / (self.avg_response_time + 1))

        # 可靠性评分 (30%)
        reliability_score = self.success_rate

        # 使用满意度评分 (20%)
        satisfaction_score = self.user_satisfaction if self.user_satisfaction > 0 else 0.8

        # 负载评分 (10%) - 负载越低分数越高
        load_score = max(0.1, 1.0 - (self.total_calls / self.load_capacity))

        self.confidence_score = (
            performance_score * 0.4
            + reliability_score * 0.3
            + satisfaction_score * 0.2
            + load_score * 0.1
        )

        return self.confidence_score

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        # 处理category - 可能是枚举或字符串
        category_value = self.category.value

        return {
            "service_id": self.service_id,
            "service_name": self.service_name,
            "category": category_value,
            "description": self.description,
            "keywords": self.keywords,
            "semantic_tags": self.semantic_tags,
            "capabilities": self.capabilities,
            "input_types": self.input_types,
            "output_types": self.output_types,
            "avg_response_time": self.avg_response_time,
            "success_rate": self.success_rate,
            "load_capacity": self.load_capacity,
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "user_satisfaction": self.user_satisfaction,
            "confidence_score": self.confidence_score,
            "metadata": self.metadata,
        }


class ServiceKnowledgeGraph:
    """服务能力知识图谱"""

    def __init__(self, kg_path: str | None = None):
        self.services: dict[str, ServiceCapability] = {}
        self.keyword_index: dict[str, list[str]] = {}  # keyword -> service_ids
        self.semantic_index: dict[str, list[str]] = {}  # semantic_tag -> service_ids
        self.category_index: dict[ServiceCategory, list[str]] = {}  # category -> service_ids

        self.kg_path = kg_path or "data/service_kg.json"
        self._load_kg()

    def _load_kg(self):
        """加载知识图谱"""
        kg_file = Path(self.kg_path)
        if kg_file.exists():
            try:
                with open(kg_file, encoding="utf-8") as f:
                    data = json.load(f)
                    for svc_data in data.get("services", []):
                        # 字段验证:只保留ServiceCapability定义的字段
                        valid_fields = {f.name for f in fields(ServiceCapability)}
                        filtered_data = {k: v for k, v in svc_data.items() if k in valid_fields}
                        # 确保category是枚举类型
                        if "category" in filtered_data and isinstance(
                            filtered_data["category"], str
                        ):
                            filtered_data["category"] = ServiceCategory(filtered_data["category"])
                        svc = ServiceCapability(**filtered_data)
                        self.register_service(svc)
                logger.info(f"已加载知识图谱,包含 {len(self.services)} 个服务")
            except (json.JSONDecodeError, TypeError, ValueError) as e:
                logger.error(f"加载知识图谱失败: {e}")
            except Exception as e:
                logger.error(f"加载知识图谱时发生未知错误: {e}")

    def _save_kg(self):
        """保存知识图谱"""
        try:
            kg_file = Path(self.kg_path)
            kg_file.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "services": [svc.to_dict() for svc in self.services.values()],
                "version": "1.0.0",
            }

            with open(kg_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"知识图谱已保存到 {self.kg_path}")
        except Exception as e:
            logger.error(f"保存知识图谱失败: {e}")

    def register_service(self, service: ServiceCapability):
        """注册服务到知识图谱"""
        self.services[service.service_id] = service

        # 更新关键词索引
        for keyword in service.keywords:
            if keyword not in self.keyword_index:
                self.keyword_index[keyword] = []
            if service.service_id not in self.keyword_index[keyword]:
                self.keyword_index[keyword].append(service.service_id)

        # 更新语义标签索引
        for tag in service.semantic_tags:
            if tag not in self.semantic_index:
                self.semantic_index[tag] = []
            if service.service_id not in self.semantic_index[tag]:
                self.semantic_index[tag].append(service.service_id)

        # 更新分类索引
        if service.category not in self.category_index:
            self.category_index[service.category] = []
        if service.service_id not in self.category_index[service.category]:
            self.category_index[service.category].append(service.service_id)

        # 计算置信度
        service.calculate_confidence()

        logger.info(f"服务已注册: {service.service_name} ({service.service_id})")

    def search_by_keywords(self, keywords: list[str], top_k: int = 5) -> list[tuple[str, int]]:
        """通过关键词搜索服务"""
        scores = {}

        for keyword in keywords:
            if keyword in self.keyword_index:
                for service_id in self.keyword_index[keyword]:
                    scores[service_id] = scores.get(service_id, 0) + 1

        # 按匹配数量排序
        sorted_services = sorted(scores.items(), key=lambda x: x[1], reverse=True)  # type: ignore[arg-type]

        return sorted_services[:top_k]

    def search_by_category(self, category: ServiceCategory, top_k: int = 10) -> list[str]:
        """通过分类搜索服务"""
        services = self.category_index.get(category, [])
        # 按置信度排序
        sorted_services = sorted(
            services, key=lambda sid: self.services[sid].confidence_score, reverse=True
        )
        return sorted_services[:top_k]

    def semantic_search(
        self, query: str, embedding_model: Any = None, top_k: int = 5
    ) -> list[tuple[str, int]]:
        """语义搜索服务"""
        # 这里需要集成向量嵌入模型
        # 暂时使用关键词匹配作为替代
        query_lower = query.lower()
        scores = {}

        for service_id, service in self.services.items():
            # 匹配描述
            if query_lower in service.description.lower():
                scores[service_id] = scores.get(service_id, 0) + 2

            # 匹配能力
            for capability in service.capabilities:
                if query_lower in capability.lower():
                    scores[service_id] = scores.get(service_id, 0) + 1

        sorted_services = sorted(scores.items(), key=lambda x: x[1], reverse=True)  # type: ignore[arg-type]
        return sorted_services[:top_k]

    def get_service(self, service_id: str) -> ServiceCapability | None:
        """获取服务详情"""
        return self.services.get(service_id)

    def get_all_services(self) -> list[ServiceCapability]:
        """获取所有服务"""
        return list(self.services.values())

    def update_service_stats(self, service_id: str, success: bool, response_time: float):
        """更新服务统计信息"""
        service = self.services.get(service_id)
        if not service:
            return

        service.total_calls += 1
        if success:
            service.successful_calls += 1

        # 更新平均响应时间
        if service.avg_response_time == 0:
            service.avg_response_time = response_time
        else:
            service.avg_response_time = service.avg_response_time * 0.9 + response_time * 0.1

        # 更新成功率
        service.success_rate = service.successful_calls / service.total_calls

        # 重新计算置信度
        service.calculate_confidence()

    def record_feedback(self, service_id: str, satisfaction: float):
        """记录用户反馈"""
        service = self.services.get(service_id)
        if not service:
            return

        # 更新满意度
        if service.user_satisfaction == 0:
            service.user_satisfaction = satisfaction
        else:
            service.user_satisfaction = service.user_satisfaction * 0.8 + satisfaction * 0.2

        # 重新计算置信度
        service.calculate_confidence()

    def export_kg(self) -> dict[str, Any]:
        """导出知识图谱"""
        return {
            "services": [svc.to_dict() for svc in self.services.values()],
            "statistics": {
                "total_services": len(self.services),
                "categories": {
                    cat.value: len(services)  # type: ignore[assignment]
                    for cat, services in self.category_index.items()
                },
                "total_keywords": len(self.keyword_index),
                "total_semantic_tags": len(self.semantic_index),
            },
            "version": "1.0.0",
        }


# 初始化全局知识图谱实例
_service_kg: ServiceKnowledgeGraph | None = None


def get_service_kg() -> ServiceKnowledgeGraph:
    """获取全局服务知识图谱实例"""
    global _service_kg
    if _service_kg is None:
        _service_kg = ServiceKnowledgeGraph()
    return _service_kg
