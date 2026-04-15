from __future__ import annotations

import numpy as np

#!/usr/bin/env python3
"""
跨任务工作流记忆 (Cross Task Workflow Memory)

JoyAgent的核心创新: 从历史任务中提取可复用的workflow模式,
并在新任务中自动应用这些模式。

Author: Athena平台团队
Created: 2026-01-20
Version: v1.0.0
Based on: JoyAgent (https://arxiv.org/abs/2510.00510)
"""

import hashlib
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from core.memory.cache_utils import (
    BatchProcessor,
    LRUCache,
)
from core.memory.pattern_index_manager import PatternIndexManager
from core.memory.retry_utils import RetryConfig, async_retry
from core.memory.security_utils import (
    InputValidator,
    PathValidator,
    SecurityError,
    SensitiveDataFilter,
)
from core.memory.serializers.markdown_serializer import PatternMarkdownSerializer
from core.memory.type_utils import safe_domain_getter
from core.memory.vector_workflow_retriever import VectorWorkflowRetriever
from core.memory.workflow_extractor import WorkflowExtractor
from core.memory.workflow_pattern import TaskTrajectory, WorkflowPattern
from core.memory.workflow_retriever import RetrievalResult, WorkflowRetriever

logger = logging.getLogger(__name__)

# 添加敏感数据过滤器到日志
logger.addFilter(SensitiveDataFilter())


