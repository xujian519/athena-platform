#!/usr/bin/env python3
from __future__ import annotations
"""
Neo4j增强的意图识别器
Neo4j Enhanced Intent Classifier

版本: v3.0.0
99%准确率目标 - 结合知识图谱的高精度意图识别系统
技术决策: TD-001 - 统一图数据库选择为Neo4j
"""

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import torch
from sklearn.decomposition import TruncatedSVD
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier, VotingClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder

from core.config.unified_config import get_database_config
from core.logging_config import setup_logging

logger = setup_logging()


@dataclass
class IntentClassificationResult:
    """意图分类结果"""

    intent: str
    confidence: float
    graph_evidence: list[dict[str, Any]]
    reasoning_path: list[str]
    features_used: dict[str, float]
    model_predictions: dict[str, float]


class Neo4jGraphConnection:
    """Neo4j连接管理器 (TD-001: 替换NebulaGraph)"""

    def __init__(self):
        self.driver = None
        self.connected = False

        # 从统一配置获取连接信息
        db_config = get_database_config()
        neo4j_config = db_config.get("neo4j", {})

        self.uri = neo4j_config.get("uri", "bolt://localhost:7687")
        self.username = neo4j_config.get("username", "neo4j")
        self.password = neo4j_config.get("password", "password")
        self.database = neo4j_config.get("database", "neo4j")

    async def connect(self) -> bool:
        """连接到Neo4j"""
        try:
            from neo4j import GraphDatabase

            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password),
            )

            # 测试连接
            with self.driver.session(database=self.database) as session:
                result = session.run("RETURN 'Connection OK' as message")
                record = result.single()
                if record and record["message"] == "Connection OK":
                    self.connected = True
                    logger.info("✅ 成功连接到Neo4j")
                    return True

            return False

        except ImportError:
            logger.warning("⚠️ Neo4j驱动未安装")
            return False

        except Exception as e:
            logger.error(f"❌ Neo4j连接失败: {e}")
            return False

    async def execute_query(self, query: str, params: Optional[dict[str, Any]] = None):
        """执行Cypher查询"""
        if not self.connected:
            return None

        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(query, params or {})
                return list(result)
        except Exception as e:
            logger.error(f"❌ 查询执行失败: {e}")
            return None

    async def search_entities(self, keywords: list[str], limit: int = 10) -> list[dict[str, Any]]:
        """搜索实体"""
        entities = []

        for keyword in keywords:
            # 参数化查询,防止注入
            query = """
                MATCH (v:PatentEntity)
                WHERE v.name CONTAINS $keyword
                   OR v.description CONTAINS $keyword
                RETURN v.name AS name, v.type AS type, v.description AS description
                LIMIT $limit
            """
            results = await self.execute_query(query, {"keyword": keyword, "limit": limit})

            if results:
                for record in results:
                    entities.append({
                        "name": record["name"],
                        "type": record["type"],
                        "description": record["description"],
                    })

        return entities

    async def find_entity_relations(self, entity_name: str, depth: int = 2) -> list[dict[str, Any]]:
        """查找实体关系"""
        # 使用Cypher查询关系
        query = f"""
            MATCH path = (src {{name: $entity_name}})-[*1..{depth}]-(related)
            RETURN related.name AS related_entity,
                   [r in relationships(path) | type(r)][0] AS relation_type
            LIMIT 20
        """
        results = await self.execute_query(query, {"entity_name": entity_name})

        relations = []
        if results:
            for record in results:
                relations.append({
                    "related_entity": record["related_entity"],
                    "relation_type": record["relation_type"],
                    "path_depth": depth,
                })

        return relations

    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()
            self.connected = False


