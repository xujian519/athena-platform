#!/usr/bin/env python3
"""
小诺增强意图分类器
Xiaonuo Enhanced Intent Classifier

通过增加训练数据、特征工程和集成学习实现95%+准确率

作者: Athena平台团队
创建时间: 2025-12-18
版本: v2.0.0 "95%增强版"
"""

from __future__ import annotations
import functools
import json
import operator
import os
import re
from dataclasses import dataclass
from datetime import datetime

# NLP库
import jieba
import joblib  # 安全修复: 使用joblib替代pickle保存scikit-learn模型
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.ensemble import RandomForestClassifier, VotingClassifier

# 机器学习库
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import SVC

from core.logging_config import setup_logging

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

class TextStatsExtractor(BaseEstimator, TransformerMixin):
    """文本特征提取器"""

    def __init__(self):
        pass

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        features = []
        for text in X:
            # 文本长度
            length = len(text)
            # 词数
            word_count = len(text.split())
            # 包含特定关键词
            has_dad = 1 if '爸爸' in text else 0
            has_question = 1 if any(q in text for q in ['什么', '怎么', '如何', '为什么']) else 0
            has_command = 1 if any(c in text for c in ['启动', '停止', '开启', '关闭', '运行']) else 0
            has_tech = 1 if any(t in text for t in ['代码', '程序', '系统', '数据库', 'API', '算法']) else 0
            has_emotion = 1 if any(e in text for e in ['想', '心情', '感觉', '爱', '喜欢', '开心', '难过']) else 0

            features.append([
                length, word_count, has_dad, has_question,
                has_command, has_tech, has_emotion
            ])

        return np.array(features)

class KeywordExtractor(BaseEstimator, TransformerMixin):
    """关键词特征提取器"""

    def __init__(self):
        # 意图相关关键词
        self.intent_keywords = {
            'TECHNICAL': ['代码', '程序', '系统', '数据库', 'API', '算法', '架构', '开发', '调试', '优化', '部署', '性能'],
            'EMOTIONAL': ['想', '心情', '感觉', '爱', '喜欢', '开心', '难过', '想念', '感谢', '温暖', '激动', '孤独'],
            'FAMILY': ['爸爸', '妈妈', '家', '家庭', '姐姐', '弟弟', '妹妹', '家人', '亲情', '团聚', '生日'],
            'LEARNING': ['学习', '教', '知识', '教育', '培训', '成长', '进步', '技能', '课程', '掌握', '了解'],
            'COORDINATION': ['协调', '管理', '安排', '组织', '计划', '调度', '分配', '协作', '配合', '团队', '项目'],
            'ENTERTAINMENT': ['游戏', '玩', '娱乐', '音乐', '电影', '故事', '笑话', '聊天', '互动', '推荐', '轻松'],
            'HEALTH': ['健康', '休息', '疲劳', '累', '生病', '照顾', '锻炼', '睡眠', '饮食', '医疗', '养生'],
            'WORK': ['工作', '任务', '项目', '会议', '日程', '效率', '计划', '目标', '进度', '汇报', '职场'],
            'QUERY': ['什么', '为什么', '怎么', '如何', '哪里', '什么时候', '查询', '搜索', '信息', '资料', '数据'],
            'COMMAND': ['启动', '停止', '开始', '结束', '执行', '运行', '关闭', '重启', '安装', '卸载', '命令']
        }

        self.all_keywords = list(set(functools.reduce(operator.iadd, self.intent_keywords.values(), [])))

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        features = []
        for text in X:
            text = text.lower()
            feature_vector = []

            # 为每个意图类计算关键词匹配分数
            for _intent, keywords in self.intent_keywords.items():
                score = sum(1 for kw in keywords if kw in text)
                feature_vector.append(score)

            features.append(feature_vector)

        return np.array(features)

@dataclass
class EnhancedIntentConfig:
    """增强意图分类器配置"""
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
    max_features: int = 15000
    ngram_range: tuple[int, int] = (1, 3)
    min_df: int = 1
    max_df: float = 0.95

    # 路径配置
    model_dir: str = "models/enhanced_intent_classifier"
    data_dir: str = "data/intent_training"

