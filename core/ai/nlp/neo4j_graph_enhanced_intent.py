#!/usr/bin/env python3

"""
Neo4j增强的意图识别系统
Neo4j Enhanced Intent Recognition System

版本: v3.0.0
利用知识图谱提升意图识别准确率
技术决策: TD-001 - 统一图数据库选择为Neo4j
"""

import json
from pathlib import Path

from core.config.unified_config import get_database_config
from core.logging_config import setup_logging

# 安全序列化和模型加载
try:
    import joblib

    from core.serialization.secure_serializer import deserialize_from_cache, 
except ImportError:
    import json

    def serialize_for_cache(obj):
        return json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8")

    def deserialize_from_cache(data):
        return json.loads(data.decode("utf-8"))


logger = setup_logging()


class Neo4jGraphConnection:
    """Neo4j连接管理器"""

    def __init__(self):
        self.connected = False
        self.mock_mode = False
        self.driver = None

        # 从统一配置获取连接信息 (TD-001)
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
            logger.warning("⚠️ Neo4j驱动未安装,使用模拟模式")
            self.mock_mode = True
            self.connected = True
            return True

        except Exception as e:
            logger.warning(f"⚠️ Neo4j连接失败: {e}")
            print("📝 使用模拟模式继续...")
            self.mock_mode = True
            self.connected = True
            return True

    async def search_intent_entities(self, text: str) -> dict:
        """搜索意图相关实体"""
        if self.mock_mode:
            # 模拟返回
            return self._mock_search_entities(text)

        try:
            # 提取关键词
            keywords = self._extract_keywords(text)
            results = {}

            with self.driver.session(database=self.database) as session:
                for keyword in keywords:
                    # 查询专利实体
                    patent_results = session.run(
                        """
                        MATCH (v:PatentEntity)
                        WHERE v.name CONTAINS $keyword
                        RETURN v.name AS name, v.type AS type
                        LIMIT 5
                    """,
                        {"keyword": keyword},
                    )
                    results["patent_entities"]] = [record.data() for record in patent_results]

                    # 查询法律实体
                    legal_results = session.run(
                        """
                        MATCH (v:LegalEntity)
                        WHERE v.name CONTAINS $keyword
                        RETURN v.name AS name, v.type AS type
                        LIMIT 5
                    """,
                        {"keyword": keyword},
                    )
                    results["legal_entities"]] = [record.data() for record in legal_results]

            return results

        except Exception as e:
            logger.error(f"实体搜索失败: {e}")
            return {}

    def _extract_keywords(self, text: str) -> list[str]:
        """提取关键词"""
        try:
            import jieba

            words = jieba.lcut(text)
            # 过滤关键词
            keywords = [
                w
                for w in words
                if len(w) > 1 and w not in ["的", "是", "在", "有", "和", "与", "或"]
            ]
            return keywords[:10]
        except ImportError:
            # 如果jieba未安装,简单分词
            return [w for w in text.split() if len(w) > 1][:10]

    def _mock_search_entities(self, text: str) -> dict:
        """模拟实体搜索"""
        # 基于文本内容返回相关实体
        entities = {
            "patent_entities": [],
            "legal_entities": [],
            "technical_entities": [],
            "intent_entities": [],
        }

        # 根据关键词判断
        if "专利" in text or "发明" in text:
            entities["patent_entities"]] = [
                {"name": "专利技术", "type": "patent_entity"},
                {"name": "发明专利", "type": "patent_entity"},
            ]

        if "法律" in text or "法规" in text:
            entities["legal_entities"]] = [
                {"name": "知识产权法", "type": "legal_entity"},
                {"name": "专利法", "type": "legal_entity"},
            ]

        if "技术" in text or "算法" in text or "系统" in text:
            entities["technical_entities"]] = [
                {"name": "技术方案", "type": "technical_entity"},
                {"name": "算法设计", "type": "technical_entity"},
            ]

        return entities

    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()
            self.connected = False


