#!/usr/bin/env python3
"""
⚠️  DEPRECATED - NebulaGraph版本已废弃
DEPRECATED - NebulaGraph version deprecated

废弃日期: 2026-01-26
废弃原因: TD-001 - 系统已迁移到Neo4j
影响范围: 整个文件
建议操作: 使用 core/nlp/neo4j_graph_enhanced_intent.py

原功能说明:
NebulaGraph增强的意图识别器
99%准确率目标
结合知识图谱的高精度意图识别系统
"""

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

# 安全修复: 使用joblib替代pickle序列化scikit-learn模型
import joblib
import torch
from nebula3.common import *
from nebula3.Config import Config
from nebula3.gclient.net import ConnectionPool
from sklearn.decomposition import TruncatedSVD
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier, VotingClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from transformers import AutoModel, AutoTokenizer

from core.config.secure_config import get_config
from core.logging_config import setup_logging

config = get_config()


if TYPE_CHECKING:
    from nebula3.data.ResultSet import ResultSet

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


@dataclass
class IntentClassificationResult:
    """意图分类结果"""

    intent: str
    confidence: float
    graph_evidence: list[dict]
    reasoning_path: list[str]
    features_used: dict[str, float]
    model_predictions: dict[str, float]


class NebulaGraphConnection:
    """NebulaGraph连接管理器"""

    def __init__(self):
        self.configs = Config()
        self.configs.max_connection_pool_size = 10
        self.connection_pool = ConnectionPool()

        # NebulaGraph连接参数
        self.hosts = ["127.0.0.1:9669"]
        self.username = "root"
        self.password = config.get("NEBULA_PASSWORD", required=True)
        self.space_name = "patent_kg"

        # 验证space名称(防止nGQL注入)
        import re

        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", self.space_name):
            raise ValueError(f"Invalid space name: {self.space_name}")

        # 缓存连接
        self.session = None

    async def connect(self) -> bool:
        """连接到NebulaGraph"""
        try:
            if self.connection_pool.connect([(self.hosts[0], self.configs)]):
                logger.info("✅ 成功连接到NebulaGraph")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ NebulaGraph连接失败: {e}")
            return False

    async def execute_query(self, query: str) -> ResultSet:
        """执行查询"""
        try:
            if not self.session:
                self.session = self.connection_pool.get_session(self.username, self.password)

            # 使用图空间
            await self.session.execute(f"USE {self.space_name}")

            # 执行查询
            result = await self.session.execute(query)
            return result
        except Exception as e:
            logger.error(f"❌ 查询执行失败: {e}")
            return None

    async def search_entities(self, keywords: list[str], limit: int = 10) -> list[dict]:
        """搜索实体

        ⚠️ 安全说明:keyword参数经过转义处理,防止nGQL注入
        """
        entities = []

        for keyword in keywords:
            # 转义keyword,防止nGQL注入
            escaped_keyword = keyword.replace("\\", "\\\\").replace('"', '\\"')

            query = f"""
            MATCH (v:patent_entity)
            WHERE v.name CONTAINS \"{escaped_keyword}\"
               OR v.description CONTAINS \"{escaped_keyword}\"
            RETURN v.name AS name, v.type AS type, v.description AS description
            LIMIT {limit}
            """

            result = await self.execute_query(query)
            if result:
                for record in result:
                    entities.append(
                        {
                            "name": record.values[0].as_string(),
                            "type": record.values[1].as_string(),
                            "description": record.values[2].as_string(),
                        }
                    )

        return entities

    async def find_entity_relations(self, entity_name: str, depth: int = 2) -> list[dict]:
        """查找实体关系

        ⚠️ 安全说明:entity_name参数经过转义处理,防止nGQL注入
        """
        # 转义entity_name,防止nGQL注入
        escaped_entity_name = entity_name.replace("\\", "\\\\").replace('"', '\\"')

        query = f"""
        GO {depth} STEPS FROM \"{escaped_entity_name}\"
        OVER patent_relation
        YIELD dst(edge) AS related, properties($$).relation_type AS relation_type
        """

        result = await self.execute_query(query)
        relations = []

        if result:
            for record in result:
                relations.append(
                    {
                        "related_entity": record.values[0].as_string(),
                        "relation_type": record.values[1].as_string(),
                        "path_depth": depth,
                    }
                )

        return relations


