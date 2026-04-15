#!/usr/bin/env python3
"""
专利规则构建系统 - 数据质量验证器
Patent Rules Builder - Data Quality Validator

数据质量验证和自动化测试系统，确保系统各组件的数据质量和功能正确性

作者: Athena平台团队
创建时间: 2025-12-20
版本: v1.0.0
"""

from __future__ import annotations
import asyncio
import json
import logging
import re

# 导入系统组件
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np

# 使用安全哈希函数替代不安全的MD5/SHA1
from production.utils.security_helpers import short_hash

sys.path.append(str(Path(__file__).parent))

from bert_extractor_simple import PatentEntityRelationExtractor
from nebula_graph_builder import NebulaGraphBuilder
from qdrant_vector_store_simple import QdrantVectorStoreSimple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ValidationLevel(Enum):
    """验证级别"""
    CRITICAL = "关键"    # 关键问题，必须修复
    HIGH = "高"         # 高优先级问题
    MEDIUM = "中"       # 中等优先级问题
    LOW = "低"          # 低优先级问题
    INFO = "信息"       # 仅信息提示

class ValidationStatus(Enum):
    """验证状态"""
    PASSED = "通过"
    FAILED = "失败"
    WARNING = "警告"
    SKIPPED = "跳过"
    ERROR = "错误"

@dataclass
class ValidationRule:
    """验证规则"""
    name: str
    description: str
    level: ValidationLevel
    validator_func: str
    parameters: dict[str, Any] = None
    enabled: bool = True

@dataclass
class ValidationResult:
    """验证结果"""
    rule_name: str
    status: ValidationStatus
    level: ValidationLevel
    message: str
    details: dict[str, Any] = None
    timestamp: datetime = None
    execution_time: float = 0.0

@dataclass
class QualityReport:
    """质量报告"""
    component: str
    total_rules: int
    passed_rules: int
    failed_rules: int
    warning_rules: int
    skipped_rules: int
    error_rules: int
    validation_time: float
    results: list[ValidationResult]
    score: float  # 0-100