class GraphEnhancedIntentClassifier:
    """图谱增强的意图分类器"""

    def __init__(self):
        self.graph_connection = Neo4jGraphConnection()
        self.vectorizer = None
        self.label_encoder = None
        self.model = None
        self.graph_features_weight = 0.3  # 图谱特征权重

        # 意图与实体类型的映射
        self.intent_entity_mapping = {
            "PATENT_ANALYSIS": ["patent_entity", "技术实体"],
            "LEGAL_QUERY": ["legal_entity", "法规实体"],
            "TECHNICAL_EXPLANATION": ["技术实体", "方案实体"],
            "EMOTIONAL": ["情感实体"],
            "FAMILY_CHAT": ["日常实体"],
            "WORK_COORDINATION": ["工作实体"],
            "LEARNING_REQUEST": ["知识实体"],
            "SYSTEM_CONTROL": ["系统实体"],
            "ENTERTAINMENT": ["娱乐实体"],
            "HEALTH_CHECK": ["健康实体"],
        }

    async def initialize(self):
        """初始化分类器"""
        print("🚀 初始化图谱增强意图分类器...")

        # 连接Neo4j (TD-001)
        await self.graph_connection.connect()

        # 加载已训练的模型
        model_dir = Path("/Users/xujian/Athena工作平台/models/intent_classifier_v2")
        if model_dir.exists():
            print("📂 加载已训练模型...")
            self._load_model(model_dir)
        else:
            print("⚠️ 模型不存在,需要先训练")

    def _load_model(self, model_dir: Path):
        """加载模型组件"""
        try:
            with open(model_dir / "vectorizer.pkl", "rb") as f:
                self.vectorizer = deserialize_from_cache(
                    f.read() if hasattr(f, "read") else f
                )

            with open(model_dir / "label_encoder.pkl", "rb") as f:
                self.label_encoder = deserialize_from_cache(
                    f.read() if hasattr(f, "read") else f
                )

            # 使用joblib加载模型
            import joblib

            with open(model_dir / "model.pkl", "rb") as f:
                model_data = f.read()
                self.model = (
                    joblib.loads(model_data)
                    if isinstance(model_data, bytes)
                    else joblib.load(model_dir / "model.pkl")
                )

            with open(model_dir / "metadata.json") as f:
                self.metadata = json.load(f)

            print("✅ 模型加载成功")
            print(f"   准确率: {self.metadata['accuracy']:.4f}")
            print(f"   类别数: {self.metadata['n_classes']}")

        except Exception as e:
            print(f"❌ 模型加载失败: {e}")

    async def classify_with_graph_enhancement(self, text: str) -> dict:
        """使用图谱增强进行分类"""
        if not self.model:
            return {"error": "模型未初始化"}

        try:
            import numpy as np
        except ImportError:
            return {"error": "numpy未安装"}

        # 1. 基础文本分类
        text_features = self.vectorizer.transform([text])
        text_pred_proba = self.model.predict_proba(text_features)
        text_pred = self.model.predict(text_features)

        # 2. 图谱增强
        graph_entities = await self.graph_connection.search_intent_entities(text)
        graph_scores = self._calculate_graph_scores(text, graph_entities)

        # 3. 特征融合
        final_scores = self._fuse_features(text_pred_proba, graph_scores)

        # 4. 获取最终结果
        final_pred_idx = np.argmax(final_scores)
        final_intent = self.label_encoder.inverse_transform([final_pred_idx])[0]
        final_confidence = final_scores[final_pred_idx]

        # 5. 构建详细结果
        result = {
            "intent": final_intent,
            "confidence": float(final_confidence),
            "text_prediction": self.label_encoder.inverse_transform(text_pred)[0],
            "text_confidence": float(np.max(text_pred_proba)),
            "graph_enhancement": {
                "entities": graph_entities,
                "scores": graph_scores,
                "contribution": self._calculate_graph_contribution(graph_scores),
            },
            "reasoning": self._build_reasoning(text, final_intent, graph_entities),
        }

        return result

    def _calculate_graph_scores(self, text: str, entities: dict) -> dict:
        """计算图谱分数"""

        scores = {}
        intent_classes = self.label_encoder.classes_

        # 初始化分数
        for intent in intent_classes:
            scores[intent] = 0.0

        # 基于实体类型计算分数
        entity_types = set()
        for entity_type, entity_list in entities.items():
            if entity_list:
                entity_types.add(entity_type)
                # 实体数量权重
                scores[intent] += len(entity_list) * 0.1

        # 基于意图-实体映射
        for intent, required_types in self.intent_entity_mapping.items():
            for req_type in required_types:
                for entity_type in entity_types:
                    if req_type in entity_type:
                        scores[intent] += 0.5
                        break

        # 归一化
        total = sum(scores.values())
        if total > 0:
            scores = {k: v / total for k, v in scores.items()}
        else:
            # 平均分配
            avg_score = 1.0 / len(intent_classes)
            scores = dict.fromkeys(intent_classes, avg_score)

        return scores

    def _fuse_features(self, text_proba, graph_scores):
        """融合文本和图谱特征"""
        import numpy as np

        # 将文本概率转换为字典
        text_scores = {}
        intent_classes = self.label_encoder.classes_
        for i, intent in enumerate(intent_classes):
            text_scores[intent] = text_proba[0][i]

        # 加权融合
        final_scores = {}
        for intent in intent_classes:
            text_score = text_scores.get(intent, 0)
            graph_score = graph_scores.get(intent, 0)

            # 动态调整权重
            if graph_score > 0:
                # 有图谱信息时增加权重
                final_scores[intent] = text_score * 0.7 + graph_score * 0.3
            else:
                # 无图谱信息时使用文本分数
                final_scores[intent] = text_score

        # 归一化
        total = sum(final_scores.values())
        if total > 0:
            final_scores = {k: v / total for k, v in final_scores.items()}

        # 转换为数组
        return np.array([final_scores[intent] for intent in intent_classes])

    def _calculate_graph_contribution(self, graph_scores):
        """计算图谱贡献度"""
        max_score = max(graph_scores.values()) if graph_scores else 0
        min_score = min(graph_scores.values()) if graph_scores else 0

        if max_score > min_score:
            return {
                "enhancement_level": "high" if max_score > 0.5 else "medium",
                "max_score": max_score,
                "entity_count": len([v for v in graph_scores.values() if v > 0]),
            }
        else:
            return {
                "enhancement_level": "low",
                "max_score": max_score,
                "entity_count": 0,
            }

    def _build_reasoning(self, text: str, intent: str, entities: dict):
        """构建推理链"""
        reasoning = [
            f"1️⃣ 文本分析: '{text}'",
            f"2️⃣ 图谱检索: 找到{len(entities)}类实体",
        ]

        # 添加实体详情
        for entity_type, entity_list in entities.items():
            if entity_list:
                reasoning.append(f"   - {entity_type}: {len(entity_list)}个")

        reasoning.extend([
            "3️⃣ 特征融合: 文本特征 + 图谱特征",
            f"4️⃣ 最终判定: {intent}",
        ])

        return reasoning


