#!/usr/bin/env python3
"""
DSPy专利案例分析训练系统 v3 - 增强版
DSPy Patent Case Analysis Training System v3 - Enhanced

改进内容:
1. 结构化输出Signature
2. 使用增强评估指标
3. 使用精选100条高质量数据
4. 优化提示词模板

作者: Athena平台团队
创建时间: 2025-12-30
版本: 3.0.0-enhanced
"""

from __future__ import annotations
import json
import logging
import random
from datetime import datetime
from pathlib import Path
from typing import Any

import dspy

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

# ===============================
# 0. LLM配置
# ===============================


def setup_llm() -> Any:
    """配置DSPy的LLM"""
    try:
        from .lm_config import configure_dspy_lm_with_fallback

        lm = configure_dspy_lm_with_fallback(
            primary_model="glm-4-plus", fallback_model="deepseek-chat", max_workers=4
        )
        logger.info("✅ LLM配置成功")
        return lm
    except ImportError:
        logger.warning("⚠️ lm_config不可用,使用默认配置")
        # 使用LiteLLM配置
        import os

        api_key = os.getenv("ZHIPUAI_API_KEY", "")
        if not api_key:
            logger.warning("⚠️ 未设置ZHIPUAI_API_KEY,使用模拟模式")

        # 配置GLM-4
        lm = dspy.LM(
            model="zai/glm-4-plus",
            api_key=api_key or "dummy",
            api_base="https://open.bigmodel.cn/api/paas/v4/",
        )
        dspy.configure(lm=lm)
        logger.info("✅ 使用默认GLM-4配置")
        return lm


# 在模块加载时配置LLM
_lm = setup_llm()


# ===============================
# 1. Signature定义 - 结构化输出
# ===============================


class StructuredPatentCaseAnalysis(dspy.Signature):
    """结构化专利案例分析Signature

    强制要求结构化输出,提高训练效果

    输入:
    - background: 案由描述
    - technical_field: 技术领域
    - patent_number: 专利号

    输出(结构化):
    - case_type: 单个案例类型关键词
    - legal_issues: 逗号分隔的法律问题
    - reasoning: 分段落的推理过程
    - conclusion: 简短结论
    """

    """根据专利案例信息进行结构化分析"""

    # 输入字段
    background = dspy.InputField(desc="""
案由描述,包括:
- 专利基本信息(专利号、申请日、授权公告日等)
- 无效宣告请求人的主张
- 涉及的证据
- 争议焦点
""")

    technical_field = dspy.InputField(desc="""
技术领域,如:
- 人工智能、机器人、智能汽车
- 医疗器械、生物医药、化学工程
- 机械制造、新能源、电子技术
- 食品工业、通用
""")

    patent_number = dspy.InputField(desc="""
专利号或申请号,格式如:
- CN1234567A (发明专利)
- CN1234567U (实用新型)
- CN1234567S (外观设计)
""")

    # 输出字段 - 明确要求结构化格式
    case_type = dspy.OutputField(desc="""
案例类型(必须选择其一):
- novelty (新颖性问题)
- creative (创造性问题)
- disclosure (充分公开问题)
- clarity (清楚性问题)

只输出一个词,如: novelty
""")

    legal_issues = dspy.OutputField(desc="""
法律问题列表(使用具体术语):
格式要求: 用逗号分隔,如: "新颖性问题,创造性问题,清楚问题"

常用术语:
- 新颖性问题
- 创造性问题
- 充分公开问题
- 清楚问题
- 程序问题
- 实用性问题
""")

    reasoning = dspy.OutputField(desc="""
决定理由(分段结构化):

第一段: 争议概述
- 简述无效宣告请求人的主张
- 列出主要证据

第二段: 法律依据
- 引用专利法具体条款
- 如: "根据专利法第22条第2款..."

第三段: 分析推理
- 逐条分析法律问题
- 结合证据进行论证

第四段: 结论
- 明确决定结果
""")

    conclusion = dspy.OutputField(desc="""
简短结论(一句话总结):
格式: "本专利[决定结果],因为[主要原因]"
示例: "本专利权全部无效,因为权利要求1不具备新颖性"
""")


# ===============================
# 2. Module实现 - 增强版
# ===============================