class DataQualityValidator:
    """数据质量验证器"""

    def __init__(self,
                 data_dir: str = "/Users/xujian/Athena工作平台/production/data/patent_rules"):
        self.data_dir = Path(data_dir)

        # 初始化组件
        self.vector_store = QdrantVectorStoreSimple()
        self.entity_extractor = PatentEntityRelationExtractor()
        self.graph_builder = NebulaGraphBuilder()

        # 定义验证规则
        self.validation_rules = self._define_validation_rules()

        # 统计信息
        self.stats = {
            "total_validations": 0,
            "components_validated": 0,
            "issues_found": 0,
            "critical_issues": 0
        }

        # 质量基准
        self.quality_benchmarks = {
            "vector_similarity_threshold": 0.7,
            "entity_confidence_threshold": 0.8,
            "graph_connectivity_threshold": 0.6,
            "data_completeness_threshold": 0.9
        }

    def _define_validation_rules(self) -> dict[str, list[ValidationRule]]:
        """定义验证规则"""
        rules = {
            "vector_store": [
                ValidationRule(
                    name="vector_dimension_check",
                    description="验证向量维度一致性",
                    level=ValidationLevel.CRITICAL,
                    validator_func="_validate_vector_dimensions"
                ),
                ValidationRule(
                    name="vector_normalization_check",
                    description="验证向量归一化",
                    level=ValidationLevel.HIGH,
                    validator_func="_validate_vector_normalization"
                ),
                ValidationRule(
                    name="duplicate_vectors_check",
                    description="检查重复向量",
                    level=ValidationLevel.MEDIUM,
                    validator_func="_validate_duplicate_vectors"
                ),
                ValidationRule(
                    name="vector_similarity_distribution",
                    description="分析向量相似度分布",
                    level=ValidationLevel.INFO,
                    validator_func="_validate_similarity_distribution"
                ),
                ValidationRule(
                    name="document_completeness",
                    description="验证文档完整性",
                    level=ValidationLevel.HIGH,
                    validator_func="_validate_document_completeness"
                )
            ],
            "entity_extraction": [
                ValidationRule(
                    name="entity_consistency_check",
                    description="验证实体一致性",
                    level=ValidationLevel.HIGH,
                    validator_func="_validate_entity_consistency"
                ),
                ValidationRule(
                    name="entity_confidence_threshold",
                    description="验证实体置信度",
                    level=ValidationLevel.MEDIUM,
                    validator_func="_validate_entity_confidence"
                ),
                ValidationRule(
                    name="entity_type_coverage",
                    description="检查实体类型覆盖",
                    level=ValidationLevel.INFO,
                    validator_func="_validate_entity_type_coverage"
                ),
                ValidationRule(
                    name="relation_validation",
                    description="验证关系提取",
                    level=ValidationLevel.MEDIUM,
                    validator_func="_validate_relations"
                )
            ],
            "knowledge_graph": [
                ValidationRule(
                    name="graph_connectivity",
                    description="验证图谱连通性",
                    level=ValidationLevel.HIGH,
                    validator_func="_validate_graph_connectivity"
                ),
                ValidationRule(
                    name="node_type_distribution",
                    description="检查节点类型分布",
                    level=ValidationLevel.INFO,
                    validator_func="_validate_node_type_distribution"
                ),
                ValidationRule(
                    name="edge_validation",
                    description="验证边关系",
                    level=ValidationLevel.MEDIUM,
                    validator_func="_validate_edge_validation"
                ),
                ValidationRule(
                    name="orphan_nodes_check",
                    description="检查孤立节点",
                    level=ValidationLevel.MEDIUM,
                    validator_func="_validate_orphan_nodes"
                )
            ],
            "data_consistency": [
                ValidationRule(
                    name="cross_component_consistency",
                    description="跨组件一致性检查",
                    level=ValidationLevel.CRITICAL,
                    validator_func="_validate_cross_component_consistency"
                ),
                ValidationRule(
                    name="2025_modification_integrity",
                    description="2025修改数据完整性",
                    level=ValidationLevel.HIGH,
                    validator_func="_validate_modification_2025_integrity"
                ),
                ValidationRule(
                    name="citation_validation",
                    description="引用验证",
                    level=ValidationLevel.MEDIUM,
                    validator_func="_validate_citations"
                )
            ]
        }

        return rules

    async def validate_all_components(self) -> dict[str, QualityReport]:
        """验证所有组件"""
        logger.info("开始数据质量验证...")

        reports = {}
        total_start_time = time.time()

        # 验证各个组件
        components = list(self.validation_rules.keys())
        for component in components:
            logger.info(f"\n验证组件: {component}")
            report = await self.validate_component(component)
            reports[component] = report

            # 更新统计
            self.stats["components_validated"] += 1
            if report.failed_rules > 0:
                self.stats["issues_found"] += report.failed_rules
            if report.error_rules > 0:
                self.stats["critical_issues"] += report.error_rules

        total_time = time.time() - total_start_time
        self.stats["total_validations"] += sum(r.total_rules for r in reports.values())

        logger.info(f"\n验证完成，总耗时: {total_time:.2f}s")
        return reports

    async def validate_component(self, component_name: str) -> QualityReport:
        """验证单个组件"""
        rules = self.validation_rules.get(component_name, [])
        results = []

        start_time = time.time()

        for rule in rules:
            if not rule.enabled:
                results.append(ValidationResult(
                    rule_name=rule.name,
                    status=ValidationStatus.SKIPPED,
                    level=rule.level,
                    message="规则已禁用",
                    timestamp=datetime.now()
                ))
                continue

            try:
                rule_start_time = time.time()
                result = await self._execute_validation_rule(rule)
                result.execution_time = time.time() - rule_start_time
                results.append(result)

                status_icon = "✅" if result.status == ValidationStatus.PASSED else "❌"
                logger.info(f"  {status_icon} {rule.name}: {result.status.value}")

            except Exception as e:
                logger.error(f"  ❌ {rule.name}: 验证失败 - {e}")
                results.append(ValidationResult(
                    rule_name=rule.name,
                    status=ValidationStatus.ERROR,
                    level=ValidationLevel.HIGH,
                    message=f"验证执行失败: {str(e)}",
                    timestamp=datetime.now()
                ))

        # 计算统计信息
        validation_time = time.time() - start_time
        total_rules = len(results)
        passed_rules = sum(1 for r in results if r.status == ValidationStatus.PASSED)
        failed_rules = sum(1 for r in results if r.status == ValidationStatus.FAILED)
        warning_rules = sum(1 for r in results if r.status == ValidationStatus.WARNING)
        skipped_rules = sum(1 for r in results if r.status == ValidationStatus.SKIPPED)
        error_rules = sum(1 for r in results if r.status == ValidationStatus.ERROR)

        # 计算质量分数
        score = self._calculate_quality_score(passed_rules, failed_rules, warning_rules, error_rules)

        return QualityReport(
            component=component_name,
            total_rules=total_rules,
            passed_rules=passed_rules,
            failed_rules=failed_rules,
            warning_rules=warning_rules,
            skipped_rules=skipped_rules,
            error_rules=error_rules,
            validation_time=validation_time,
            results=results,
            score=score
        )

    async def _execute_validation_rule(self, rule: ValidationRule) -> ValidationResult:
        """执行验证规则"""
        validator = getattr(self, rule.validator_func)
        parameters = rule.parameters or {}

        # 执行验证
        passed, message, details = await validator(**parameters)

        # 确定状态
        if passed:
            status = ValidationStatus.PASSED
        elif "警告" in message:
            status = ValidationStatus.WARNING
        else:
            status = ValidationStatus.FAILED

        return ValidationResult(
            rule_name=rule.name,
            status=status,
            level=rule.level,
            message=message,
            details=details,
            timestamp=datetime.now()
        )

    # 向量存储验证规则
    async def _validate_vector_dimensions(self) -> tuple[bool, str, dict]:
        """验证向量维度一致性"""
        try:
            collection_file = self.data_dir / "qdrant_store" / "patent_rules.json"

            if not collection_file.exists():
                return False, "向量存储文件不存在", {}

            with open(collection_file, encoding='utf-8') as f:
                data = json.load(f)

            if not data:
                return False, "向量存储为空", {}

            # 检查维度一致性
            dimensions = set()
            for item in data[:100]:  # 抽样检查
                vector = item.get("vector", [])
                if vector:
                    dimensions.add(len(vector))

            if len(dimensions) == 1:
                dimension = dimensions.pop()
                details = {"dimension": dimension, "sample_count": len(data)}
                return True, f"向量维度一致: {dimension}维", details
            else:
                details = {"dimensions": list(dimensions), "inconsistent": True}
                return False, f"向量维度不一致: {dimensions}", details

        except Exception as e:
            return False, f"验证失败: {str(e)}", {"error": str(e)}

    async def _validate_vector_normalization(self) -> tuple[bool, str, dict]:
        """验证向量归一化"""
        try:
            collection_file = self.data_dir / "qdrant_store" / "patent_rules.json"

            if not collection_file.exists():
                return False, "向量存储文件不存在", {}

            with open(collection_file, encoding='utf-8') as f:
                data = json.load(f)

            # 检查向量归一化
            norms = []
            for item in data[:50]:  # 抽样检查
                vector = item.get("vector", [])
                if vector:
                    norm = np.linalg.norm(vector)
                    norms.append(norm)

            if not norms:
                return False, "没有找到向量数据", {}

            avg_norm = np.mean(norms)
            std_norm = np.std(norms)

            # 判断是否归一化（理想情况下范数应该接近1）
            is_normalized = 0.95 <= avg_norm <= 1.05 and std_norm < 0.1

            details = {
                "avg_norm": float(avg_norm),
                "std_norm": float(std_norm),
                "sample_count": len(norms)
            }

            if is_normalized:
                return True, "向量已正确归一化", details
            else:
                return False, f"向量未归一化，平均范数: {avg_norm:.3f}", details

        except Exception as e:
            return False, f"验证失败: {str(e)}", {"error": str(e)}

    async def _validate_duplicate_vectors(self) -> tuple[bool, str, dict]:
        """检查重复向量"""
        try:
            collection_file = self.data_dir / "qdrant_store" / "patent_rules.json"

            if not collection_file.exists():
                return False, "向量存储文件不存在", {}

            with open(collection_file, encoding='utf-8') as f:
                data = json.load(f)

            # 检查重复向量
            vector_hashes = {}
            duplicates = []

            for item in data:
                vector = item.get("vector", [])
                if vector:
                    # 使用哈希值快速比较
                    vector_hash = short_hash(str(vector).encode())

                    if vector_hash in vector_hashes:
                        duplicates.append({
                            "id": item.get("id"),
                            "duplicate_of": vector_hashes[vector_hash]
                        })
                    else:
                        vector_hashes[vector_hash] = item.get("id")

            duplicate_rate = len(duplicates) / len(data) if data else 0

            details = {
                "total_vectors": len(data),
                "duplicate_count": len(duplicates),
                "duplicate_rate": duplicate_rate,
                "duplicates": duplicates[:5]  # 只保留前5个示例
            }

            if duplicate_rate < 0.01:  # 少于1%的重复
                return True, f"重复向量很少: {len(duplicates)}个", details
            else:
                return False, f"发现较多重复向量: {len(duplicates)}个 ({duplicate_rate:.1%})", details

        except Exception as e:
            return False, f"验证失败: {str(e)}", {"error": str(e)}

    async def _validate_similarity_distribution(self) -> tuple[bool, str, dict]:
        """分析向量相似度分布"""
        try:
            collection_file = self.data_dir / "qdrant_store" / "patent_rules.json"

            if not collection_file.exists():
                return False, "向量存储文件不存在", {}

            with open(collection_file, encoding='utf-8') as f:
                data = json.load(f)

            # 计算相似度分布
            vectors = [item.get("vector", []) for item in data[:100] if item.get("vector")]

            if len(vectors) < 2:
                return False, "向量数量不足", {}

            # 随机抽样计算相似度
            similarities = []
            import random
            random.seed(42)

            for _ in range(min(500, len(vectors) * 10)):
                v1, v2 = random.sample(vectors, 2)
                similarity = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
                similarities.append(similarity)

            avg_similarity = np.mean(similarities)
            std_similarity = np.std(similarities)

            details = {
                "sample_count": len(similarities),
                "avg_similarity": float(avg_similarity),
                "std_similarity": float(std_similarity),
                "min_similarity": float(min(similarities)),
                "max_similarity": float(max(similarities))
            }

            # 相似度分布应该合理（不过高也不过低）
            if 0.2 <= avg_similarity <= 0.6:
                return True, f"相似度分布正常: 平均{avg_similarity:.3f}", details
            else:
                return False, f"相似度分布异常: 平均{avg_similarity:.3f}", details

        except Exception as e:
            return False, f"验证失败: {str(e)}", {"error": str(e)}

    async def _validate_document_completeness(self) -> tuple[bool, str, dict]:
        """验证文档完整性"""
        try:
            collection_file = self.data_dir / "qdrant_store" / "patent_rules.json"

            if not collection_file.exists():
                return False, "向量存储文件不存在", {}

            with open(collection_file, encoding='utf-8') as f:
                data = json.load(f)

            # 检查必填字段
            required_fields = ["id", "vector", "payload"]
            missing_fields = []
            incomplete_docs = []

            for item in data:
                doc_id = item.get("id")
                missing = []

                for field in required_fields:
                    if field not in item or not item[field]:
                        missing.append(field)

                if missing:
                    incomplete_docs.append({
                        "id": doc_id,
                        "missing_fields": missing
                    })
                    missing_fields.extend(missing)

            completeness_rate = 1 - len(incomplete_docs) / len(data) if data else 0

            details = {
                "total_documents": len(data),
                "complete_documents": len(data) - len(incomplete_docs),
                "incomplete_documents": len(incomplete_docs),
                "completeness_rate": completeness_rate,
                "missing_fields_distribution": {}
            }

            # 统计缺失字段分布
            for doc in incomplete_docs:
                for field in doc["missing_fields"]:
                    details["missing_fields_distribution"][field] = \
                        details["missing_fields_distribution"].get(field, 0) + 1

            if completeness_rate >= 0.95:
                return True, f"文档完整性好: {completeness_rate:.1%}", details
            else:
                return False, f"文档完整性不足: {completeness_rate:.1%}", details

        except Exception as e:
            return False, f"验证失败: {str(e)}", {"error": str(e)}

    # 实体提取验证规则
    async def _validate_entity_consistency(self) -> tuple[bool, str, dict]:
        """验证实体一致性"""
        try:
            # 检查提取的示例数据
            example_file = self.data_dir / "bert_extraction_example.json"

            if not example_file.exists():
                # 创建测试数据
                await self._create_test_extraction_data()

            with open(example_file, encoding='utf-8') as f:
                data = json.load(f)

            entities = data.get("entities", [])

            # 检查实体一致性
            issues = []
            entity_types = set()

            for entity in entities:
                # 检查必填字段
                if "entity_text" not in entity or not entity["entity_text"]:
                    issues.append("实体文本为空")

                if "entity_type" not in entity:
                    issues.append("缺少实体类型")
                else:
                    entity_types.add(entity["entity_type"])

                # 检查置信度
                confidence = entity.get("confidence", 0)
                if confidence < 0 or confidence > 1:
                    issues.append(f"置信度无效: {confidence}")

            details = {
                "total_entities": len(entities),
                "entity_types": list(entity_types),
                "issues_count": len(issues),
                "issues": issues[:5]  # 只显示前5个问题
            }

            if len(issues) == 0:
                return True, f"实体数据一致，共{len(entities)}个实体", details
            else:
                return False, f"发现{len(issues)}个一致性问题", details

        except Exception as e:
            return False, f"验证失败: {str(e)}", {"error": str(e)}

    async def _create_test_extraction_data(self):
        """创建测试提取数据"""
        from bert_extractor_simple import PatentEntityRelationExtractor

        extractor = PatentEntityRelationExtractor()

        # 创建测试文档
        test_docs = [
            {
                "doc_id": "validation_test_001",
                "content": "专利法第一条为了保护专利权人的合法权益，鼓励发明创造。2025年修改新增了AI相关发明的审查标准。",
                "metadata": {}
            },
            {
                "doc_id": "validation_test_002",
                "content": "发明专利的保护期限为二十年，实用新型专利权为十年。审查指南规定了申请的具体流程。",
                "metadata": {}
            }
        ]

        results = []
        for doc in test_docs:
            result = await extractor.extract(doc["content"], doc["doc_id"])

            # 转换为存储格式
            doc_result = {
                "doc_id": result.doc_id,
                "entities": [
                    {
                        "entity_id": e.entity_id,
                        "entity_type": e.entity_type.value,
                        "entity_text": e.entity_text,
                        "confidence": e.confidence
                    } for e in result.entities
                ],
                "relations": [
                    {
                        "relation_id": r.relation_id,
                        "relation_type": r.relation_type.value,
                        "confidence": r.confidence
                    } for r in result.relations
                ],
                "statistics": result.statistics
            }
            results.append(doc_result)

        # 保存测试数据
        example_file = self.data_dir / "bert_extraction_example.json"
        with open(example_file, 'w', encoding='utf-8') as f:
            json.dump(results[0], f, ensure_ascii=False, indent=2)

    async def _validate_entity_confidence(self) -> tuple[bool, str, dict]:
        """验证实体置信度"""
        try:
            example_file = self.data_dir / "bert_extraction_example.json"

            if not example_file.exists():
                return False, "提取示例数据不存在", {}

            with open(example_file, encoding='utf-8') as f:
                data = json.load(f)

            entities = data.get("entities", [])

            if not entities:
                return False, "没有实体数据", {}

            # 分析置信度分布
            confidences = [e.get("confidence", 0) for e in entities]
            avg_confidence = np.mean(confidences)
            low_confidence_count = sum(1 for c in confidences if c < self.quality_benchmarks["entity_confidence_threshold"])

            details = {
                "total_entities": len(entities),
                "avg_confidence": float(avg_confidence),
                "min_confidence": min(confidences),
                "max_confidence": max(confidences),
                "low_confidence_count": low_confidence_count,
                "threshold": self.quality_benchmarks["entity_confidence_threshold"]
            }

            if low_confidence_count / len(entities) < 0.1:
                return True, f"实体置信度良好: 平均{avg_confidence:.3f}", details
            else:
                return False, f"过多低置信度实体: {low_confidence_count}/{len(entities)}", details

        except Exception as e:
            return False, f"验证失败: {str(e)}", {"error": str(e)}

    async def _validate_entity_type_coverage(self) -> tuple[bool, str, dict]:
        """检查实体类型覆盖"""
        try:
            example_file = self.data_dir / "bert_extraction_example.json"

            if not example_file.exists():
                return False, "提取示例数据不存在", {}

            with open(example_file, encoding='utf-8') as f:
                data = json.load(f)

            entities = data.get("entities", [])

            # 统计实体类型
            type_counts = {}
            for entity in entities:
                entity_type = entity.get("entity_type", "")
                type_counts[entity_type] = type_counts.get(entity_type, 0) + 1

            # 期望的实体类型（至少应该有一些）
            expected_types = ["法律条文", "概念", "2025年修改", "审查指南"]
            found_types = [t for t in expected_types if t in type_counts]

            details = {
                "total_types": len(type_counts),
                "type_distribution": type_counts,
                "expected_types_found": found_types,
                "coverage_rate": len(found_types) / len(expected_types)
            }

            if len(found_types) >= 2:  # 至少找到2种期望类型
                return True, f"实体类型覆盖良好: {len(found_types)}/{len(expected_types)}", details
            else:
                return False, f"实体类型覆盖不足: {len(found_types)}/{len(expected_types)}", details

        except Exception as e:
            return False, f"验证失败: {str(e)}", {"error": str(e)}

    async def _validate_relations(self) -> tuple[bool, str, dict]:
        """验证关系提取"""
        try:
            example_file = self.data_dir / "bert_extraction_example.json"

            if not example_file.exists():
                return False, "提取示例数据不存在", {}

            with open(example_file, encoding='utf-8') as f:
                data = json.load(f)

            relations = data.get("relations", [])

            # 检查关系质量
            issues = []
            relation_types = set()

            for relation in relations:
                # 检查必填字段
                if "relation_type" not in relation:
                    issues.append("缺少关系类型")
                else:
                    relation_types.add(relation["relation_type"])

                # 检查置信度
                confidence = relation.get("confidence", 0)
                if confidence < 0 or confidence > 1:
                    issues.append(f"关系置信度无效: {confidence}")

            details = {
                "total_relations": len(relations),
                "relation_types": list(relation_types),
                "issues_count": len(issues)
            }

            if len(issues) == 0:
                return True, f"关系数据良好，共{len(relations)}个关系", details
            else:
                return False, f"关系数据有问题: {len(issues)}个问题", details

        except Exception as e:
            return False, f"验证失败: {str(e)}", {"error": str(e)}

    # 知识图谱验证规则
    async def _validate_graph_connectivity(self) -> tuple[bool, str, dict]:
        """验证图谱连通性"""
        try:
            vertices_file = self.data_dir / "knowledge_graph" / "vertices.json"
            edges_file = self.data_dir / "knowledge_graph" / "edges.json"

            if not vertices_file.exists() or not edges_file.exists():
                return False, "知识图谱文件不存在", {}

            with open(vertices_file, encoding='utf-8') as f:
                vertices = json.load(f)

            with open(edges_file, encoding='utf-8') as f:
                edges = json.load(f)

            # 构建邻接表
            adjacents = {}
            for edge in edges:
                src = edge.get("src")
                dst = edge.get("dst")

                if src not in adjacents:
                    adjacents[src] = []
                if dst not in adjacents:
                    adjacents[dst] = []

                adjacents[src].append(dst)
                adjacents[dst].append(src)

            # 计算连通性
            connected_nodes = 0
            isolated_nodes = 0

            for vertex in vertices:
                vertex_id = vertex.get("vertex_id")
                if vertex_id in adjacents and adjacents[vertex_id]:
                    connected_nodes += 1
                else:
                    isolated_nodes += 1

            connectivity_rate = connected_nodes / len(vertices) if vertices else 0

            details = {
                "total_vertices": len(vertices),
                "total_edges": len(edges),
                "connected_nodes": connected_nodes,
                "isolated_nodes": isolated_nodes,
                "connectivity_rate": connectivity_rate
            }

            if connectivity_rate >= self.quality_benchmarks["graph_connectivity_threshold"]:
                return True, f"图谱连通性良好: {connectivity_rate:.1%}", details
            else:
                return False, f"图谱连通性不足: {connectivity_rate:.1%}", details

        except Exception as e:
            return False, f"验证失败: {str(e)}", {"error": str(e)}

    async def _validate_node_type_distribution(self) -> tuple[bool, str, dict]:
        """检查节点类型分布"""
        try:
            vertices_file = self.data_dir / "knowledge_graph" / "vertices.json"

            if not vertices_file.exists():
                return False, "知识图谱文件不存在", {}

            with open(vertices_file, encoding='utf-8') as f:
                vertices = json.load(f)

            # 统计节点类型
            type_counts = {}
            for vertex in vertices:
                vertex_type = vertex.get("type", "")
                type_counts[vertex_type] = type_counts.get(vertex_type, 0) + 1

            # 检查关键节点类型
            key_types = ["Document", "LawArticle", "Concept", "Modification2025"]
            found_key_types = [t for t in key_types if t in type_counts]

            details = {
                "total_vertices": len(vertices),
                "type_distribution": type_counts,
                "key_types_found": found_key_types,
                "type_diversity": len(type_counts)
            }

            if len(found_key_types) >= 3:
                return True, f"节点类型分布良好: {len(type_counts)}种类型", details
            else:
                return False, f"关键节点类型不足: {len(found_key_types)}/4", details

        except Exception as e:
            return False, f"验证失败: {str(e)}", {"error": str(e)}

    async def _validate_edge_validation(self) -> tuple[bool, str, dict]:
        """验证边关系"""
        try:
            edges_file = self.data_dir / "knowledge_graph" / "edges.json"

            if not edges_file.exists():
                return False, "知识图谱文件不存在", {}

            with open(edges_file, encoding='utf-8') as f:
                edges = json.load(f)

            # 检查边的有效性
            valid_edges = 0
            edge_types = set()
            issues = []

            for edge in edges:
                src = edge.get("src")
                dst = edge.get("dst")
                edge_type = edge.get("type")

                # 检查必填字段
                if not src or not dst:
                    issues.append("边缺少源或目标节点")
                    continue

                if edge_type:
                    edge_types.add(edge_type)

                valid_edges += 1

            details = {
                "total_edges": len(edges),
                "valid_edges": valid_edges,
                "edge_types": list(edge_types),
                "issues_count": len(issues)
            }

            if len(issues) == 0:
                return True, f"边关系良好: {valid_edges}个有效边", details
            else:
                return False, f"边关系有问题: {len(issues)}个问题", details

        except Exception as e:
            return False, f"验证失败: {str(e)}", {"error": str(e)}

    async def _validate_orphan_nodes(self) -> tuple[bool, str, dict]:
        """检查孤立节点"""
        try:
            vertices_file = self.data_dir / "knowledge_graph" / "vertices.json"
            edges_file = self.data_dir / "knowledge_graph" / "edges.json"

            if not vertices_file.exists() or not edges_file.exists():
                return False, "知识图谱文件不存在", {}

            with open(vertices_file, encoding='utf-8') as f:
                vertices = json.load(f)

            with open(edges_file, encoding='utf-8') as f:
                edges = json.load(f)

            # 找出所有连接的节点
            connected_nodes = set()
            for edge in edges:
                connected_nodes.add(edge.get("src"))
                connected_nodes.add(edge.get("dst"))

            # 找出孤立节点
            orphan_nodes = []
            for vertex in vertices:
                vertex_id = vertex.get("vertex_id")
                if vertex_id not in connected_nodes:
                    orphan_nodes.append(vertex)

            orphan_rate = len(orphan_nodes) / len(vertices) if vertices else 0

            details = {
                "total_vertices": len(vertices),
                "connected_nodes": len(connected_nodes),
                "orphan_nodes": len(orphan_nodes),
                "orphan_rate": orphan_rate,
                "orphan_node_ids": [v.get("vertex_id") for v in orphan_nodes[:5]]
            }

            if orphan_rate < 0.1:  # 少于10%的孤立节点
                return True, f"孤立节点较少: {len(orphan_nodes)}个", details
            else:
                return False, f"孤立节点较多: {len(orphan_nodes)}个 ({orphan_rate:.1%})", details

        except Exception as e:
            return False, f"验证失败: {str(e)}", {"error": str(e)}

    # 数据一致性验证规则
    async def _validate_cross_component_consistency(self) -> tuple[bool, str, dict]:
        """跨组件一致性检查"""
        try:
            # 检查文档在各组件中的一致性
            consistency_issues = []

            # 检查向量存储和实体提取的一致性
            collection_file = self.data_dir / "qdrant_store" / "patent_rules.json"
            extraction_file = self.data_dir / "bert_extraction_example.json"

            doc_ids_vector = set()
            doc_ids_entity = set()

            if collection_file.exists():
                with open(collection_file, encoding='utf-8') as f:
                    vector_data = json.load(f)
                    doc_ids_vector = {item.get("id") for item in vector_data}

            if extraction_file.exists():
                with open(extraction_file, encoding='utf-8') as f:
                    entity_data = json.load(f)
                    doc_ids_entity.add(entity_data.get("doc_id"))

            # 检查文档ID一致性
            if doc_ids_vector and doc_ids_entity:
                intersection = doc_ids_vector & doc_ids_entity
                if not intersection:
                    consistency_issues.append("向量存储和实体提取没有共同的文档ID")

            details = {
                "vector_doc_count": len(doc_ids_vector),
                "entity_doc_count": len(doc_ids_entity),
                "common_doc_count": len(doc_ids_vector & doc_ids_entity),
                "issues": consistency_issues
            }

            if len(consistency_issues) == 0:
                return True, "跨组件数据一致性良好", details
            else:
                return False, f"发现{len(consistency_issues)}个一致性问题", details

        except Exception as e:
            return False, f"验证失败: {str(e)}", {"error": str(e)}

    async def _validate_modification_2025_integrity(self) -> tuple[bool, str, dict]:
        """2025修改数据完整性"""
        try:
            # 检查各组件中2025修改数据的完整性
            mod_2025_found = {
                "vector_store": False,
                "entity_extraction": False,
                "knowledge_graph": False
            }

            # 检查向量存储
            collection_file = self.data_dir / "qdrant_store" / "patent_rules.json"
            if collection_file.exists():
                with open(collection_file, encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data:
                        payload = item.get("payload", {})
                        if "2025" in payload.get("doc_type", "") or "2025" in payload.get("content", ""):
                            mod_2025_found["vector_store"] = True
                            break

            # 检查实体提取
            extraction_file = self.data_dir / "bert_extraction_example.json"
            if extraction_file.exists():
                with open(extraction_file, encoding='utf-8') as f:
                    data = json.load(f)
                    entities = data.get("entities", [])
                    for entity in entities:
                        if "2025" in entity.get("entity_type", "") or "2025" in entity.get("entity_text", ""):
                            mod_2025_found["entity_extraction"] = True
                            break

            # 检查知识图谱
            vertices_file = self.data_dir / "knowledge_graph" / "vertices.json"
            if vertices_file.exists():
                with open(vertices_file, encoding='utf-8') as f:
                    vertices = json.load(f)
                    for vertex in vertices:
                        if "Modification2025" in vertex.get("type", ""):
                            mod_2025_found["knowledge_graph"] = True
                            break

            coverage = sum(mod_2025_found.values()) / len(mod_2025_found)

            details = {
                "component_coverage": mod_2025_found,
                "coverage_rate": coverage
            }

            if coverage >= 0.66:  # 至少2/3的组件有2025数据
                return True, f"2025修改数据完整性良好: {coverage:.1%}", details
            else:
                return False, f"2025修改数据完整性不足: {coverage:.1%}", details

        except Exception as e:
            return False, f"验证失败: {str(e)}", {"error": str(e)}

    async def _validate_citations(self) -> tuple[bool, str, dict]:
        """引用验证"""
        try:
            # 检查引用的格式和有效性
            citation_pattern = r'第[一二三四五六七八九十\d]+条'

            # 从各组件提取引用
            all_citations = []

            # 从向量存储提取
            collection_file = self.data_dir / "qdrant_store" / "patent_rules.json"
            if collection_file.exists():
                with open(collection_file, encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data:
                        content = item.get("payload", {}).get("content", "")
                        citations = re.findall(citation_pattern, content)
                        all_citations.extend(citations)

            # 验证引用格式
            valid_citations = []
            invalid_citations = []

            for citation in set(all_citations):
                if re.match(r'^第[一二三四五六七八九十\d]+条$', citation):
                    valid_citations.append(citation)
                else:
                    invalid_citations.append(citation)

            details = {
                "total_citations": len(all_citations),
                "unique_citations": len(set(all_citations)),
                "valid_citations": len(valid_citations),
                "invalid_citations": len(invalid_citations),
                "sample_citations": list(set(all_citations))[:10]
            }

            if len(invalid_citations) == 0:
                return True, f"引用格式正确: {len(valid_citations)}个引用", details
            else:
                return False, f"发现无效引用: {len(invalid_citations)}个", details

        except Exception as e:
            return False, f"验证失败: {str(e)}", {"error": str(e)}

    def _calculate_quality_score(self, passed: int, failed: int, warning: int, error: int) -> float:
        """计算质量分数"""
        total = passed + failed + warning + error
        if total == 0:
            return 0

        # 基础分数
        base_score = (passed / total) * 100

        # 失败和错误的惩罚
        penalty = (failed * 10) + (error * 20)

        # 警告的小幅惩罚
        warning_penalty = warning * 2

        final_score = max(0, base_score - penalty - warning_penalty)
        return min(100, final_score)

    async def generate_quality_report(self) -> dict[str, Any]:
        """生成质量报告"""
        logger.info("生成数据质量报告...")

        # 执行所有验证
        reports = await self.validate_all_components()

        # 计算总体分数
        total_score = sum(r.score for r in reports.values()) / len(reports)

        # 生成报告
        quality_report = {
            "report_time": datetime.now().isoformat(),
            "overall_score": total_score,
            "grade": self._get_grade(total_score),
            "components": {}
        }

        # 组件详情
        for component, report in reports.items():
            quality_report["components"][component] = {
                "score": report.score,
                "grade": self._get_grade(report.score),
                "total_rules": report.total_rules,
                "passed_rules": report.passed_rules,
                "failed_rules": report.failed_rules,
                "warning_rules": report.warning_rules,
                "error_rules": report.error_rules,
                "validation_time": report.validation_time,
                "summary": self._generate_component_summary(report)
            }

        # 关键问题
        critical_issues = []
        for component, report in reports.items():
            for result in report.results:
                if result.level == ValidationLevel.CRITICAL and result.status != ValidationStatus.PASSED:
                    critical_issues.append({
                        "component": component,
                        "rule": result.rule_name,
                        "message": result.message
                    })

        quality_report["critical_issues"] = critical_issues
        quality_report["recommendations"] = self._generate_recommendations(reports)

        # 保存报告
        report_file = self.data_dir / "quality_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(quality_report, f, ensure_ascii=False, indent=2)

        logger.info(f"质量报告已保存: {report_file}")
        return quality_report

    def _get_grade(self, score: float) -> str:
        """获取等级"""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"

    def _generate_component_summary(self, report: QualityReport) -> str:
        """生成组件摘要"""
        if report.score >= 90:
            return f"优秀 - {report.passed_rules}/{report.total_rules} 规则通过"
        elif report.score >= 70:
            return f"良好 - {report.failed_rules} 个规则需要改进"
        elif report.score >= 50:
            return f"一般 - {report.failed_rules} 个规则失败"
        else:
            return f"需要改进 - {report.failed_rules + report.error_rules} 个严重问题"

    def _generate_recommendations(self, reports: dict[str, QualityReport]) -> list[str]:
        """生成改进建议"""
        recommendations = []

        for component, report in reports.items():
            if report.score < 70:
                recommendations.append(f"优先修复 {component} 组件的问题")

            # 具体建议
            if component == "vector_store" and report.score < 80:
                recommendations.append("重新生成向量并确保归一化")

            if component == "entity_extraction" and report.score < 80:
                recommendations.append("调整实体提取模型参数")

            if component == "knowledge_graph" and report.score < 80:
                recommendations.append("增强图谱连通性，减少孤立节点")

        if not recommendations:
            recommendations.append("数据质量良好，继续保持")

        return recommendations

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "quality_benchmarks": self.quality_benchmarks
        }

# 使用示例
async def main():
    """主函数示例"""
    validator = DataQualityValidator()

    # 生成质量报告
    report = await validator.generate_quality_report()

    print("\n数据质量报告")
    print("="*50)
    print(f"总体分数: {report['overall_score']:.1f} ({report['grade']})")

    for component, info in report['components'].items():
        print(f"\n{component}:")
        print(f"  分数: {info['score']:.1f} ({info['grade']})")
        print(f"  摘要: {info['summary']}")

    if report['critical_issues']:
        print("\n关键问题:")
        for issue in report['critical_issues']:
            print(f"  - {issue['component']}: {issue['message']}")

    print("\n改进建议:")
    for rec in report['recommendations']:
        print(f"  - {rec}")

if __name__ == "__main__":
    asyncio.run(main())