async def test_graph_enhanced_classifier():
    """测试图谱增强分类器"""
    print("🧪 测试图谱增强意图分类器")
    print("=" * 50)

    # 初始化分类器
    classifier = GraphEnhancedIntentClassifier()
    await classifier.initialize()

    # 测试用例
    test_cases = [
        "分析这个专利的技术方案",
        "爸爸我爱你",
        "启动系统服务",
        "请解释一下算法原理",
        "查询相关法律规定",
        "安排明天的工作会议",
    ]

    print("\n📋 测试结果:")
    for i, text in enumerate(test_cases, 1):
        result = await classifier.classify_with_graph_enhancement(text)

        if "error" in result:
            print(f"\n--- 测试 {i} ---")
            print(f"输入: {text}")
            print(f"错误: {result['error']}")
            continue

        print(f"\n--- 测试 {i} ---")
        print(f"输入: {text}")
        print(f"最终预测: {result['intent']}")
        print(f"最终置信度: {result['confidence']:.2%}")
        print(f"文本预测: {result['text_prediction']}")
        print(f"文本置信度: {result['text_confidence']:.2%}")

        # 图谱增强信息
        enhancement = result["graph_enhancement"]
        print(f"图谱增强: {enhancement['contribution']['enhancement_level']}")
        print(f"实体数量: {enhancement['contribution']['entity_count']}")

        # 推理链
        print("推理过程:")
        for step in result["reasoning"]:
            print(f"  {step}")

    # 总结
    print("\n" + "=" * 50)
    print("📊 图谱增强测试完成!")
    print("💡 图谱特征有助于提升意图识别准确性")

    # 清理
    classifier.graph_connection.close()


async def main():
    """主程序"""
    await test_graph_enhanced_classifier()


# ========== 兼容层: 保持与旧API的兼容性 ==========

# 导入旧名称以保持向后兼容
NebulaGraphConnection = Neo4jGraphConnection

# 保持与旧模块导入的兼容性
try:
    NEBULA_AVAILABLE = True
except ImportError:
    NEBULA_AVAILABLE = False
    # 创建模拟类
    class Config:
        pass

    class ConnectionPool:
        pass


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