class EnhancedPatentAnalyzer(dspy.Module):
    """增强版专利案例分析器

    使用结构化输出和思维链
    """

    def __init__(self, use_cot: bool = True):
        """初始化分析器

        Args:
            use_cot: 是否使用ChainOfThought
        """
        super().__init__()

        if use_cot:
            # 使用CoT进行复杂推理
            self.analyze = dspy.ChainOfThought(StructuredPatentCaseAnalysis)
        else:
            # 直接预测
            self.analyze = dspy.Predict(StructuredPatentCaseAnalysis)

    def forward(self, background: str, technical_field: str, patent_number: str) -> dspy.Prediction:
        """前向传播

        Args:
            background: 案由描述
            technical_field: 技术领域
            patent_number: 专利号

        Returns:
            结构化分析结果
        """
        # 限制输入长度,避免超出LLM限制
        background_max = 3000
        background_truncated = background[:background_max]

        if len(background) > background_max:
            logger.debug(f"Background截断: {len(background)} -> {background_max}")

        result = self.analyze(
            background=background_truncated,
            technical_field=technical_field,
            patent_number=patent_number,
        )

        return result


class EnhancedPatentRAGAnalyzer(dspy.Module):
    """带检索增强的专利分析器 v3

    结合向量检索的增强版
    """

    def __init__(self, k: int = 3):
        """初始化RAG分析器

        Args:
            k: 检索的相似案例数量
        """
        super().__init__()
        self.k = k

        # 分析器
        self.analyze = dspy.ChainOfThought(StructuredPatentCaseAnalysis)

        # 检索器(可选)
        self.vector_retriever = None
        self._init_retrievers()

    def _init_retrievers(self) -> Any:
        """初始化检索器"""
        try:
            from ..retrievers import AthenaVectorRetriever

            self.vector_retriever = AthenaVectorRetriever()
            logger.info("✅ 向量检索器初始化成功")
        except Exception as e:
            logger.debug(f"⚠️ 向量检索器未启用: {e}")

    def forward(self, background: str, technical_field: str, patent_number: str) -> dspy.Prediction:
        """前向传播(带检索增强)

        Args:
            background: 案由描述
            technical_field: 技术领域
            patent_number: 专利号

        Returns:
            分析结果
        """
        # 构建增强的背景信息
        enhanced_background = background

        # 如果有检索器,添加相关案例
        if self.vector_retriever:
            try:
                retrieved = self.vector_retriever(background, k=self.k)
                if retrieved and len(retrieved) > 0:
                    enhanced_background += "\n\n[参考案例]\n"
                    for i, case in enumerate(retrieved[: self.k]):
                        case_type = case.get("case_type", "unknown")
                        case_brief = case.get("background", "")[:100]
                        enhanced_background += f"\n参考{i+1} ({case_type}): {case_brief}..."
            except Exception as e:
                logger.debug(f"检索失败: {e}")

        result = self.analyze(
            background=enhanced_background[:3000],
            technical_field=technical_field,
            patent_number=patent_number,
        )

        return result


# ===============================
# 3. 评估指标 - 使用增强版
# ===============================


def enhanced_metric(example: dspy.Example, pred: dspy.Prediction, trace=None) -> float:
    """增强的评估指标

    使用新的EnhancedPatentMetrics进行评估

    Args:
        example: 标准答案
        pred: 模型预测
        trace: 训练轨迹

    Returns:
        评分 (0.0 - 1.0)
    """
    try:
        from .enhanced_metrics import evaluate_enhanced

        return evaluate_enhanced(example, pred, trace)
    except ImportError:
        logger.warning("enhanced_metrics不可用,使用fallback评估")
        return fallback_metric(example, pred)


def fallback_metric(example: dspy.Example, pred: dspy.Prediction, trace=None) -> float:
    """Fallback评估指标

    当enhanced_metrics不可用时使用
    """
    score = 0.0

    # Case type匹配 (40%)
    if hasattr(pred, "case_type") and hasattr(example, "case_type"):
        if str(pred.case_type).lower() == str(example.case_type).lower():
            score += 0.40

    # Legal issues匹配 (30%)
    if hasattr(pred, "legal_issues"):
        pred_issues = str(pred.legal_issues).lower()
        if hasattr(example, "legal_issues"):
            for issue in example.legal_issues:
                if issue.lower() in pred_issues:
                    score += 0.15  # 每个匹配的issue给15分

    # Reasoning长度 (30%)
    if hasattr(pred, "reasoning"):
        reasoning_len = len(str(pred.reasoning))
        if 100 <= reasoning_len <= 1000:
            score += 0.30
        elif reasoning_len >= 50:
            score += 0.15

    return min(score, 1.0)


# ===============================
# 4. 训练配置
# ===============================


