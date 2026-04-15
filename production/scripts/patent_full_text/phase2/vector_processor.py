#!/usr/bin/env python3
"""
BGE向量化处理模块（优化版）
使用本地BGE模型对专利文本进行向量化，并存储到Qdrant
支持Hybrid检索（密集向量 + 稀疏向量）

作者: Athena平台团队
创建时间: 2025-12-24
更新时间: 2025-12-24
"""

from __future__ import annotations
import logging
import re
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

# 使用安全哈希函数替代不安全的MD5/SHA1
from production.utils.security_helpers import short_hash

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

# 导入配置管理
try:
    from .config import get_config
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    logger = logging.getLogger(__name__)

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
if not CONFIG_AVAILABLE:
    logger = logging.getLogger(__name__)

# 尝试导入依赖
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("⚠️ sentence-transformers未安装")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("⚠️ requests未安装")


@dataclass
class VectorizationResult:
    """向量化结果"""
    patent_number: str
    vector_id: str
    success: bool
    error_message: str | None = None
    vector_dimension: int = 0


class Chunk:
    """文本块"""
    def __init__(
        self,
        chunk_id: str,
        patent_number: str,
        section: str,
        text: str,
        chunk_index: int,
        metadata: dict[str, Any] | None = None
    ):
        self.chunk_id = chunk_id
        self.patent_number = patent_number
        self.section = section  # title, abstract, claims, description
        self.text = text
        self.chunk_index = chunk_index
        self.metadata = metadata or {}

    @property
    def token_count(self) -> int:
        """估算token数量（中文按字符计算）"""
        return len(self.text)

    def __repr__(self) -> str:
        return f"Chunk({self.section}[{self.chunk_index}], {self.token_count} tokens)"