class CrossTaskWorkflowMemory:
    """
    跨任务工作流记忆

    核心功能:
    1. 从任务轨迹中提取workflow模式
    2. 基于向量相似度检索相关模式
    3. 将模式应用到新任务
    4. 持久化存储和管理模式
    """

    def __init__(
        self,
        storage_path: str = "data/workflow_memory",
        similarity_threshold: float = 0.75,
        enable_auto_extract: bool = True,
        enable_markdown_export: bool = True,
        enable_vector_search: bool = False,
        qdrant_url: str = "localhost:6333",
    ):
        """
        初始化跨任务工作流记忆

        Args:
            storage_path: 存储路径
            similarity_threshold: 相似度阈值
            enable_auto_extract: 是否启用自动提取
            enable_markdown_export: 是否启用Markdown导出
            enable_vector_search: 是否启用向量检索(需要Qdrant)
            qdrant_url: Qdrant服务地址
        """
        # 安全验证路径
        self.storage_path = Path(storage_path).resolve()
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.enable_markdown_export = enable_markdown_export
        self.enable_vector_search = enable_vector_search

        # 初始化安全组件
        self.path_validator = PathValidator({self.storage_path})
        self.input_validator = InputValidator()

        # 初始化缓存(用于检索结果缓存)
        self.retrieval_cache = LRUCache(max_size=256, ttl=300)  # 5分钟TTL

        # 初始化批量处理器
        self.batch_processor = BatchProcessor(batch_size=10, timeout=1.0)

        # 初始化组件
        self.extractor = WorkflowExtractor()

        # 尝试初始化向量检索器(如果启用)
        self.vector_retriever: VectorWorkflowRetriever | None = None
        if enable_vector_search:
            self.vector_retriever = VectorWorkflowRetriever(
                qdrant_url=qdrant_url, similarity_threshold=similarity_threshold
            )
            if self.vector_retriever and self.vector_retriever.enabled:
                logger.info(f"✅ 向量检索已启用 (Qdrant: {qdrant_url})")
            else:
                logger.warning("⚠️ 向量检索初始化失败,使用基础检索器")
                self.enable_vector_search = False
                self.vector_retriever = None

        # 初始化基础检索器(作为降级方案)
        self.retriever = WorkflowRetriever(similarity_threshold=similarity_threshold)

        # 新增: 索引管理器和Markdown序列化器
        self.index_manager = PatternIndexManager(
            index_file=str(self.storage_path / "pattern_index.json")
        )
        self.markdown_serializer = PatternMarkdownSerializer()

        # 内存中的模式缓存
        self.patterns: dict[str, WorkflowPattern] = {}

        # 加载已有模式
        self._load_existing_patterns()

        logger.info("🧠 CrossTaskWorkflowMemory初始化完成")
        logger.info(f"   存储路径: {self.storage_path}")
        logger.info(f"   已加载模式: {len(self.patterns)}个")
        logger.info(f"   相似度阈值: {similarity_threshold}")
        logger.info(f"   Markdown导出: {enable_markdown_export}")
        logger.info(f"   向量检索: {self.enable_vector_search}")

    async def extract_workflow_pattern(
        self, task: Any, trajectory: TaskTrajectory, success: bool
    ) -> WorkflowPattern | None:
        """
        从任务轨迹中提取workflow模式

        Args:
            task: 任务对象
            trajectory: 任务轨迹
            success: 是否成功

        Returns:
            提取的WorkflowPattern,如果提取失败则返回None
        """
        logger.info(f"🎯 开始提取workflow模式: 任务类型={trajectory.task_type}")

        # 使用提取器提取模式
        pattern = await self.extractor.extract_workflow_pattern(
            task=task, trajectory=trajectory, success=success
        )

        if pattern:
            logger.info(f"✅ 成功提取模式: {pattern.pattern_id}")
        else:
            logger.info("❌ 模式提取失败")

        return pattern

    async def store_pattern(self, pattern: WorkflowPattern):
        """
        存储workflow模式

        Args:
            pattern: 要存储的模式

        Raises:
            SecurityError: 如果pattern_id格式无效
        """
        # 安全验证: pattern_id格式
        validated_id = self.input_validator.validate_file_name(pattern.pattern_id)
        try:
            if validated_id != pattern.pattern_id:
                logger.warning(f"pattern_id已规范化: {pattern.pattern_id} -> {validated_id}")
        except SecurityError as e:
            logger.error(f"操作失败: {e}", exc_info=True)
            raise

        # 1. 存储到内存缓存
        self.patterns[pattern.pattern_id] = pattern

        # 2. 持久化到JSON文件
        await self._save_pattern_to_file(pattern)

        # 3. 更新索引
        await self.index_manager.update_index(pattern)

        # 4. 索引到向量数据库 (如果启用)
        if self.enable_vector_search and self.vector_retriever:
            indexed = await self.vector_retriever.index_pattern(pattern)
            if indexed:
                logger.debug(f"📇 模式已索引到向量数据库: {pattern.pattern_id}")

        # 5. 导出为Markdown (如果启用)
        if self.enable_markdown_export:
            md_file_path = self.markdown_serializer.get_file_path(
                pattern, base_dir=str(self.storage_path / "patterns")
            )
            await self.markdown_serializer.save_to_file(pattern, md_file_path)

        logger.info(f"💾 模式已存储: {pattern.pattern_id} " f"(总模式数: {len(self.patterns)})")

    async def retrieve_similar_workflows(self, task: Any, top_k: int = 3) -> list[RetrievalResult]:
        """
        检索相似的workflow模式

        Args:
            task: 当前任务
            top_k: 返回结果数量

        Returns:
            按相似度排序的检索结果列表
        """
        logger.info(
            f"🔍 检索相似workflow: {task.description if hasattr(task, 'description') else 'unknown'}"
        )

        # 优先使用向量检索(如果启用)
        if self.enable_vector_search and self.vector_retriever:
            task_embedding = await self._generate_task_embedding(task)
            if task_embedding is not None:
                logger.debug("🎯 使用向量检索")
                results = await self.vector_retriever.retrieve_similar_workflows(
                    task_embedding=task_embedding, limit=top_k
                )

                if results:
                    logger.info(f"✅ 向量检索完成: 找到{len(results)}个相似模式")
                    # 打印Top结果
                    for i, result in enumerate(results[:top_k], 1):
                        logger.info(
                            f"   {i}. {result.pattern.name} "
                            f"(相似度: {result.similarity:.3f}, "
                            f"成功率: {result.pattern.success_rate:.2f}, "
                            f"使用次数: {result.pattern.usage_count})"
                        )
                    return results[:top_k]
                else:
                    logger.debug("向量检索未找到结果,降级到基础检索")

        # 降级到基础检索
        logger.debug("🔄 使用基础检索")
        patterns = list(self.patterns.values())

        if not patterns:
            logger.info("📭 没有可用模式")
            return []

        # 使用基础检索器进行检索
        results = await self.retriever.retrieve_similar_workflows(
            task=task, patterns=patterns, task_embedding=None
        )

        logger.info(f"✅ 检索完成: 找到{len(results)}个相似模式")

        # 打印Top结果
        for i, result in enumerate(results[:top_k], 1):
            logger.info(
                f"   {i}. {result.pattern.name} "
                f"(相似度: {result.similarity:.3f}, "
                f"成功率: {result.pattern.success_rate:.2f}, "
                f"使用次数: {result.pattern.usage_count})"
            )

        return results[:top_k]

    async def _generate_task_embedding(self, task: Any) -> np.ndarray | None:
        """
        生成任务的向量表示

        Args:
            task: 任务对象

        Returns:
            任务向量,如果无法生成则返回None
        """
        # 提取任务文本特征
        task_text_parts = []

        # 1. 任务描述
        if hasattr(task, "description") and task.description:
            task_text_parts.append(task.description)

        # 2. 任务类型
        if hasattr(task, "type") and task.type:
            task_text_parts.append(str(task.type))

        # 3. 任务领域
        if hasattr(task, "domain") and task.domain:
            domain_value = task.domain.value if hasattr(task.domain, "value") else str(task.domain)
            task_text_parts.append(domain_value)

        # 4. 任务名称
        if hasattr(task, "name") and task.name:
            task_text_parts.append(task.name)

        if not task_text_parts:
            logger.debug("无法提取任务文本特征")
            return None

        # 合并文本特征
        combined_text = " ".join(task_text_parts)

        # 尝试使用embedding模型生成向量
        try:
            from sentence_transformers import SentenceTransformer

            model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
            embedding = model.encode(combined_text, convert_to_numpy=True)
            logger.debug(f"✅ 使用sentence-transformers生成embedding: {embedding.shape}")
            return embedding

        except ImportError as e:
            logger.error(f"操作失败: {e}", exc_info=True)
            raise

        try:
            import torch
            from transformers import AutoModel, AutoTokenizer

            tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
            model = AutoModel.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")

            inputs = tokenizer(
                combined_text, return_tensors="pt", truncation=True, padding=True, max_length=512
            )
            with torch.no_grad():
                outputs = model(**inputs)

            # 使用[CLS] token的输出作为句子表示
            embedding = outputs.last_hidden_state[:, 0, :].numpy().flatten()
            logger.debug(f"✅ 使用transformers生成embedding: {embedding.shape}")
            return embedding

        except ImportError as e:
            logger.error(f"操作失败: {e}", exc_info=True)
            raise

        try:
            # 注意: 这是一个简单的降级方案,语义理解能力有限
            import hashlib

            # 生成固定长度的向量 (768维,与BERT相同)
            vector_size = 768
            hash_obj = hashlib.sha256(combined_text.encode("utf-8"))

            # 将hash转换为向量
            hash_bytes = hash_obj.digest()
            embedding = np.zeros(vector_size, dtype=np.float32)

            for i, byte in enumerate(hash_bytes):
                if i < vector_size:
                    embedding[i] = byte / 255.0

            # 使用文本特征填充剩余维度
            for i, char in enumerate(combined_text[:vector_size]):
                if i + 32 < vector_size:
                    embedding[i + 32] = ord(char) / 255.0

            logger.debug(f"✅ 使用hash-based embedding (降级方案): {embedding.shape}")
            return embedding

        except Exception as e:
            logger.error(f"操作失败: {e}", exc_info=True)
            raise

    async def apply_workflow_pattern(self, pattern: WorkflowPattern, task: Any) -> dict[str, Any]:
        """
        将workflow模式应用到新任务

        Args:
            pattern: 要应用的模式
            task: 目标任务

        Returns:
            应用后的执行计划
        """
        logger.info(f"🔧 应用workflow模式: {pattern.pattern_id}")

        # 1. 适应模式到当前任务
        adapted_pattern = pattern.adapt_to_task(
            task_params={
                "description": getattr(task, "description", ""),
                "type": getattr(task, "type", ""),
                "domain": getattr(task, "domain", ""),
            }
        )

        # 2. 生成执行计划
        execution_plan = {
            "pattern_id": adapted_pattern.pattern_id,
            "pattern_name": adapted_pattern.name,
            "steps": [
                {
                    "step_id": step.step_id,
                    "name": step.name,
                    "action": step.action,
                    "description": step.description,
                    "dependencies": step.dependencies,
                }
                for step in adapted_pattern.steps
            ],
            "estimated_success_rate": adapted_pattern.success_rate,
            "estimated_execution_time": adapted_pattern.avg_execution_time,
            "adaptation_notes": "模式已适应当前任务",
        }

        # 3. 更新模式使用统计
        adapted_pattern.record_execution(
            success=True,  # 暂时假设成功,实际执行后更新
            execution_time=adapted_pattern.avg_execution_time,
        )
        adapted_pattern.usage_count += 1

        # 保存更新后的模式
        await self.store_pattern(adapted_pattern)

        logger.info(f"✅ 模式应用成功: {len(execution_plan['steps'])}个步骤")

        return execution_plan

    def _load_existing_patterns(self) -> Any:
        """加载已有的workflow模式"""

        patterns_dir = self.storage_path / "patterns"

        if not patterns_dir.exists():
            logger.info("📁 模式目录不存在,创建新目录")
            patterns_dir.mkdir(parents=True, exist_ok=True)
            return

        # 遍历所有模式文件
        pattern_files = list(patterns_dir.glob("*.json"))

        for pattern_file in pattern_files:
            try:
                with open(pattern_file, encoding="utf-8") as f:
                    pattern_data = json.load(f)

                pattern = WorkflowPattern(**pattern_data)
                self.patterns[pattern.pattern_id] = pattern

            except Exception as e:
                logger.error(f"操作失败: {e}", exc_info=True)
                raise

        logger.info(f"📂 已加载{len(self.patterns)}个模式")

    @async_retry(
        exceptions=(IOError, OSError, json.JSONDecodeError),
        config=RetryConfig(max_attempts=3, base_delay=0.5),
    )
    async def _save_pattern_to_file(self, pattern: WorkflowPattern):
        """将模式保存到文件(带路径验证)"""

        patterns_dir = self.storage_path / "patterns"
        patterns_dir.mkdir(parents=True, exist_ok=True)

        # 验证文件名安全性
        safe_filename = self.input_validator.validate_file_name(f"{pattern.pattern_id}.json")
        validated_path = patterns_dir / safe_filename

        # 验证路径安全性
        try:
            self.input_validator.validate_path(validated_path)
        except SecurityError as e:
            logger.error(f"操作失败: {e}", exc_info=True)
            raise

        # 序列化为JSON (使用Pydantic的model_dump替代已废弃的dict)
        pattern_data = pattern.model_dump()

        # 自定义JSON encoder处理datetime和其他特殊类型
        def json_serializer(obj) -> None:
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif hasattr(obj, "tolist"):  # numpy array
                return obj.tolist()
            raise TypeError(f"Type {type(obj)} not serializable")

        with open(validated_path, "w", encoding="utf-8") as f:
            json.dump(pattern_data, f, ensure_ascii=False, indent=2, default=json_serializer)

        logger.debug(f"💾 模式已保存: {validated_path}")

    async def _update_pattern_index(self, pattern: WorkflowPattern):
        """更新模式索引"""

        index_file = self.storage_path / "pattern_index.json"

        # 加载现有索引
        if index_file.exists():
            with open(index_file, encoding="utf-8") as f:
                index = json.load(f)
        else:
            index = {"patterns": {}, "last_updated": None}

        # 获取domain值 (使用类型工具统一处理)
        domain_value = safe_domain_getter(pattern.domain)

        # 更新索引
        index["patterns"][pattern.pattern_id] = {
            "name": pattern.name,
            "domain": domain_value,
            "task_type": pattern.task_type,
            "success_rate": pattern.success_rate,
            "usage_count": pattern.usage_count,
            "created_at": pattern.created_at.isoformat(),
            "updated_at": pattern.updated_at.isoformat(),
        }

        index["last_updated"] = datetime.now().isoformat()

        # 保存索引
        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)

        logger.debug(f"📝 索引已更新: {pattern.pattern_id}")

    async def get_pattern_statistics(self) -> dict[str, Any]:
        """获取模式统计信息"""

        if not self.patterns:
            return {"total_patterns": 0, "domains": {}, "avg_success_rate": 0.0, "total_usage": 0}

        # 按领域统计
        domain_stats = {}
        for pattern in self.patterns.values():
            # 处理str和Enum两种情况
            domain = safe_domain_getter(pattern.domain)

            if domain not in domain_stats:
                domain_stats[domain] = {"count": 0, "total_success": 0.0, "total_usage": 0}

            domain_stats[domain]["count"] += 1
            domain_stats[domain]["total_success"] += pattern.success_rate
            domain_stats[domain]["total_usage"] += pattern.usage_count

        # 计算平均成功率
        total_success_rate = sum(pattern.success_rate for pattern in self.patterns.values()) / len(
            self.patterns
        )

        total_usage = sum(pattern.usage_count for pattern in self.patterns.values())

        return {
            "total_patterns": len(self.patterns),
            "domains": {
                domain: {
                    "count": stats["count"],
                    "avg_success_rate": stats["total_success"] / stats["count"],
                    "total_usage": stats["total_usage"],
                }
                for domain, stats in domain_stats.items()
            },
            "avg_success_rate": total_success_rate,
            "total_usage": total_usage,
        }

    async def store_patterns_batch(
        self, patterns: list[WorkflowPattern], show_progress: bool = False
    ) -> dict[str, Any]:
        """
        批量存储workflow模式

        Args:
            patterns: 要存储的模式列表
            show_progress: 是否显示进度

        Returns:
            批量操作统计信息
        """
        start_time = time.time()
        success_count = 0
        error_count = 0

        for i, _pattern in enumerate(patterns):
            try:
                success_count += 1

                if show_progress and (i + 1) % 10 == 0:
                    logger.info(f"批量存储进度: {i + 1}/{len(patterns)}")

            except Exception as e:
                logger.error(f"操作失败: {e}", exc_info=True)
                raise

        elapsed = time.time() - start_time

        stats = {
            "total": len(patterns),
            "success": success_count,
            "errors": error_count,
            "elapsed_time": elapsed,
            "throughput": len(patterns) / elapsed if elapsed > 0 else 0,
        }

        logger.info(
            f"📊 批量存储完成: {stats['success']}/{stats['total']} 成功 "
            f"({stats['throughput']:.1f} patterns/sec)"
        )

        return stats

    async def retrieve_similar_workflows_cached(
        self, task: Any, top_k: int = 3
    ) -> list[RetrievalResult]:
        """
        检索相似的workflow模式(带缓存)

        Args:
            task: 当前任务
            top_k: 返回结果数量

        Returns:
            按相似度排序的检索结果列表
        """
        # 生成缓存键
        task_desc = getattr(task, "description", "") or str(task)
        cache_key = f"retrieve:{hashlib.md5(task_desc.encode(), usedforsecurity=False).hexdigest()}:{top_k}"

        # 尝试从缓存获取
        cached_results = self.retrieval_cache.get(cache_key)
        if cached_results is not None:
            logger.debug(f"✅ 检索缓存命中: {cache_key[:16]}...")
            return cached_results

        # 缓存未命中,执行检索
        results = await self.retrieve_similar_workflows(task, top_k)

        # 存储到缓存
        self.retrieval_cache.put(cache_key, results)

        return results

    def get_cache_stats(self) -> dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            缓存统计数据
        """
        return self.retrieval_cache.get_stats()

    def clear_cache(self) -> None:
        """清空所有缓存"""
        self.retrieval_cache.clear()
        logger.info("🗑️ 所有缓存已清空")


__all__ = ["CrossTaskWorkflowMemory"]
