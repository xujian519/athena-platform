#!/usr/bin/env python3
"""
DSPy专利案例分析训练系统 V2 - 改进版
DSPy Patent Case Analysis Training System V2 - Enhanced

主要改进:
1. 支持分批处理避免上下文窗口溢出
2. 支持训练进度保存和恢复
3. 智能上下文窗口管理
4. 更好的错误处理和日志记录

作者: 小娜·天秤女神
创建时间: 2025-12-30
版本: 2.0.0
"""

import json
import logging
import pickle
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import dspy

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


# ===============================
# 数据类定义
# ===============================


@dataclass
class TrainingCheckpoint:
    """训练检查点数据"""

    timestamp: str
    optimizer_type: str
    current_batch: int
    total_batches: int
    best_score: float
    training_history: list[dict[str, Any]]
    model_state: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TrainingCheckpoint":
        """从字典创建实例"""
        return cls(**data)

    def save(self, filepath: Path) -> Any:
        """保存检查点到文件"""
        with open(filepath, "wb") as f:
            pickle.dump(self, f)
        logger.info(f"检查点已保存: {filepath}")

    @classmethod
    def load(cls, filepath: Path) -> "TrainingCheckpoint":
        """从文件加载检查点"""
        with open(filepath, "rb") as f:
            checkpoint = pickle.load(f)
        logger.info(f"检查点已加载: {filepath}")
        return checkpoint


# ===============================
# 上下文窗口管理器
# ===============================


class ContextWindowManager:
    """上下文窗口管理器

    用于智能管理训练过程中的prompt长度,避免超过模型上下文窗口限制
    """

    # 模型上下文窗口限制(tokens)
    MODEL_CONTEXT_LIMITS = {
        "glm-4-plus": 128000,
        "glm-4.7": 128000,
        "glm-4.6": 128000,
        "glm-4.5": 128000,
        "glm-4-air": 128000,
        "glm-4-flash": 128000,
        "deepseek-chat": 64000,
        "deepseek-coder": 64000,
        "gpt-4o": 128000,
        "gpt-4o-mini": 128000,
    }

    # 安全系数(保留20%的缓冲空间)
    SAFETY_FACTOR = 0.8

    # 预估的prompt模板开销(tokens)
    PROMPT_TEMPLATE_OVERHEAD = 1000

    def __init__(self, model_name: str = "glm-4-plus"):
        """初始化上下文窗口管理器

        Args:
            model_name: 使用的模型名称
        """
        self.model_name = model_name
        self.context_limit = self.MODEL_CONTEXT_LIMITS.get(model_name, 64000)  # 默认64K
        self.safe_limit = int(self.context_limit * self.SAFETY_FACTOR)
        self.available_for_examples = self.safe_limit - self.PROMPT_TEMPLATE_OVERHEAD

        logger.info("上下文窗口管理器初始化:")
        logger.info(f"  模型: {model_name}")
        logger.info(f"  硬限制: {self.context_limit:,} tokens")
        logger.info(f"  安全限制: {self.safe_limit:,} tokens")
        logger.info(f"  可用于示例: {self.available_for_examples:,} tokens")

    def estimate_tokens(self, text: str) -> int:
        """估算文本的token数量

        使用简单规则:中文约1.5字符/token,英文约4字符/token

        Args:
            text: 输入文本

        Returns:
            预估的token数量
        """
        if not text:
            return 0

        # 统计中文字符和非中文字符
        chinese_chars = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
        non_chinese_chars = len(text) - chinese_chars

        # 估算tokens
        chinese_tokens = chinese_chars * 1.5
        non_chinese_tokens = non_chinese_chars / 4

        return int(chinese_tokens + non_chinese_tokens)

    def estimate_example_tokens(self, example: dspy.Example) -> int:
        """估算单个示例的token数量

        Args:
            example: DSPy示例对象

        Returns:
            预估的token数量
        """
        total_text = ""

        # 收集所有输入字段
        for field_name in example.inputs():
            if hasattr(example, field_name):
                value = getattr(example, field_name)
                if value:
                    total_text += str(value) + " "

        # 收集所有输出字段
        for field_name in example.labels():
            if hasattr(example, field_name):
                value = getattr(example, field_name)
                if isinstance(value, list):
                    total_text += " ".join(str(v) for v in value) + " "
                else:
                    total_text += str(value) + " "

        return self.estimate_tokens(total_text)

    def calculate_max_examples(
        self, example_token_counts: list[int], max_bootstrapped_demos: int
    ) -> int:
        """计算在上下文窗口限制内最多可以保留多少示例

        Args:
            example_token_counts: 每个示例的token数量列表
            max_bootstrapped_demos: 配置的最大bootstrap示例数

        Returns:
            实际可用的最大示例数
        """
        if not example_token_counts:
            return 0

        # 按token数量排序(优先保留较短的示例)
        sorted_counts = sorted(example_token_counts)

        # 计算可以保留多少个示例
        total_tokens = 0
        max_examples = 0

        for count in sorted_counts:
            if total_tokens + count <= self.available_for_examples:
                total_tokens += count
                max_examples += 1
            else:
                break

        # 不超过配置的最大值
        result = min(max_examples, max_bootstrapped_demos)

        logger.info("示例数量计算:")
        logger.info(f"  配置的最大值: {max_bootstrapped_demos}")
        logger.info(f"  基于上下文窗口的最大值: {max_examples}")
        logger.info(f"  最终使用: {result}")
        logger.info(f"  预估总token数: {total_tokens:,}")

        return result

    def truncate_example(self, example: dspy.Example, max_tokens: int) -> dspy.Example:
        """截断示例以适应token限制

        Args:
            example: 输入示例
            max_tokens: 最大token数量

        Returns:
            截断后的示例
        """
        # 简单实现:截断background字段
        if hasattr(example, "background"):
            background = str(example.background)
            current_tokens = self.estimate_tokens(background)

            if current_tokens > max_tokens:
                # 按比例截断
                ratio = max_tokens / current_tokens
                truncated_length = int(len(background) * ratio)
                example = example.with_inputs(background=background[:truncated_length] + "...")

        return example