class TrainingConfig:
    """训练配置类"""

    # 数据集
    TRAINSET_MODULE = "core.intelligence.dspy.data.training_data_QUALITY_100_dspy"

    # 训练参数
    MAX_BOOTSTRAPPED_DEMOS = 5  # BootstrapFewShot的最大示例数
    MAX_LABELED_DEMOS = 10  # 标记示例数
    MAX_ROUNDS = 30  # MIPROv2最大轮数
    NUM_TRIALS = 20  # 每轮尝试次数

    # 评估参数
    THRESHOLD = 0.5  # 目标分数阈值
    METRIC = enhanced_metric  # 评估指标函数

    # 输出目录
    OUTPUT_DIR = Path("/Users/xujian/Athena工作平台/core/intelligence/dspy/models")

    @classmethod
    def get_trainset(cls) -> list[dspy.Example]:
        """加载训练数据集"""
        try:
            from importlib import import_module

            module = import_module(cls.TRAINSET_MODULE)
            return module.trainset
        except ImportError as e:
            logger.error(f"无法加载训练数据集: {e}")
            return []


# ===============================
# 5. 训练流程
# ===============================


def run_training_phase1() -> Any:
    """运行Phase 1训练: BootstrapFewShot建立基线"""

    logger.info("=" * 70)
    logger.info("🚀 DSPy训练 Phase 1: BootstrapFewShot基线训练")
    logger.info("=" * 70)

    # 加载数据
    trainset = TrainingConfig.get_trainset()
    if not trainset:
        logger.error("❌ 无法加载训练数据")
        return None

    logger.info(f"✅ 加载训练数据: {len(trainset)} 条")

    # 划分训练集和验证集
    random.seed(42)
    shuffled = trainset.copy()
    random.shuffle(shuffled)

    split_idx = int(len(shuffled) * 0.8)
    train_data = shuffled[:split_idx]
    val_data = shuffled[split_idx:]

    logger.info(f"  - 训练集: {len(train_data)} 条")
    logger.info(f"  - 验证集: {len(val_data)} 条")

    # 创建分析器
    analyzer = EnhancedPatentAnalyzer(use_cot=True)

    # 配置BootstrapFewShot
    optimizer = dspy.BootstrapFewShot(
        metric=TrainingConfig.METRIC,
        max_bootstrapped_demos=TrainingConfig.MAX_BOOTSTRAPPED_DEMOS,
        max_labeled_demos=TrainingConfig.MAX_LABELED_DEMOS,
        teacher_settings={"lm": dspy.settings.lm},
    )

    # 训练
    logger.info("\n📊 开始训练...")
    start_time = datetime.now()

    try:
        compiled_analyzer = optimizer.compile(student=analyzer, trainset=train_data)

        training_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ 训练完成! 用时: {training_time:.1f}秒")

        # 评估
        logger.info("\n📈 评估模型...")
        scores = []
        for example in val_data[:20]:  # 评估前20条
            try:
                pred = compiled_analyzer(
                    background=example.background,
                    technical_field=example.technical_field,
                    patent_number=example.patent_number,
                )
                score = TrainingConfig.METRIC(example, pred)
                scores.append(score)
            except Exception as e:
                logger.debug(f"评估失败: {e}")

        avg_score = sum(scores) / len(scores) if scores else 0.0
        logger.info(f"  平均分数: {avg_score:.3f} ({avg_score*100:.1f}%)")

        # 保存模型
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_path = TrainingConfig.OUTPUT_DIR / f"patent_analyzer_bootstrap_v3_{timestamp}.json"

        TrainingConfig.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        model_info = {
            "version": "3.0.0-enhanced",
            "training_phase": "BootstrapFewShot",
            "timestamp": timestamp,
            "training_time_seconds": training_time,
            "avg_score": avg_score,
            "num_samples": len(train_data),
            "config": {
                "max_bootstrapped_demos": TrainingConfig.MAX_BOOTSTRAPPED_DEMOS,
                "max_labeled_demos": TrainingConfig.MAX_LABELED_DEMOS,
            },
        }

        with open(model_path, "w", encoding="utf-8") as f:
            json.dump(model_info, f, ensure_ascii=False, indent=2)

        logger.info(f"💾 模型已保存: {model_path}")

        return compiled_analyzer, avg_score

    except Exception as e:
        logger.error(f"❌ 训练失败: {e}")
        import traceback

        traceback.print_exc()
        return None, 0.0


