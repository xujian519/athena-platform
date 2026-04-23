#!/usr/bin/env python3

"""
判决书向量化模块
Judgment Vectorizer

功能:
- 使用BGE-M3模型生成向量
- 支持三层粒度向量化(L1法条/L2焦点/L3论点)
- MPS加速支持
"""

import json
import pickle
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import numpy as np

from core.logging_config import setup_logging

logger = setup_logging()


@dataclass
class VectorizedData:
    """向量化数据"""

    vector_id: str  # 向量ID
    layer: str  # 层级(L1/L2/L3)
    content: dict[str, Any]  # 原始内容
    embedding: np.ndarray  # 向量(1024维)
    metadata: dict[str, Any]  # 元数据


class JudgmentVectorizer:
    """判决书向量化器"""

    def __init__(self, config: Optional[dict[str, Any]] = None):
        """
        初始化向量化器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.bge_m3_loader = None
        self.model = None
        self.is_loaded = False

        # 统计信息
        self.stats = {
            "total_vectors": 0,
            "layer1_count": 0,
            "layer2_count": 0,
            "layer3_count": 0,
            "processing_time": 0.0,
        }

    def load_model(self) -> bool:
        """
        加载BGE-M3模型

        Returns:
            是否加载成功
        """
        try:
            from core.ai.nlp.bge_m3_loader import load_bge_m3_model

            logger.info("🔄 正在加载BGE-M3模型...")
            self.bge_m3_loader = load_bge_m3_model()

            if self.bge_m3_loader and self.bge_m3_loader.is_loaded:
                self.model = self.bge_m3_loader.model
                self.is_loaded = True
                logger.info("✅ BGE-M3模型加载成功")
                return True
            else:
                logger.error("❌ BGE-M3模型加载失败")
                return False

        except Exception as e:
            logger.error(f"❌ 模型加载异常: {e!s}")
            return False

    def vectorize_judgment(
        self, structured_data: dict[str, Any], force_reload: bool = False
    ) -> list[VectorizedData]:
        """
        向量化判决书(三层粒度)

        Args:
            structured_data: 结构化判决书数据
            force_reload: 是否强制重新加载模型

        Returns:
            向量化数据列表
        """
        # 确保模型已加载
        if (not self.is_loaded or force_reload) and not self.load_model():
            return []

        start_time = datetime.now()
        vectors = []

        case_id = structured_data["case_info"]["case_id"]

        # L1层:法条层向量化
        if structured_data.get("layer1"):
            layer1_vectors = self._vectorize_layer1(case_id, structured_data["layer1"])
            vectors.extend(layer1_vectors)

        # L2层:争议焦点层向量化
        if structured_data.get("layer2"):
            layer2_vectors = self._vectorize_layer2(case_id, structured_data["layer2"])
            vectors.extend(layer2_vectors)

        # L3层:论点层向量化
        if structured_data.get("layer3"):
            layer3_vectors = self._vectorize_layer3(case_id, structured_data["layer3"])
            vectors.extend(layer3_vectors)

        # 更新统计
        processing_time = (datetime.now() - start_time).total_seconds()
        self.stats["processing_time"] += processing_time
        self.stats["total_vectors"] += len(vectors)

        logger.info(
            f"✅ {case_id} 向量化完成: "
            f"L1={len([v for v in vectors if v.layer == 'L1'])}, "
            f"L2={len([v for v in vectors if v.layer == 'L2'])}, "
            f"L3={len([v for v in vectors if v.layer == 'L3'])}, "
            f"耗时={processing_time:.2f}秒"
        )

        return vectors

    def encode_query(self, query: str, force_reload: bool = False) -> np.ndarray:
        """
        将查询文本编码为向量

        Args:
            query: 查询文本
            force_reload: 是否强制重新加载模型

        Returns:
            查询向量 (1024维)
        """
        # 确保模型已加载
        if (not self.is_loaded or force_reload) and not self.load_model():
            return np.zeros(1024, dtype=np.float32)

        try:
            # 使用BGE-M3编码查询 (使用与向量化相同的方法)
            embedding = self.bge_m3_loader.encode_single(query, normalize=True)
            return embedding

        except Exception as e:
            logger.error(f"❌ 查询编码失败: {e!s}")
            return np.zeros(1024, dtype=np.float32)

    def _vectorize_layer1(self, case_id: str, layer1_data: dict[str, Any]) -> list[VectorizedData]:
        """
        向量化L1层(法条层)

        Args:
            case_id: 案号
            layer1_data: L1层数据

        Returns:
            向量化数据列表
        """
        vectors = []

        for article_name, article_data in layer1_data.items():
            # 构建文本
            text = self._build_layer1_text(case_id, article_name, article_data)

            # 生成向量
            embedding = self.bge_m3_loader.encode_single(text, normalize=True)

            # 创建向量化数据
            vector = VectorizedData(
                vector_id=f"{case_id}_L1_{article_name}",
                layer="L1",
                content={
                    "case_id": case_id,
                    "article_name": article_name,
                    "related_cases": article_data["related_cases"],
                },
                embedding=embedding,
                metadata={
                    "created_at": datetime.now().isoformat(),
                    "vector_type": "legal_article",
                },
            )

            vectors.append(vector)
            self.stats["layer1_count"] += 1

        return vectors

    def _vectorize_layer2(self, case_id: str, layer2_data: dict[str, Any]) -> list[VectorizedData]:
        """
        向量化L2层(争议焦点层)

        Args:
            case_id: 案号
            layer2_data: L2层数据

        Returns:
            向量化数据列表
        """
        vectors = []

        for focus_description, focus_data in layer2_data.items():
            # 构建文本
            text = self._build_layer2_text(case_id, focus_description, focus_data)

            # 生成向量
            embedding = self.bge_m3_loader.encode_single(text, normalize=True)

            # 创建向量化数据
            vector = VectorizedData(
                vector_id=f"{case_id}_L2_{hash(focus_description)}",
                layer="L2",
                content={
                    "case_id": case_id,
                    "focus_description": focus_description,
                    "related_cases": focus_data["related_cases"],
                },
                embedding=embedding,
                metadata={
                    "created_at": datetime.now().isoformat(),
                    "vector_type": "dispute_focus",
                },
            )

            vectors.append(vector)
            self.stats["layer2_count"] += 1

        return vectors

    def _vectorize_layer3(
        self, case_id: str, layer3_data: list[dict[str, Any]) -> list[VectorizedData]]:
        """
        向量化L3层(论点层)

        Args:
            case_id: 案号
            layer3_data: L3层数据

        Returns:
            向量化数据列表
        """
        vectors = []

        for argument in layer3_data:
            # 构建文本
            text = self._build_layer3_text(case_id, argument)

            # 生成向量
            embedding = self.bge_m3_loader.encode_single(text, normalize=True)

            # 创建向量化数据
            vector = VectorizedData(
                vector_id=argument["argument_id"],
                layer="L3",
                content={
                    "case_id": case_id,
                    "argument_id": argument["argument_id"],
                    "dispute_focus": argument["dispute_focus"],
                    "legal_articles": argument["legal_articles"],
                    "argument_logic": argument["argument_logic"],
                },
                embedding=embedding,
                metadata={
                    "created_at": datetime.now().isoformat(),
                    "vector_type": "argument",
                    "confidence": argument.get("confidence", 0.8),
                },
            )

            vectors.append(vector)
            self.stats["layer3_count"] += 1

        return vectors

    def _build_layer1_text(
        self, case_id: str, article_name: str, article_data: dict[str, Any]]
    ) -> str:
        """构建L1层文本"""
        text_parts = [
            f"法律条文:{article_name}",
            f"案例:{case_id}",
            f"适用案件数:{len(article_data['related_cases'])}份",
        ]

        return " ".join(text_parts)

    def _build_layer2_text(
        self, case_id: str, focus_description: str, focus_data: dict[str, Any]]
    ) -> str:
        """构建L2层文本"""
        text_parts = [
            f"争议焦点:{focus_description}",
            f"案例:{case_id}",
        ]

        return " ".join(text_parts)

    def _build_layer3_text(self, case_id: str, argument: dict[str, Any]) -> str:
        """构建L3层文本"""
        # 提取法律条文
        legal_articles = " ".join(
            [art["article_name"] for art in argument.get("legal_articles", [])]
        )

        # 提取论证逻辑
        logic = argument.get("argument_logic", {})
        premise = logic.get("premise", "")
        reasoning = logic.get("reasoning", "")
        conclusion = logic.get("conclusion", "")

        text_parts = [
            f"案例:{case_id}",
            f"法律条文:{legal_articles}",
            f"争议焦点:{argument.get('dispute_focus', '')}",
            f"前提:{premise}",
            f"推理:{reasoning}",
            f"结论:{conclusion}",
        ]

        # 过滤空字符串
        text_parts = [p for p in text_parts if p]

        return " ".join(text_parts)

    def save_vectors(self, vectors: list[VectorizedData], output_dir: str) -> bool:
        """
        保存向量化数据到磁盘

        Args:
            vectors: 向量化数据列表
            output_dir: 输出目录

        Returns:
            是否成功
        """
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # 按层级分组保存
            for layer in ["L1", "L2", "L3"]:
                layer_vectors = [v for v in vectors if v.layer == layer]

                if not layer_vectors:
                    continue

                # 保存为pickle格式
                layer_file = output_path / f"{layer}_vectors.pkl"
                with open(layer_file, "ab") as f:  # 追加模式
                    for vec in layer_vectors:
                        pickle.dump(vec, f)

                # 保存元数据为JSON
                meta_file = output_path / f"{layer}_metadata.json"
                metadata_list = []
                for vec in layer_vectors:
                    meta_dict = asdict(vec)
                    # 将numpy数组转换为列表
                    meta_dict["embedding"] = vec.embedding.tolist()
                    metadata_list.append(meta_dict)

                with open(meta_file, "w", encoding="utf-8") as f:
                    json.dump(metadata_list, f, ensure_ascii=False, indent=2)

            logger.info(f"✅ 向量数据已保存到: {output_dir}")
            return True

        except Exception as e:
            logger.error(f"❌ 保存向量数据失败: {e!s}")
            return False

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "total_vectors": self.stats["total_vectors"],
            "layer1_count": self.stats["layer1_count"],
            "layer2_count": self.stats["layer2_count"],
            "layer3_count": self.stats["layer3_count"],
            "processing_time": self.stats["processing_time"],
            "avg_time_per_vector": (
                self.stats["processing_time"] / self.stats["total_vectors"]
                if self.stats["total_vectors"] > 0
                else 0
            ),
        }

    def print_stats(self) -> Any:
        """打印统计信息"""
        stats = self.get_stats()

        logger.info("\n" + "=" * 60)
        logger.info("📊 向量化统计信息")
        logger.info("=" * 60)
        logger.info(f"📦 总向量数: {stats['total_vectors']}")
        logger.info(f"  - L1层(法条): {stats['layer1_count']}")
        logger.info(f"  - L2层(焦点): {stats['layer2_count']}")
        logger.info(f"  - L3层(论点): {stats['layer3_count']}")
        logger.info(f"⏱️  总处理时间: {stats['processing_time']:.2f}秒")
        logger.info(f"📊 平均时间: {stats['avg_time_per_vector']:.3f}秒/向量")
        logger.info("=" * 60 + "\n")


# 便捷函数
def vectorize_judgment(
    structured_data: Optional[dict[str, Any], config: dict[str, Any] = None
) -> list[VectorizedData]:
    """
    向量化判决书

    Args:
        structured_data: 结构化判决书数据
        config: 配置字典

    Returns:
        向量化数据列表
    """
    vectorizer = JudgmentVectorizer(config)
    return vectorizer.vectorize_judgment(structured_data)


if __name__ == "__main__":
    # 测试代码
    # setup_logging()  # 日志配置已移至模块导入

    # 测试向量化
    test_structured_data = {
        "case_info": {
            "case_id": "(2020)最高法知行终197号",
            "court": "最高人民法院",
            "level": "最高法院",
            "case_type": "发明专利权无效行政纠纷",
            "date": "2020-12-15",
        },
        "layer1": {
            "专利法第22条第3款": {
                "article_name": "专利法第22条第3款",
                "related_cases": ["(2020)最高法知行终197号"],
            }
        },
        "layer2": {
            "本专利是否具备创造性?": {
                "focus_description": "本专利是否具备创造性?",
                "related_cases": ["(2020)最高法知行终197号"],
            }
        },
        "layer3": [
            {
                "argument_id": "(2020)最高法知行终197号_001",
                "case_id": "(2020)最高法知行终197号",
                "dispute_focus": "本专利是否具备创造性?",
                "legal_articles": [{"article_name": "专利法第22条第3款", "is_direct_quote": True}],
                "argument_logic": {
                    "premise": "区别特征1是本领域常规技术手段",
                    "reasoning": "对比文献1+2无结合启示",
                    "conclusion": "不具备创造性",
                },
                "confidence": 0.9,
            }
        ],
    }

    # 向量化
    vectorizer = JudgmentVectorizer()
    vectors = vectorizer.vectorize_judgment(test_structured_data)

    # 输出结果
    if vectors:
        print("\n" + "=" * 60)
        print("✅ 向量化成功")
        print("=" * 60)
        print(f"总向量数: {len(vectors)}")
        for vec in vectors:
            print(f"  - {vec.vector_id}: {vec.embedding.shape}")
        print("=" * 60)

        # 打印统计
        vectorizer.print_stats()

