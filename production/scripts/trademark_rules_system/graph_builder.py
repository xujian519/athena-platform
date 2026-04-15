#!/usr/bin/env python3
"""
NebulaGraph知识图谱构建
NebulaGraph Knowledge Graph Builder for Trademark Rules

构建商标规则知识图谱

作者: Athena AI系统
创建时间: 2025-01-15
"""

from __future__ import annotations
import asyncio
import hashlib
import logging
from typing import Any

from tqdm import tqdm

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TrademarkGraphBuilder:
    """商标规则知识图谱构建器"""

    def __init__(self, nebula_session, config: dict[str, Any] | None = None):
        """
        初始化图构建器

        Args:
            nebula_session: NebulaGraph会话
            config: 配置字典
        """
        self.session = nebula_session
        self.config = config or {}
        self.space_name = self.config.get('space_name', 'trademark_graph')

        # 统计信息
        self.stats = {
            'total_nodes': 0,
            'total_edges': 0,
            'created_nodes': 0,
            'created_edges': 0
        }

    def _generate_vid(self, content: str, prefix: str = "node") -> str:
        """
        生成顶点ID

        Args:
            content: 内容
            prefix: 前缀

        Returns:
            顶点ID
        """
        hash_value = hashlib.md5(content.encode('utf-8'), usedforsecurity=False).hexdigest()
        return f"{prefix}_{hash_value}"

    async def create_schema(self) -> bool:
        """
        创建图模式

        Returns:
            是否成功
        """
        try:
            # 使用空间
            use_space_sql = f"USE {self.space_name};"

            # 创建标签类型
            tags = [
                # 商标法规标签
                "CREATE TAG IF NOT EXISTS trademark_norm(name string, document_type string, issuing_authority string, status string);",

                # 商标条款标签
                "CREATE TAG IF NOT EXISTS trademark_article(article_number string, content string, chapter string);",

                # 商标概念标签
                "CREATE TAG IF NOT EXISTS trademark_concept(name string, category string, description string);",

                # 法律概念标签
                "CREATE TAG IF NOT EXISTS legal_concept(name string, type string);"
            ]

            # 创建边类型
            edges = [
                # 法规包含条款
                "CREATE EDGE IF NOT EXISTS has_article(order int);",

                # 条款引用概念
                "CREATE EDGE IF NOT EXISTS refers_to();",

                # 法规定义概念
                "CREATE EDGE IF NOT EXISTS defines();",

                # 概念相关
                "CREATE EDGE IF NOT EXISTS relates_to(relation_type string);"
            ]

            # 执行创建
            self.session.execute(use_space_sql)

            for tag_sql in tags:
                try:
                    result = self.session.execute(tag_sql)
                    logger.info("✅ 创建标签成功")
                except Exception as e:
                    if "already exists" not in str(e):
                        logger.warning(f"⚠️  创建标签警告: {e}")

            for edge_sql in edges:
                try:
                    result = self.session.execute(edge_sql)
                    logger.info("✅ 创建边成功")
                except Exception as e:
                    if "already exists" not in str(e):
                        logger.warning(f"⚠️  创建边警告: {e}")

            logger.info("✅ 知识图谱模式创建完成")
            return True

        except Exception as e:
            logger.error(f"❌ 创建模式失败: {e}")
            return False

    async def insert_norm_node(self, norm_data: dict[str, Any]) -> str | None:
        """
        插入法规节点

        Args:
            norm_data: 法规数据

        Returns:
            节点ID
        """
        try:
            vid = self._generate_vid(norm_data['id'], "norm")

            # 使用空间
            self.session.execute(f"USE {self.space_name};")

            # 插入顶点
            insert_sql = f'''
                INSERT VERTEX trademark_norm(name, document_type, issuing_authority, status)
                VALUES "{vid}", "{norm_data['name']}", "{norm_data.get('document_type', '')}", "{norm_data.get('status', '现行有效')}"
            '''

            result = self.session.execute(insert_sql)

            self.stats['created_nodes'] += 1
            return vid

        except Exception as e:
            logger.error(f"❌ 插入法规节点失败: {e}")
            return None

    async def insert_article_nodes_batch(
        self,
        articles: list[dict[str, Any]],
        norm_id: str
    ) -> list[str]:
        """
        批量插入条款节点

        Args:
            articles: 条款列表
            norm_id: 法规ID

        Returns:
            节点ID列表
        """
        node_ids = []

        try:
            self.session.execute(f"USE {self.space_name};")

            for article in tqdm(articles, desc="插入条款节点"):
                vid = self._generate_vid(f"{norm_id}_{article['article_number']}", "article")

                insert_sql = f'''
                    INSERT VERTEX trademark_article(article_number, content, chapter)
                    VALUES "{vid}", "{article['article_number']}", "{article.get('original_text', '')[:200]}", "{article.get('chapter_name', '')}"
                '''

                try:
                    result = self.session.execute(insert_sql)
                    node_ids.append(vid)
                    self.stats['created_nodes'] += 1

                    # 创建法规-条款边
                    await self._create_has_article_edge(norm_id, vid, article.get('order', 0))

                except Exception as e:
                    logger.error(f"❌ 插入条款节点失败: {e}")

        except Exception as e:
            logger.error(f"❌ 批量插入失败: {e}")

        return node_ids

    async def _create_has_article_edge(self, norm_vid: str, article_vid: str, order: int = 0):
        """
        创建法规-条款边

        Args:
            norm_vid: 法规节点ID
            article_vid: 条款节点ID
            order: 顺序
        """
        try:
            self.session.execute(f"USE {self.space_name};")

            edge_sql = f'''
                INSERT EDGE has_article(order)
                VALUES "{norm_vid}" -> "{article_vid}" ({order})
            '''

            result = self.session.execute(edge_sql)
            self.stats['created_edges'] += 1

        except Exception as e:
            logger.error(f"❌ 创建边失败: {e}")

    async def extract_and_insert_concepts(
        self,
        articles: list[dict[str, Any]],
        min_frequency: int = 3
    ) -> dict[str, int]:
        """
        提取并插入概念节点

        Args:
            articles: 条款列表
            min_frequency: 最小出现频率

        Returns:
            概念统计
        """
        import re

        # 简单概念提取（实际应该使用NLP）
        concept_patterns = [
            r'商标[^\s，。]{1,10}',
            r'注册[^\s，。]{1,10}',
            r'申请人[^\s，。]{1,10}',
            r'异议[^\s，。]{1,10}',
            r'无效[^\s，。]{1,10}',
            r'撤销[^\s，。]{1,10}',
            r'审查[^\s，。]{1,10}',
            r'决定[^\s，。]{1,10}'
        ]

        concept_count = {}

        # 统计概念频率
        for article in articles:
            text = article.get('original_text', '')
            for pattern in concept_patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    concept_count[match] = concept_count.get(match, 0) + 1

        # 过滤低频概念
        frequent_concepts = {
            k: v for k, v in concept_count.items()
            if v >= min_frequency
        }

        # 插入概念节点
        self.session.execute(f"USE {self.space_name};")

        for concept, count in tqdm(frequent_concepts.items(), desc="插入概念节点"):
            vid = self._generate_vid(concept, "concept")

            insert_sql = f'''
                INSERT VERTEX trademark_concept(name, category, description)
                VALUES "{vid}", "{concept}", "商标概念", "出现频率: {count}"
            '''

            try:
                result = self.session.execute(insert_sql)
                self.stats['created_nodes'] += 1
            except Exception as e:
                logger.warning(f"⚠️  插入概念节点警告: {e}")

        return frequent_concepts

    async def query_norm_by_type(self, document_type: str) -> list[dict[str, Any]]:
        """
        按类型查询法规

        Args:
            document_type: 文档类型

        Returns:
            查询结果
        """
        try:
            self.session.execute(f"USE {self.space_name};")

            query_sql = f'''
                MATCH (n:trademark_norm)
                WHERE n.document_type == "{document_type}"
                RETURN n
            '''

            result = self.session.execute(query_sql)
            return result

        except Exception as e:
            logger.error(f"❌ 查询失败: {e}")
            return []

    async def get_stats(self) -> dict[str, Any]:
        """
        获取图谱统计信息

        Returns:
            统计信息
        """
        try:
            self.session.execute(f"USE {self.space_name};")

            # 统计各类型节点数量
            stats = {}

            tag_types = ['trademark_norm', 'trademark_article', 'trademark_concept']

            for tag in tag_types:
                count_sql = f'''
                    MATCH (n:{tag})
                    RETURN COUNT(*)
                '''

                try:
                    result = self.session.execute(count_sql)
                    stats[tag] = result
                except Exception as e:
                    logger.debug(f"空except块已触发: {e}")
                    stats[tag] = 0

            return stats

        except Exception as e:
            logger.error(f"❌ 获取统计失败: {e}")
            return {}


async def main():
    """测试知识图谱构建"""
    logger.info("🧪 知识图谱构建模块已就绪")


if __name__ == "__main__":
    asyncio.run(main())