class Neo4jEnhancedIntentClassifier:
    """Neo4j增强的意图识别器 (v3.0.0)"""

    def __init__(self):
        self.name = "Neo4j增强意图识别器"
        self.version = "v3.0.0 - 99%准确率目标 (TD-001: 统一图数据库)"

        # 模型组件
        self.tfidf_vectorizer: TfidfVectorizer | None = None
        self.svd: TruncatedSVD | None = None
        self.label_encoder: LabelEncoder | None = None
        self.ensemble_classifier: VotingClassifier | None = None

        # BERT模型(可选)
        self.bert_tokenizer = None
        self.bert_model = None
        self.device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

        # Neo4j连接 (TD-001)
        self.graph_connection = Neo4jGraphConnection()

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

        self.model_loaded = False

    async def initialize(self) -> bool:
        """初始化模型"""
        try:
            logger.info("🚀 初始化Neo4j增强意图识别器...")

            # 连接Neo4j (TD-001)
            graph_connected = await self.graph_connection.connect()
            if not graph_connected:
                logger.warning("⚠️ Neo4j连接失败,将使用降级模式")

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

    async def classify_intent(
        self, text: str, context: Optional[dict[str, Any]] = None
    ) -> IntentClassificationResult:
        """分类意图"""
        if not self.model_loaded:
            await self.initialize()

        # 1. 基础特征提取
        base_features = await self._extract_base_features(text)

        # 2. 图谱增强特征
        graph_features = await self._extract_graph_features(text)

        # 3. 上下文特征
        context_features = self._extract_context_features(context)

        # 4. 集成预测
        predictions = await self._ensemble_predict(
            base_features, graph_features, context_features
        )

        # 5. 选择最佳意图
        best_intent = max(predictions.items(), key=lambda x: x[1])

        # 6. 收集证据
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

        tfidf_vector = self.tfidf_vectorizer.transform([text])
        reduced_vector = self.svd.transform(tfidf_vector)
        return reduced_vector[0]

    async def _extract_graph_features(self, text: str) -> dict[str, Any]:
        """提取图谱特征"""
        if not self.graph_connection.connected:
            return {}

        try:
            keywords = self._extract_keywords(text)
            entities = await self.graph_connection.search_entities(keywords)

            entity_types: dict[str, int] = {}
            for entity in entities:
                entity_type = entity.get("type", "unknown")
                entity_types[entity_type] = entity_types.get(entity_type, 0) + 1

            return {
                "entities": entities,
                "entity_types": entity_types,
                "entity_count": len(entities),
            }

        except Exception as e:
            logger.warning(f"⚠️ 图谱特征提取失败: {e}")
            return {}

    def _extract_context_features(self, context: dict[str, Any]) -> dict[str, Any]:
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
        graph_features: dict[str, Any],        context_features: dict[str, Any],    ) -> dict[str, float]:
        """集成预测"""
        predictions: dict[str, float] = {}

        # 基础模型预测
        if self.ensemble_classifier and self.label_encoder is not None:
            base_pred = self.ensemble_classifier.predict_proba([base_features])
            for i, intent in enumerate(self.label_encoder.classes_):
                predictions[intent] = base_pred[0][i]

        # 图谱增强预测
        if graph_features:
            graph_scores = self._calculate_graph_scores(graph_features)
            for intent, score in graph_scores.items():
                weight = self.graph_enhancement_weights.get(intent, 0.1)
                predictions[intent] = predictions.get(intent, 0) * (1 - weight) + score * weight

        return predictions

    def _calculate_graph_scores(self, graph_features: dict[str, Any]) -> dict[str, float]:
        """基于图谱特征计算意图分数"""
        scores: dict[str, float] = {}
        entity_types = graph_features.get("entity_types", {})

        type_intent_mapping = {
            "patent": "PATENT_ANALYSIS",
            "legal": "LEGAL_QUERY",
            "tech": "TECHNICAL_EXPLANATION",
        }

        for entity_type, count in entity_types.items():
            for pattern, intent in type_intent_mapping.items():
                if pattern in entity_type.lower():
                    scores[intent] = scores.get(intent, 0) + count * 0.1

        total = sum(scores.values())
        if total > 0:
            scores = {k: v / total for k, v in scores.items()}

        return scores

    async def _collect_evidence(
        self, text: str, intent: str, graph_features: dict[str, Any]
    ) -> dict[str, Any]:
        """收集证据"""
        evidence = {"graph_evidence": [], "reasoning_path": [], "features_used": {}}

        if graph_features and graph_features.get("entities"):
            for entity in graph_features["entities"][:3]:
                evidence["graph_evidence"].append({
                    "type": "entity_match",
                    "entity": entity["name"],
                    "entity_type": entity["type"],
                    "confidence": 0.8,
                })

        evidence["reasoning_path"] = [
            f"输入文本: {text}",
            f"识别关键词: {', '.join(self._extract_keywords(text))}",
            f"图谱匹配: 找到{len(graph_features.get('entities', []))}个相关实体",
            f"意图判定: {intent}",
        ]

        evidence["features_used"] = {
            "text_features": 0.6,
            "graph_features": 0.3,
            "context_features": 0.1,
        }

        return evidence

    def _extract_keywords(self, text: str) -> list[str]:
        """提取关键词"""
        try:
            import jieba
            words = jieba.lcut(text)
            stop_words = {"的", "了", "在", "是", "我", "你", "他", "她", "它", "们", "这", "那"}
            keywords = [w for w in words if len(w) > 1 and w not in stop_words]
            return keywords[:10]
        except ImportError:
            return [w for w in text.split() if len(w) > 1][:10]

    async def train_model(self):
        """训练意图识别模型"""
        logger.info("📚 开始训练意图识别模型...")

        # 准备训练数据
        training_data = self._prepare_training_data()
        if not training_data:
            logger.error("❌ 训练数据不足")
            return

        texts = [item["text"] for item in training_data]
        labels = [item["intent"] for item in training_data]

        # TF-IDF特征提取
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=10000, ngram_range=(1, 3), stop_words=None
        )
        tfidf_features = self.tfidf_vectorizer.fit_transform(texts)

        # SVD降维
        self.svd = TruncatedSVD(n_components=300, random_state=42)
        reduced_features = self.svd.fit_transform(tfidf_features)

        # 编码标签
        self.label_encoder = LabelEncoder()
        encoded_labels = self.label_encoder.fit_transform(labels)

        # 训练集成分类器
        rf_classifier = RandomForestClassifier(
            n_estimators=200, max_depth=20, random_state=42, n_jobs=-1
        )
        gb_classifier = GradientBoostingClassifier(
            n_estimators=200, learning_rate=0.1, max_depth=6, random_state=42
        )

        self.ensemble_classifier = VotingClassifier(
            estimators=[("rf", rf_classifier), ("gb", gb_classifier)], voting="soft"
        )
        self.ensemble_classifier.fit(reduced_features, encoded_labels)

        await self.save_model()
        logger.info("✅ 模型训练完成")

    def _prepare_training_data(self) -> list[dict[str, Any]]:
        """准备训练数据"""
        return [
            {"text": "分析这个专利的技术创新点", "intent": "PATENT_ANALYSIS"},
            {"text": "帮我查询专利的法律状态", "intent": "PATENT_ANALYSIS"},
            {"text": "这个法律条款怎么解释", "intent": "LEGAL_QUERY"},
            {"text": "相关案例判决结果", "intent": "LEGAL_QUERY"},
            {"text": "解释一下这个算法原理", "intent": "TECHNICAL_EXPLANATION"},
            {"text": "技术实现方案设计", "intent": "TECHNICAL_EXPLANATION"},
            {"text": "爸爸,我爱你", "intent": "EMOTIONAL"},
            {"text": "今天心情不太好", "intent": "EMOTIONAL"},
            {"text": "今天晚饭吃什么", "intent": "FAMILY_CHAT"},
            {"text": "周末有什么安排", "intent": "FAMILY_CHAT"},
            {"text": "安排明天的会议", "intent": "WORK_COORDINATION"},
            {"text": "项目进度更新", "intent": "WORK_COORDINATION"},
            {"text": "教我新的知识", "intent": "LEARNING_REQUEST"},
            {"text": "推荐学习资源", "intent": "LEARNING_REQUEST"},
            {"text": "启动小诺服务", "intent": "SYSTEM_CONTROL"},
            {"text": "查看系统状态", "intent": "SYSTEM_CONTROL"},
        ]

    async def save_model(self):
        """保存模型"""
        model_dir = Path("/Users/xujian/Athena工作平台/models/enhanced_intent_classifier")
        model_dir.mkdir(parents=True, exist_ok=True)

        if self.tfidf_vectorizer:
            joblib.dump(self.tfidf_vectorizer, model_dir / "tfidf_vectorizer.joblib")
        if self.svd:
            joblib.dump(self.svd, model_dir / "svd.joblib")
        if self.label_encoder:
            joblib.dump(self.label_encoder, model_dir / "label_encoder.joblib")
        if self.ensemble_classifier:
            joblib.dump(self.ensemble_classifier, model_dir / "ensemble_classifier.joblib")

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
            self.tfidf_vectorizer = joblib.load(model_dir / "tfidf_vectorizer.joblib")
            self.svd = joblib.load(model_dir / "svd.joblib")
            self.label_encoder = joblib.load(model_dir / "label_encoder.joblib")
            self.ensemble_classifier = joblib.load(model_dir / "ensemble_classifier.joblib")

            with open(model_dir / "config.json", encoding="utf-8") as f:
                config = json.load(f)
            self.intent_classes = config.get("intent_classes", self.intent_classes)

            logger.info(f"✅ 模型已从 {model_dir} 加载")
        except Exception as e:
            logger.error(f"❌ 模型加载失败: {e}")
            await self.train_model()


# ========== 兼容层: 保持与旧API的兼容性 ==========

# 导入旧名称以保持向后兼容
NebulaGraphConnection = Neo4jGraphConnection
NebulaEnhancedIntentClassifier = Neo4jEnhancedIntentClassifier


async def test_classifier():
    """测试意图识别器"""
    print("🧪 测试Neo4j增强意图识别器...")

    classifier = Neo4jEnhancedIntentClassifier()
    await classifier.initialize()

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

    # 清理
    classifier.graph_connection.close()


if __name__ == "__main__":
    asyncio.run(test_classifier())
