#!/usr/bin/env python3
"""
专利规则构建系统 - 自动化测试套件
Patent Rules Builder - Automated Test Suite

完整的自动化测试系统，包含单元测试、集成测试、性能测试和回归测试

作者: Athena平台团队
创建时间: 2025-12-20
版本: v1.0.0
"""

from __future__ import annotations
import asyncio
import json
import logging

# 导入系统组件
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

sys.path.append(str(Path(__file__).parent))

from bert_extractor_simple import PatentEntityRelationExtractor
from nebula_graph_builder import NebulaGraphBuilder
from ollama_rag_system import OllamaRAGSystem
from qdrant_vector_store_simple import QdrantVectorStoreSimple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestType(Enum):
    """测试类型"""
    UNIT = "单元测试"
    INTEGRATION = "集成测试"
    PERFORMANCE = "性能测试"
    REGRESSION = "回归测试"
    SMOKE = "冒烟测试"
    STRESS = "压力测试"

class TestStatus(Enum):
    """测试状态"""
    PASSED = "通过"
    FAILED = "失败"
    SKIPPED = "跳过"
    ERROR = "错误"
    TIMEOUT = "超时"

class TestPriority(Enum):
    """测试优先级"""
    CRITICAL = "关键"
    HIGH = "高"
    MEDIUM = "中"
    LOW = "低"

@dataclass
class TestCase:
    """测试用例"""
    id: str
    name: str
    description: str
    test_type: TestType
    priority: TestPriority
    test_func: str
    parameters: dict[str, Any] = None
    timeout: int = 60
    enabled: bool = True
    tags: list[str] = None

@dataclass
class TestResult:
    """测试结果"""
    test_id: str
    test_name: str
    status: TestStatus
    duration: float
    message: str
    details: dict[str, Any] = None
    error: str | None = None
    start_time: datetime = None
    end_time: datetime = None

@dataclass
class TestSuiteResult:
    """测试套件结果"""
    suite_name: str
    test_type: TestType
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    error_tests: int
    timeout_tests: int
    total_duration: float
    results: list[TestResult]
    success_rate: float