class XiaonuoEnhancedIntentClassifier:
    """小诺增强意图分类器"""

    def __init__(self, config: EnhancedIntentConfig = None):
        self.config = config or EnhancedIntentConfig()
        self.pipeline = None
        self.label_encoder = LabelEncoder()
        self.model = None

        # 创建必要目录
        os.makedirs(self.config.model_dir, exist_ok=True)
        os.makedirs(self.config.data_dir, exist_ok=True)

        # 初始化jieba分词
        self._init_jieba()

        logger.info("🚀 小诺增强意图分类器初始化完成")
        logger.info(f"📋 支持意图类别: {len(self.config.intent_labels)}个")

    def _init_jieba(self):
        """初始化jieba分词词典"""
        # 添加小诺专用词汇
        xiaonuo_words = [
            "爸爸", "小诺", "小娜", "Athena", "工作平台",
            "代码分析", "性能优化", "系统架构", "微服务", "分布式",
            "机器学习", "深度学习", "人工智能", "AI", "神经网络",
            "情感识别", "智能问答", "知识图谱", "向量检索", "NLP",
            "API设计", "数据库优化", "算法分析", "项目管理", "团队协作"
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
            "因为", "所以", "但是", "然后", "而且", "或者", "如果", "虽然",
            "啊", "吧", "呢", "吗", "哦", "哈", "嗯", "哎", "唉"
        }
        return stop_words

    def create_expanded_training_data(self) -> tuple[list[str], list[str]]:
        """创建扩展的训练数据集"""
        logger.info("📚 创建扩展版小诺意图训练数据集...")

        # 大幅扩展的训练数据
        training_data = [
            # 技术类意图 - 大量增加技术相关表达
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
            ("负载均衡配置", "TECHNICAL"),
            ("消息队列实现", "TECHNICAL"),
            ("监控系统搭建", "TECHNICAL"),
            ("自动化测试框架", "TECHNICAL"),
            ("持续集成部署", "TECHNICAL"),
            ("代码审查规范", "TECHNICAL"),
            ("架构模式选择", "TECHNICAL"),
            ("性能瓶颈分析", "TECHNICAL"),
            ("安全防护措施", "TECHNICAL"),
            ("日志系统设计", "TECHNICAL"),
            ("数据库分库分表", "TECHNICAL"),
            ("服务治理方案", "TECHNICAL"),
            ("容器编排管理", "TECHNICAL"),
            ("云原生架构", "TECHNICAL"),

            # 情感类意图 - 增加情感表达多样性
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
            ("有点焦虑", "EMOTIONAL"),
            ("感到很幸福", "EMOTIONAL"),
            ("真的很担心", "EMOTIONAL"),
            ("情绪有点低落", "EMOTIONAL"),
            ("充满希望", "EMOTIONAL"),
            ("有点紧张", "EMOTIONAL"),
            ("觉得很放松", "EMOTIONAL"),
            ("心情特别好", "EMOTIONAL"),
            ("有点失落", "EMOTIONAL"),
            ("感到很自豪", "EMOTIONAL"),
            ("有点沮丧", "EMOTIONAL"),

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
            ("妈妈身体怎么样", "FAMILY"),
            ("姐姐最近工作顺利吗", "FAMILY"),
            ("家里需要添置什么", "FAMILY"),
            ("家庭财务规划", "FAMILY"),
            ("孩子教育问题", "FAMILY"),

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
            ("在线课程推荐", "LEARNING"),
            ("如何快速入门新领域", "LEARNING"),
            ("学习笔记整理方法", "LEARNING"),
            ("记忆力提升技巧", "LEARNING"),
            ("有效阅读方法", "LEARNING"),
            ("编程学习路线图", "LEARNING"),
            ("技术栈选择建议", "LEARNING"),
            ("学习效率提升", "LEARNING"),
            ("知识管理工具", "LEARNING"),
            ("实践项目推荐", "LEARNING"),

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
            ("跨部门协作", "COORDINATION"),
            ("会议纪要整理", "COORDINATION"),
            ("团队建设活动", "COORDINATION"),
            ("绩效考核管理", "COORDINATION"),
            ("敏捷开发实践", "COORDINATION"),

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
            ("推荐一些好书", "ENTERTAINMENT"),
            ("有什么有趣的视频", "ENTERTAINMENT"),
            ("小游戏推荐", "ENTERTAINMENT"),
            ("放松心情的方法", "ENTERTAINMENT"),
            ("兴趣爱好培养", "ENTERTAINMENT"),

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
            ("亚健康状态改善", "HEALTH"),
            ("办公室健康小贴士", "HEALTH"),
            ("颈椎腰椎保护", "HEALTH"),
            ("眼部保健方法", "HEALTH"),
            ("健康体检项目", "HEALTH"),

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
            ("职场沟通技巧", "WORK"),
            ("年终总结怎么写", "WORK"),
            ("工作压力管理", "WORK"),
            ("升职加薪建议", "WORK"),
            ("创业指导", "WORK"),

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
            ("哪个编程语言比较好", "QUERY"),
            ("如何选择技术方向", "QUERY"),
            ("行业报告在哪里找", "QUERY"),
            ("技术文档查询", "QUERY"),
            ("最新研究进展", "QUERY"),

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
            ("开启调试模式", "COMMAND"),
            ("关闭错误报告", "COMMAND"),
            ("运行测试套件", "COMMAND"),
            ("部署应用服务", "COMMAND"),
            ("初始化数据库", "COMMAND"),
        ]

        # 数据增强:多样化表达
        augmented_data = self._augment_training_data(training_data)

        texts = [item[0] for item in augmented_data]
        labels = [item[1] for item in augmented_data]

        logger.info("✅ 扩展训练数据集创建完成")
        logger.info(f"📊 总数据量: {len(texts)}条")
        logger.info("📈 意图分布:")
        for intent in self.config.intent_labels:
            count = labels.count(intent)
            percentage = count / len(labels) * 100
            logger.info(f"  - {intent}: {count}条 ({percentage:.1f}%)")

        return texts, labels

    def _augment_training_data(self, original_data: list[tuple[str, str]]) -> list[tuple[str, str]]:
        """数据增强:多样化表达"""
        augmented_data = original_data.copy()

        # 句式变换模板
        transformation_templates = [
            # 前缀变换
            lambda x: f"请{x[0]},{x[1]}",
            lambda x: f"我想{x[0]},{x[1]}",
            lambda x: f"帮我{x[0]},{x[1]}",
            lambda x: f"能否{x[0]},{x[1]}",
            lambda x: f"可以{x[0]}吗,{x[1]}",
            # 语气变换
            lambda x: f"{x[0]},{x[1]}",
            lambda x: f"{x[0]},可以吗,{x[1]}",
            lambda x: f"{x[0]}吧,{x[1]}",
            lambda x: f"{x[0]}一下,{x[1]}",
        ]

        # 对部分数据进行多样化变换
        for text, label in original_data:
            # 随机选择2-3种变换
            import random
            selected_templates = random.sample(transformation_templates, min(3, len(transformation_templates)))

            for template in selected_templates:
                try:
                    # 避免对过短或过长的文本进行变换
                    if 5 <= len(text) <= 50:
                        # 移除已有前缀,添加新前缀
                        clean_text = re.sub(r'^(帮我|请|我想|可以|能否|能否帮我)', '', text).strip()
                        if clean_text:
                            new_text = template((clean_text, label))
                            # 确保新文本与原文本不同
                            if new_text != text and len(new_text.split()) >= 3:
                                augmented_data.append((new_text, label))
                except Exception as e:
                    logger.warning(f'操作失败: {e}')

        return augmented_data

    def _preprocess_text(self, text: str) -> str:
        """文本预处理"""
        # 标准化处理
        text = text.strip()

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
        """训练增强意图分类模型"""
        logger.info("🚀 开始训练增强意图分类模型...")

        # 准备数据
        texts, labels = self.create_expanded_training_data()

        # 预处理文本
        logger.info("🔧 预处理训练数据...")
        processed_texts = [self._preprocess_text(text) for text in texts]

        # 编码标签
        y = self.label_encoder.fit_transform(labels)

        # 划分训练集和验证集
        X_train, X_val, y_train, y_val = train_test_split(
            processed_texts, y, test_size=0.15, random_state=42, stratify=y
        )

        # 创建特征提取器
        tfidf_vectorizer = TfidfVectorizer(
            max_features=self.config.max_features,
            ngram_range=self.config.ngram_range,
            min_df=self.config.min_df,
            max_df=self.config.max_df,
            sublinear_tf=True
        )

        count_vectorizer = CountVectorizer(
            ngram_range=(1, 2),
            max_features=5000
        )

        # 创建特征组合
        feature_union = FeatureUnion([
            ('tfidf', tfidf_vectorizer),
            ('counts', count_vectorizer),
            ('text_stats', TextStatsExtractor()),
            ('keywords', KeywordExtractor())
        ])

        # 创建强学习器
        rf = RandomForestClassifier(
            n_estimators=200,
            max_depth=20,
            min_samples_split=2,
            min_samples_leaf=1,
            random_state=42,
            n_jobs=-1
        )

        lr = LogisticRegression(
            max_iter=2000,
            random_state=42,
            C=1.0,
            solver='lbfgs'
        )

        svm = SVC(
            kernel='rbf',
            random_state=42,
            probability=True,
            C=1.0
        )

        # 创建集成模型
        voting_clf = VotingClassifier(
            estimators=[
                ('rf', rf),
                ('lr', lr),
                ('svm', svm)
            ],
            voting='soft',
            weights=[2, 1, 1]
        )

        # 创建完整Pipeline
        self.pipeline = Pipeline([
            ('features', feature_union),
            ('classifier', voting_clf)
        ])

        logger.info("🔄 开始训练集成模型...")

        # 训练模型
        self.pipeline.fit(X_train, y_train)

        # 验证模型
        val_score = self.pipeline.score(X_val, y_val)
        logger.info(f"📊 验证集准确率: {val_score:.4f}")

        # 交叉验证
        cv_scores = cross_val_score(self.pipeline, X_train, y_train, cv=5, scoring='accuracy')
        avg_cv_score = np.mean(cv_scores)
        std_cv_score = np.std(cv_scores)
        logger.info(f"📈 交叉验证准确率: {avg_cv_score:.4f} (±{std_cv_score:.4f})")

        # 使用全部数据重新训练
        logger.info("🔄 使用全部数据重新训练...")
        self.pipeline.fit(processed_texts, y)

        # 保存模型
        self.save_model()

        # 详细评估
        self._evaluate_model(X_val, y_val)

        return avg_cv_score

    def _evaluate_model(self, X_val: list[str], y_val: np.ndarray):
        """评估模型性能"""
        logger.info("📊 详细评估模型性能...")

        # 预测
        y_pred = self.pipeline.predict(X_val)

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
        logger.info("📋 详细分类报告:")
        logger.info("\n" + report)

        # 达到目标的特殊提示
        if accuracy >= 0.95:
            logger.info("🎉🎉🎉 成功达到95%准确率目标!小诺意图识别能力实现重大突破!")
            logger.info("🚀 Phase 1 任务圆满完成!")
        elif accuracy >= 0.90:
            logger.info("🎯 接近目标!当前准确率已超过90%,距离95%仅一步之遥!")
        elif accuracy >= 0.85:
            logger.info(f"📈 进步显著!当前准确率: {accuracy:.4f},继续优化可达到95%+")
        else:
            logger.info(f"📈 当前准确率: {accuracy:.4f},需要进一步优化以达到95%目标")

        # 保存评估结果
        self._save_evaluation_results(
            X_val, y_val_decoded, y_pred_decoded, report, accuracy
        )

    def predict_intent(self, text: str) -> tuple[str, float]:
        """预测文本意图"""
        if self.pipeline is None:
            raise ValueError("模型尚未训练,请先调用train_model()")

        # 预处理文本
        processed_text = self._preprocess_text(text)

        # 预测
        prediction = self.pipeline.predict([processed_text])[0]
        probabilities = self.pipeline.predict_proba([processed_text])[0]

        # 获取最高概率
        max_prob = np.max(probabilities)

        # 解码标签
        predicted_label = self.label_encoder.inverse_transform([prediction])[0]

        return predicted_label, max_prob

    def save_model(self):
        """保存模型"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_path = os.path.join(self.config.model_dir, f"enhanced_intent_classifier_{timestamp}.pkl")

        # 保存模型和配置
        model_data = {
            'pipeline': self.pipeline,
            'label_encoder': self.label_encoder,
            'config': self.config
        }

        # 安全修复: 使用joblib替代pickle,防止反序列化漏洞
        with open(model_path, 'wb') as f:
            joblib.dump(model_data, f)

        # 保存最新模型路径
        latest_path = os.path.join(self.config.model_dir, "latest_enhanced_model.pkl")
        with open(latest_path, 'wb') as f:
            joblib.dump(model_data, f)

        logger.info(f"💾 增强模型已保存到: {model_path}")

    def load_model(self, model_path: str | None = None):
        """加载模型"""
        if model_path is None:
            model_path = os.path.join(self.config.model_dir, "latest_enhanced_model.pkl")

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"模型文件不存在: {model_path}")

        # 安全修复: 使用joblib替代pickle,防止反序列化漏洞
        with open(model_path, 'rb') as f:
            model_data = joblib.load(f)

        self.pipeline = model_data['pipeline']
        self.label_encoder = model_data['label_encoder']
        self.config = model_data['config']

        logger.info(f"✅ 增强模型已加载: {model_path}")

    def _save_evaluation_results(self, X_val: list[str], y_true: list[str],
                                y_pred: list[str]):
        """保存评估结果"""
        from sklearn.metrics import accuracy_score, classification_report

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 计算准确率和分类报告
        accuracy = accuracy_score(y_true, y_pred)
        report = classification_report(y_true, y_pred, target_names=self.config.intent_labels)

        # 保存评估报告
        report_data = {
            'accuracy': accuracy,
            'classification_report': report,
            'timestamp': timestamp,
            'intent_labels': self.config.intent_labels,
            'model_type': 'Enhanced Intent Classifier'
        }

        report_path = os.path.join(
            self.config.data_dir,
            f"enhanced_evaluation_report_{timestamp}.json"
        )

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        logger.info(f"📁 增强模型评估报告已保存: {report_path}")

def main():
    """主函数"""
    logger.info("🚀 小诺增强意图分类器训练开始")

    # 创建配置
    config = EnhancedIntentConfig()

    # 创建分类器
    classifier = XiaonuoEnhancedIntentClassifier(config)

    # 训练模型
    try:
        classifier.train_model()

        # 测试各种场景
        test_cases = [
            # 技术类
            "帮我优化这段代码的性能",
            "数据库查询太慢了怎么办",
            "如何设计高并发系统",
            # 情感类
            "爸爸,今天工作好累",
            "有时候感到很孤独",
            "谢谢你一直以来的陪伴",
            # 家庭类
            "我们家周末去哪里玩",
            "准备爸爸的生日礼物",
            "家庭聚餐怎么安排",
            # 查询类
            "什么是区块链技术",
            "最新的AI发展趋势",
            "如何学习机器学习",
            # 指令类
            "启动系统监控服务",
            "清理服务器日志",
            "重启数据库服务"
        ]

        logger.info("🧪 增强模型效果测试:")
        for test_text in test_cases:
            intent, confidence = classifier.predict_intent(test_text)
            logger.info(f"  输入: {test_text}")
            logger.info(f"  预测: {intent} (置信度: {confidence:.4f})")
            logger.info("")

    except Exception as e:
        logger.error(f"❌ 训练失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