def run_training_phase2(base_analyzer, base_score: float) -> None:
    """运行Phase 2训练: MIPROv2优化

    Args:
        base_analyzer: Phase 1训练的基线模型
        base_score: Phase 1的基线分数

    Returns:
        优化后的模型和分数
    """

    logger.info("\n" + "=" * 70)
    logger.info("🚀 DSPy训练 Phase 2: MIPROv2优化训练")
    logger.info(f"基线分数: {base_score:.3f} ({base_score*100:.1f}%)")
    logger.info("=" * 70)

    # 加载数据
    trainset = TrainingConfig.get_trainset()
    if not trainset:
        logger.error("❌ 无法加载训练数据")
        return None, 0.0

    # 重要:MIPROv2需要未编译的模型
    # 创建一个新的未编译实例
    logger.info("🔧 创建未编译的模型实例用于MIPROv2优化...")
    raw_analyzer = EnhancedPatentAnalyzer(use_cot=True)

    # 配置MIPROv2
    optimizer = dspy.MIPROv2(
        metric=TrainingConfig.METRIC,
        num_threads=TrainingConfig.NUM_TRIALS,
        teacher_settings={"lm": dspy.settings.lm},
    )

    # 训练
    logger.info("\n📊 开始优化训练...")
    logger.info(f"  尝试次数: {TrainingConfig.NUM_TRIALS}")

    start_time = datetime.now()

    try:
        # 使用原始未编译的模型进行MIPROv2优化
        optimized_analyzer = optimizer.compile(
            student=raw_analyzer,  # 使用未编译的模型
            trainset=trainset,
            max_bootstrapped_demos=TrainingConfig.MAX_BOOTSTRAPPED_DEMOS,
            max_labeled_demos=TrainingConfig.MAX_LABELED_DEMOS,
            requires_permission_to_run=False,  # 跳过用户确认
        )

        training_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ 优化完成! 用时: {training_time:.1f}秒")

        # 评估
        logger.info("\n📈 评估优化后的模型...")
        scores = []
        for example in trainset[:30]:  # 评估前30条
            try:
                pred = optimized_analyzer(
                    background=example.background,
                    technical_field=example.technical_field,
                    patent_number=example.patent_number,
                )
                score = TrainingConfig.METRIC(example, pred)
                scores.append(score)
            except Exception as e:
                logger.debug(f"评估失败: {e}")

        avg_score = sum(scores) / len(scores) if scores else 0.0
        improvement = avg_score - base_score

        logger.info(f"  平均分数: {avg_score:.3f} ({avg_score*100:.1f}%)")
        logger.info(f"  提升: {improvement:+.3f} ({improvement*100:+.1f}%)")

        # 保存模型
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_path = TrainingConfig.OUTPUT_DIR / f"patent_analyzer_miprov2_v3_{timestamp}.json"

        model_info = {
            "version": "3.0.0-enhanced",
            "training_phase": "MIPROv2",
            "timestamp": timestamp,
            "training_time_seconds": training_time,
            "base_score": base_score,
            "optimized_score": avg_score,
            "improvement": improvement,
            "num_samples": len(trainset),
            "config": {"num_threads": TrainingConfig.NUM_TRIALS},
        }

        with open(model_path, "w", encoding="utf-8") as f:
            json.dump(model_info, f, ensure_ascii=False, indent=2)

        logger.info(f"💾 模型已保存: {model_path}")

        return optimized_analyzer, avg_score

    except Exception as e:
        logger.error(f"❌ 优化训练失败: {e}")
        import traceback

        traceback.print_exc()
        return None, 0.0


# ===============================
# 6. 主程序
# ===============================


def main() -> None:
    """主训练流程"""

    logger.info("\n" + "=" * 70)
    logger.info("🎯 DSPy专利案例分析训练系统 v3 - 增强版")
    logger.info("=" * 70)

    # Phase 1: 建立基线
    baseline_analyzer, baseline_score = run_training_phase1()

    if baseline_analyzer is None:
        logger.error("❌ Phase 1训练失败,终止")
        return

    logger.info(f"\n✅ Phase 1完成! 基线分数: {baseline_score:.3f}")

    # 检查是否达到Phase 2启动条件
    if baseline_score >= 0.15:  # 15%阈值
        logger.info("✅ 基线分数达标,进入Phase 2优化...")

        # Phase 2: MIPROv2优化
        optimized_analyzer, optimized_score = run_training_phase2(baseline_analyzer, baseline_score)

        if optimized_analyzer:
            logger.info(f"\n✅ Phase 2完成! 最终分数: {optimized_score:.3f}")

            # 总体提升
            total_improvement = optimized_score - 0.3  # 与原始0.3相比
            logger.info(f"📊 总体提升: {total_improvement:+.3f} ({total_improvement*100:+.1f}%)")

            if optimized_score >= 0.5:
                logger.info("🎉 达到目标分数 (≥50%)!")
            else:
                logger.info(f"⚠️ 未达到目标分数 (50%),当前: {optimized_score*100:.1f}%")
    else:
        logger.warning(f"⚠️ 基线分数 {baseline_score:.3f} 未达到阈值 0.15,跳过Phase 2")

    logger.info("\n" + "=" * 70)
    logger.info("🏁 训练完成!")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