class NebulaEnhancedIntentClassifier:
    """NebulaGraph增强的意图识别器"""

    def __init__(self):
        self.name = "NebulaGraph增强意图识别器"
        self.version = "v2.0 - 99%准确率目标"

        # 模型组件
        self.tfidf_vectorizer = None
        self.svd = None
        self.label_encoder = None
        self.ensemble_classifier = None

        # BERT模型
        self.bert_tokenizer = None
        self.bert_model = None
        self.device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

        # NebulaGraph连接
        self.graph_connection = NebulaGraphConnection()

        # 意图类别定义
        self.intent_classes = [
            "PATENT_ANALYSIS",  # 专利分析
            "LEGAL_QUERY",  # 法律查询
            "TECHNICAL_EXPLANATION",  # 技术解释
            "EMOTIONAL",  # 情感表达
            "FAMILY_CHAT",  # 家庭聊天
            "WORK_COORDINATION",  # 工作协调
            "LEARNING_REQUEST",  # 学习请求
            "SYSTEM_CONTROL",  # 系统控制
            "ENTERTAINMENT",  # 娱乐请求
            "HEALTH_CHECK",  # 健康检查
        ]

        # 图谱增强权重
        self.graph_enhancement_weights = {
            "PATENT_ANALYSIS": 0.4,
            "LEGAL_QUERY": 0.4,
            "TECHNICAL_EXPLANATION": 0.3,
            "EMOTIONAL": 0.1,
            "FAMILY_CHAT": 0.1,
            "WORK_COORDINATION": 0.2,
            "LEARNING_REQUEST": 0.3,
            "SYSTEM_CONTROL": 0.2,
            "ENTERTAINMENT": 0.1,
            "HEALTH_CHECK": 0.1,
        }

        # 模型已加载标志
        self.model_loaded = False

    async def initialize(self) -> bool:
        """初始化模型"""
        try:
            logger.info("🚀 初始化NebulaGraph增强意图识别器...")

            # 连接NebulaGraph
            graph_connected = await self.graph_connection.connect()
            if not graph_connected:
                logger.warning("⚠️ NebulaGraph连接失败,将使用降级模式")

            # 加载或训练模型
            model_path = Path("/Users/xujian/Athena工作平台/models/enhanced_intent_classifier")
            if model_path.exists():
                await self.load_model(model_path)
            else:
                await self.train_model()

            self.model_loaded = True
            logger.info("✅ 意图识别器初始化完成")
            return True

        except Exception as e:
            logger.error(f"❌ 初始化失败: {e}")
            return False

    async def train_model(self):
        """训练意图识别模型"""
        logger.info("📚 开始训练意图识别模型...")

        # 准备训练数据
        training_data = await self.prepare_training_data()

        if not training_data:
            logger.error("❌ 训练数据不足")
            return

        texts = [item["text"] for item in training_data]
        labels = [item["intent"] for item in training_data]

        # 1. TF-IDF特征提取
        logger.info("🔤 提取TF-IDF特征...")
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=10000, ngram_range=(1, 3), stop_words=None
        )
        tfidf_features = self.tfidf_vectorizer.fit_transform(texts)

        # 2. SVD降维
        logger.info("📉 应用SVD降维...")
        self.svd = TruncatedSVD(n_components=300, random_state=42)
        reduced_features = self.svd.fit_transform(tfidf_features)

        # 3. 编码标签
        self.label_encoder = LabelEncoder()
        encoded_labels = self.label_encoder.fit_transform(labels)

        # 4. 训练集成分类器
        logger.info("🤖 训练集成分类器...")

        # 基础分类器
        rf_classifier = RandomForestClassifier(
            n_estimators=200, max_depth=20, random_state=42, n_jobs=-1
        )

        gb_classifier = GradientBoostingClassifier(
            n_estimators=200, learning_rate=0.1, max_depth=6, random_state=42
        )

        # 创建投票分类器
        self.ensemble_classifier = VotingClassifier(
            estimators=[("rf", rf_classifier), ("gb", gb_classifier)], voting="soft"
        )

        # 训练模型
        self.ensemble_classifier.fit(reduced_features, encoded_labels)

        # 5. 加载BERT模型用于语义增强
        try:
            logger.info("🧠 加载BERT模型...")
            model_name = "BAAI/bge-m3"
            self.bert_tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.bert_model = AutoModel.from_pretrained(model_name)
            self.bert_model.to(self.device)
            self.bert_model.eval()
        except Exception as e:
            logger.warning(f"⚠️ BERT模型加载失败: {e}")

        # 6. 保存模型
        await self.save_model()

        logger.info("✅ 模型训练完成")

    async def prepare_training_data(self) -> list[dict]:
        """准备训练数据"""
        # 核心训练数据集
        training_samples = [
            # PATENT_ANALYSIS
            {"text": "分析这个专利的技术创新点", "intent": "PATENT_ANALYSIS"},
            {"text": "帮我查询专利的法律状态", "intent": "PATENT_ANALYSIS"},
            {"text": "这个专利的IPC分类是什么", "intent": "PATENT_ANALYSIS"},
            {"text": "检索相似的专利技术", "intent": "PATENT_ANALYSIS"},
            {"text": "专利侵权风险评估", "intent": "PATENT_ANALYSIS"},
            # LEGAL_QUERY
            {"text": "这个法律条款怎么解释", "intent": "LEGAL_QUERY"},
            {"text": "相关案例判决结果", "intent": "LEGAL_QUERY"},
            {"text": "合同条款审查", "intent": "LEGAL_QUERY"},
            {"text": "知识产权保护策略", "intent": "LEGAL_QUERY"},
            {"text": "诉讼时效是多久", "intent": "LEGAL_QUERY"},
            # TECHNICAL_EXPLANATION
            {"text": "解释一下这个算法原理", "intent": "TECHNICAL_EXPLANATION"},
            {"text": "技术实现方案设计", "intent": "TECHNICAL_EXPLANATION"},
            {"text": "系统架构优化建议", "intent": "TECHNICAL_EXPLANATION"},
            {"text": "代码性能分析", "intent": "TECHNICAL_EXPLANATION"},
            {"text": "数据库设计原理", "intent": "TECHNICAL_EXPLANATION"},
            # EMOTIONAL
            {"text": "爸爸,我爱你", "intent": "EMOTIONAL"},
            {"text": "今天心情不太好", "intent": "EMOTIONAL"},
            {"text": "感觉很累需要休息", "intent": "EMOTIONAL"},
            {"text": "谢谢你诺诺", "intent": "EMOTIONAL"},
            {"text": "想念你了", "intent": "EMOTIONAL"},
            # FAMILY_CHAT
            {"text": "今天晚饭吃什么", "intent": "FAMILY_CHAT"},
            {"text": "周末有什么安排", "intent": "FAMILY_CHAT"},
            {"text": "聊聊家常", "intent": "FAMILY_CHAT"},
            {"text": "家里的事情", "intent": "FAMILY_CHAT"},
            {"text": "家人的近况", "intent": "FAMILY_CHAT"},
            # WORK_COORDINATION
            {"text": "安排明天的会议", "intent": "WORK_COORDINATION"},
            {"text": "项目进度更新", "intent": "WORK_COORDINATION"},
            {"text": "任务分配调整", "intent": "WORK_COORDINATION"},
            {"text": "团队协作优化", "intent": "WORK_COORDINATION"},
            {"text": "工作计划制定", "intent": "WORK_COORDINATION"},
            # LEARNING_REQUEST
            {"text": "教我新的知识", "intent": "LEARNING_REQUEST"},
            {"text": "推荐学习资源", "intent": "LEARNING_REQUEST"},
            {"text": "知识体系梳理", "intent": "LEARNING_REQUEST"},
            {"text": "学习方法指导", "intent": "LEARNING_REQUEST"},
            {"text": "技能提升建议", "intent": "LEARNING_REQUEST"},
            # SYSTEM_CONTROL
            {"text": "启动小诺服务", "intent": "SYSTEM_CONTROL"},
            {"text": "查看系统状态", "intent": "SYSTEM_CONTROL"},
            {"text": "重启应用服务", "intent": "SYSTEM_CONTROL"},
            {"text": "系统性能监控", "intent": "SYSTEM_CONTROL"},
            {"text": "服务配置更新", "intent": "SYSTEM_CONTROL"},
            # ENTERTAINMENT
            {"text": "播放音乐", "intent": "ENTERTAINMENT"},
            {"text": "推荐电影", "intent": "ENTERTAINMENT"},
            {"text": "讲个笑话", "intent": "ENTERTAINMENT"},
            {"text": "游戏推荐", "intent": "ENTERTAINMENT"},
            {"text": "娱乐资讯", "intent": "ENTERTAINMENT"},
            # HEALTH_CHECK
            {"text": "检查系统健康", "intent": "HEALTH_CHECK"},
            {"text": "服务运行状态", "intent": "HEALTH_CHECK"},
            {"text": "性能指标查询", "intent": "HEALTH_CHECK"},
            {"text": "错误日志检查", "intent": "HEALTH_CHECK"},
            {"text": "资源使用情况", "intent": "HEALTH_CHECK"},
        ]

        # 数据增强 - 添加同义词和变体
        augmented_data = []
        for sample in training_samples:
            augmented_data.append(sample)
            # 添加变体
            augmented_data.extend(self._generate_variants(sample))

        return augmented_data

    def _generate_variants(self, sample: dict) -> list[dict]:
        """生成训练数据变体"""
        text = sample["text"]
        intent = sample["intent"]
        variants = []

        # 简单的同义词替换
        replacements = {
            "分析": ["研究", "查看", "检查", "评估"],
            "查询": ["搜索", "检索", "查找"],
            "帮助": ["协助", "支持"],
            "解释": ["说明", "阐述", "讲解"],
            "启动": ["开启", "运行"],
            "查看": ["显示", "展示"],
        }

        for word, synonyms in replacements.items():
            if word in text:
                for synonym in synonyms:
                    variant_text = text.replace(word, synonym)
                    variants.append({"text": variant_text, "intent": intent})

        return variants[:2]  # 最多添加2个变体

    async def classify_intent(
        self, text: str, context: dict | None = None
    ) -> IntentClassificationResult:
        """分类意图"""
        if not self.model_loaded:
            await self.initialize()

        # 1. 基础特征提取
        base_features = await self._extract_base_features(text)

        # 2. 图谱增强特征
        graph_features = await self._extract_graph_features(text)

        # 3. BERT语义特征
        semantic_features = await self._extract_semantic_features(text)

        # 4. 上下文特征
        context_features = self._extract_context_features(context)

        # 5. 集成预测
        predictions = await self._ensemble_predict(
            base_features, graph_features, semantic_features, context_features
        )

        # 6. 选择最佳意图
        best_intent = max(predictions.items(), key=lambda x: x[1])

        # 7. 收集证据
        evidence = await self._collect_evidence(text, best_intent[0], graph_features)

        return IntentClassificationResult(
            intent=best_intent[0],
            confidence=best_intent[1],
            graph_evidence=evidence.get("graph_evidence", []),
            reasoning_path=evidence.get("reasoning_path", []),
            features_used=evidence.get("features_used", {}),
            model_predictions=predictions,
        )

    async def _extract_base_features(self, text: str) -> np.ndarray:
        """提取基础特征"""
        if not self.tfidf_vectorizer or not self.svd:
            return np.zeros(300)

        # TF-IDF向量化
        tfidf_vector = self.tfidf_vectorizer.transform([text])

        # SVD降维
        reduced_vector = self.svd.transform(tfidf_vector)

        return reduced_vector[0]

    async def _extract_graph_features(self, text: str) -> dict:
        """提取图谱特征"""
        if not self.graph_connection:
            return {}

        try:
            # 提取关键词
            keywords = self._extract_keywords(text)

            # 搜索相关实体
            entities = await self.graph_connection.search_entities(keywords)

            # 统计实体类型分布
            entity_types = {}
            for entity in entities:
                entity_type = entity.get("type", "unknown")
                entity_types[entity_type] = entity_types.get(entity_type, 0) + 1

            # 查找实体关系
            relations = []
            for entity in entities[:3]:  # 只查询前3个最相关实体
                entity_relations = await self.graph_connection.find_entity_relations(
                    entity["name"], depth=2
                )
                relations.extend(entity_relations)

            return {
                "entities": entities,
                "entity_types": entity_types,
                "relations": relations,
                "entity_count": len(entities),
                "relation_count": len(relations),
            }

        except Exception as e:
            logger.warning(f"⚠️ 图谱特征提取失败: {e}")
            return {}

    async def _extract_semantic_features(self, text: str) -> np.ndarray:
        """提取BERT语义特征"""
        if not self.bert_tokenizer or not self.bert_model:
            return np.zeros(768)  # BERT base hidden size

        try:
            # 编码文本
            inputs = self.bert_tokenizer(
                text, return_tensors="pt", truncation=True, padding=True, max_length=512
            )

            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # 获取BERT输出
            with torch.no_grad():
                outputs = self.bert_model(**inputs)
                # 使用[CLS] token的表示
                features = outputs.last_hidden_state[:, 0, :].cpu().numpy()

            return features[0]

        except Exception as e:
            logger.warning(f"⚠️ 语义特征提取失败: {e}")
            return np.zeros(768)

    def _extract_context_features(self, context: dict,) -> dict:
        """提取上下文特征"""
        if not context:
            return {}

        return {
            "previous_intent": context.get("previous_intent"),
            "conversation_length": context.get("conversation_length", 0),
            "time_of_day": datetime.now().hour,
            "session_id": context.get("session_id"),
        }

    async def _ensemble_predict(
        self,
        base_features: np.ndarray,
        graph_features: dict,
        semantic_features: np.ndarray,
        context_features: dict,
    ) -> dict:
        """集成预测"""
        predictions = {}

        # 1. 基础模型预测
        if self.ensemble_classifier:
            base_pred = self.ensemble_classifier.predict_proba([base_features])
            for i, intent in enumerate(self.label_encoder.classes_):
                predictions[intent] = base_pred[0][i]

        # 2. 图谱增强预测
        if graph_features:
            graph_scores = self._calculate_graph_scores(graph_features)
            for intent, score in graph_scores.items():
                weight = self.graph_enhancement_weights.get(intent, 0.1)
                predictions[intent] = predictions.get(intent, 0) * (1 - weight) + score * weight

        # 3. 语义相似度预测
        if hasattr(self, "semantic_embeddings"):
            semantic_scores = self._calculate_semantic_scores(semantic_features)
            for intent, score in semantic_scores.items():
                predictions[intent] = predictions.get(intent, 0) * 0.7 + score * 0.3

        return predictions

    def _calculate_graph_scores(self, graph_features: dict) -> dict:
        """基于图谱特征计算意图分数"""
        scores = {}

        entity_types = graph_features.get("entity_types", {})

        # 基于实体类型匹配
        type_intent_mapping = {
            "专利": "PATENT_ANALYSIS",
            "法律": "LEGAL_QUERY",
            "技术": "TECHNICAL_EXPLANATION",
            "申请人": "PATENT_ANALYSIS",
            "发明人": "PATENT_ANALYSIS",
            "IPC": "PATENT_ANALYSIS",
        }

        for entity_type, count in entity_types.items():
            for pattern, intent in type_intent_mapping.items():
                if pattern in entity_type:
                    scores[intent] = scores.get(intent, 0) + count * 0.1

        # 归一化
        total = sum(scores.values())
        if total > 0:
            scores = {k: v / total for k, v in scores.items()}

        return scores

    async def _collect_evidence(self, text: str, intent: str, graph_features: dict) -> dict:
        """收集证据"""
        evidence = {"graph_evidence": [], "reasoning_path": [], "features_used": {}}

        # 图谱证据
        if graph_features and graph_features.get("entities"):
            for entity in graph_features["entities"][:3]:
                evidence["graph_evidence"].append(
                    {
                        "type": "entity_match",
                        "entity": entity["name"],
                        "entity_type": entity["type"],
                        "confidence": 0.8,
                    }
                )

        # 推理路径
        evidence["reasoning_path"] = [
            f"输入文本: {text}",
            f"识别关键词: {', '.join(self._extract_keywords(text))}",
            f"图谱匹配: 找到{len(graph_features.get('entities', []))}个相关实体",
            f"意图判定: {intent}",
        ]

        # 特征重要性
        evidence["features_used"] = {
            "text_features": 0.4,
            "graph_features": 0.3,
            "semantic_features": 0.2,
            "context_features": 0.1,
        }

        return evidence

    def _extract_keywords(self, text: str) -> list[str]:
        """提取关键词"""
        # 简单的关键词提取
        import jieba

        words = jieba.lcut(text)
        # 过滤停用词
        stop_words = {"的", "了", "在", "是", "我", "你", "他", "她", "它", "们", "这", "那"}
        keywords = [w for w in words if len(w) > 1 and w not in stop_words]
        return keywords[:10]  # 返回前10个关键词

    async def save_model(self):
        """保存模型"""
        model_dir = Path("/Users/xujian/Athena工作平台/models/enhanced_intent_classifier")
        model_dir.mkdir(parents=True, exist_ok=True)

        # 保存sklearn组件
        if self.tfidf_vectorizer:
            # 安全修复: 使用joblib替代pickle
            joblib.dump(self.tfidf_vectorizer, model_dir / "tfidf_vectorizer.joblib")

        if self.svd:
            joblib.dump(self.svd, model_dir / "svd.joblib")

        if self.label_encoder:
            joblib.dump(self.label_encoder, model_dir / "label_encoder.joblib")

        if self.ensemble_classifier:
            joblib.dump(self.ensemble_classifier, model_dir / "ensemble_classifier.joblib")

        # 保存配置
        config = {
            "intent_classes": self.intent_classes,
            "version": self.version,
            "created_at": datetime.now().isoformat(),
        }

        with open(model_dir / "config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ 模型已保存到: {model_dir}")

    async def load_model(self, model_dir: Path):
        """加载模型"""
        try:
            # 加载sklearn组件 - 安全修复: 使用joblib替代pickle
            self.tfidf_vectorizer = joblib.load(model_dir / "tfidf_vectorizer.joblib")
            self.svd = joblib.load(model_dir / "svd.joblib")
            self.label_encoder = joblib.load(model_dir / "label_encoder.joblib")
            self.ensemble_classifier = joblib.load(model_dir / "ensemble_classifier.joblib")

            # 加载配置
            with open(model_dir / "config.json", encoding="utf-8") as f:
                config = json.load(f)

            self.intent_classes = config.get("intent_classes", self.intent_classes)

            logger.info(f"✅ 模型已从 {model_dir} 加载")

        except Exception as e:
            logger.error(f"❌ 模型加载失败: {e}")
            await self.train_model()  # 加载失败则重新训练


async def test_classifier():
    """测试意图识别器"""
    print("🧪 测试NebulaGraph增强意图识别器...")

    classifier = NebulaEnhancedIntentClassifier()
    await classifier.initialize()

    # 测试用例
    test_cases = [
        "分析这个专利的技术创新点",
        "查看系统运行状态",
        "爸爸,我爱你",
        "帮我解释一下机器学习算法",
        "启动向量数据库服务",
    ]

    for test_text in test_cases:
        result = await classifier.classify_intent(test_text)
        print(f"\n输入: {test_text}")
        print(f"意图: {result.intent}")
        print(f"置信度: {result.confidence:.2%}")
        print(f"图谱证据: {len(result.graph_evidence)}个")


if __name__ == "__main__":
    asyncio.run(test_classifier())
