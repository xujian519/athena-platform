"""
依赖注入配置

在应用启动时注册所有依赖注入，实现控制反转（IoC）。

使用方式：
    1. 在应用启动时调用 setup_dependency_injection()
    2. 在代码中使用 DIContainer.resolve() 获取实例
    3. 优先使用依赖注入而非直接导入
"""

from typing import Dict, Type, TypeVar, Optional, Any
from core.interfaces.vector_store import VectorStoreProvider
from core.interfaces.knowledge_base import KnowledgeBaseService
from core.interfaces.patent_service import PatentRetrievalService

T = TypeVar('T')


class DIContainer:
    """
    依赖注入容器

    管理接口与实现的映射关系。
    """

    _registry: Dict[Type, Any] = {}
    _singletons: Dict[Type, Any] = {}

    @classmethod
    def register(cls, interface: Type[T], implementation: T, singleton: bool = True):
        """
        注册实现

        Args:
            interface: 接口类型
            implementation: 实现实例
            singleton: 是否单例（默认True）
        """
        cls._registry[interface] = implementation
        if singleton:
            cls._singletons[interface] = implementation

    @classmethod
    def resolve(cls, interface: Type[T]) -> Optional[T]:
        """
        解析实现

        Args:
            interface: 接口类型

        Returns:
            实现实例，如果未注册返回None
        """
        # 优先返回单例
        if interface in cls._singletons:
            return cls._singletons[interface]

        # 返回注册的实现
        return cls._registry.get(interface)

    @classmethod
    def clear(cls):
        """清空所有注册"""
        cls._registry.clear()
        cls._singletons.clear()

    @classmethod
    def is_registered(cls, interface: Type[T]) -> bool:
        """检查接口是否已注册"""
        return interface in cls._registry


def setup_dependency_injection():
    """
    设置依赖注入

    在应用启动时调用，注册所有核心依赖。
    注意：此函数在导入具体实现时可能会触发services/domains的导入，
    这是预期的，因为依赖注入就是在这里建立连接。
    """
    # 延迟导入，避免循环依赖
    try:
        # 向量存储 - Qdrant
        from services.agent_services.vector_db.optimized_qdrant_client import OptimizedQdrantClient
        DIContainer.register(
            VectorStoreProvider,
            OptimizedQdrantClient(),
            singleton=True
        )
        print("✅ VectorStoreProvider registered: OptimizedQdrantClient")
    except ImportError as e:
        print(f"⚠️  OptimizedQdrantClient not available: {e}")

    try:
        # 知识库 - SQLite
        from services.sqlite_patent_knowledge_service import get_sqlite_patent_knowledge_service
        DIContainer.register(
            KnowledgeBaseService,
            get_sqlite_patent_knowledge_service(),
            singleton=True
        )
        print("✅ KnowledgeBaseService registered: SQLitePatentKnowledgeService")
    except ImportError as e:
        print(f"⚠️  SQLitePatentKnowledgeService not available: {e}")

    try:
        # 专利检索 - Google Patents
        from services.patents.google_patents_retriever import GooglePatentsRetriever
        DIContainer.register(
            PatentRetrievalService,
            GooglePatentsRetriever(),
            singleton=True
        )
        print("✅ PatentRetrievalService registered: GooglePatentsRetriever")
    except ImportError as e:
        print(f"⚠️  GooglePatentsRetriever not available: {e}")


def get_vector_store() -> Optional[VectorStoreProvider]:
    """便捷方法：获取向量存储提供者"""
    return DIContainer.resolve(VectorStoreProvider)


def get_knowledge_base() -> Optional[KnowledgeBaseService]:
    """便捷方法：获取知识库服务"""
    return DIContainer.resolve(KnowledgeBaseService)


def get_patent_service() -> Optional[PatentRetrievalService]:
    """便捷方法：获取专利检索服务"""
    return DIContainer.resolve(PatentRetrievalService)


# 开发环境：注册模拟实现
def setup_mock_dependency_injection():
    """
    设置模拟依赖注入（用于测试）

    注册轻量级的模拟实现，避免依赖外部服务。
    """
    from unittest.mock import Mock

    # 创建Mock实现
    mock_vector_store = Mock(spec=VectorStoreProvider)
    mock_vector_store.health_check.return_value = True
    mock_vector_store.search_vectors.return_value = []
    mock_vector_store.insert_vectors.return_value = True

    mock_knowledge_base = Mock(spec=KnowledgeBaseService)
    mock_knowledge_base.health_check.return_value = True
    mock_knowledge_base.query_knowledge.return_value = []

    mock_patent_service = Mock(spec=PatentRetrievalService)
    mock_patent_service.health_check.return_value = True
    mock_patent_service.search_patents.return_value = []
    mock_patent_service.get_patent_detail.return_value = None

    # 注册
    DIContainer.register(VectorStoreProvider, mock_vector_store)
    DIContainer.register(KnowledgeBaseService, mock_knowledge_base)
    DIContainer.register(PatentRetrievalService, mock_patent_service)

    print("✅ Mock dependency injection setup complete")


if __name__ == "__main__":
    # 测试依赖注入
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🔧 依赖注入配置测试")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()

    # 设置依赖注入
    setup_dependency_injection()
    print()

    # 解析依赖
    vector_store = get_vector_store()
    knowledge_base = get_knowledge_base()
    patent_service = get_patent_service()

    print(f"VectorStoreProvider: {vector_store}")
    print(f"KnowledgeBaseService: {knowledge_base}")
    print(f"PatentRetrievalService: {patent_service}")
    print()

    # 检查注册状态
    print("注册状态:")
    print(f"  VectorStoreProvider: {DIContainer.is_registered(VectorStoreProvider)}")
    print(f"  KnowledgeBaseService: {DIContainer.is_registered(KnowledgeBaseService)}")
    print(f"  PatentRetrievalService: {DIContainer.is_registered(PatentRetrievalService)}")