# ===============================
# 导入原有的Signature和Module
# ===============================

# 从原模块导入
import sys

sys.path.insert(0, str(Path(__file__).parent))

try:
    from training_system import (
        PatentAnalyzer,
        PatentCaseAnalysis,
        PatentCaseMetrics,
        PatentCaseTypeClassifier,
        PatentRAGAnalyzer,
        PatentTypeClassifier,
    )

    logger.info("成功从training_system导入组件")
except ImportError as e:
    logger.error(f"无法导入training_system组件: {e}")
    raise


# ===============================
# 增强的训练管理器
# ===============================


class DSPyTrainingManagerV2:
    """DSPy训练管理器 V2 - 增强版

    主要改进:
    1. 支持分批处理
    2. 支持训练进度保存和恢复
    3. 智能上下文窗口管理
    """

    def __init__(
        self,
        trainset_path: str = "core/intelligence/dspy/data/training_data_FINAL_800_latest_dspy.py",
        output_dir: str = "core/intelligence/dspy/models",
        checkpoint_dir: str = "core/intelligence/dspy/checkpoints",
        model_name: str = "glm-4-plus",
    ):
        """初始化训练管理器

        Args:
            trainset_path: 训练数据路径
            output_dir: 模型输出目录
            checkpoint_dir: 检查点保存目录
            model_name: 使用的模型名称
        """
        self.trainset_path = Path(trainset_path)
        self.output_dir = Path(output_dir)
        self.checkpoint_dir = Path(checkpoint_dir)
        self.model_name = model_name

        # 创建目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # 初始化上下文窗口管理器
        self.context_manager = ContextWindowManager(model_name)

        # 加载训练数据
        self.trainset = self._load_trainset()

        # 配置DSPy
        self._configure_dspy()

    def _load_trainset(self) -> Any:
        """加载训练数据集"""
        logger.info(f"加载训练数据: {self.trainset_path}")

        try:
            import importlib.util

            spec = importlib.util.spec_from_file_location("trainset_module", self.trainset_path)
            trainset_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(trainset_module)

            trainset = trainset_module.trainset
            logger.info(f"成功加载 {len(trainset)} 个训练案例")

            # 分析训练数据
            self._analyze_trainset(trainset)

            return trainset

        except Exception as e:
            logger.error(f"加载训练数据失败: {e}")
            return []

    def _analyze_trainset(self, trainset: list[dspy.Example]) -> Any:
        """分析训练数据集

        Args:
            trainset: 训练数据集
        """
        logger.info("=" * 60)
        logger.info("训练数据分析")
        logger.info("=" * 60)

        # 估算每个示例的token数
        token_counts = []
        for example in trainset:
            count = self.context_manager.estimate_example_tokens(example)
            token_counts.append(count)

        # 统计
        total_tokens = sum(token_counts)
        avg_tokens = total_tokens / len(token_counts) if token_counts else 0
        max_tokens = max(token_counts) if token_counts else 0
        min_tokens = min(token_counts) if token_counts else 0

        logger.info(f"总样本数: {len(trainset)}")
        logger.info(f"总token数: {total_tokens:,}")
        logger.info(f"平均token数/样本: {avg_tokens:.0f}")
        logger.info(f"最大token数/样本: {max_tokens:,}")
        logger.info(f"最小token数/样本: {min_tokens:,}")

        # 估算在不同batch size下的内存使用
        logger.info("\nBatch大小预估:")
        for batch_size in [10, 20, 30, 50, 100]:
            batch_tokens = sum(sorted(token_counts)[:batch_size])
            logger.info(
                f"  {batch_size}个样本: ~{batch_tokens:,} tokens "
                f"({batch_tokens / self.context_manager.context_limit:.1%} of context)"
            )

    def _configure_dspy(self) -> Any:
        """配置DSPy设置"""
        try:
            from lm_config import configure_dspy_lm_with_fallback
        except (ImportError, ValueError):
            from core.intelligence.dspy.lm_config import configure_dspy_lm_with_fallback

        # 配置LM
        lm = configure_dspy_lm_with_fallback(
            primary_model=self.model_name, fallback_model="deepseek-chat", max_workers=4
        )

        logger.info(f"DSPy LM配置成功: {lm.model}")

    def split_data(
        self, train_ratio: float = 0.6, val_ratio: float = 0.3, min_valset_size: int = 100
    ) -> tuple[list[dspy.Example], list[dspy.Example], list[dspy.Example]]:
        """划分数据集

        Args:
            train_ratio: 训练集比例
            val_ratio: 验证集比例
            min_valset_size: 验证集最小大小(MIPROv2要求)

        Returns:
            (trainset, valset, testset)
        """
        if not self.trainset:
            logger.error("训练数据为空,无法划分")
            return [], [], []

        n = len(self.trainset)

        # 确保验证集足够大(MIPROv2要求valset大小 >= minibatch大小)
        required_val_size = max(int(n * val_ratio), min_valset_size)
        train_end = n - required_val_size - int(n * 0.1)  # 剩余10%给测试集

        trainset = self.trainset[:train_end]
        valset = self.trainset[train_end : train_end + required_val_size]
        testset = self.trainset[train_end + required_val_size :]

        logger.info(f"数据划分完成: 训练{len(trainset)}, 验证{len(valset)}, 测试{len(testset)}")

        return trainset, valset, testset

    def train_mipro_with_batches(
        self,
        num_trials: int = 30,
        max_rounds: int = 3,
        max_labeled_demos: int = 5,
        batch_size: int = 50,
        max_samples: int = 100,
        resume_from_checkpoint: Path | None = None,
        save_every_batch: bool = True,
    ) -> dspy.Module:
        """使用MIPROv2进行分批训练

        Args:
            num_trials: 每批的优化试验次数
            max_rounds: 最大优化轮数
            max_labeled_demos: 最大标注示例数
            batch_size: 每批处理的样本数量
            max_samples: 最大训练样本数(0=使用全部数据)
            resume_from_checkpoint: 从检查点恢复训练
            save_every_batch: 是否每批保存检查点

        Returns:
            优化后的模型
        """
        logger.info("=" * 60)
        logger.info("开始DSPy分批MIPROv2训练")
        logger.info("=" * 60)

        # 划分数据
        trainset, valset, testset = self.split_data()

        # 限制训练样本数量
        if max_samples > 0 and len(trainset) > max_samples:
            logger.info(f"限制训练样本数: {len(trainset)} → {max_samples}")
            trainset = trainset[:max_samples]

        if not trainset:
            logger.error("无法训练:训练数据为空")
            return None

        # 计算实际的max_bootstrapped_demos
        example_token_counts = [
            self.context_manager.estimate_example_tokens(ex) for ex in trainset[:batch_size]
        ]
        actual_num_trials = self.context_manager.calculate_max_examples(
            example_token_counts, num_trials
        )

        # 分批处理
        num_batches = (len(trainset) + batch_size - 1) // batch_size
        logger.info(f"总批数: {num_batches}")
        logger.info(f"每批样本数: {batch_size}")
        logger.info(f"每批试验次数: {actual_num_trials} (基于上下文窗口优化)")

        # 创建模型
        model = PatentAnalyzer()

        # 训练历史
        training_history = []
        best_score = 0.0
        best_model_state = None

        # 从检查点恢复
        start_batch = 0
        if resume_from_checkpoint and resume_from_checkpoint.exists():
            try:
                checkpoint = TrainingCheckpoint.load(resume_from_checkpoint)
                start_batch = checkpoint.current_batch + 1
                best_score = checkpoint.best_score
                training_history = checkpoint.training_history
                logger.info(f"从检查点恢复: 批次 {start_batch}/{num_batches}")
            except Exception as e:
                logger.warning(f"加载检查点失败: {e},从头开始")

        # 分批训练
        for batch_idx in range(start_batch, num_batches):
            logger.info("=" * 60)
            logger.info(f"批次 {batch_idx + 1}/{num_batches}")
            logger.info("=" * 60)

            # 获取当前批次的数据
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, len(trainset))
            batch_trainset = trainset[start_idx:end_idx]

            logger.info(f"处理样本 {start_idx}-{end_idx} ({len(batch_trainset)} 个)")

            try:
                # 配置MIPROv2优化器
                optimizer = dspy.MIPROv2(
                    metric=PatentCaseMetrics.evaluate_exact_match,
                    max_bootstrapped_demos=actual_num_trials,  # 使用优化后的值
                    max_labeled_demos=max_labeled_demos,
                    num_threads=4,
                    teacher_settings={"max_workers": 4},
                )

                # 运行优化
                # MIPROv2要求valset大小 >= batch_size
                valset_size = min(len(valset), len(batch_trainset) + 20) if valset else 0
                optimized_model = optimizer.compile(
                    student=model,
                    trainset=batch_trainset,
                    valset=valset[:valset_size] if valset_size > 0 else None,
                    requires_permission_to_run=False,
                )

                # 评估当前批次
                if testset:
                    batch_score = self._evaluate_model(optimized_model, testset[:10], verbose=False)
                else:
                    batch_score = 0.0

                # 记录历史
                history_entry = {
                    "batch": batch_idx + 1,
                    "samples": len(batch_trainset),
                    "score": batch_score,
                    "timestamp": datetime.now().isoformat(),
                }
                training_history.append(history_entry)

                # 更新最佳模型
                if batch_score > best_score:
                    best_score = batch_score
                    best_model_state = optimized_model
                    logger.info(f"✓ 新的最佳模型! 分数: {best_score:.2%}")

                # 保存检查点
                if save_every_batch:
                    checkpoint = TrainingCheckpoint(
                        timestamp=datetime.now().strftime("%Y%m%d_%H%M%S"),
                        optimizer_type="miprov2",
                        current_batch=batch_idx,
                        total_batches=num_batches,
                        best_score=best_score,
                        training_history=training_history,
                    )
                    checkpoint_path = self.checkpoint_dir / f"miprov2_batch_{batch_idx}.pkl"
                    checkpoint.save(checkpoint_path)

                logger.info(f"批次 {batch_idx + 1} 完成, 分数: {batch_score:.2%}")

            except Exception as e:
                logger.error(f"批次 {batch_idx + 1} 失败: {e}")
                # 继续下一批次
                continue

        logger.info("=" * 60)
        logger.info("所有批次训练完成!")
        logger.info(f"最佳分数: {best_score:.2%}")
        logger.info("=" * 60)

        # 使用最佳模型
        final_model = best_model_state if best_model_state else model

        # 最终评估
        if testset:
            self._evaluate_model(final_model, testset[:20])

        # 保存模型
        self._save_model(
            final_model,
            "miprov2_v2",
            {
                "num_batches": num_batches,
                "batch_size": batch_size,
                "actual_num_trials": actual_num_trials,
                "best_score": best_score,
                "training_history": training_history,
            },
        )

        # 保存最终检查点
        final_checkpoint = TrainingCheckpoint(
            timestamp=datetime.now().strftime("%Y%m%d_%H%M%S"),
            optimizer_type="miprov2",
            current_batch=num_batches,
            total_batches=num_batches,
            best_score=best_score,
            training_history=training_history,
        )
        final_checkpoint.save(self.checkpoint_dir / "miprov2_final.pkl")

        return final_model

    def _evaluate_model(
        self, model: dspy.Module, testset: list[dspy.Example], verbose: bool = True
    ) -> float:
        """评估模型性能

        Args:
            model: 训练好的模型
            testset: 测试集
            verbose: 是否输出详细信息

        Returns:
            平均分数
        """
        if verbose:
            logger.info(f"评估模型性能 (测试集: {len(testset)}个样本)")

        exact_scores = []
        type_scores = []

        for example in testset:
            try:
                pred = model(
                    background=example.background,
                    technical_field=example.technical_field,
                    patent_number=example.patent_number,
                )

                exact_score = PatentCaseMetrics.evaluate_exact_match(example, pred)
                type_score = PatentCaseMetrics.evaluate_type_accuracy(example, pred)

                exact_scores.append(exact_score)
                type_scores.append(type_score)

            except Exception as e:
                logger.debug(f"评估失败: {e}")
                continue

        if exact_scores:
            avg_exact = sum(exact_scores) / len(exact_scores)
            avg_type = sum(type_scores) / len(type_scores)

            if verbose:
                logger.info(f"精确匹配准确率: {avg_exact:.2%}")
                logger.info(f"类型准确率: {avg_type:.2%}")

            return avg_exact

        return 0.0

    def _save_model(
        self, model: dspy.Module, optimizer_name: str, metadata: dict[str, Any] | None = None
    ):
        """保存模型

        Args:
            model: 训练好的模型
            optimizer_name: 优化器名称
            metadata: 额外的元数据
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_file = self.output_dir / f"patent_analyzer_{optimizer_name}_{timestamp}.json"

        try:
            model_info = {
                "optimizer": optimizer_name,
                "timestamp": timestamp,
                "model_class": model.__class__.__name__,
                "trainset_size": len(self.trainset),
                "model_name": self.model_name,
                "metadata": metadata or {},
            }

            with open(model_file, "w", encoding="utf-8") as f:
                json.dump(model_info, f, ensure_ascii=False, indent=2)

            logger.info(f"模型已保存: {model_file}")

        except Exception as e:
            logger.error(f"保存模型失败: {e}")

    def test_model(self, model: dspy.Module | None = None) -> Any:
        """测试模型

        Args:
            model: 模型(可选,默认使用未优化的模型)
        """
        if model is None:
            model = PatentAnalyzer()

        # 测试案例
        test_case = dspy.Example(
            background="本专利涉及一种新型锂电池正极材料,申请人声称该材料具有高能量密度和长循环寿命。请求人认为该专利不具备创造性,因为该材料与现有技术中的材料结构相似。",
            technical_field="新能源",
            patent_number="CN202310123456.7",
            case_type="creative",
            legal_issues=["创造性问题"],
            reasoning="",
        ).with_inputs("background", "technical_field", "patent_number")

        logger.info("=" * 60)
        logger.info("测试模型")
        logger.info("=" * 60)
        logger.info(f"输入背景: {test_case.background[:100]}...")

        try:
            pred = model(
                background=test_case.background,
                technical_field=test_case.technical_field,
                patent_number=test_case.patent_number,
            )

            logger.info("\n预测结果:")
            logger.info(f"  案例类型: {pred.case_type}")
            logger.info(f"  法律问题: {pred.legal_issues}")
            logger.info(
                f"  决定理由: {pred.reasoning[:200] if hasattr(pred, 'reasoning') else 'N/A'}..."
            )

            # 计算分数
            exact_score = PatentCaseMetrics.evaluate_exact_match(test_case, pred)
            type_score = PatentCaseMetrics.evaluate_type_accuracy(test_case, pred)

            logger.info("\n评分:")
            logger.info(f"  精确匹配: {exact_score:.2%}")
            logger.info(f"  类型准确: {type_score:.2%}")

        except Exception as e:
            logger.error(f"测试失败: {e}")


# ===============================
# 主程序
# ===============================


def main() -> None:
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="DSPy专利案例分析训练系统 V2")
    parser.add_argument(
        "--mode", choices=["test", "train-mipro", "resume"], default="test", help="运行模式"
    )
    parser.add_argument("--trials", type=int, default=30, help="优化试验次数")
    parser.add_argument("--rounds", type=int, default=3, help="最大优化轮数")
    parser.add_argument("--batch-size", type=int, default=50, help="批次大小")
    parser.add_argument(
        "--max-samples", type=int, default=100, help="最大训练样本数 (0=使用全部数据)"
    )
    parser.add_argument("--resume-checkpoint", type=str, help="恢复训练的检查点路径")
    parser.add_argument(
        "--model",
        type=str,
        default="glm-4-plus",
        choices=["glm-4-plus", "glm-4.7", "deepseek-chat"],
        help="使用的模型",
    )

    args = parser.parse_args()

    # 创建训练管理器
    manager = DSPyTrainingManagerV2(model_name=args.model)

    if args.mode == "test":
        # 测试模式
        logger.info("运行测试模式...")
        manager.test_model()

    elif args.mode == "train-mipro":
        # MIPROv2训练
        logger.info("运行MIPROv2训练模式...")
        manager.train_mipro_with_batches(
            num_trials=args.trials,
            max_rounds=args.rounds,
            batch_size=args.batch_size,
            max_samples=args.max_samples,
        )

    elif args.mode == "resume":
        # 恢复训练
        if not args.resume_checkpoint:
            logger.error("请指定--resume-checkpoint参数")
            return

        checkpoint_path = Path(args.resume_checkpoint)
        if not checkpoint_path.exists():
            logger.error(f"检查点文件不存在: {checkpoint_path}")
            return

        logger.info(f"从检查点恢复训练: {checkpoint_path}")
        manager.train_mipro_with_batches(
            num_trials=args.trials,
            max_rounds=args.rounds,
            batch_size=args.batch_size,
            max_samples=args.max_samples,
            resume_from_checkpoint=checkpoint_path,
        )


if __name__ == "__main__":
    main()
