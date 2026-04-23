#!/usr/bin/env python3
from __future__ import annotations
"""
知识图谱导入模块
Knowledge Graph Importer

将处理好的法律知识导入到NebulaGraph图数据库

作者: Athena AI系统
创建时间: 2025-01-06
版本: 1.0.0
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from nebula3.Config import Config

# NebulaGraph客户端
from nebula3.gclient.net import ConnectionPool

from core.config.secure_config import get_config

config = get_config()


logger = logging.getLogger(__name__)


class KnowledgeGraphImporter:
    """知识图谱导入器"""

    def __init__(self, config: Optional[dict[str, Any]] = None):
        """
        初始化导入器

        Args:
            config: 配置字典,包含:
                - nebula_hosts: NebulaGraph主机列表
                - nebula_port: NebulaGraph端口
                - space_name: 图空间名称
                - username: 用户名
                - password: 密码
        """
        self.config = config or {}
        self.nebula_hosts = self.config.get("nebula_hosts", ["127.0.0.1"])
        self.nebula_port = self.config.get("nebula_port", 9669)
        self.space_name = self.config.get("space_name", "legal_books")
        self.username = self.config.get("username", "root")
        self.password = self.config.get("password", config.get("NEBULA_PASSWORD", required=True))

        # 初始化NebulaGraph连接池
        self.connection_pool = None
        self.session = None

        logger.info("🕸️ 知识图谱导入器初始化完成")

    async def connect(self):
        """连接到NebulaGraph"""
        try:
            config = Config()
            config.max_connection_pool_size = 10

            self.connection_pool = ConnectionPool()
            await self.connection_pool.init(
                self.nebula_hosts, self.nebula_port, self.username, self.password, config
            )

            # 获取会话
            self.session = self.connection_pool.get_session(self.space_name)

            logger.info(f"✅ 成功连接到NebulaGraph: {self.space_name}")

        except Exception as e:
            logger.error(f"❌ 连接NebulaGraph失败: {e}")
            raise

    async def close(self):
        """关闭连接"""
        if self.session:
            self.session.release()
        if self.connection_pool:
            await self.connection_pool.close()
        logger.info("🔌 NebulaGraph连接已关闭")

    async def import_knowledge_graph(self, graph_data: dict[str, Any]) -> dict[str, Any]:
        """
        导入知识图谱

        Args:
            graph_data: 图谱数据,包含nodes和relations

        Returns:
            导入结果
        """
        logger.info("🕸️ 开始导入知识图谱到NebulaGraph")

        # 连接数据库
        await self.connect()

        try:
            # 确保图空间存在
            await self._ensure_space_exists()

            # 创建数据模型(标签和边类型)
            await self._create_schema()

            # 导入节点
            nodes_result = await self._import_nodes(graph_data["nodes"])

            # 导入关系
            relations_result = await self._import_relations(graph_data["relations"])

            logger.info("✅ 知识图谱导入完成")

            return {
                "status": "success",
                "nodes_imported": nodes_result["success_count"],
                "relations_imported": relations_result["success_count"],
                "nodes_failed": nodes_result["failed_count"],
                "relations_failed": relations_result["failed_count"],
                "space_name": self.space_name,
            }

        except Exception as e:
            logger.error(f"❌ 导入失败: {e}")
            raise

        finally:
            await self.close()

    async def _ensure_space_exists(self):
        """确保图空间存在"""
        try:
            # 检查图空间是否存在
            check_query = "SHOW SPACES;"
            result = self.session.execute(check_query)

            space_exists = False
            if result.is_succeeded():
                for record in result:
                    space_name = record.values[0].as_string()
                    if space_name == self.space_name:
                        space_exists = True
                        break

            if not space_exists:
                logger.info(f"📦 创建新图空间: {self.space_name}")
                create_query = f"""
                CREATE SPACE IF NOT EXISTS {self.space_name} (
                    partition_num = 10,
                    replica_factor = 1,
                    vid_type = FIXED_STRING(32)
                );
                """
                result = self.session.execute(create_query)

                if result.is_succeeded():
                    logger.info(f"✅ 图空间 {self.space_name} 创建成功")
                    # 等待空间生效
                    await asyncio.sleep(10)
                else:
                    raise Exception(f"创建图空间失败: {result.error_msg()}")
            else:
                logger.info(f"📦 图空间 {self.space_name} 已存在")

            # 使用图空间
            use_query = f"USE {self.space_name};"
            self.session.execute(use_query)

        except Exception as e:
            logger.error(f"❌ 图空间操作失败: {e}")
            raise

    async def _create_schema(self):
        """创建数据模型(标签和边类型)"""
        logger.info("📐 创建数据模型")

        # 创建标签(Tag)
        tags = {
            "Book": "name string, category string, publisher string, year string",
            "Case": "source string, extracted_at string",
            "LegalRule": "name string, article_number string, law string, source string",
            "Concept": "name string, definition string",
            "Procedure": "name string, description string",
            "Criterion": "name string, description string",
        }

        for tag_name, props in tags.items():
            create_tag_query = f"""
            CREATE TAG IF NOT EXISTS {tag_name} (
                {props}
            );
            """
            result = self.session.execute(create_tag_query)
            if result.is_succeeded():
                logger.info(f"✅ 创建标签: {tag_name}")
            else:
                logger.warning(f"⚠️ 创建标签失败: {tag_name} - {result.error_msg()}")

        # 创建边类型(Edge Type)
        edges = {
            "BELONGS_TO": "",
            "REFERENCES": "context string",
            "DEFINES": "",
            "CONTAINS": "",
            "SUPERSEDES": "",
            "PREREQUISITE": "",
            "EXAMPLES": "",
            "EXCEPTION": "",
        }

        for edge_name, props in edges.items():
            create_edge_query = f"""
            CREATE EDGE IF NOT EXISTS {edge_name} (
                {props}
            );
            """
            result = self.session.execute(create_edge_query)
            if result.is_succeeded():
                logger.info(f"✅ 创建边类型: {edge_name}")
            else:
                logger.warning(f"⚠️ 创建边类型失败: {edge_name} - {result.error_msg()}")

        # 等待schema生效
        await asyncio.sleep(5)

    async def _import_nodes(self, nodes: list[dict[str, Any]]) -> dict[str, Any]:
        """
        导入节点

        Args:
            nodes: 节点列表

        Returns:
            导入结果
        """
        success_count = 0
        failed_count = 0
        errors = []

        for node in nodes:
            try:
                vertex_id = node["id"]
                tag = node["type"]
                properties = node.get("properties", {})

                # 构建INSERT语句
                props_str = ", ".join(
                    [
                        f"{k}: '{v}'" if isinstance(v, str) else f"{k}: {v}"
                        for k, v in properties.items()
                    ]
                )

                insert_query = f"""
                INSERT VERTEX {tag} ({", ".join(properties.keys())})
                VALUES "{vertex_id}": ({props_str});
                """

                result = self.session.execute(insert_query)

                if result.is_succeeded():
                    success_count += 1
                else:
                    failed_count += 1
                    error_msg = f"节点 {vertex_id} 导入失败: {result.error_msg()}"
                    errors.append(error_msg)
                    logger.warning(error_msg)

            except Exception as e:
                failed_count += 1
                error_msg = f"节点 {node.get('id')} 处理异常: {e!s}"
                errors.append(error_msg)
                logger.error(error_msg)

        logger.info(f"📊 节点导入完成: 成功 {success_count}, 失败 {failed_count}")

        return {"success_count": success_count, "failed_count": failed_count, "errors": errors}

    async def _import_relations(self, relations: list[dict[str, Any]]) -> dict[str, Any]:
        """
        导入关系

        Args:
            relations: 关系列表

        Returns:
            导入结果
        """
        success_count = 0
        failed_count = 0
        errors = []

        for relation in relations:
            try:
                source_id = relation["source"]
                target_id = relation["target"]
                edge_type = relation["type"]
                properties = relation.get("properties", {})

                # 构建INSERT语句
                if properties:
                    props_str = ", ".join(
                        [
                            f"{k}: '{v}'" if isinstance(v, str) else f"{k}: {v}"
                            for k, v in properties.items()
                        ]
                    )

                insert_query = f"""
                INSERT EDGE {edge_type} {f"({', '.join(properties.keys())})" if properties else ""}
                VALUES "{source_id}"->"{target_id}": {f"({props_str})" if properties else "()"};
                """

                result = self.session.execute(insert_query)

                if result.is_succeeded():
                    success_count += 1
                else:
                    failed_count += 1
                    error_msg = f"关系 {source_id}->{target_id} 导入失败: {result.error_msg()}"
                    errors.append(error_msg)
                    logger.warning(error_msg)

            except Exception as e:
                failed_count += 1
                error_msg = (
                    f"关系 {relation.get('source')}->{relation.get('target')} 处理异常: {e!s}"
                )
                errors.append(error_msg)
                logger.error(error_msg)

        logger.info(f"📊 关系导入完成: 成功 {success_count}, 失败 {failed_count}")

        return {"success_count": success_count, "failed_count": failed_count, "errors": errors}

    async def query_graph(self, query: str) -> list[dict[str, Any]]:
        """
        执行图查询

        Args:
            query: nGQL查询语句

        Returns:
            查询结果
        """
        if not self.session:
            await self.connect()

        result = self.session.execute(query)

        if not result.is_succeeded():
            raise Exception(f"查询失败: {result.error_msg()}")

        # 格式化结果
        results = []
        for record in result:
            row = {}
            for i, value in enumerate(record.values):
                row[f"col_{i}"] = value.as_string()
            results.append(row)

        return results


async def main():
    """测试知识图谱导入"""
    # 读取之前生成的图谱数据
    graph_data_file = Path("./data/legal_books/yianshuofa/knowledge_graph_20250106_xxxxxx.json")

    if not graph_data_file.exists():
        print("❌ 知识图谱文件不存在,请先运行 legal_book_pipeline.py")
        return

    with open(graph_data_file, encoding="utf-8") as f:
        graph_data = json.load(f)

    # 配置导入器
    config = {
        "nebula_hosts": ["127.0.0.1"],
        "nebula_port": 9669,
        "space_name": "legal_books_yianshuofa",
        "username": "root",
        "password": config.get("NEBULA_PASSWORD", required=True),
    }

    # 创建并执行导入
    importer = KnowledgeGraphImporter(config)
    result = await importer.import_knowledge_graph(graph_data)

    print("\n" + "=" * 50)
    print("🕸️ 知识图谱导入完成!")
    print("=" * 50)
    print(json.dumps(result, ensure_ascii=False, indent=2))


# 入口点: @async_main装饰器已添加到main函数
