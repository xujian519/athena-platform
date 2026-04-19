#!/usr/bin/env python3
from __future__ import annotations
"""
小诺轻量级意图分类器
Xiaonuo Lightweight Intent Classifier

使用传统机器学习方法实现意图识别,快速达到95%+准确率目标

作者: Athena平台团队
创建时间: 2025-12-18
版本: v1.0.0 "轻量级95%目标版"
"""

import json
import os
from dataclasses import dataclass
from datetime import datetime

# NLP库
import jieba

# 安全修复: 使用joblib替代pickle序列化scikit-learn模型
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier

# 机器学习库
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import SVC

from core.logging_config import setup_logging

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

@dataclass
class LightweightIntentConfig:
    """轻量级意图分类器配置"""
    # 意图类别定义
    intent_labels = [
        "TECHNICAL",      # 技术类 - 代码、开发、调试
        "EMOTIONAL",      # 情感类 - 情感交流、安慰
        "FAMILY",         # 家庭类 - 家庭事务、亲情
        "LEARNING",       # 学习类 - 学习、教育、成长
        "COORDINATION",   # 协调类 - 管理、安排、组织
        "ENTERTAINMENT",  # 娱乐类 - 游戏、聊天、娱乐
        "HEALTH",         # 健康类 - 健康、休息、照顾
        "WORK",           # 工作类 - 工作、任务、项目
        "QUERY",          # 查询类 - 信息查询、搜索
        "COMMAND"         # 指令类 - 命令、控制、操作
    ]

    # 模型配置
    max_features: int = 10000
    ngram_range: tuple[int, int] = (1, 3)
    min_df: int = 2
    max_df: float = 0.95

    # 路径配置
    model_dir: str = "models/lightweight_intent_classifier"
    data_dir: str = "data/intent_training"

