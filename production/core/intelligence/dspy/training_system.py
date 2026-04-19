#!/usr/bin/env python3
from __future__ import annotations
"""
DSPy专利案例分析训练系统
DSPy Patent Case Analysis Training System

完整的DSPy训练流程:
1. 定义Signature (输入输出规范)
2. 实现Module (处理逻辑)
3. 配置评估指标 (metric)
4. 运行MIPROv2优化器
5. 保存优化结果

作者: 小娜·天秤女神
创建时间: 2025-12-29
版本: 1.0.0
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import dspy

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


# ===============================
# 1. Signature定义
# ===============================


class PatentCaseAnalysis(dspy.Signature):
    """专利案例分析Signature

    输入:
    - background: 案由描述
    - technical_field: 技术领域
    - patent_number: 专利号

    输出:
    - case_type: 案例类型 (novelty/creative/disclosure/clarity/procedural)
    - legal_issues: 法律问题列表
    - reasoning: 决定理由
    """

    """分析专利案例的法律问题和决定理由"""

    # 输入字段
    background = dspy.InputField(desc="案由描述,包括专利基本信息和争议背景")
    technical_field = dspy.InputField(desc="技术领域,如医药、机械、电子等")
    patent_number = dspy.InputField(desc="专利号或申请号")

    # 输出字段
    case_type = dspy.OutputField(
        desc="案例类型: novelty(新颖性)、creative(创造性)、disclosure(充分公开)、clarity(清楚性)、procedural(程序性)"
    )
    legal_issues = dspy.OutputField(desc="法律问题列表,如['新颖性问题', '创造性问题']")
    reasoning = dspy.OutputField(desc="决定理由,包括法律依据和推理过程")


class PatentCaseTypeClassifier(dspy.Signature):
    """专利案例类型分类Signature (简化版)

    仅用于分类任务,不需要生成完整推理
    """

    """根据专利案例信息判断其类型"""

    background = dspy.InputField(desc="案由描述")
    technical_field = dspy.InputField(desc="技术领域")

    case_type = dspy.OutputField(desc="案例类型: novelty/creative/disclosure/clarity/procedural")
    confidence = dspy.OutputField(desc="判断置信度,0-1之间的分数", prefix="置信度:")


# ===============================
# 2. Module实现
# ===============================


class PatentAnalyzer(dspy.Module):
    """专利案例分析器 - 完整版

    使用ChainOfThought进行复杂推理
    """

    def __init__(self):
        super().__init__()
        # 使用CoT进行推理
        self.analyze = dspy.ChainOfThought(PatentCaseAnalysis)

    def forward(self, background: str, technical_field: str, patent_number: str) -> dspy.Prediction:
        """前向传播

        Args:
            background: 案由描述
            technical_field: 技术领域
            patent_number: 专利号

        Returns:
            分析结果
        """
        return self.analyze(
            background=background, technical_field=technical_field, patent_number=patent_number
        )


class PatentTypeClassifier(dspy.Module):
    """专利案例类型分类器 - 简化版

    用于快速分类任务
    """

    def __init__(self):
        super().__init__()
        self.classify = dspy.Predict(PatentCaseTypeClassifier)

    def forward(self, background: str, technical_field: str) -> dspy.Prediction:
        """前向传播

        Args:
            background: 案由描述
            technical_field: 技术领域

        Returns:
            分类结果
        """
        return self.classify(
            background=background[:500], technical_field=technical_field  # 限制长度
        )


class PatentRAGAnalyzer(dspy.Module):
    """带检索增强的专利分析器

    结合向量检索和知识图谱查询
    """

    def __init__(self, k: int = 3):
        """初始化RAG分析器

        Args:
            k: 检索的相似案例数量
        """
        super().__init__()
        self.k = k

        # 初始化检索器(如果可用)
        self.vector_retriever = None
        self.graph_retriever = None

        try:
            from .retrievers import AthenaVectorRetriever

            self.vector_retriever = AthenaVectorRetriever()
            logger.info("向量检索器初始化成功")
        except Exception as e:
            logger.warning(f"向量检索器初始化失败: {e}")

        try:
            from .retrievers import AthenaGraphRetriever

            self.graph_retriever = AthenaGraphRetriever()
            logger.info("知识图谱检索器初始化成功")
        except Exception as e:
            logger.warning(f"知识图谱检索器初始化失败: {e}")

        # 分析器
        self.analyze = dspy.ChainOfThought(PatentCaseAnalysis)

    def forward(self, background: str, technical_field: str, patent_number: str) -> dspy.Prediction:
        """前向传播(带检索增强)

        Args:
            background: 案由描述
            technical_field: 技术领域
            patent_number: 专利号

        Returns:
            分析结果
        """
        # 检索相关案例
        context_parts = []

        if self.vector_retriever:
            try:
                retrieved = self.vector_retriever(background, k=self.k)
                if retrieved:
                    context_parts.append("相关案例:")
                    for i, case in enumerate(retrieved[: self.k]):
                        context_parts.append(f"  案例{i+1}: {case.get('case_type', 'unknown')}")
            except Exception as e:
                logger.debug(f"向量检索失败: {e}")

        if self.graph_retriever:
            try:
                retrieved = self.graph_retriever(technical_field, k=self.k)
                if retrieved:
                    context_parts.append("相关法律知识:")
                    for i, item in enumerate(retrieved[: self.k]):
                        context_parts.append(f"  知识{i+1}: {str(item)[:100]}")
            except Exception as e:
                logger.debug(f"图谱检索失败: {e}")

        # 构建增强的背景
        enhanced_background = background
        if context_parts:
            enhanced_background = f"""{background}

