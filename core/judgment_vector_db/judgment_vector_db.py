#!/usr/bin/env python3
"""
专利判决向量数据库系统
Patent Judgment Vector Database System

统一的系统入口,整合所有功能模块
"""

from typing import Any, Dict, List, Optional

from core.logging_config import setup_logging

logger = setup_logging()


class PatentJudgmentVectorDB:
    """专利判决向量数据库系统"""

    def __init__(self, config_path: str):
        """
        初始化系统

        Args:
            config_path: 配置文件路径
        """
        import yaml

        # 加载配置
        with open(config_path) as f:
            self.config = yaml.safe_load(f)

        # 初始化各模块
        self.qdrant_client = None
        self.postgres_client = None
        self.nebula_client = None
        self.vectorizer = None
        self.query_classifier = None
        self.hybrid_retriever = None
        self.viewpoint_analyzer = None
        self.article_generator = None
        self.dialogue_interface = None

        # 系统状态
        self.is_initialized = False

    def initialize(self) -> bool:
        """
        初始化系统

        Returns:
            是否成功
        """
        logger.info("🚀 初始化专利判决向量数据库系统...")

        try:
            # 1. 初始化存储层
            if not self._initialize_storage():
                logger.error("❌ 存储层初始化失败")
                return False

            # 2. 初始化向量化器
            if not self._initialize_vectorizer():
                logger.error("❌ 向量化器初始化失败")
                return False

            # 3. 初始化检索引擎
            if not self._initialize_retrieval():
                logger.error("❌ 检索引擎初始化失败")
                return False

            # 4. 初始化分析引擎
            if not self._initialize_analysis():
                logger.error("❌ 分析引擎初始化失败")
                return False

            # 5. 初始化生成引擎
            if not self._initialize_generation():
                logger.error("❌ 生成引擎初始化失败")
                return False

            # 6. 初始化对话接口
            if not self._initialize_dialogue():
                logger.error("❌ 对话接口初始化失败")
                return False

            self.is_initialized = True
            logger.info("✅ 系统初始化完成")
            return True

        except Exception as e:
            logger.error(f"❌ 系统初始化异常: {e!s}")
            return False

    def _initialize_storage(self) -> bool:
        """初始化存储层"""
        # TD-001: 迁移到Neo4j统一图数据库
        from core.judgment_vector_db.storage.neo4j_client import (
            Neo4jJudgmentClient,
        )
        from core.judgment_vector_db.storage.postgres_client import PostgreSQLClient
        from core.judgment_vector_db.storage.qdrant_client import QdrantClient

        # Qdrant
        try:
            self.qdrant_client = QdrantClient(self.config.get("qdrant", {}))
            if self.qdrant_client.connect():
                self.qdrant_client.initialize_collections()
                logger.info("✅ Qdrant初始化成功")
            else:
                logger.warning("⚠️ Qdrant连接失败")
        except Exception as e:
            logger.warning(f"⚠️ Qdrant初始化异常: {e!s}")

        # PostgreSQL
        try:
            self.postgres_client = PostgreSQLClient(self.config.get("postgresql", {}))
            if self.postgres_client.connect():
                self.postgres_client.initialize_tables()
                logger.info("✅ PostgreSQL初始化成功")
            else:
                logger.warning("⚠️ PostgreSQL连接失败")
                return False
        except Exception as e:
            logger.error(f"❌ PostgreSQL初始化异常: {e!s}")
            return False

        # Neo4j (TD-001: 统一图数据库,替换NebulaGraph)
        try:
            self.neo4j_client = Neo4jJudgmentClient(self.config.get("neo4j", {}))
            if self.neo4j_client.connect():
                self.neo4j_client.initialize_graph()
                logger.info("✅ Neo4j初始化成功")
            else:
                logger.warning("⚠️ Neo4j连接失败(可选)")
        except Exception as e:
            logger.warning(f"⚠️ Neo4j初始化异常: {e!s}")

        # 兼容层: 保持nebula_client属性指向neo4j_client
        self.nebula_client = self.neo4j_client

        return True

    def _initialize_vectorizer(self) -> bool:
        """初始化向量化器"""
        from core.judgment_vector_db.data_processing.vectorizer import JudgmentVectorizer

        try:
            self.vectorizer = JudgmentVectorizer(self.config.get("bge_m3_model", {}))
            logger.info("✅ 向量化器初始化成功")
            return True
        except Exception as e:
            logger.error(f"❌ 向量化器初始化异常: {e!s}")
            return False

    def _initialize_retrieval(self) -> bool:
        """初始化检索引擎"""
        from core.judgment_vector_db.retrieval.hybrid_retriever import HybridRetriever
        from core.judgment_vector_db.retrieval.query_classifier import QueryClassifier

        try:
            # 查询分类器
            self.query_classifier = QueryClassifier(self.config)

            # 混合检索引擎
            self.hybrid_retriever = HybridRetriever(
                qdrant_client=self.qdrant_client,
                postgres_client=self.postgres_client,
                nebula_client=self.nebula_client,
                vectorizer=self.vectorizer,
                config=self.config,
            )

            logger.info("✅ 检索引擎初始化成功")
            return True
        except Exception as e:
            logger.error(f"❌ 检索引擎初始化异常: {e!s}")
            return False

    def _initialize_analysis(self) -> bool:
        """初始化分析引擎"""
        from core.judgment_vector_db.analysis.viewpoint_analyzer import ViewpointAnalyzer

        try:
            self.viewpoint_analyzer = ViewpointAnalyzer(
                postgres_client=self.postgres_client,
                hybrid_retriever=self.hybrid_retriever,
                config=self.config,
            )
            logger.info("✅ 分析引擎初始化成功")
            return True
        except Exception as e:
            logger.error(f"❌ 分析引擎初始化异常: {e!s}")
            return False

    def _initialize_generation(self) -> bool:
        """初始化生成引擎"""
        from core.judgment_vector_db.generation.article_generator import ArticleGenerator

        try:
            self.article_generator = ArticleGenerator(
                viewpoint_analyzer=self.viewpoint_analyzer,
                hybrid_retriever=self.hybrid_retriever,
                config=self.config,
            )
            logger.info("✅ 生成引擎初始化成功")
            return True
        except Exception as e:
            logger.error(f"❌ 生成引擎初始化异常: {e!s}")
            return False

    def _initialize_dialogue(self) -> bool:
        """初始化对话接口"""
        from core.judgment_vector_db.integration.dialogue_interface import PureDialogueInterface

        try:
            self.dialogue_interface = PureDialogueInterface(
                query_classifier=self.query_classifier,
                hybrid_retriever=self.hybrid_retriever,
                viewpoint_analyzer=self.viewpoint_analyzer,
                article_generator=self.article_generator,
                config=self.config,
            )
            logger.info("✅ 对话接口初始化成功")
            return True
        except Exception as e:
            logger.error(f"❌ 对话接口初始化异常: {e!s}")
            return False

    def query(self, user_input: str, session_id: str = "default") -> dict[str, Any]:
        """
        处理用户查询

        Args:
            user_input: 用户输入
            session_id: 会话ID

        Returns:
            响应字典
        """
        if not self.is_initialized:
            return {"error": "系统未初始化", "message": "请先调用 initialize() 方法"}

        try:
            response = self.dialogue_interface.process_user_input(
                user_input=user_input, session_id=session_id
            )

            return {
                "response_text": response.response_text,
                "intent": response.intent.value,
                "suggestions": response.suggestions,
                "needs_clarification": response.needs_clarification,
                "metadata": response.metadata,
            }

        except Exception as e:
            logger.error(f"❌ 查询处理异常: {e!s}")
            return {"error": str(e), "message": "查询处理失败"}

    def analyze(self, topic: str) -> dict[str, Any]:
        """
        分析主题

        Args:
            topic: 分析主题

        Returns:
            分析报告
        """
        if not self.is_initialized:
            return {"error": "系统未初始化", "message": "请先调用 initialize() 方法"}

        try:
            report = self.viewpoint_analyzer.generate_analysis_report(query=topic)
            return report
        except Exception as e:
            logger.error(f"❌ 分析异常: {e!s}")
            return {"error": str(e), "message": "分析失败"}

    def generate_article(self, topic: str, article_type: str = "review") -> dict[str, Any]:
        """
        生成文章

        Args:
            topic: 文章主题
            article_type: 文章类型

        Returns:
            文章数据
        """
        if not self.is_initialized:
            return {"error": "系统未初始化", "message": "请先调用 initialize() 方法"}

        try:
            from core.judgment_vector_db.generation.article_generator import ArticleType

            article = self.article_generator.generate_article(
                topic=topic, article_type=ArticleType(article_type)
            )

            return self.article_generator.export_json(article)
        except Exception as e:
            logger.error(f"❌ 文章生成异常: {e!s}")
            return {"error": str(e), "message": "文章生成失败"}

    def get_status(self) -> dict[str, Any]:
        """获取系统状态"""
        status = {"is_initialized": self.is_initialized, "storage": {}, "modules": {}}

        if self.qdrant_client:
            status["storage"]["qdrant"] = self.qdrant_client.is_connected

        if self.postgres_client:
            status["storage"]["postgresql"] = self.postgres_client.is_connected

        # TD-001: Neo4j统一图数据库 (替换NebulaGraph)
        if self.neo4j_client:
            status["storage"]["neo4j"] = self.neo4j_client.is_connected

        status["modules"]["vectorizer"] = self.vectorizer is not None
        status["modules"]["query_classifier"] = self.query_classifier is not None
        status["modules"]["hybrid_retriever"] = self.hybrid_retriever is not None
        status["modules"]["viewpoint_analyzer"] = self.viewpoint_analyzer is not None
        status["modules"]["article_generator"] = self.article_generator is not None
        status["modules"]["dialogue_interface"] = self.dialogue_interface is not None

        return status


# 便捷函数
def create_judgment_vector_db(
    config_path: str = "/Users/xujian/Athena工作平台/config/judgment_vector_db_config.yaml",
) -> PatentJudgmentVectorDB:
    """
    创建专利判决向量数据库系统

    Args:
        config_path: 配置文件路径

    Returns:
        PatentJudgmentVectorDB实例
    """
    db = PatentJudgmentVectorDB(config_path)
    db.initialize()
    return db


if __name__ == "__main__":
    # 测试代码
    # setup_logging()  # 日志配置已移至模块导入

    # 创建系统
    db = create_judgment_vector_db()

    # 检查状态
    status = db.get_status()
    print("\n系统状态:")
    print(f"初始化: {status['is_initialized']}")
    print(f"存储: {status['storage']}")
    print(f"模块: {status['modules']}")

    # 测试查询
    if status["is_initialized"]:
        print("\n测试查询...")
        response = db.query("专利法第22条第3款的相关案例")
        print(response["response_text"])
