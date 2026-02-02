#!/usr/bin/env python3
"""
ArangoDB多数据库设置脚本
Setup script for ArangoDB multi-database configuration
"""

import asyncio
import json
import logging
from typing import Dict, List, Any
from arango import ArangoClient
from arango.database import StandardDatabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ArangoDBSetup:
    def __init__(self, host: str = "localhost", port: int = 8529,
                 username: str = "root", password: str = "password"):
        self.client = ArangoClient(f"http://{host}:{port}")
        self.username = username
        self.password = password
        self.sys_db = None

    async def connect(self):
        """连接到ArangoDB系统数据库"""
        try:
            # 连接到系统数据库
            self.sys_db = self.client.db(
                "_system",
                username=self.username,
                password=self.password
            )
            logger.info("✅ 成功连接到ArangoDB系统数据库")
            return True
        except Exception as e:
            logger.error(f"❌ 连接失败: {e}")
            return False

    async def create_databases(self):
        """创建业务数据库"""
        databases_config = [
            {
                "name": "patent_graph",
                "description": "专利关系图数据库",
                "collections": {
                    "vertices": [
                        {"name": "patents", "schema": self.get_patent_schema()},
                        {"name": "companies", "schema": self.get_company_schema()},
                        {"name": "inventors", "schema": self.get_inventor_schema()},
                        {"name": "ipc_classes", "schema": self.get_ipc_schema()}
                    ],
                    "edges": [
                        {"name": "cited_by", "from": "patents", "to": "patents"},
                        {"name": "owned_by", "from": "patents", "to": "companies"},
                        {"name": "invented_by", "from": "patents", "to": "inventors"},
                        {"name": "classified_as", "from": "patents", "to": "ipc_classes"}
                    ]
                }
            },
            {
                "name": "knowledge_graph",
                "description": "知识图谱数据库",
                "collections": {
                    "vertices": [
                        {"name": "concepts", "schema": self.get_concept_schema()},
                        {"name": "domains", "schema": self.get_domain_schema()},
                        {"name": "entities", "schema": self.get_entity_schema()}
                    ],
                    "edges": [
                        {"name": "related_to", "from": "concepts", "to": "concepts"},
                        {"name": "belongs_to", "from": "concepts", "to": "domains"},
                        {"name": "is_a", "from": "entities", "to": "concepts"}
                    ]
                }
            },
            {
                "name": "legal_graph",
                "description": "法律关系图数据库",
                "collections": {
                    "vertices": [
                        {"name": "clauses", "schema": self.get_clause_schema()},
                        {"name": "cases", "schema": self.get_case_schema()},
                        {"name": "statutes", "schema": self.get_statute_schema()}
                    ],
                    "edges": [
                        {"name": "refers_to", "from": "clauses", "to": "statutes"},
                        {"name": "cites", "from": "cases", "to": "cases"},
                        {"name": "applies", "from": "cases", "to": "clauses"}
                    ]
                }
            },
            {
                "name": "user_graph",
                "description": "用户关系图数据库",
                "collections": {
                    "vertices": [
                        {"name": "users", "schema": self.get_user_schema()},
                        {"name": "roles", "schema": self.get_role_schema()},
                        {"name": "permissions", "schema": self.get_permission_schema()}
                    ],
                    "edges": [
                        {"name": "has_role", "from": "users", "to": "roles"},
                        {"name": "has_permission", "from": "roles", "to": "permissions"},
                        {"name": "knows", "from": "users", "to": "users"}
                    ]
                }
            }
        ]

        for db_config in databases_config:
            await self.create_database_with_collections(db_config)

    async def create_database_with_collections(self, db_config: Dict[str, Any]):
        """创建数据库及其集合"""
        db_name = db_config["name"]

        # 检查数据库是否已存在
        if self.sys_db.has_database(db_name):
            logger.info(f"⚠️ 数据库 {db_name} 已存在，跳过创建")
            db = self.client.db(db_name, username=self.username, password=self.password)
        else:
            # 创建新数据库
            try:
                self.sys_db.create_database(db_name)
                logger.info(f"✅ 成功创建数据库: {db_name}")
                db = self.client.db(db_name, username=self.username, password=self.password)
            except Exception as e:
                logger.error(f"❌ 创建数据库 {db_name} 失败: {e}")
                return

        # 创建顶点集合
        if "vertices" in db_config["collections"]:
            for collection in db_config["collections"]["vertices"]:
                if not db.has_collection(collection["name"]):
                    db.create_collection(
                        collection["name"],
                        schema=collection.get("schema")
                    )
                    logger.info(f"✅ 创建顶点集合: {collection['name']}")

        # 创建边集合
        if "edges" in db_config["collections"]:
            for edge in db_config["collections"]["edges"]:
                if not db.has_collection(edge["name"]):
                    db.create_collection(
                        edge["name"],
                        edge=True,
                        from_collections=[edge["from"]],
                        to_collections=[edge["to"]]
                    )
                    logger.info(f"✅ 创建边集合: {edge['name']}")

        # 创建索引
        await self.create_indexes(db, db_config["collections"])

    async def create_indexes(self, db: StandardDatabase, collections: Dict[str, Any]):
        """为集合创建索引"""
        # 为patents集合创建索引
        if db.has_collection("patents"):
            patents = db.collection("patents")

            # 创建唯一索引
            if "patent_id" not in patents.indexes():
                patents.add_hash_index(["patent_id"], unique=True)
                logger.info("✅ 创建patent_id唯一索引")

            # 创建复合索引
            if ["title", "abstract"] not in patents.indexes():
                patents.add_hash_index(["title", "abstract"])
                logger.info("✅ 创建title+abstract复合索引")

        # 为其他集合创建类似索引...

    # Schema定义方法
    def get_patent_schema(self) -> Dict[str, Any]:
        """专利文档schema"""
        return {
            "rule": {
                "type": "object",
                "properties": {
                    "patent_id": {"type": "string"},
                    "title": {"type": "string"},
                    "abstract": {"type": "string"},
                    "application_date": {"type": "string"},
                    "publication_date": {"type": "string"},
                    "status": {"type": "string"},
                    "applicants": {"type": "array", "items": {"type": "string"}},
                    "inventors": {"type": "array", "items": {"type": "string"}},
                    "ipc_codes": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["patent_id", "title"]
            }
        }

    def get_company_schema(self) -> Dict[str, Any]:
        """公司schema"""
        return {
            "rule": {
                "type": "object",
                "properties": {
                    "company_id": {"type": "string"},
                    "name": {"type": "string"},
                    "country": {"type": "string"},
                    "industry": {"type": "string"},
                    "founded_year": {"type": "integer"}
                },
                "required": ["company_id", "name"]
            }
        }

    def get_inventor_schema(self) -> Dict[str, Any]:
        """发明人schema"""
        return {
            "rule": {
                "type": "object",
                "properties": {
                    "inventor_id": {"type": "string"},
                    "name": {"type": "string"},
                    "country": {"type": "string"},
                    "patent_count": {"type": "integer"}
                },
                "required": ["inventor_id", "name"]
            }
        }

    def get_ipc_schema(self) -> Dict[str, Any]:
        """IPC分类schema"""
        return {
            "rule": {
                "type": "object",
                "properties": {
                    "ipc_code": {"type": "string"},
                    "description": {"type": "string"},
                    "section": {"type": "string"},
                    "class": {"type": "string"},
                    "subclass": {"type": "string"}
                },
                "required": ["ipc_code"]
            }
        }

    # 其他schema定义...
    def get_concept_schema(self) -> Dict[str, Any]:
        return {"rule": {"type": "object", "properties": {"concept_id": {"type": "string"}, "name": {"type": "string"}}}}

    def get_domain_schema(self) -> Dict[str, Any]:
        return {"rule": {"type": "object", "properties": {"domain_id": {"type": "string"}, "name": {"type": "string"}}}}

    def get_entity_schema(self) -> Dict[str, Any]:
        return {"rule": {"type": "object", "properties": {"entity_id": {"type": "string"}, "name": {"type": "string"}}}}

    def get_clause_schema(self) -> Dict[str, Any]:
        return {"rule": {"type": "object", "properties": {"clause_id": {"type": "string"}, "content": {"type": "string"}}}}

    def get_case_schema(self) -> Dict[str, Any]:
        return {"rule": {"type": "object", "properties": {"case_id": {"type": "string"}, "title": {"type": "string"}}}}

    def get_statute_schema(self) -> Dict[str, Any]:
        return {"rule": {"type": "object", "properties": {"statute_id": {"type": "string"}, "title": {"type": "string"}}}}

    def get_user_schema(self) -> Dict[str, Any]:
        return {"rule": {"type": "object", "properties": {"user_id": {"type": "string"}, "username": {"type": "string"}}}}

    def get_role_schema(self) -> Dict[str, Any]:
        return {"rule": {"type": "object", "properties": {"role_id": {"type": "string"}, "name": {"type": "string"}}}}

    def get_permission_schema(self) -> Dict[str, Any]:
        return {"rule": {"type": "object", "properties": {"permission_id": {"type": "string"}, "name": {"type": "string"}}}}

    async def setup_users(self):
        """设置数据库用户和权限"""
        # 创建应用用户
        users = [
            {
                "username": "patent_user",
                "password": "patent_pass_123",
                "databases": ["patent_graph"]
            },
            {
                "username": "kb_user",
                "password": "kb_pass_123",
                "databases": ["knowledge_graph"]
            },
            {
                "username": "legal_user",
                "password": "legal_pass_123",
                "databases": ["legal_graph"]
            },
            {
                "username": "app_user",
                "password": "app_pass_123",
                "databases": ["patent_graph", "knowledge_graph", "legal_graph", "user_graph"]
            }
        ]

        for user_config in users:
            try:
                if not self.sys_db.has_user(user_config["username"]):
                    self.sys_db.create_user(
                        user_config["username"],
                        user_config["password"],
                        active=True
                    )
                    logger.info(f"✅ 创建用户: {user_config['username']}")

                # 授予数据库权限
                for db_name in user_config["databases"]:
                    if self.sys_db.has_database(db_name):
                        db = self.client.db(db_name, username=self.username, password=self.password)
                        if not db.has_user(user_config["username"]):
                            db.grant_access(user_config["username"], "rw")
                            logger.info(f"✅ 授予 {user_config['username']} 对 {db_name} 的读写权限")
            except Exception as e:
                logger.error(f"❌ 设置用户 {user_config['username']} 失败: {e}")

    async def verify_setup(self):
        """验证设置是否成功"""
        logger.info("\n🔍 验证ArangoDB设置...")

        databases = self.sys_db.databases()
        expected_dbs = ["patent_graph", "knowledge_graph", "legal_graph", "user_graph"]

        for db_name in expected_dbs:
            if db_name in databases:
                db = self.client.db(db_name, username=self.username, password=self.password)
                collections = db.collections()
                logger.info(f"✅ 数据库 {db_name}: {len(collections)} 个集合")

                # 列出集合
                for collection in collections:
                    logger.info(f"   - {collection['name']}")
            else:
                logger.error(f"❌ 数据库 {db_name} 未找到")


async def main():
    """主函数"""
    setup = ArangoDBSetup(
        host="localhost",
        port=8529,
        username="root",
        password="your_password"  # 从环境变量读取
    )

    if await setup.connect():
        await setup.create_databases()
        await setup.setup_users()
        await setup.verify_setup()
        logger.info("\n🎉 ArangoDB设置完成！")
    else:
        logger.error("❌ 设置失败，请检查连接信息")


if __name__ == "__main__":
    asyncio.run(main())