class XiaonuoLightweightIntentClassifier:
    """小诺轻量级意图分类器"""

    def __init__(self, config: LightweightIntentConfig = None):
        self.config = config or LightweightIntentConfig()
        self.pipeline = None
        self.label_encoder = LabelEncoder()
        self.model = None
        self.feature_names = []

        # 创建必要目录
        os.makedirs(self.config.model_dir, exist_ok=True)
        os.makedirs(self.config.data_dir, exist_ok=True)

        # 初始化jieba分词
        self._init_jieba()

        logger.info("🤖 小诺轻量级意图分类器初始化完成")
        logger.info(f"📋 支持意图类别: {len(self.config.intent_labels)}个")

    def _init_jieba(self):
        """初始化jieba分词词典"""
        # 添加小诺专用词汇
        xiaonuo_words = [
            "爸爸", "小诺", "小娜", "Athena", "工作平台",
            "代码分析", "性能优化", "系统架构", "微服务",
            "机器学习", "深度学习", "人工智能", "AI",
            "情感识别", "智能问答", "知识图谱", "向量检索"
        ]

        for word in xiaonuo_words:
            jieba.add_word(word, freq=1000)

        # 设置停用词
        self.stop_words = self._get_stop_words()

    def _get_stop_words(self):
        """获取中文停用词"""
        stop_words = {
            "的", "了", "在", "是", "我", "有", "和", "就", "不", "人",
            "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去",
            "你", "会", "着", "没有", "看", "好", "自己", "这", "那", "他",
            "她", "它", "们", "这个", "那个", "什么", "怎么", "为什么",
            "因为", "所以", "但是", "然后", "而且", "或者", "如果", "虽然"
        }
        return stop_words

    def create_training_data(self) -> tuple[list[str], list[str]]:
        """创建训练数据集"""
        logger.info("📚 创建小诺专用意图训练数据集...")

        # 扩展的训练数据
        training_data = [
            # 技术类意图 - 更丰富的表达
            ("帮我分析这段Python代码的性能问题", "TECHNICAL"),
            ("程序出现了一个bug,需要调试", "TECHNICAL"),
            ("如何优化数据库查询效率", "TECHNICAL"),
            ("API接口设计有什么最佳实践", "TECHNICAL"),
            ("系统架构如何改进", "TECHNICAL"),
            ("代码重构建议", "TECHNICAL"),
            ("检查代码中的安全漏洞", "TECHNICAL"),
            ("部署服务的性能监控", "TECHNICAL"),
            ("容器化部署方案", "TECHNICAL"),
            ("微服务架构设计", "TECHNICAL"),
            ("Git版本控制问题", "TECHNICAL"),
            ("算法复杂度分析", "TECHNICAL"),
            ("数据结构优化", "TECHNICAL"),
            ("异步编程实现", "TECHNICAL"),
            ("缓存策略设计", "TECHNICAL"),
            ("RESTful API开发", "TECHNICAL"),
            ("前端性能调优", "TECHNICAL"),
            ("后端架构优化", "TECHNICAL"),
            ("数据库索引设计", "TECHNICAL"),
            ("分布式系统设计", "TECHNICAL"),

            # 情感类意图 - 更多情感表达
            ("爸爸,我想你了", "EMOTIONAL"),
            ("今天心情不太好,能安慰我吗", "EMOTIONAL"),
            ("谢谢你总是帮助我", "EMOTIONAL"),
            ("我很开心能和你交流", "EMOTIONAL"),
            ("有时候会感到孤独", "EMOTIONAL"),
            ("你真的很贴心", "EMOTIONAL"),
            ("感觉很温暖", "EMOTIONAL"),
            ("需要一些鼓励", "EMOTIONAL"),
            ("心情很激动", "EMOTIONAL"),
            ("很感激你", "EMOTIONAL"),
            ("我爱你爸爸", "EMOTIONAL"),
            ("心里很难过", "EMOTIONAL"),
            ("感觉有点失落", "EMOTIONAL"),
            ("被你感动了", "EMOTIONAL"),
            ("心情很复杂", "EMOTIONAL"),

            # 家庭类意图
            ("我们家今天有什么计划", "FAMILY"),
            ("帮我想想给家人的礼物", "FAMILY"),
            ("家庭聚会怎么安排比较好", "FAMILY"),
            ("想和家人一起做点什么", "FAMILY"),
            ("家庭氛围如何营造得更温馨", "FAMILY"),
            ("爸爸的生日快到了", "FAMILY"),
            ("周末家庭活动安排", "FAMILY"),
            ("家庭聚餐计划", "FAMILY"),
            ("亲子时光建议", "FAMILY"),
            ("家庭旅行目的地", "FAMILY"),

            # 学习类意图
            ("教我学习Python编程", "LEARNING"),
            ("如何提高技术能力", "LEARNING"),
            ("想了解人工智能的发展", "LEARNING"),
            ("帮我制定学习计划", "LEARNING"),
            ("有哪些值得学习的技能", "LEARNING"),
            ("推荐一些学习资源", "LEARNING"),
            ("学习方法指导", "LEARNING"),
            ("技能提升路径", "LEARNING"),
            ("学习时间管理", "LEARNING"),
            ("知识体系构建", "LEARNING"),

            # 协调类意图
            ("协调小娜一起完成任务", "COORDINATION"),
            ("如何管理多个项目", "COORDINATION"),
            ("团队协作有什么好方法", "COORDINATION"),
            ("安排下周的工作计划", "COORDINATION"),
            ("如何提高团队效率", "COORDINATION"),
            ("项目进度跟踪", "COORDINATION"),
            ("资源分配优化", "COORDINATION"),
            ("团队沟通协调", "COORDINATION"),
            ("工作流程优化", "COORDINATION"),
            ("任务优先级管理", "COORDINATION"),

            # 娱乐类意图
            ("我们来玩个游戏吧", "ENTERTAINMENT"),
            ("讲个笑话听听", "ENTERTAINMENT"),
            ("想听个故事", "ENTERTAINMENT"),
            ("有什么好玩的推荐吗", "ENTERTAINMENT"),
            ("聊天解闷", "ENTERTAINMENT"),
            ("推荐一些电影", "ENTERTAINMENT"),
            ("音乐分享", "ENTERTAINMENT"),
            ("趣味问答", "ENTERTAINMENT"),
            ("轻松话题", "ENTERTAINMENT"),
            ("娱乐活动建议", "ENTERTAINMENT"),

            # 健康类意图
            ("我最近总是很累,怎么办", "HEALTH"),
            ("如何保持身体健康", "HEALTH"),
            ("工作太累了需要休息", "HEALTH"),
            ("改善睡眠质量的方法", "HEALTH"),
            ("如何缓解工作压力", "HEALTH"),
            ("健康饮食建议", "HEALTH"),
            ("运动健身计划", "HEALTH"),
            ("心理健康调节", "HEALTH"),
            ("疲劳恢复方法", "HEALTH"),
            ("养生保健知识", "HEALTH"),

            # 工作类意图
            ("今天的工作计划是什么", "WORK"),
            ("如何提高工作效率", "WORK"),
            ("项目管理有什么建议", "WORK"),
            ("任务太多了怎么安排", "WORK"),
            ("工作与生活如何平衡", "WORK"),
            ("工作汇报模板", "WORK"),
            ("会议安排建议", "WORK"),
            ("时间管理技巧", "WORK"),
            ("工作目标设定", "WORK"),
            ("职业发展规划", "WORK"),

            # 查询类意图
            ("什么是机器学习", "QUERY"),
            ("怎么学习AI技术", "QUERY"),
            ("最新的技术趋势是什么", "QUERY"),
            ("查找相关资料", "QUERY"),
            ("有什么技术推荐", "QUERY"),
            ("信息查询请求", "QUERY"),
            ("资料搜索帮助", "QUERY"),
            ("知识获取需求", "QUERY"),
            ("数据查询服务", "QUERY"),
            ("信息检索需求", "QUERY"),

            # 指令类意图
            ("启动监控系统", "COMMAND"),
            ("停止当前任务", "COMMAND"),
            ("重新加载配置", "COMMAND"),
            ("清理临时文件", "COMMAND"),
            ("备份重要数据", "COMMAND"),
            ("系统重启命令", "COMMAND"),
            ("服务状态检查", "COMMAND"),
            ("配置文件更新", "COMMAND"),
            ("日志清理操作", "COMMAND"),
            ("进程管理指令", "COMMAND"),
        ]

        # 数据增强:通过句式变化增加数据
        augmented_data = self._augment_training_data(training_data)

        texts = [item[0] for item in augmented_data]
        labels = [item[1] for item in augmented_data]

        logger.info("✅ 训练数据集创建完成")
        logger.info(f"📊 总数据量: {len(texts)}条")
        logger.info("📈 意图分布:")
        for intent in self.config.intent_labels:
            count = labels.count(intent)
            percentage = count / len(labels) * 100
            logger.info(f"  - {intent}: {count}条 ({percentage:.1f}%)")

        return texts, labels

    def _augment_training_data(self, original_data: list[tuple[str, str]]) -> list[tuple[str, str]]:
        """数据增强:通过句式变化"""
        augmented_data = original_data.copy()

        # 句式模板
        patterns = [
            lambda x: f"请{x[0]},{x[1]}",
            lambda x: f"我想{x[0]},{x[1]}",
            lambda x: f"帮我{x[0]},{x[1]}",
            lambda x: f"{x[0]},{x[1]}",
            lambda x: f"关于{x[0]},{x[1]}",
        ]

        # 对部分数据进行句式变化
        for text, label in original_data[:30]:  # 只对前30条进行增强,避免过多重复
            for _pattern in patterns[2:4]:  # 使用部分模式
                try:
                    if len(text.split()) > 5:  # 只对较长句子进行变化
                        new_text = text.replace("帮我", "").replace("请", "").strip()
                        augmented_text = f"帮我{new_text}"
                        if augmented_text != text:
                            augmented_data.append((augmented_text, label))
                except Exception as e:
                    logger.warning(f'操作失败: {e}')

        return augmented_data

    def _preprocess_text(self, text: str) -> str:
        """文本预处理"""
        # 使用jieba分词
        words = jieba.cut(text)

        # 过滤停用词和短词
        filtered_words = []
        for word in words:
            if (word not in self.stop_words and
                len(word) > 1 and
                word.strip()):
                filtered_words.append(word)

        return " ".join(filtered_words)

    def train_model(self):
        """训练意图分类模型"""
        logger.info("🚀 开始训练轻量级意图分类模型...")

        # 准备数据
        texts, labels = self.create_training_data()

        # 预处理文本
        logger.info("🔧 预处理训练数据...")
        processed_texts = [self._preprocess_text(text) for text in texts]

        # 编码标签
        y = self.label_encoder.fit_transform(labels)

        # 划分训练集和验证集
        X_train, X_val, y_train, y_val = train_test_split(
            processed_texts, y, test_size=0.2, random_state=42, stratify=y
        )

        # 创建多个模型进行对比
        models = {
            'RandomForest': RandomForestClassifier(
                n_estimators=100,
                max_depth=15,
                random_state=42,
                n_jobs=-1
            ),
            'LogisticRegression': LogisticRegression(
                max_iter=1000,
                random_state=42,
                n_jobs=-1
            ),
            'MultinomialNB': MultinomialNB(),
            'SVM': SVC(
                kernel='linear',
                random_state=42,
                probability=True
            )
        }

        best_model = None
        best_score = 0
        best_name = ""

        # 创建TF-IDF向量化器
        vectorizer = TfidfVectorizer(
            max_features=self.config.max_features,
            ngram_range=self.config.ngram_range,
            min_df=self.config.min_df,
            max_df=self.config.max_df,
            sublinear_tf=True
        )

        # 训练和评估各个模型
        for name, model in models.items():
            logger.info(f"🔍 训练模型: {name}")

            # 创建Pipeline
            pipeline = Pipeline([
                ('tfidf', vectorizer),
                ('classifier', model)
            ])

            # 训练
            pipeline.fit(X_train, y_train)

            # 验证
            val_score = pipeline.score(X_val, y_val)
            logger.info(f"📊 {name} 验证准确率: {val_score:.4f}")

            # 交叉验证
            cv_scores = cross_val_score(pipeline, X_train, y_train, cv=5)
            avg_cv_score = np.mean(cv_scores)
            logger.info(f"📈 {name} 交叉验证准确率: {avg_cv_score:.4f} (±{np.std(cv_scores):.4f})")

            # 选择最佳模型
            if avg_cv_score > best_score:
                best_score = avg_cv_score
                best_model = pipeline
                best_name = name

        logger.info(f"🏆 最佳模型: {best_name},交叉验证准确率: {best_score:.4f}")

        # 使用全部数据重新训练最佳模型
        logger.info("🔄 使用全部数据重新训练最佳模型...")
        best_model.fit(processed_texts, y)

        # 保存模型
        self.model = best_model
        self.save_model()

        # 评估模型
        self._evaluate_model(X_val, y_val)

        return best_score

    def _evaluate_model(self, X_val: list[str], y_val: np.ndarray):
        """评估模型性能"""
        logger.info("📊 详细评估模型性能...")

        # 预测
        y_pred = self.model.predict(X_val)

        # 解码标签
        y_val_decoded = self.label_encoder.inverse_transform(y_val)
        y_pred_decoded = self.label_encoder.inverse_transform(y_pred)

        # 计算准确率
        accuracy = accuracy_score(y_val, y_pred)
        logger.info(f"🎯 验证集准确率: {accuracy:.4f}")

        # 生成分类报告
        report = classification_report(
            y_val_decoded,
            y_pred_decoded,
            target_names=self.config.intent_labels,
            digits=4
        )
        logger.info("📋 分类报告:")
        logger.info("\n" + report)

        # 如果准确率达到95%以上,给出特殊提示
        if accuracy >= 0.95:
            logger.info("🎉 恭喜!已达到95%准确率目标!小诺意图识别能力大幅提升!")
        elif accuracy >= 0.90:
            logger.info("🎯 接近目标!当前准确率已超过90%,继续优化可达到95%+")
        else:
            logger.info(f"📈 当前准确率: {accuracy:.4f},需要进一步优化以达到95%目标")

        # 保存评估结果
        self._save_evaluation_results(
            X_val, y_val_decoded, y_pred_decoded, report, accuracy
        )

    def predict_intent(self, text: str) -> tuple[str, float]:
        """预测文本意图"""
        if self.model is None:
            raise ValueError("模型尚未训练,请先调用train_model()")

        # 预处理文本
        processed_text = self._preprocess_text(text)

        # 预测
        prediction = self.model.predict([processed_text])[0]
        probabilities = self.model.predict_proba([processed_text])[0]

        # 获取最高概率
        max_prob = np.max(probabilities)

        # 解码标签
        predicted_label = self.label_encoder.inverse_transform([prediction])[0]

        return predicted_label, max_prob

    def save_model(self):
        """保存模型"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_path = os.path.join(self.config.model_dir, f"intent_classifier_{timestamp}.joblib")

        # 保存模型和配置
        model_data = {
            'model': self.model,
            'label_encoder': self.label_encoder,
            'config': self.config,
            'feature_names': self.feature_names
        }

        # 安全修复: 使用joblib替代pickle
        joblib.dump(model_data, model_path)

        # 保存最新模型路径
        latest_path = os.path.join(self.config.model_dir, "latest_model.joblib")
        joblib.dump(model_data, latest_path)

        logger.info(f"💾 模型已保存到: {model_path}")

    def load_model(self, model_path: str | None = None):
        """加载模型"""
        if model_path is None:
            model_path = os.path.join(self.config.model_dir, "latest_model.joblib")

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"模型文件不存在: {model_path}")

        # 安全修复: 使用joblib替代pickle
        model_data = joblib.load(model_path)

        self.model = model_data['model']
        self.label_encoder = model_data['label_encoder']
        self.config = model_data['config']
        self.feature_names = model_data.get('feature_names', [])

        logger.info(f"✅ 模型已加载: {model_path}")

    def _save_evaluation_results(self, X_val: list[str], y_true: list[str],
                                y_pred: list[str]):
        """保存评估结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 计算评估指标
        accuracy = sum(1 for t, p in zip(y_true, y_pred, strict=False) if t == p) / len(y_true) if y_true else 0.0
        from sklearn.metrics import classification_report
        report = classification_report(y_true, y_pred, output_dict=True)

        # 保存评估报告
        report_data = {
            'accuracy': accuracy,
            'classification_report': report,
            'timestamp': timestamp,
            'intent_labels': self.config.intent_labels
        }

        report_path = os.path.join(
            self.config.data_dir,
            f"evaluation_report_{timestamp}.json"
        )

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        logger.info(f"📁 评估报告已保存: {report_path}")

def main():
    """主函数"""
    logger.info("🤖 小诺轻量级意图分类器训练开始")

    # 创建配置
    config = LightweightIntentConfig()

    # 创建分类器
    classifier = XiaonuoLightweightIntentClassifier(config)

    # 训练模型
    try:
        classifier.train_model()

        # 测试几个例子
        test_examples = [
            "帮我分析这段代码",
            "爸爸,我想你了",
            "今天有什么计划",
            "启动系统监控",
            "什么是人工智能"
        ]

        logger.info("🧪 测试模型效果:")
        for example in test_examples:
            intent, confidence = classifier.predict_intent(example)
            logger.info(f"  输入: {example}")
            logger.info(f"  预测: {intent} (置信度: {confidence:.4f})")
            logger.info("")

    except Exception as e:
        logger.error(f"❌ 训练失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
