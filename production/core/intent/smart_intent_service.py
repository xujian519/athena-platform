#!/usr/bin/env python3
"""
智能意图识别服务
Smart Intent Recognition Service

集成P0-P3学习引擎的意图识别服务:
- MPS优化的BGE-M3模型
- 实时性能监控
- 自动学习和优化
- 持续改进能力

作者: Athena AI Team
版本: 2.0.0
创建: 2026-01-29
"""

from __future__ import annotations
import asyncio

# 添加项目路径
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.logging_config import setup_logging
from production.core.intent.learning_integration import get_intent_learning_orchestrator

logger = setup_logging()


class SmartIntentService:
    """
    智能意图识别服务

    集成了学习引擎的增强版意图识别服务
    """

    def __init__(
        self,
        enable_learning: bool = True,
        auto_optimize: bool = True,
        optimize_interval: int = 100,  # 每N次预测后自动优化
    ):
        """
        初始化智能意图识别服务

        Args:
            enable_learning: 是否启用学习引擎
            auto_optimize: 是否自动触发优化
            optimize_interval: 自动优化间隔
        """
        # 基础分类器配置
        self.model_path = str(
            Path(__file__).parent.parent.parent.parent
            / "models" / "converted" / "BAAI" / "bge-m3"
        )
        self.device = self._select_device()
        self.model: SentenceTransformer | None = None
        self.template_embeddings: np.ndarray | None = None
        self.template_labels: list[str] = []
        self.template_texts: list[str] = []

        # 意图模板
        self.intent_templates = self._initialize_intent_templates()

        # 性能统计
        self.stats = {
            "total_requests": 0,
            "total_time": 0.0,
            "mps_accelerated": False
        }

        # 学习引擎配置
        self.enable_learning = enable_learning
        self.auto_optimize = auto_optimize
        self.optimize_interval = optimize_interval

        # 学习引擎编排器
        self.learning_orchestrator: Any | None = None

        # 初始化
        self._initialize()

        # 初始化学习引擎
        if self.enable_learning:
            self._initialize_learning()

        logger.info("✅ 智能意图识别服务初始化完成")
        logger.info(f"   学习引擎: {'✅ 启用' if self.enable_learning else '❌ 禁用'}")
        logger.info(f"   自动优化: {'✅ 启用' if self.auto_optimize else '❌ 禁用'}")
        logger.info(f"   优化间隔: 每{self.optimize_interval}次预测")

    def _select_device(self) -> str:
        """智能选择计算设备"""
        if torch.backends.mps.is_available():
            logger.info("🍎 使用MPS GPU加速 (Apple Silicon)")
            return "mps"
        elif torch.cuda.is_available():
            logger.info("✅ 使用CUDA GPU加速")
            return "cuda"
        else:
            logger.info("⚠️  使用CPU模式")
            return "cpu"

    def _initialize_intent_templates(self) -> dict[str, list[str]]:
        """初始化意图模板"""
        return {
            "PATENT_SEARCH": [
                "搜索专利", "查找专利", "检索专利", "查询专利", "专利检索"
            ],
            "PATENT_ANALYSIS": [
                "分析专利", "专利分析", "分析专利的创造性", "专利新颖性分析"
            ],
            "PATENT_DRAFTING": [
                "写专利", "撰写专利", "专利申请", "专利说明书", "权利要求书"
            ],
            "PATENT_COMPARISON": [
                "对比专利", "专利对比", "比较专利", "专利差异分析"
            ],
            "OPINION_RESPONSE": [
                "答复审查意见", "审查意见答复", "答复审查意见通知书",
                "审查意见陈述", "专利审查答复"
            ],
            "LEGAL_QUERY": [
                "法律咨询", "法律问题", "法律条文", "法规查询"
            ],
            "CODE_GENERATION": [
                "写代码", "生成代码", "代码生成", "编程实现"
            ],
            "GENERAL_CHAT": [
                "你好", "嗨", "聊天", "闲聊"
            ]
        }

    def _initialize(self):
        """初始化模型"""
        try:
            logger.info(f"📂 加载BGE-M3模型: {self.model_path}")

            start = time.time()
            self.model = SentenceTransformer(
                self.model_path,
                device=self.device
            )
            load_time = time.time() - start

            logger.info(f"✅ BGE-M3模型加载成功 ({load_time:.2f}s)")
            logger.info(f"📊 向量维度: {self.model.get_sentence_embedding_dimension()}")
            logger.info(f"🚀 设备: {self.device}")

            # 预计算模板向量
            self._precompute_template_embeddings()

            self.stats["mps_accelerated"] = (self.device == "mps")

        except Exception as e:
            logger.error(f"❌ 模型加载失败: {e}")
            raise

    def _initialize_learning(self):
        """初始化学习引擎"""
        try:
            logger.info("🧠 初始化学习引擎编排器...")
            self.learning_orchestrator = get_intent_learning_orchestrator(
                agent_id="smart_intent_service",
                enable_all=True,  # 启用P0-P3所有学习引擎
            )
            logger.info("✅ 学习引擎初始化成功")
            logger.info("   - P0: 自主学习 (性能监控)")
            logger.info("   - P1: 在线学习 (模型优化)")
            logger.info("   - P2: 强化学习 (策略优化)")
            logger.info("   - P3: 元学习 (快速适应)")

        except Exception as e:
            logger.warning(f"⚠️ 学习引擎初始化失败: {e}")
            self.enable_learning = False

    def _precompute_template_embeddings(self):
        """预计算意图模板向量"""
        logger.info("🔄 预计算意图模板向量...")

        all_templates = []
        intent_labels = []

        for intent, templates in self.intent_templates.items():
            for template in templates:
                all_templates.append(template)
                intent_labels.append(intent)

        # 编码所有模板
        self.template_embeddings = self.model.encode(
            all_templates,
            show_progress_bar=False,
            convert_to_numpy=True
        )

        self.template_labels = intent_labels
        self.template_texts = all_templates

        logger.info(f"✅ 预计算完成: {len(all_templates)}个模板")

    # ==============================================================================
    # 核心接口: 带学习的意图识别
    # ==============================================================================

    async def recognize(
        self,
        query: str,
        true_intent: str | None = None,
        user_satisfaction: float | None = None,
    ) -> dict[str, Any]:
        """
        识别意图（带学习功能）

        Args:
            query: 用户查询
            true_intent: 真实意图（用户反馈）
            user_satisfaction: 用户满意度 (0-1)

        Returns:
            识别结果
        """
        # 执行意图识别
        result = self.recognize_intent(query)

        # 如果启用了学习，记录经验
        if self.enable_learning and self.learning_orchestrator:
            await self._record_and_learn(
                query=query,
                result=result,
                true_intent=true_intent,
                user_satisfaction=user_satisfaction,
            )

        # 自动优化（如果需要）
        if self.auto_optimize and self.stats["total_requests"] % self.optimize_interval == 0:
            await self._auto_optimize()

        return result

    def recognize_intent(
        self,
        text: str,
        top_k: int = 3,
        threshold: float = 0.6
    ) -> dict[str, Any]:
        """
        识别意图（同步版本）

        Args:
            text: 输入文本
            top_k: 返回前k个结果
            threshold: 置信度阈值

        Returns:
            识别结果
        """
        start = time.time()

        # 编码输入文本
        query_embedding = self.model.encode(
            [text],
            show_progress_bar=False,
            convert_to_numpy=True
        )[0]

        # 计算与所有模板的相似度
        similarities = cosine_similarity(
            [query_embedding],
            self.template_embeddings
        )[0]

        # 获取top-k结果
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            intent = self.template_labels[idx]
            template = self.template_texts[idx]
            score = float(similarities[idx])

            if score >= threshold:
                results.append({
                    "intent": intent,
                    "template": template,
                    "score": score,
                    "confidence": score
                })

        processing_time = (time.time() - start) * 1000

        # 更新统计
        self.stats["total_requests"] += 1
        self.stats["total_time"] += processing_time

        # 返回最佳结果
        best_result = results[0] if results else {
            "intent": "GENERAL_CHAT",
            "template": "默认意图",
            "score": 0.0,
            "confidence": 0.0
        }

        return {
            "intent": best_result["intent"],
            "confidence": best_result["confidence"],
            "matched_template": best_result["template"],
            "all_results": results,
            "processing_time_ms": processing_time,
            "device": self.device,
            "mps_accelerated": self.stats["mps_accelerated"]
        }

    async def _record_and_learn(
        self,
        query: str,
        result: dict[str, Any],
        true_intent: str | None = None,
        user_satisfaction: float | None = None,
    ):
        """
        记录经验并触发学习

        Args:
            query: 用户查询
            result: 识别结果
            true_intent: 真实意图（用户反馈）
            user_satisfaction: 用户满意度
        """
        try:
            # 记录学习经验
            await self.learning_orchestrator.record_experience(
                query=query,
                predicted_intent=result["intent"],
                confidence=result["confidence"],
                response_time_ms=result["processing_time_ms"],
                true_intent=true_intent,
                user_satisfaction=user_satisfaction,
            )

            logger.debug(
                f"📚 学习经验已记录: {result['intent']} "
                f"(置信度: {result['confidence']:.2%})"
            )

        except Exception as e:
            logger.error(f"❌ 记录学习经验失败: {e}")

    async def _auto_optimize(self):
        """触发自动优化"""
        try:
            logger.info("🔧 触发自动优化...")

            optimization_result = await self.learning_orchestrator.optimize_system()

            if optimization_result["status"] == "optimized":
                logger.info(
                    f"✅ 系统已优化: "
                    f"准确率 {optimization_result['recent_accuracy']:.1%}"
                )
            elif optimization_result["status"] == "good":
                logger.info(f"✅ {optimization_result['message']}")

        except Exception as e:
            logger.error(f"❌ 自动优化失败: {e}")

    # ==============================================================================
    # 批量处理
    # ==============================================================================

    async def batch_recognize(
        self,
        queries: list[str],
        true_intents: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """批量识别意图（带学习）"""
        results = []

        for i, query in enumerate(queries):
            true_intent = true_intents[i] if true_intents else None
            result = await self.recognize(query, true_intent=true_intent)
            results.append(result)

        return results

    # ==============================================================================
    # 状态和统计
    # ==============================================================================

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        if self.stats["total_requests"] > 0:
            avg_time = self.stats["total_time"] / self.stats["total_requests"]
        else:
            avg_time = 0.0

        stats = {
            "total_requests": self.stats["total_requests"],
            "average_time_ms": avg_time,
            "device": self.device,
            "mps_accelerated": self.stats["mps_accelerated"],
            "vector_dimension": self.model.get_sentence_embedding_dimension() if self.model else None,
            "model_path": self.model_path,
        }

        # 添加学习引擎状态
        if self.enable_learning and self.learning_orchestrator:
            learning_status = self.learning_orchestrator.get_learning_status()
            stats["learning"] = {
                "enabled": True,
                "total_experiences": learning_status["total_experiences"],
                "accuracy": learning_status["metrics"]["accuracy"],
                "learning_cycles": learning_status["metrics"]["learning_cycles"],
            }

        return stats

    async def get_learning_metrics(self) -> dict[str, Any] | None:
        """获取学习指标"""
        if not self.enable_learning or not self.learning_orchestrator:
            return None

        return self.learning_orchestrator.get_learning_status()

    async def export_learning_data(self, filepath: str | None = None) -> str | None:
        """导出学习数据"""
        if not self.enable_learning or not self.learning_orchestrator:
            logger.warning("学习引擎未启用，无法导出数据")
            return None

        return self.learning_orchestrator.export_experiences(filepath)


# =============================================================================
# 全局单例
# =============================================================================
_smart_service: SmartIntentService | None = None


def get_smart_intent_service(
    enable_learning: bool = True,
    auto_optimize: bool = True,
) -> SmartIntentService:
    """
    获取智能意图识别服务单例

    Args:
        enable_learning: 是否启用学习引擎
        auto_optimize: 是否自动优化

    Returns:
        SmartIntentService: 服务实例
    """
    global _smart_service

    if _smart_service is None:
        _smart_service = SmartIntentService(
            enable_learning=enable_learning,
            auto_optimize=auto_optimize,
        )

    return _smart_service


# =============================================================================
# 测试代码
# =============================================================================
if __name__ == "__main__":
    import asyncio

    async def main():
        print("=" * 80)
        print("🧠 智能意图识别服务测试")
        print("=" * 80)

        # 创建服务
        print("\n🚀 初始化智能意图识别服务...")
        service = get_smart_intent_service(
            enable_learning=True,
            auto_optimize=True,
        )

        # 测试查询
        test_queries = [
            ("搜索人工智能专利", "PATENT_SEARCH"),
            ("分析这个专利的创造性", "PATENT_ANALYSIS"),
            ("答复审查意见", "OPINION_RESPONSE"),
            ("写专利申请书", "PATENT_DRAFTING"),
        ]

        print("\n🧪 测试意图识别（带学习）:")
        print("-" * 80)

        for query, true_intent in test_queries:
            # 带用户反馈的识别
            result = await service.recognize(
                query=query,
                true_intent=true_intent,
                user_satisfaction=0.9,
            )

            print(f"\n查询: {query}")
            print(f"真实意图: {true_intent}")
            print(f"识别意图: {result['intent']}")
            print(f"置信度: {result['confidence']:.2%}")
            print(f"响应时间: {result['processing_time_ms']:.1f}ms")
            print(f"匹配: {'✅' if result['intent'] == true_intent else '❌'}")

        # 获取统计信息
        print("\n" + "=" * 80)
        print("📊 统计信息:")
        print("-" * 80)

        stats = service.get_stats()
        for key, value in stats.items():
            if key != "learning":
                print(f"  {key}: {value}")

        # 获取学习指标
        learning_metrics = await service.get_learning_metrics()
        if learning_metrics:
            print("\n📚 学习指标:")
            for key, value in learning_metrics["metrics"].items():
                print(f"  {key}: {value}")

        # 导出学习数据
        export_path = await service.export_learning_data()
        if export_path:
            print(f"\n📤 学习数据已导出: {export_path}")

        print("\n" + "=" * 80)
        print("✅ 测试完成!")
        print("=" * 80)

    asyncio.run(main())