参考信息:
{chr(10).join(context_parts)}"""

        return self.analyze(
            background=enhanced_background[:2000],  # 限制总长度
            technical_field=technical_field,
            patent_number=patent_number,
        )


# ===============================
# 3. 评估指标
# ===============================


class PatentCaseMetrics:
    """专利案例分析评估指标"""

    @staticmethod
    def evaluate_exact_match(example: dspy.Example, pred: dspy.Prediction, trace=None) -> float:
        """精确匹配评估

        完全匹配得1分,否则0分

        Args:
            example: 标准答案
            pred: 预测结果
            trace: 调试信息(可选)

        Returns:
            评分 (0-1)
        """
        score = 0.0

        # 检查case_type
        if pred.case_type == example.case_type:
            score += 0.4

        # 检查legal_issues (简化:只检查是否有交集)
        if hasattr(pred, "legal_issues") and hasattr(example, "legal_issues"):
            pred_issues = (
                set(pred.legal_issues)
                if isinstance(pred.legal_issues, list)
                else {pred.legal_issues}
            )
            actual_issues = (
                set(example.legal_issues)
                if isinstance(example.legal_issues, list)
                else {example.legal_issues}
            )

            if pred_issues & actual_issues:  # 有交集
                score += 0.3

        # 检查reasoning (简化:检查长度和关键词)
        if hasattr(pred, "reasoning"):
            reasoning = pred.reasoning
            # 检查长度
            if len(reasoning) >= 50:
                score += 0.15
            # 检查关键词
            if any(kw in reasoning for kw in ["专利法", "认为", "因此", "不符合", "规定"]):
                score += 0.15

        return min(score, 1.0)

    @staticmethod
    def evaluate_type_accuracy(example: dspy.Example, pred: dspy.Prediction, trace=None) -> float:
        """类型准确率评估

        只评估case_type是否正确

        Args:
            example: 标准答案
            pred: 预测结果
            trace: 调试信息(可选)

        Returns:
            评分 (0-1)
        """
        return 1.0 if pred.case_type == example.case_type else 0.0

    @staticmethod
    def evaluate_soft_match(example: dspy.Example, pred: dspy.Prediction, trace=None) -> float:
        """软匹配评估

        考虑部分正确的情况

        Args:
            example: 标准答案
            pred: 预测结果
            trace: 调试信息(可选)

        Returns:
            评分 (0-1)
        """
        score = 0.0

        # Case type完全匹配
        if pred.case_type == example.case_type:
            score += 0.5
        # Case type相关 (如novelty和creative相关)
        elif (pred.case_type in ["novelty", "creative"] and example.case_type in [
            "novelty",
            "creative",
        ]) or (pred.case_type in ["disclosure", "clarity"] and example.case_type in [
            "disclosure",
            "clarity",
        ]):
            score += 0.25

        # Legal issues有部分匹配
        if hasattr(pred, "legal_issues") and hasattr(example, "legal_issues"):
            pred_issues = (
                set(pred.legal_issues)
                if isinstance(pred.legal_issues, list)
                else {str(pred.legal_issues)}
            )
            actual_issues = (
                set(example.legal_issues)
                if isinstance(example.legal_issues, list)
                else {str(example.legal_issues)}
            )

            intersection = pred_issues & actual_issues
            union = pred_issues | actual_issues

            if union:
                score += 0.5 * (len(intersection) / len(union))

        # Reasoning有内容
        if hasattr(pred, "reasoning") and pred.reasoning and len(pred.reasoning) >= 100:
            score += 0.1

        return min(score, 1.0)


# ===============================
# 4. 训练管理器
# ===============================


class DSPyTrainingManager:
    """DSPy训练管理器

    管理完整的训练流程
    """

    def __init__(
        self,
        trainset_path: str = "core/intelligence/dspy/data/training_data_FINAL_800_latest_dspy.py",
        output_dir: str = "core/intelligence/dspy/models",
    ):
        """初始化训练管理器

        Args:
            trainset_path: 训练数据路径
            output_dir: 模型输出目录
        """
        self.trainset_path = Path(trainset_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 加载训练数据
        self.trainset = self._load_trainset()

        # 配置DSPy
        self._configure_dspy()

    def _load_trainset(self) -> Any:
        """加载训练数据集"""
        logger.info(f"加载训练数据: {self.trainset_path}")

        try:
            # 动态导入训练数据
            import importlib.util

            spec = importlib.util.spec_from_file_location("trainset_module", self.trainset_path)
            trainset_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(trainset_module)

            trainset = trainset_module.trainset
            logger.info(f"成功加载 {len(trainset)} 个训练案例")
            return trainset

        except Exception as e:
            logger.error(f"加载训练数据失败: {e}")
            return []

    def _configure_dspy(self) -> Any:
        """配置DSPy设置 - 使用GLM-4.7作为默认后端"""
        try:
            # 使用新的LM配置模块(支持直接运行和模块导入)
            try:
                from .lm_config import configure_dspy_lm_with_fallback
            except (ImportError, ValueError):
                # 相对导入失败时尝试绝对导入
                from core.intelligence.dspy.lm_config import configure_dspy_lm_with_fallback

            # 配置GLM-4-Plus,失败时回退到DeepSeek
            lm = configure_dspy_lm_with_fallback(
                primary_model="glm-4-plus", fallback_model="deepseek-chat", max_workers=4
            )

            logger.info(f"DSPy LM配置成功: {lm.model}")

        except Exception as e:
            logger.error(f"DSPy LM配置完全失败: {e}")
            logger.info("将跳过LM配置,仅用于数据处理")

    def split_data(self, train_ratio: float = 0.7, val_ratio: float = 0.2) -> Any:
        """划分数据集

        Args:
            train_ratio: 训练集比例
            val_ratio: 验证集比例
        """
        if not self.trainset:
            logger.error("训练数据为空,无法划分")
            return None, None, None

        n = len(self.trainset)
        train_end = int(n * train_ratio)
        val_end = int(n * (train_ratio + val_ratio))

        trainset = self.trainset[:train_end]
        valset = self.trainset[train_end:val_end]
        testset = self.trainset[val_end:]

        logger.info(f"数据划分完成: 训练{len(trainset)}, 验证{len(valset)}, 测试{len(testset)}")

        return trainset, valset, testset

    def train_simple(self, num_trials: int = 20, max_rounds: int = 1) -> dspy.Module:
        """使用BootstrapFewShot进行简单训练

        Args:
            num_trials: 优化试验次数
            max_rounds: 最大优化轮数

        Returns:
            优化后的模型
        """
        logger.info("=" * 60)
        logger.info("开始DSPy简单训练 (BootstrapFewShot)")
        logger.info("=" * 60)

        # 划分数据
        trainset, _valset, testset = self.split_data()

        if not trainset:
            logger.error("无法训练:训练数据为空")
            return None

        # 创建模型
        model = PatentAnalyzer()

        # 配置优化器
        optimizer = dspy.BootstrapFewShot(
            metric=PatentCaseMetrics.evaluate_exact_match,
            max_bootstrapped_demos=num_trials,  # DSPy 2.6.5参数名
            max_labeled_demos=5,
            max_rounds=max_rounds,
            teacher_settings={"max_workers": 4},
        )

        # 运行优化
        logger.info(f"开始优化: {num_trials}次bootstrap, {max_rounds}轮, {len(trainset)}个训练样本")

        try:
            # BootstrapFewShot不使用valset参数
            optimized_model = optimizer.compile(
                student=model, trainset=trainset[:50]  # 限制样本数量加快训练
            )

            logger.info("优化完成!")

            # 评估
            if testset:
                self._evaluate_model(optimized_model, testset[:10])

            # 保存模型
            self._save_model(optimized_model, "bootstrap_fewshot")

            return optimized_model

        except Exception as e:
            logger.error(f"训练失败: {e}")
            return None

    def train_mipro(
        self, num_trials: int = 30, max_rounds: int = 3, max_labeled_demos: int = 5
    ) -> dspy.Module:
        """使用MIPROv2进行高级训练

        Args:
            num_trials: 优化试验次数
            max_rounds: 最大优化轮数
            max_labeled_demos: 最大标注示例数

        Returns:
            优化后的模型
        """
        logger.info("=" * 60)
        logger.info("开始DSPy高级训练 (MIPROv2)")
        logger.info("=" * 60)

        # 划分数据
        trainset, valset, testset = self.split_data()

        if not trainset:
            logger.error("无法训练:训练数据为空")
            return None

        # 创建模型
        model = PatentAnalyzer()

        # 配置MIPROv2优化器
        optimizer = dspy.MIPROv2(
            metric=PatentCaseMetrics.evaluate_exact_match,
            max_bootstrapped_demos=num_trials,  # DSPy 2.6.5参数名
            max_labeled_demos=max_labeled_demos,
            num_threads=4,  # 并行线程数
            teacher_settings={"max_workers": 4},
        )

        # 运行优化
        logger.info(f"开始MIPROv2优化: {num_trials}次试验, {max_labeled_demos}个标注示例")

        try:
            optimized_model = optimizer.compile(
                student=model,
                trainset=trainset[:100],  # 限制样本数量
                valset=valset[:30] if valset else None,
                requires_permission_to_run=False,  # 不需要权限确认
            )

            logger.info("MIPROv2优化完成!")

            # 评估
            if testset:
                self._evaluate_model(optimized_model, testset[:10])

            # 保存模型
            self._save_model(optimized_model, "miprov2")

            return optimized_model

        except Exception as e:
            logger.error(f"MIPROv2训练失败: {e}")
            logger.info("回退到简单训练...")
            return self.train_simple()

    def _evaluate_model(self, model: dspy.Module, testset: list[dspy.Example]) -> Any:
        """评估模型性能

        Args:
            model: 训练好的模型
            testset: 测试集
        """
        logger.info(f"评估模型性能 (测试集: {len(testset)}个样本)")

        # 精确匹配评估
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

            logger.info(f"精确匹配准确率: {avg_exact:.2%}")
            logger.info(f"类型准确率: {avg_type:.2%}")

    def _save_model(self, model: dspy.Module, optimizer_name: str) -> Any:
        """保存模型

        Args:
            model: 训练好的模型
            optimizer_name: 优化器名称
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_file = self.output_dir / f"patent_analyzer_{optimizer_name}_{timestamp}.json"

        try:
            # 保存模型配置
            model_info = {
                "optimizer": optimizer_name,
                "timestamp": timestamp,
                "model_class": model.__class__.__name__,
                "trainset_size": len(self.trainset),
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
            logger.info(f"  决定理由: {pred.reasoning[:200]}...")

            # 计算分数
            exact_score = PatentCaseMetrics.evaluate_exact_match(test_case, pred)
            type_score = PatentCaseMetrics.evaluate_type_accuracy(test_case, pred)

            logger.info("\n评分:")
            logger.info(f"  精确匹配: {exact_score:.2%}")
            logger.info(f"  类型准确: {type_score:.2%}")

        except Exception as e:
            logger.error(f"测试失败: {e}")


# ===============================
# 5. 主程序
# ===============================


def main() -> None:
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="DSPy专利案例分析训练系统")
    parser.add_argument(
        "--mode", choices=["test", "train-simple", "train-mipro"], default="test", help="运行模式"
    )
    parser.add_argument("--trials", type=int, default=20, help="优化试验次数")
    parser.add_argument("--rounds", type=int, default=3, help="最大优化轮数")

    args = parser.parse_args()

    # 创建训练管理器
    manager = DSPyTrainingManager()

    if args.mode == "test":
        # 测试模式
        logger.info("运行测试模式...")
        manager.test_model()

    elif args.mode == "train-simple":
        # 简单训练
        logger.info("运行简单训练模式...")
        manager.train_simple(num_trials=args.trials)

    elif args.mode == "train-mipro":
        # MIPROv2训练
        logger.info("运行MIPROv2训练模式...")
        manager.train_mipro(num_trials=args.trials, max_rounds=args.rounds)


if __name__ == "__main__":
    main()