class TextChunker:
    """文本分块器 - 按照参考方案的分块策略"""

    def __init__(
        self,
        chunk_size: int = 500,  # tokens
        chunk_overlap: int = 50,
        max_chunks: int = 20
    ):
        """
        初始化分块器

        Args:
            chunk_size: 块大小（tokens）
            chunk_overlap: 重叠大小
            max_chunks: 最大分块数
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.max_chunks = max_chunks

    def chunk_text(
        self,
        text: str,
        patent_number: str,
        section: str
    ) -> list[Chunk]:
        """
        对文本进行分块

        Args:
            text: 待分块文本
            patent_number: 专利号
            section: 所属部分

        Returns:
            List[Chunk]: 文本块列表
        """
        if not text or not text.strip():
            return []

        chunks = []

        # 按段落分割
        paragraphs = [p.strip() for p in text.split('\n') if p.strip()]

        current_chunk = ""
        chunk_index = 0
        char_limit = self.chunk_size * 2  # 中文约2字符=1token

        for para in paragraphs:
            # 如果单个段落就超过限制，需要切分
            if len(current_chunk) + len(para) > char_limit and current_chunk:
                # 保存当前块
                chunks.append(self._create_chunk(
                    current_chunk, patent_number, section, chunk_index
                ))
                chunk_index += 1
                current_chunk = para

                # 如果段落仍然太长，强制切分
                while len(current_chunk) > char_limit * 1.5:
                    split_point = int(char_limit)
                    chunks.append(self._create_chunk(
                        current_chunk[:split_point],
                        patent_number, section, chunk_index
                    ))
                    chunk_index += 1
                    current_chunk = current_chunk[split_point:]

                    if chunk_index >= self.max_chunks:
                        break
            else:
                current_chunk += "\n" + para if current_chunk else para

            if chunk_index >= self.max_chunks:
                break

        # 保存最后一块
        if current_chunk and chunk_index < self.max_chunks:
            chunks.append(self._create_chunk(
                current_chunk, patent_number, section, chunk_index
            ))

        return chunks

    def _create_chunk(
        self,
        text: str,
        patent_number: str,
        section: str,
        index: int
    ) -> Chunk:
        """创建文本块"""
        chunk_id = f"{patent_number}_{section}_{index}"
        return Chunk(
            chunk_id=chunk_id,
            patent_number=patent_number,
            section=section,
            text=text.strip(),
            chunk_index=index,
            metadata={"section": section, "index": index}
        )


class SparseVectorGenerator:
    """稀疏向量生成器（BM25关键词）"""

    def __init__(self):
        """初始化稀疏向量生成器"""
        # 中文停用词
        self.stopwords = self._load_stopwords()

    def _load_stopwords(self) -> set:
        """加载停用词"""
        return {
            "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一",
            "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有",
            "看", "好", "自己", "这", "那", "里", "就是", "可以", "一个", "中", "被",
            "所述", "其", "该", "通过", "实现", "包括", "其中", "如图", "所示",
            "一种", "方法", "系统", "装置", "特征"
        }

    def generate(self, text: str, top_k: int = 20) -> dict[int, float]:
        """
        生成稀疏向量（基于BM25的关键词）

        Args:
            text: 输入文本
            top_k: 返回前K个关键词

        Returns:
            Dict[int, float]: {token_hash: weight}
        """
        # 简单分词（按字符和常见词汇边界）
        words = self._tokenize(text)

        # 过滤停用词
        words = [w for w in words if w not in self.stopwords and len(w) > 1]

        # 统计词频
        word_counts = Counter(words)

        # 取top_k
        top_words = word_counts.most_common(top_k)

        # 生成稀疏向量 {hash(token): score}
        sparse_vector = {}
        for word, count in top_words:
            token_hash = hash(word) % (2**31)  # 转为正整数
            sparse_vector[token_hash] = float(count)

        return sparse_vector

    def _tokenize(self, text: str) -> list[str]:
        """简单分词"""
        # 移除标点符号
        text = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', text)
        # 分割
        words = text.split()
        return words


class BGEVectorizer:
    """BGE向量化处理器（优化版）"""

    def __init__(
        self,
        model_path: str | None = None,  # 本地模型路径
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
        collection_name: str = "patent_full_text",
        enable_hybrid: bool = True,  # 是否启用Hybrid检索
        config=None  # 配置对象（可选）
    ):
        """
        初始化向量化处理器

        Args:
            model_path: 本地BGE模型路径（优先使用本地模型）
            qdrant_host: Qdrant主机
            qdrant_port: Qdrant端口
            collection_name: 集合名称
            enable_hybrid: 是否启用Hybrid检索（dense + sparse）
            config: 配置对象（可选，优先级高于其他参数）
        """
        # 使用配置对象（如果提供）
        if config is not None and CONFIG_AVAILABLE:
            qdrant_host = config.qdrant.host
            qdrant_port = config.qdrant.port
            collection_name = config.qdrant.collection_name
            if model_path is None:
                model_path = config.bge_model.model_path
            enable_hybrid = config.qdrant.enable_sparse

        self.collection_name = collection_name
        self.qdrant_url = f"http://{qdrant_host}:{qdrant_port}"
        self.enable_hybrid = enable_hybrid

        # 创建requests session（解决Qdrant 502问题）
        if REQUESTS_AVAILABLE:
            self.http_session = requests.Session()
            self.http_session.trust_env = False  # 禁用代理检测
        else:
            self.http_session = None

        # 查找本地模型
        if model_path is None:
            model_path = self._find_local_model()

        self.model_path = model_path
        self.model = None
        self.vector_dimension = 1024  # BGE-M3的维度

        # 稀疏向量生成器
        self.sparse_generator = SparseVectorGenerator() if enable_hybrid else None

        self._initialize_model()

    def _find_local_model(self) -> str | None:
        """查找本地BGE模型"""
        # 常见路径
        search_paths = [
            "/Users/xujian/Athena工作平台/models/converted/BAAI/bge-m3",
            "/Users/xujian/Athena工作平台/models/bge-m3",
            "~/models/BAAI/bge-m3",
        ]

        for path in search_paths:
            p = Path(path).expanduser()
            if p.exists() and (p / "config.json").exists():
                logger.info(f"🔍 找到本地模型: {p}")
                return str(p)

        logger.warning("⚠️ 未找到本地BGE模型")
        return None

    def _initialize_model(self) -> Any:
        """初始化模型（优先使用本地）"""
        if self.model_path and SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                logger.info(f"🔄 加载本地BGE模型: {self.model_path}")
                # 使用modules参数直接加载，避免Pooling层初始化问题
                from sentence_transformers import models

                # 加载BERT模型
                word_embedding_model = models.Transformer(self.model_path)

                # 使用BERT模型自带的池化配置
                pooling_model = models.Pooling(
                    word_embedding_model.get_word_embedding_dimension(),
                    pooling_mode_mean_tokens=True,
                    pooling_mode_cls_token=False,
                    pooling_mode_max_tokens=False
                )

                # 组合模型
                self.model = SentenceTransformer(modules=[word_embedding_model, pooling_model])
                logger.info("✅ 本地模型加载成功")

                # 获取实际向量维度
                test_vec = self.model.encode("测试")
                self.vector_dimension = len(test_vec)
                logger.info(f"   向量维度: {self.vector_dimension}")

            except Exception as e:
                logger.warning(f"⚠️ 本地模型加载失败: {e}")
                self.model = None
        else:
            logger.info("📡 本地模型不可用，将使用API方式")

    def ensure_collection(self) -> Any:
        """确保Qdrant集合存在"""
        if not self.http_session:
            return False

        try:
            # 检查集合是否存在
            check_url = f"{self.qdrant_url}/collections/{self.collection_name}"
            response = self.http_session.get(check_url, timeout=10)

            if response.status_code == 200:
                logger.info(f"✅ 集合已存在: {self.collection_name}")
                return True

            # 创建集合
            logger.info(f"🔨 创建集合: {self.collection_name}")

            # 基础配置
            vectors_config = {
                "size": self.vector_dimension,
                "distance": "Cosine"
            }

            # Sparse向量配置（Hybrid检索）
            payload = {
                "vectors": vectors_config
            }

            if self.enable_hybrid:
                payload["sparse_vectors"] = {
                    "sparse": {
                        "index": {
                            "type": "sparse_inverted_index",
                            "full_scan_threshold": 10000
                        }
                    }
                }

            create_url = f"{self.qdrant_url}/collections/{self.collection_name}"
            response = self.http_session.put(create_url, json=payload, timeout=30)

            if response.status_code == 200:
                logger.info(f"✅ 集合创建成功: {self.collection_name}")
                return True
            else:
                logger.error(f"❌ 集合创建失败: {response.text}")
                return False

        except Exception as e:
            logger.error(f"❌ 集合操作失败: {e}")
            return False

    def vectorize_chunk(
        self,
        chunk: Chunk,
        postgres_id: str | None = None
    ) -> VectorizationResult:
        """
        对单个文本块进行向量化

        Args:
            chunk: 文本块
            postgres_id: PostgreSQL记录ID

        Returns:
            VectorizationResult: 向量化结果
        """
        if not self.model:
            return VectorizationResult(
                patent_number=chunk.patent_number,
                vector_id="",
                success=False,
                error_message="模型未初始化"
            )

        try:
            # 生成密集向量
            dense_vector = self.model.encode(
                chunk.text,
                normalize_embeddings=True,
                show_progress_bar=False
            )

            # 生成稀疏向量（可选）
            sparse_vector = None
            if self.sparse_generator:
                sparse_vector = self.sparse_generator.generate(chunk.text)

            # 准备payload
            payload = {
                "patent_number": chunk.patent_number,
                "section": chunk.section,
                "chunk_index": chunk.chunk_index,
                "text": chunk.text[:500],  # 限制payload大小
                "text_length": len(chunk.text),
                "vectorized_at": datetime.now().isoformat()
            }

            if postgres_id:
                payload["postgres_id"] = postgres_id

            # 上传到Qdrant
            success = self._upsert_to_qdrant(
                chunk.chunk_id,
                dense_vector.tolist(),
                sparse_vector,
                payload
            )

            if success:
                return VectorizationResult(
                    patent_number=chunk.patent_number,
                    vector_id=chunk.chunk_id,
                    success=True,
                    vector_dimension=len(dense_vector)
                )
            else:
                return VectorizationResult(
                    patent_number=chunk.patent_number,
                    vector_id="",
                    success=False,
                    error_message="Qdrant存储失败"
                )

        except Exception as e:
            logger.error(f"❌ 向量化失败: {e}")
            return VectorizationResult(
                patent_number=chunk.patent_number,
                vector_id="",
                success=False,
                error_message=str(e)
            )

    def _upsert_to_qdrant(
        self,
        point_id: str,
        dense_vector: list[float],
        sparse_vector: dict[int, float] | None,
        payload: dict[str, Any]
    ) -> bool:
        """上传到Qdrant"""
        if not self.http_session:
            return False

        try:
            url = f"{self.qdrant_url}/collections/{self.collection_name}/points"

            # 使用UUID格式的ID（将字符串hash转为UUID）
            import uuid

            # 生成稳定的UUID
            id_hash = short_hash(point_id.encode())
            point_uuid = uuid.UUID(id_hash[:32])

            # 构建point数据
            point = {
                "id": str(point_uuid),  # 使用字符串格式的UUID
                "vector": dense_vector,
                "payload": payload
            }

            # 添加原始ID到payload
            point["payload"]["chunk_id"] = point_id

            # 添加稀疏向量（Hybrid）
            if sparse_vector:
                point["sparse_vector"] = {
                    "index": sparse_vector,
                    "vector": sparse_vector
                }

            data = {"points": [point]}

            response = self.http_session.put(url, json=data, timeout=30)
            response.raise_for_status()

            return True

        except Exception as e:
            logger.error(f"❌ Qdrant上传失败: {e}")
            return False

    def vectorize_patent(
        self,
        patent_number: str,
        title: str,
        abstract: str,
        claims: str,
        description: str,
        postgres_id: str | None = None
    ) -> dict[str, VectorizationResult]:
        """
        对专利进行分块并向量化

        Args:
            patent_number: 专利号
            title: 标题
            abstract: 摘要
            claims: 权利要求
            description: 说明书
            postgres_id: PostgreSQL记录ID

        Returns:
            Dict[str, VectorizationResult]: 各部分的向量化结果
        """
        # 确保集合存在
        self.ensure_collection()

        results = {}
        chunker = TextChunker()

        # 对各部分进行分块和向量化
        sections = {
            "title": title,
            "abstract": abstract,
            "claims": claims,
            "description": description
        }

        total_chunks = 0
        successful_chunks = 0

        for section, text in sections.items():
            if not text:
                continue

            chunks = chunker.chunk_text(text, patent_number, section)
            total_chunks += len(chunks)

            section_results = []
            for chunk in chunks:
                result = self.vectorize_chunk(chunk, postgres_id)
                section_results.append(result)
                if result.success:
                    successful_chunks += 1

            # 记录该section的结果
            if section_results:
                results[section] = section_results[0]  # 取第一个作为代表

        logger.info(
            f"✅ 专利向量化完成: {patent_number}, "
            f"{successful_chunks}/{total_chunks} 块成功"
        )

        return results


# ==================== 示例使用 ====================

def main() -> None:
    """示例使用"""
    # 初始化向量化器（自动查找本地模型）
    vectorizer = BGEVectorizer(enable_hybrid=True)

    # 测试文本分块
    chunker = TextChunker()
    test_text = """
    一种基于人工智能的图像识别方法，包括以下步骤：
    首先获取待识别的图像数据，然后对图像进行预处理操作，
    预处理包括去噪、归一化和增强处理。
    接着使用预训练的深度卷积神经网络提取图像特征，
    最后通过全连接层进行分类识别，输出识别结果。
    该方法能够有效提升识别准确率，降低计算复杂度。
    """ * 5  # 扩展文本以测试分块

    print("=" * 70)
    print("BGE向量化处理 - 示例")
    print("=" * 70)

    chunks = chunker.chunk_text(test_text, "TEST001", "abstract")
    print(f"\n📝 分块结果: {len(chunks)} 个块")
    for i, chunk in enumerate(chunks[:3]):
        print(f"   块{i+1}: {chunk.chunk_id}, {chunk.token_count} tokens")
        print(f"      预览: {chunk.text[:50]}...")

    # 测试稀疏向量
    if vectorizer.sparse_generator:
        sparse_vec = vectorizer.sparse_generator.generate(test_text, top_k=10)
        print(f"\n🔑 稀疏向量（关键词）: {len(sparse_vec)} 个")
        for i, (k, v) in enumerate(list(sparse_vec.items())[:5]):
            print(f"   项{k}: {v}")

    # 测试向量化
    if vectorizer.model:
        print(f"\n🔄 模型路径: {vectorizer.model_path}")
        print(f"   向量维度: {vectorizer.vector_dimension}")

        # 生成测试向量
        test_vector = vectorizer.model.encode("测试文本")
        print(f"   测试向量维度: {len(test_vector)}")
        print(f"   向量范数: {sum(test_vector**2)**0.5:.4f}")


if __name__ == "__main__":
    main()
