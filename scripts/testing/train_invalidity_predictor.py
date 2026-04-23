#!/usr/bin/env python3
"""
无效性预测模型训练脚本
Train Invalidity Prediction Model

基于论文#19《Predicting Patent Invalidity》
- Gradient Boosting模型: AUC=0.80
- 关键特征: 审查历史、权利要求特征、引用模式

作者: 小娜·天秤女神
创建时间: 2026-03-20
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class PatentFeatures:
    """专利特征数据类"""
    # 审查历史特征 (35%重要性)
    prosecution_days: int = 0
    office_actions: int = 0
    rejections: int = 0
    claim_amendments: int = 0
    examiner_changes: int = 0

    # 权利要求特征 (25%重要性)
    independent_claims: int = 0
    total_claims: int = 0
    avg_claim_length: float = 0.0
    qualifier_density: float = 0.0

    # 引用特征 (20%重要性)
    forward_cites: int = 0
    backward_cites: int = 0
    np_cite_ratio: float = 0.0
    self_cites: int = 0

    # 权利人特征 (10%重要性)
    is_npe: bool = False
    patent_portfolio_size: int = 0
    assignee_type: str = "unknown"

    # 技术领域特征 (10%重要性)
    is_software_patent: bool = False
    is_business_method: bool = False
    tech_breadth: float = 0.0

    # 标签
    invalidated: bool | None = None  # True/False/None(未知)

    def to_feature_vector(self) -> np.ndarray:
        """转换为特征向量"""
        return np.array([
            # 审查历史特征 (标准化)
            self.prosecution_days / 3650,
            self.office_actions / 10,
            self.rejections / 10,
            self.claim_amendments / 10,
            self.examiner_changes / 3,

            # 权利要求特征
            self.independent_claims / 5,
            self.total_claims / 30,
            self.avg_claim_length / 500,
            self.qualifier_density,

            # 引用特征
            np.log1p(self.forward_cites) / 10,
            np.log1p(self.backward_cites) / 10,
            self.np_cite_ratio,
            self.self_cites / 10,

            # 权利人特征
            1.0 if self.is_npe else 0.0,
            np.log1p(self.patent_portfolio_size) / 10,
            1.0 if self.assignee_type == "individual" else 0.0,

            # 技术领域特征
            1.0 if self.is_software_patent else 0.0,
            1.0 if self.is_business_method else 0.0,
            self.tech_breadth,
        ])


@dataclass
class TrainingData:
    """训练数据集"""
    features: np.ndarray
    labels: np.ndarray
    patent_ids: list[str] = field(default_factory=list)

    def __post_init__(self):
        if len(self.patent_ids) == 0:
            self.patent_ids = [f"patent_{i}" for i in range(len(self.labels))]


def generate_synthetic_training_data(n_samples: int = 1000) -> TrainingData:
    """
    生成合成训练数据

    实际应用中应使用真实的专利无效数据

    Args:
        n_samples: 样本数量

    Returns:
        TrainingData: 训练数据集
    """
    np.random.seed(42)

    features_list = []
    labels = []

    for _i in range(n_samples):
        # 生成随机特征
        patent = PatentFeatures(
            # 审查历史
            prosecution_days=np.random.randint(365, 3650),
            office_actions=np.random.randint(1, 8),
            rejections=np.random.randint(0, 5),
            claim_amendments=np.random.randint(0, 6),
            examiner_changes=np.random.randint(0, 3),

            # 权利要求
            independent_claims=np.random.randint(1, 5),
            total_claims=np.random.randint(5, 25),
            avg_claim_length=np.random.uniform(50, 400),
            qualifier_density=np.random.uniform(0.1, 0.8),

            # 引用
            forward_cites=np.random.randint(0, 50),
            backward_cites=np.random.randint(3, 30),
            np_cite_ratio=np.random.uniform(0.0, 0.5),
            self_cites=np.random.randint(0, 10),

            # 权利人
            is_npe=np.random.random() < 0.15,
            patent_portfolio_size=np.random.randint(1, 500),
            assignee_type=np.random.choice(["company", "individual", "university", "unknown"], p=[0.6, 0.2, 0.1, 0.1]),

            # 技术领域
            is_software_patent=np.random.random() < 0.3,
            is_business_method=np.random.random() < 0.15,
            tech_breadth=np.random.uniform(0.2, 1.0),
        )

        features_list.append(patent.to_feature_vector())

        # 基于论文#19的特征重要性生成标签
        # 审查历史特征最重要 (35%)
        invalidity_prob = 0.3  # 基础概率

        if patent.office_actions > 3:
            invalidity_prob += 0.15
        if patent.rejections > 1:
            invalidity_prob += 0.10
        if patent.prosecution_days > 2000:
            invalidity_prob += 0.10

        # 权利要求特征 (25%)
        if patent.independent_claims < 2:
            invalidity_prob += 0.08
        if patent.qualifier_density < 0.3:
            invalidity_prob += 0.08

        # 技术领域 (论文#20)
        if patent.is_software_patent:
            invalidity_prob += 0.10
        if patent.is_business_method:
            invalidity_prob += 0.15
        if patent.is_npe:
            invalidity_prob += 0.10

        # 添加随机性
        invalidity_prob = min(0.95, max(0.05, invalidity_prob + np.random.normal(0, 0.1)))

        # 生成标签
        label = 1 if np.random.random() < invalidity_prob else 0
        labels.append(label)

    return TrainingData(
        features=np.array(features_list),
        labels=np.array(labels),
    )


class InvalidityPredictorTrainer:
    """
    无效性预测模型训练器

    基于论文#19实现:
    - Gradient Boosting分类器
    - 特征重要性分析
    - 交叉验证评估
    """

    # 特征名称
    FEATURE_NAMES = [
        "prosecution_days", "office_actions", "rejections", "claim_amendments", "examiner_changes",
        "independent_claims", "total_claims", "avg_claim_length", "qualifier_density",
        "forward_cites", "backward_cites", "np_cite_ratio", "self_cites",
        "is_npe", "portfolio_size", "is_individual",
        "is_software", "is_business_method", "tech_breadth",
    ]

    # 特征重要性分组
    FEATURE_GROUPS = {
        "examination_history": ["prosecution_days", "office_actions", "rejections", "claim_amendments", "examiner_changes"],
        "claim_features": ["independent_claims", "total_claims", "avg_claim_length", "qualifier_density"],
        "citation_features": ["forward_cites", "backward_cites", "np_cite_ratio", "self_cites"],
        "assignee_features": ["is_npe", "portfolio_size", "is_individual"],
        "technology_features": ["is_software", "is_business_method", "tech_breadth"],
    }

    def __init__(self, model_dir: str = "models/invalidity_prediction"):
        """初始化训练器"""
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)

        self.model = None
        self.scaler = None
        self.feature_importance = None

        self.logger = logging.getLogger(self.__class__.__name__)

    def train(self, training_data: TrainingData) -> dict:
        """
        训练模型

        Args:
            training_data: 训练数据

        Returns:
            训练结果
        """
        from sklearn.ensemble import GradientBoostingClassifier
        from sklearn.model_selection import cross_val_score, train_test_split
        from sklearn.preprocessing import StandardScaler

        self.logger.info(f"🏋️ 开始训练，样本数: {len(training_data.labels)}")

        X = training_data.features
        y = training_data.labels

        # 数据标准化
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        # 划分训练集和测试集
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42
        )

        # 创建Gradient Boosting模型
        self.model = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            min_samples_split=10,
            min_samples_leaf=5,
            random_state=42,
        )

        # 训练
        self.model.fit(X_train, y_train)

        # 计算特征重要性
        self.feature_importance = dict(zip(self.FEATURE_NAMES, self.model.feature_importances_, strict=False))

        # 评估
        train_score = self.model.score(X_train, y_train)
        test_score = self.model.score(X_test, y_test)

        # 交叉验证
        cv_scores = cross_val_score(self.model, X_scaled, y, cv=5)

        # 计算AUC
        try:
            from sklearn.metrics import roc_auc_score

            y_pred_proba = self.model.predict_proba(X_test)[:, 1]
            auc_score = roc_auc_score(y_test, y_pred_proba)
        except Exception:
            auc_score = 0.0

        results = {
            "train_accuracy": train_score,
            "test_accuracy": test_score,
            "cv_mean": cv_scores.mean(),
            "cv_std": cv_scores.std(),
            "auc_score": auc_score,
            "feature_importance": self.feature_importance,
            "training_samples": len(y_train),
            "test_samples": len(y_test),
            "positive_ratio": y.mean(),
            "timestamp": datetime.now().isoformat(),
        }

        self.logger.info("✅ 训练完成:")
        self.logger.info(f"  - 训练准确率: {train_score:.4f}")
        self.logger.info(f"  - 测试准确率: {test_score:.4f}")
        self.logger.info(f"  - 交叉验证: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
        self.logger.info(f"  - AUC: {auc_score:.4f}")

        return results

    def save_model(self, filename: str = "invalidity_predictor.pkl"):
        """保存模型"""
        import pickle

        model_path = self.model_dir / filename

        model_data = {
            "model": self.model,
            "scaler": self.scaler,
            "feature_importance": self.feature_importance,
            "feature_names": self.FEATURE_NAMES,
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
        }

        with open(model_path, "wb") as f:
            pickle.dump(model_data, f)

        self.logger.info(f"💾 模型已保存: {model_path}")

    def save_feature_importance_report(self, filename: str = "feature_importance_report.json"):
        """保存特征重要性报告"""
        report_path = self.model_dir / filename

        # 计算分组重要性
        group_importance = {}
        for group_name, features in self.FEATURE_GROUPS.items():
            total = sum(self.feature_importance.get(f, 0) for f in features)
            group_importance[group_name] = total

        report = {
            "feature_importance": self.feature_importance,
            "group_importance": group_importance,
            "top_features": sorted(self.feature_importance.items(), key=lambda x: x[1], reverse=True)[:10],
            "paper_reference": {
                "paper_id": "#19",
                "title": "Predicting Patent Invalidity",
                "reported_auc": 0.80,
                "key_findings": [
                    "Examination history features are most important (35%)",
                    "Claim features contribute 25%",
                    "Citation features contribute 20%",
                    "NPE patents have 55% higher invalidity rate",
                ],
            },
        }

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        self.logger.info(f"📊 特征重要性报告已保存: {report_path}")

    def print_feature_importance(self):
        """打印特征重要性"""
        self.logger.info("\n📊 特征重要性排名:")
        self.logger.info("-" * 50)

        sorted_features = sorted(self.feature_importance.items(), key=lambda x: x[1], reverse=True)

        for i, (name, importance) in enumerate(sorted_features, 1):
            bar = "█" * int(importance * 50)
            self.logger.info(f"  {i:2d}. {name:25s} {importance:.4f} {bar}")

        self.logger.info("-" * 50)

        # 分组重要性
        self.logger.info("\n📊 分组重要性:")
        for group_name, features in self.FEATURE_GROUPS.items():
            total = sum(self.feature_importance.get(f, 0) for f in features)
            self.logger.info(f"  {group_name:25s}: {total:.2%}")


def main():
    """主函数"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger.info("=" * 60)
    logger.info("🚀 开始无效性预测模型训练")
    logger.info("=" * 60)

    # 生成合成训练数据
    logger.info("\n📊 生成训练数据...")
    training_data = generate_synthetic_training_data(n_samples=2000)
    logger.info(f"  - 样本数: {len(training_data.labels)}")
    logger.info(f"  - 正样本比例: {training_data.labels.mean():.2%}")

    # 创建训练器
    trainer = InvalidityPredictorTrainer()

    # 训练模型
    logger.info("\n🏋️ 训练模型...")
    results = trainer.train(training_data)

    # 保存模型
    trainer.save_model()

    # 保存特征重要性报告
    trainer.save_feature_importance_report()

    # 打印特征重要性
    trainer.print_feature_importance()

    # 打印最终结果
    logger.info("\n" + "=" * 60)
    logger.info("✅ 训练完成!")
    logger.info("=" * 60)
    logger.info(f"  训练准确率: {results['train_accuracy']:.4f}")
    logger.info(f"  测试准确率: {results['test_accuracy']:.4f}")
    logger.info(f"  交叉验证:   {results['cv_mean']:.4f} ± {results['cv_std']:.4f}")
    logger.info(f"  AUC:        {results['auc_score']:.4f}")
    logger.info("  论文AUC:    0.80 (参考)")
    logger.info("=" * 60)

    return results


if __name__ == "__main__":
    main()