class AutomatedTestSuite:
    """自动化测试套件"""

    def __init__(self,
                 test_data_dir: str = "/Users/xujian/Athena工作平台/production/test_data",
                 report_dir: str = "/Users/xujian/Athena工作平台/production/test_reports"):
        self.test_data_dir = Path(test_data_dir)
        self.report_dir = Path(report_dir)

        # 确保目录存在
        self.test_data_dir.mkdir(parents=True, exist_ok=True)
        self.report_dir.mkdir(parents=True, exist_ok=True)

        # 初始化测试用例
        self.test_cases = self._define_test_cases()

        # 测试历史
        self.test_history = []

        # 性能基准
        self.performance_benchmarks = {
            "vector_search_time": 0.1,  # 100ms
            "entity_extraction_time": 1.0,  # 1s
            "rag_response_time": 2.0,  # 2s
            "batch_processing_time": 5.0  # 5s for 10 items
        }

    def _define_test_cases(self) -> dict[TestType, list[TestCase]]:
        """定义测试用例"""
        test_cases = {
            TestType.UNIT: [
                TestCase(
                    id="VEC_001",
                    name="向量生成测试",
                    description="测试向量生成功能",
                    test_type=TestType.UNIT,
                    priority=TestPriority.HIGH,
                    test_func="test_vector_generation",
                    tags=["vector", "generation"]
                ),
                TestCase(
                    id="ENT_001",
                    name="实体提取测试",
                    description="测试实体提取功能",
                    test_type=TestType.UNIT,
                    priority=TestPriority.HIGH,
                    test_func="test_entity_extraction",
                    tags=["entity", "extraction"]
                ),
                TestCase(
                    id="GRPH_001",
                    name="知识图谱构建测试",
                    description="测试知识图谱构建",
                    test_type=TestType.UNIT,
                    priority=TestPriority.MEDIUM,
                    test_func="test_graph_construction",
                    tags=["graph", "construction"]
                )
            ],
            TestType.INTEGRATION: [
                TestCase(
                    id="INT_001",
                    name="端到端RAG测试",
                    description="测试完整的RAG流程",
                    test_type=TestType.INTEGRATION,
                    priority=TestPriority.CRITICAL,
                    test_func="test_end_to_end_rag",
                    timeout=120,
                    tags=["rag", "integration"]
                ),
                TestCase(
                    id="INT_002",
                    name="多组件协作测试",
                    description="测试组件间协作",
                    test_type=TestType.INTEGRATION,
                    priority=TestPriority.HIGH,
                    test_func="test_component_collaboration",
                    tags=["collaboration"]
                ),
                TestCase(
                    id="INT_003",
                    name="数据流测试",
                    description="测试数据在各组件间的流动",
                    test_type=TestType.INTEGRATION,
                    priority=TestPriority.MEDIUM,
                    test_func="test_data_flow",
                    tags=["data", "flow"]
                )
            ],
            TestType.PERFORMANCE: [
                TestCase(
                    id="PERF_001",
                    name="向量搜索性能测试",
                    description="测试向量搜索性能",
                    test_type=TestType.PERFORMANCE,
                    priority=TestPriority.HIGH,
                    test_func="test_vector_search_performance",
                    parameters={"batch_size": 100},
                    tags=["performance", "vector"]
                ),
                TestCase(
                    id="PERF_002",
                    name="批量处理性能测试",
                    description="测试批量处理性能",
                    test_type=TestType.PERFORMANCE,
                    priority=TestPriority.HIGH,
                    test_func="test_batch_processing_performance",
                    parameters={"batch_size": 50},
                    tags=["performance", "batch"]
                ),
                TestCase(
                    id="PERF_003",
                    name="并发处理测试",
                    description="测试并发处理能力",
                    test_type=TestType.PERFORMANCE,
                    priority=TestPriority.MEDIUM,
                    test_func="test_concurrent_processing",
                    parameters={"concurrency": 10},
                    tags=["performance", "concurrency"]
                )
            ],
            TestType.REGRESSION: [
                TestCase(
                    id="REG_001",
                    name="核心功能回归测试",
                    description="验证核心功能未退化",
                    test_type=TestType.REGRESSION,
                    priority=TestPriority.CRITICAL,
                    test_func="test_core_functionality_regression",
                    tags=["regression", "core"]
                ),
                TestCase(
                    id="REG_002",
                    name="2025修改功能测试",
                    description="验证2025修改相关功能",
                    test_type=TestType.REGRESSION,
                    priority=TestPriority.HIGH,
                    test_func="test_modification_2025_features",
                    tags=["regression", "2025"]
                )
            ],
            TestType.SMOKE: [
                TestCase(
                    id="SMOKE_001",
                    name="系统启动测试",
                    description="验证系统可以正常启动",
                    test_type=TestType.SMOKE,
                    priority=TestPriority.CRITICAL,
                    test_func="test_system_startup",
                    timeout=30,
                    tags=["smoke", "startup"]
                ),
                TestCase(
                    id="SMOKE_002",
                    name="基本功能验证",
                    description="验证基本功能可用",
                    test_type=TestType.SMOKE,
                    priority=TestPriority.CRITICAL,
                    test_func="test_basic_functionality",
                    tags=["smoke", "basic"]
                )
            ]
        }

        return test_cases

    async def run_test_suite(self,
                           test_types: list[TestType] = None,
                           tags: list[str] = None,
                           priority: TestPriority = None) -> dict[TestType, TestSuiteResult]:
        """运行测试套件"""
        logger.info("开始运行自动化测试套件...")

        # 确定要运行的测试
        if test_types is None:
            test_types = list(TestType)

        results = {}

        for test_type in test_types:
            logger.info(f"\n{'='*60}")
            logger.info(f"运行 {test_type.value}")
            logger.info(f"{'='*60}")

            # 获取该类型的测试用例
            test_cases = self.test_cases.get(test_type, [])

            # 过滤测试用例
            filtered_cases = self._filter_test_cases(test_cases, tags, priority)

            if not filtered_cases:
                logger.info(f"没有符合条件的{test_type.value}测试用例")
                continue

            # 运行测试
            result = await self._run_test_type(test_type, filtered_cases)
            results[test_type] = result

            # 打印摘要
            logger.info(f"\n{test_type.value}摘要:")
            logger.info(f"  总数: {result.total_tests}")
            logger.info(f"  通过: {result.passed_tests}")
            logger.info(f"  失败: {result.failed_tests}")
            logger.info(f"  跳过: {result.skipped_tests}")
            logger.info(f"  错误: {result.error_tests}")
            logger.info(f"  超时: {result.timeout_tests}")
            logger.info(f"  成功率: {result.success_rate:.1%}")
            logger.info(f"  耗时: {result.total_duration:.2f}s")

        # 保存测试结果
        await self._save_test_results(results)

        # 生成测试报告
        await self._generate_test_report(results)

        return results

    def _filter_test_cases(self,
                          test_cases: list[TestCase],
                          tags: list[str] = None,
                          priority: TestPriority = None) -> list[TestCase]:
        """过滤测试用例"""
        filtered = []

        for case in test_cases:
            if not case.enabled:
                continue

            # 按标签过滤
            if tags and not any(tag in case.tags for tag in tags):
                continue

            # 按优先级过滤
            if priority:
                priority_order = {
                    TestPriority.CRITICAL: 4,
                    TestPriority.HIGH: 3,
                    TestPriority.MEDIUM: 2,
                    TestPriority.LOW: 1
                }
                if priority_order[case.priority] < priority_order[priority]:
                    continue

            filtered.append(case)

        return filtered

    async def _run_test_type(self,
                            test_type: TestType,
                            test_cases: list[TestCase]) -> TestSuiteResult:
        """运行特定类型的测试"""
        results = []
        start_time = time.time()

        for case in test_cases:
            logger.info(f"\n运行测试: {case.name}")
            logger.info(f"  ID: {case.id}")
            logger.info(f"  描述: {case.description}")

            try:
                # 执行测试
                test_method = getattr(self, case.test_func)
                test_start_time = time.time()

                # 使用asyncio.wait_for处理超时
                test_result = await asyncio.wait_for(
                    test_method(case.parameters or {}),
                    timeout=case.timeout
                )

                test_duration = time.time() - test_start_time

                # 创建测试结果
                result = TestResult(
                    test_id=case.id,
                    test_name=case.name,
                    status=TestStatus.PASSED if test_result.get("success", False) else TestStatus.FAILED,
                    duration=test_duration,
                    message=test_result.get("message", ""),
                    details=test_result,
                    start_time=datetime.fromtimestamp(test_start_time),
                    end_time=datetime.now()
                )

                logger.info(f"  结果: {result.status.value}")
                logger.info(f"  耗时: {test_duration:.2f}s")
                if result.message:
                    logger.info(f"  消息: {result.message}")

            except asyncio.TimeoutError:
                result = TestResult(
                    test_id=case.id,
                    test_name=case.name,
                    status=TestStatus.TIMEOUT,
                    duration=case.timeout,
                    message=f"测试超时 ({case.timeout}s)",
                    error="TimeoutError"
                )
                logger.error("  ❌ 测试超时")

            except Exception as e:
                result = TestResult(
                    test_id=case.id,
                    test_name=case.name,
                    status=TestStatus.ERROR,
                    duration=0,
                    message="测试执行出错",
                    error=str(e)
                )
                logger.error(f"  ❌ 测试错误: {e}")

            results.append(result)

        # 计算统计信息
        total_duration = time.time() - start_time
        passed_tests = sum(1 for r in results if r.status == TestStatus.PASSED)
        failed_tests = sum(1 for r in results if r.status == TestStatus.FAILED)
        skipped_tests = sum(1 for r in results if r.status == TestStatus.SKIPPED)
        error_tests = sum(1 for r in results if r.status == TestStatus.ERROR)
        timeout_tests = sum(1 for r in results if r.status == TestStatus.TIMEOUT)

        success_rate = passed_tests / len(results) if results else 0

        return TestSuiteResult(
            suite_name=f"{test_type.value}测试套件",
            test_type=test_type,
            total_tests=len(results),
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            skipped_tests=skipped_tests,
            error_tests=error_tests,
            timeout_tests=timeout_tests,
            total_duration=total_duration,
            results=results,
            success_rate=success_rate
        )

    # 测试方法
    async def test_vector_generation(self, parameters: dict = None) -> dict:
        """测试向量生成"""
        try:
            vector_store = QdrantVectorStoreSimple(collection_name="test_vector_gen")
            await vector_store.create_collection()

            test_text = "专利法第一条为了保护专利权人的合法权益，鼓励发明创造"
            embedding = await vector_store.generate_embedding(test_text, "专利法")

            success = (
                len(embedding) == 1024 and
                all(isinstance(x, (int, float)) for x in embedding) and
                0 <= min(embedding) <= max(embedding) <= 1
            )

            return {
                "success": success,
                "message": f"向量生成成功，维度: {len(embedding)}" if success else "向量生成失败",
                "embedding_length": len(embedding),
                "min_value": min(embedding),
                "max_value": max(embedding)
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"向量生成失败: {str(e)}",
                "error": str(e)
            }

    async def test_entity_extraction(self, parameters: dict = None) -> dict:
        """测试实体提取"""
        try:
            extractor = PatentEntityRelationExtractor()

            test_text = """
            中华人民共和国专利法
            第一条 为了保护专利权人的合法权益，鼓励发明创造，制定本法。
            第二条 本法所称的发明创造是指发明、实用新型和外观设计。
            2025年修改：新增了人工智能相关发明的审查标准。
            """

            result = await extractor.extract_entities(test_text, "test_doc")

            success = (
                result.entities and
                len(result.entities) >= 3 and
                all(e.confidence > 0 for e in result.entities)
            )

            return {
                "success": success,
                "message": f"提取到{len(result.entities)}个实体" if success else "实体提取失败",
                "entity_count": len(result.entities),
                "avg_confidence": sum(e.confidence for e in result.entities) / len(result.entities) if result.entities else 0,
                "entity_types": list({e.entity_type.value for e in result.entities})
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"实体提取失败: {str(e)}",
                "error": str(e)
            }

    async def test_graph_construction(self, parameters: dict = None) -> dict:
        """测试知识图谱构建"""
        try:
            graph_builder = NebulaGraphBuilder()

            # 初始化空间
            success = await graph_builder.initialize_space()

            return {
                "success": success,
                "message": "知识图谱初始化成功" if success else "知识图谱初始化失败"
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"图谱构建失败: {str(e)}",
                "error": str(e)
            }

    async def test_end_to_end_rag(self, parameters: dict = None) -> dict:
        """测试端到端RAG"""
        try:
            rag = OllamaRAGSystem()

            # 测试查询
            query = "专利权的保护期限是多久？"
            response = await rag.process_query(query)

            success = (
                response and
                len(response.answer) > 0 and
                response.confidence >= 0
            )

            return {
                "success": success,
                "message": f"RAG响应成功，长度: {len(response.answer) if response else 0}",
                "response_length": len(response.answer) if response else 0,
                "confidence": response.confidence if response else 0,
                "processing_time": response.processing_time if response else 0
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"RAG测试失败: {str(e)}",
                "error": str(e)
            }

    async def test_component_collaboration(self, parameters: dict = None) -> dict:
        """测试组件协作"""
        try:
            # 初始化所有组件
            vector_store = QdrantVectorStoreSimple()
            extractor = PatentEntityRelationExtractor()
            graph_builder = NebulaGraphBuilder()

            # 测试数据流
            test_text = "专利保护期限为二十年"

            # 1. 向量化
            embedding = await vector_store.generate_embedding(test_text)
            vector_success = len(embedding) > 0

            # 2. 实体提取
            entities = await extractor.extract_entities(test_text)
            entity_success = len(entities.entities) > 0 if entities else False

            # 3. 图谱初始化
            graph_success = await graph_builder.initialize_space()

            overall_success = vector_success and entity_success and graph_success

            return {
                "success": overall_success,
                "message": "组件协作成功" if overall_success else "组件协作失败",
                "vector_success": vector_success,
                "entity_success": entity_success,
                "graph_success": graph_success
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"组件协作测试失败: {str(e)}",
                "error": str(e)
            }

    async def test_data_flow(self, parameters: dict = None) -> dict:
        """测试数据流"""
        try:
            # 创建测试文档
            from qdrant_vector_store_simple import DocumentType, VectorDocument

            doc = VectorDocument(
                doc_id="flow_test_001",
                content="发明专利的保护期限为二十年",
                doc_type=DocumentType.PATENT_LAW,
                metadata={"source": "test"}
            )

            # 测试数据在系统中的流动
            vector_store = QdrantVectorStoreSimple()
            await vector_store.create_collection()

            # 索引文档
            index_success = await vector_store.index_document(doc)

            # 搜索文档
            search_results = await vector_store.search("保护期限", top_k=1)
            search_success = len(search_results) > 0

            overall_success = index_success and search_success

            return {
                "success": overall_success,
                "message": "数据流测试成功" if overall_success else "数据流测试失败",
                "index_success": index_success,
                "search_success": search_success,
                "found_document": search_results[0].doc_id if search_results else None
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"数据流测试失败: {str(e)}",
                "error": str(e)
            }

    async def test_vector_search_performance(self, parameters: dict = None) -> dict:
        """测试向量搜索性能"""
        try:
            batch_size = parameters.get("batch_size", 100)
            vector_store = QdrantVectorStoreSimple(collection_name="perf_test")
            await vector_store.create_collection()

            # 生成测试数据
            from qdrant_vector_store_simple import DocumentType, VectorDocument

            logger.info(f"  生成{batch_size}个测试文档...")
            docs = []
            for i in range(batch_size):
                doc = VectorDocument(
                    doc_id=f"perf_doc_{i:04d}",
                    content=f"测试文档{i}的内容",
                    doc_type=DocumentType.PATENT_LAW,
                    metadata={"index": i}
                )
                docs.append(doc)

            # 批量索引
            logger.info(f"  索引{batch_size}个文档...")
            start_time = time.time()
            await vector_store.batch_index(docs)
            index_time = time.time() - start_time

            # 测试搜索性能
            logger.info("  测试搜索性能...")
            queries = ["专利", "发明", "保护", "权利", "申请"]
            search_times = []

            for query in queries:
                start_time = time.time()
                results = await vector_store.search(query, top_k=10)
                search_time = time.time() - start_time
                search_times.append(search_time)

            avg_search_time = sum(search_times) / len(search_times)
            max_search_time = max(search_times)

            benchmark = self.performance_benchmarks["vector_search_time"]
            success = avg_search_time <= benchmark

            return {
                "success": success,
                "message": f"搜索性能{'达标' if success else '不达标'}",
                "batch_size": batch_size,
                "index_time": index_time,
                "avg_search_time": avg_search_time,
                "max_search_time": max_search_time,
                "benchmark": benchmark,
                "search_results": [len(await vector_store.search(q, top_k=10)) for q in queries]
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"性能测试失败: {str(e)}",
                "error": str(e)
            }

    async def test_batch_processing_performance(self, parameters: dict = None) -> dict:
        """测试批量处理性能"""
        try:
            batch_size = parameters.get("batch_size", 50)
            rag = OllamaRAGSystem()

            # 生成测试查询
            queries = [
                f"专利{i}的问题" for i in range(batch_size)
            ]

            # 批量处理
            logger.info(f"  批量处理{batch_size}个查询...")
            start_time = time.time()
            responses = await rag.batch_process(queries)
            processing_time = time.time() - start_time

            # 计算指标
            successful_responses = sum(1 for r in responses if r and len(r.answer) > 0)
            avg_time_per_query = processing_time / batch_size
            success_rate = successful_responses / batch_size

            benchmark = self.performance_benchmarks["batch_processing_time"]
            success = processing_time <= benchmark

            return {
                "success": success,
                "message": f"批量处理{'达标' if success else '不达标'}",
                "batch_size": batch_size,
                "processing_time": processing_time,
                "avg_time_per_query": avg_time_per_query,
                "success_rate": success_rate,
                "benchmark": benchmark
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"批量处理测试失败: {str(e)}",
                "error": str(e)
            }

    async def test_concurrent_processing(self, parameters: dict = None) -> dict:
        """测试并发处理"""
        try:
            concurrency = parameters.get("concurrency", 10)
            rag = OllamaRAGSystem()

            async def process_query(query_id):
                query = f"并发测试查询{query_id}"
                start_time = time.time()
                response = await rag.process_query(query)
                duration = time.time() - start_time
                return {
                    "query_id": query_id,
                    "success": bool(response and response.answer),
                    "duration": duration
                }

            # 并发执行
            logger.info(f"  并发执行{concurrency}个查询...")
            start_time = time.time()
            tasks = [process_query(i) for i in range(concurrency)]
            results = await asyncio.gather(*tasks)
            total_time = time.time() - start_time

            # 分析结果
            successful_tasks = sum(1 for r in results if r["success"])
            avg_duration = sum(r["duration"] for r in results) / len(results)
            max_duration = max(r["duration"] for r in results)

            success = successful_tasks / concurrency >= 0.8  # 80%成功率

            return {
                "success": success,
                "message": f"并发处理{'成功' if success else '失败'}",
                "concurrency": concurrency,
                "total_time": total_time,
                "successful_tasks": successful_tasks,
                "success_rate": successful_tasks / concurrency,
                "avg_duration": avg_duration,
                "max_duration": max_duration
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"并发处理测试失败: {str(e)}",
                "error": str(e)
            }

    async def test_core_functionality_regression(self, parameters: dict = None) -> dict:
        """测试核心功能回归"""
        try:
            # 执行核心功能测试
            core_tests = [
                ("向量生成", self.test_vector_generation),
                ("实体提取", self.test_entity_extraction),
                ("RAG响应", self.test_end_to_end_rag)
            ]

            results = []
            for test_name, test_func in core_tests:
                result = await test_func()
                results.append((test_name, result["success"]))

            # 检查是否所有核心测试都通过
            all_passed = all(success for _, success in results)
            passed_count = sum(success for _, success in results)

            return {
                "success": all_passed,
                "message": f"核心功能测试: {passed_count}/{len(results)} 通过",
                "test_results": results,
                "passed_count": passed_count,
                "total_tests": len(results)
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"回归测试失败: {str(e)}",
                "error": str(e)
            }

    async def test_modification_2025_features(self, parameters: dict = None) -> dict:
        """测试2025修改功能"""
        try:
            # 测试2025修改相关功能
            test_queries = [
                "2025年专利法有什么修改？",
                "AI相关发明的审查标准是什么？",
                "算法模型的专利要求有什么变化？"
            ]

            rag = OllamaRAGSystem()
            results = []

            for query in test_queries:
                response = await rag.process_query(query)
                has_2025_content = "2025" in response.answer or "AI" in response.answer
                results.append({
                    "query": query,
                    "has_response": len(response.answer) > 0,
                    "has_2025_content": has_2025_content
                })

            # 检查是否所有查询都有相关响应
            all_have_response = all(r["has_response"] for r in results)
            some_have_2025 = sum(1 for r in results if r["has_2025_content"])

            success = all_have_response and some_have_2025 > 0

            return {
                "success": success,
                "message": f"2025功能测试{'通过' if success else '部分通过'}",
                "test_results": results,
                "queries_with_2025": some_have_2025,
                "total_queries": len(test_queries)
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"2025功能测试失败: {str(e)}",
                "error": str(e)
            }

    async def test_system_startup(self, parameters: dict = None) -> dict:
        """测试系统启动"""
        try:
            # 尝试初始化所有组件
            vector_store = QdrantVectorStoreSimple()
            extractor = PatentEntityRelationExtractor()
            graph_builder = NebulaGraphBuilder()
            rag = OllamaRAGSystem()

            # 检查组件状态
            components_status = {
                "vector_store": vector_store is not None,
                "entity_extractor": extractor is not None,
                "graph_builder": graph_builder is not None,
                "rag_system": rag is not None
            }

            all_components_ready = all(components_status.values())

            return {
                "success": all_components_ready,
                "message": "系统启动成功" if all_components_ready else "部分组件启动失败",
                "components_status": components_status
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"系统启动失败: {str(e)}",
                "error": str(e)
            }

    async def test_basic_functionality(self, parameters: dict = None) -> dict:
        """测试基本功能"""
        try:
            # 测试基本操作
            rag = OllamaRAGSystem()

            # 基本查询测试
            basic_queries = [
                "什么是专利？",
                "如何申请专利？"
            ]

            responses = []
            for query in basic_queries:
                response = await rag.process_query(query)
                responses.append({
                    "query": query,
                    "has_answer": len(response.answer) > 0,
                    "answer_length": len(response.answer)
                })

            # 检查基本功能
            all_have_answers = all(r["has_answer"] for r in responses)
            avg_answer_length = sum(r["answer_length"] for r in responses) / len(responses)

            success = all_have_answers and avg_answer_length > 10

            return {
                "success": success,
                "message": "基本功能正常" if success else "基本功能异常",
                "query_results": responses,
                "avg_answer_length": avg_answer_length
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"基本功能测试失败: {str(e)}",
                "error": str(e)
            }

    async def _save_test_results(self, results: dict[TestType, TestSuiteResult]):
        """保存测试结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = self.report_dir / f"test_results_{timestamp}.json"

        # 转换结果为可序列化格式
        serializable_results = {}
        for test_type, result in results.items():
            serializable_results[test_type.value] = {
                "suite_name": result.suite_name,
                "test_type": result.test_type.value,
                "total_tests": result.total_tests,
                "passed_tests": result.passed_tests,
                "failed_tests": result.failed_tests,
                "skipped_tests": result.skipped_tests,
                "error_tests": result.error_tests,
                "timeout_tests": result.timeout_tests,
                "total_duration": result.total_duration,
                "success_rate": result.success_rate,
                "reports/reports/results": [
                    {
                        "test_id": r.test_id,
                        "test_name": r.test_name,
                        "status": r.status.value,
                        "duration": r.duration,
                        "message": r.message,
                        "details": r.details,
                        "error": r.error,
                        "start_time": r.start_time.isoformat() if r.start_time else None,
                        "end_time": r.end_time.isoformat() if r.end_time else None
                    }
                    for r in result.results
                ]
            }

        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, ensure_ascii=False, indent=2)

        logger.info(f"测试结果已保存: {result_file}")

        # 保存到历史记录
        self.test_history.append({
            "timestamp": timestamp,
            "reports/reports/results": serializable_results
        })

    async def _generate_test_report(self, results: dict[TestType, TestSuiteResult]):
        """生成测试报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.report_dir / f"test_report_{timestamp}.md"

        # 计算总体统计
        total_tests = sum(r.total_tests for r in results.values())
        total_passed = sum(r.passed_tests for r in results.values())
        total_failed = sum(r.failed_tests for r in results.values())
        total_errors = sum(r.error_tests for r in results.values())
        overall_success_rate = total_passed / total_tests if total_tests > 0 else 0

        # 生成Markdown报告
        report_content = f"""# 自动化测试报告

## 测试概览

- **测试时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **测试套件数**: {len(results)}
- **总测试数**: {total_tests}
- **通过数**: {total_passed}
- **失败数**: {total_failed}
- **错误数**: {total_errors}
- **总体成功率**: {overall_success_rate:.1%}

## 各测试套件详情

"""

        for test_type, result in results.items():
            status_icon = "✅" if result.success_rate >= 0.9 else "⚠️" if result.success_rate >= 0.7 else "❌"

            report_content += f"""### {test_type.value} {status_icon}

- **总测试数**: {result.total_tests}
- **通过数**: {result.passed_tests}
- **失败数**: {result.failed_tests}
- **错误数**: {result.error_tests}
- **成功率**: {result.success_rate:.1%}
- **总耗时**: {result.total_duration:.2f}s

#### 测试结果详情

| 测试ID | 测试名称 | 状态 | 耗时 | 消息 |
|--------|----------|------|------|------|
"""

            for test_result in result.results:
                status_icon = "✅" if test_result.status == TestStatus.PASSED else \
                            "❌" if test_result.status == TestStatus.FAILED else \
                            "⚠️" if test_result.status == TestStatus.ERROR else \
                            "⏭️"

                report_content += f"""| {test_result.test_id} | {test_result.test_name} | {status_icon} {test_result.status.value} | {test_result.duration:.2f}s | {test_result.message} |
"""

            report_content += "\n"

        # 添加失败和错误的详细信息
        failed_tests = []
        for test_type, result in results.items():
            for test_result in result.results:
                if test_result.status in [TestStatus.FAILED, TestStatus.ERROR, TestStatus.TIMEOUT]:
                    failed_tests.append({
                        "test_type": test_type.value,
                        "test_id": test_result.test_id,
                        "test_name": test_result.test_name,
                        "status": test_result.status.value,
                        "error": test_result.error,
                        "message": test_result.message
                    })

        if failed_tests:
            report_content += """## 失败和错误详情

| 测试类型 | 测试ID | 测试名称 | 状态 | 错误信息 |
|----------|--------|----------|------|----------|
"""
            for test in failed_tests:
                report_content += f"""| {test['test_type']} | {test['test_id']} | {test['test_name']} | {test['status']} | {test.get('error', test.get('message', ''))} |
"""

        # 保存报告
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)

        logger.info(f"测试报告已保存: {report_file}")

# 使用示例
async def main():
    """主函数示例"""
    test_suite = AutomatedTestSuite()

    # 运行冒烟测试
    logger.info("运行冒烟测试...")
    smoke_results = await test_suite.run_test_suite(
        test_types=[TestType.SMOKE]
    )

    # 如果冒烟测试通过，运行更多测试
    if all(r.success_rate >= 0.8 for r in smoke_results.values()):
        logger.info("\n冒烟测试通过，运行完整测试套件...")
        full_results = await test_suite.run_test_suite()
    else:
        logger.error("\n冒烟测试失败，跳过其他测试")

if __name__ == "__main__":
    asyncio.run(main())
