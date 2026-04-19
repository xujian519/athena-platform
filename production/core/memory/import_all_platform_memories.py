#!/usr/bin/env python3
from __future__ import annotations
"""
Athena平台全智能体记忆导入工具
Import All Platform Agent Memories to Unified Memory System

扫描并导入平台所有智能体的记忆数据到统一记忆系统
"""

import json
import sqlite3
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import asyncpg

from core.logging_config import setup_logging

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent.parent))

# 配置日志
logger = setup_logging()


class PlatformMemoryImporter:
    """平台记忆导入器"""

    def __init__(self):
        self.project_root = Path("/Users/xujian/Athena工作平台")
        self.data_dir = self.project_root / "data"

        # 数据库配置
        self.db_config = {
            "host": "localhost",
            "port": 5432,
            "database": "athena_memory",
            "user": "postgres",
            "password": "",
        }

        # 智能体映射
        self.agent_mapping = {
            "xiaonuo": {
                "agent_id": "xiaonuo_pisces",
                "agent_type": "xiaonuo",
                "name": "小诺·双鱼座",
                "family_related": True,
            },
            "xiaona": {
                "agent_id": "xiaona_libra",
                "agent_type": "xiaona",
                "name": "小娜·天秤女神",
                "family_related": True,
            },
            "athena": {
                "agent_id": "athena_wisdom",
                "agent_type": "athena",
                "name": "Athena.智慧女神",
                "family_related": False,
            },
            "xiaochen": {
                "agent_id": "xiaochen_sagittarius",
                "agent_type": "xiaochen",
                "name": "小宸·星河射手",
                "family_related": False,
            },
        }

        # 导入统计
        self.import_stats = {
            "total_processed": 0,
            "total_imported": 0,
            "total_skipped": 0,
            "total_errors": 0,
            "by_source": {},
            "by_agent": {},
        }

    async def import_all_memories(self):
        """导入所有记忆"""
        logger.info("🚀 开始导入平台所有智能体记忆...")
        logger.info(f"📂 项目路径: {self.project_root}")

        # 连接数据库
        conn = await asyncpg.connect(**self.db_config)
        logger.info("✅ 数据库连接成功")

        try:
            await self.import_sqlite_long_term_memories(conn)

            # 2. 导入永恒记忆JSON文件
            await self.import_eternal_memory_files(conn)

            # 3. 导入家庭记忆
            await self.import_family_memories(conn)

            # 4. 导入JSON索引记忆
            await self.import_json_index_memories(conn)

            # 5. 显示导入统计
            self.display_import_summary()

        finally:
            await conn.close()
            logger.info("✅ 数据库连接已关闭")

    async def import_sqlite_long_term_memories(self, conn):
        """导入SQLite长期记忆"""
        logger.info("═══════════════════════════════════")
        logger.info("📊 导入SQLite长期记忆")
        logger.info("═══════════════════════════════════")

        db_path = self.data_dir / "memory" / "long_term_memory.db"
        if not db_path.exists():
            logger.warning(f"⚠️ SQLite数据库不存在: {db_path}")
            return

        try:
            sqlite_conn = sqlite3.connect(db_path)
            sqlite_conn.row_factory = sqlite3.Row
            cursor = sqlite_conn.cursor()

            # 查询所有记忆
            cursor.execute("SELECT * FROM long_term_memories")
            rows = cursor.fetchall()

            logger.info(f"📦 找到 {len(rows)} 条长期记忆")

            for row in rows:
                await self.import_sqlite_memory(conn, dict(row))

            sqlite_conn.close()
            logger.info("✅ SQLite长期记忆导入完成")

        except Exception as e:
            logger.error(f"操作失败: {e}", exc_info=True)
            raise

    async def import_sqlite_memory(self, conn, memory: dict[str, Any]):
        """导入单条SQLite记忆"""
        try:
            # 提取user_id
            user_id = memory.get("user_id", "xiaonuo")

            # 映射用户ID到智能体
            agent_info = self.map_user_to_agent(user_id)
            if not agent_info:
                logger.warning(f"⚠️ 无法映射用户ID: {user_id}")
                self.import_stats["total_skipped"] += 1
                return

            # 确定记忆类型和层级
            memory_type = self.map_memory_type(memory.get("memory_type", "conversation"))
            memory_tier = self.determine_memory_tier(memory)

            # 生成内容
            content = memory.get("content", "")
            if not content:
                self.import_stats["total_skipped"] += 1
                return

            # 插入数据库
            await conn.execute(
                """
                INSERT INTO agent_memories (
                    memory_id,
                    agent_id,
                    agent_type,
                    content,
                    memory_type,
                    memory_tier,
                    importance,
                    access_count,
                    last_accessed,
                    created_at,
                    family_related,
                    work_related,
                    tags,
                    metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                ON CONFLICT (memory_id) DO NOTHING
            """,
                str(uuid.uuid4()),
                agent_info["agent_id"],
                agent_info["agent_type"],
                content[:5000],  # 限制内容长度
                memory_type,
                memory_tier,
                float(memory.get("importance", 0.5)),
                int(memory.get("access_count", 0)),
                (
                    datetime.fromtimestamp(memory.get("last_accessed", 0))
                    if memory.get("last_accessed")
                    else None
                ),
                (
                    datetime.fromtimestamp(memory.get("created_at", 0))
                    if memory.get("created_at")
                    else datetime.now()
                ),
                agent_info["family_related"],
                not agent_info["family_related"],
                [user_id, "sqlite_import"],
                json.dumps(
                    {"source": "sqlite_long_term", "original_id": memory.get("memory_id")},
                    ensure_ascii=False,
                ),
            )

            self.import_stats["total_imported"] += 1
            self.import_stats["total_processed"] += 1

            # 更新统计
            source = "sqlite"
            self.import_stats["by_source"][source] = (
                self.import_stats["by_source"].get(source, 0) + 1
            )
            agent = agent_info["name"]
            self.import_stats["by_agent"][agent] = self.import_stats["by_agent"].get(agent, 0) + 1

        except Exception as e:
            logger.error(f"操作失败: {e}", exc_info=True)
            raise

    async def import_eternal_memory_files(self, conn):
        """导入永恒记忆JSON文件"""
        logger.info("═══════════════════════════════════")
        logger.info("💎 导入永恒记忆JSON文件")
        logger.info("═══════════════════════════════════")

        eternal_dir = self.data_dir / "eternal_memories"
        if not eternal_dir.exists():
            logger.warning(f"⚠️ 永恒记忆目录不存在: {eternal_dir}")
            return

        json_files = list(eternal_dir.glob("*.json"))
        logger.info(f"📦 找到 {len(json_files)} 个永恒记忆文件")

        for json_file in json_files:
            try:
                with open(json_file, encoding="utf-8") as f:
                    memory_data = json.load(f)

                await self.import_json_memory(conn, memory_data, json_file.name, "eternal")

            except Exception as e:
                logger.error(f"操作失败: {e}", exc_info=True)
                raise

        logger.info("✅ 永恒记忆文件导入完成")

    async def import_family_memories(self, conn):
        """导入家庭记忆"""
        logger.info("═══════════════════════════════════")
        logger.info("👨‍👩‍👧‍👦 导入家庭记忆")
        logger.info("═══════════════════════════════════")

        family_dir = self.data_dir / "family"
        if not family_dir.exists():
            logger.warning(f"⚠️ 家庭记忆目录不存在: {family_dir}")
            return

        # 递归查找所有JSON文件
        json_files = list(family_dir.rglob("*.json"))
        logger.info(f"📦 找到 {len(json_files)} 个家庭记忆文件")

        for json_file in json_files:
            try:
                with open(json_file, encoding="utf-8") as f:
                    memory_data = json.load(f)

                await self.import_json_memory(conn, memory_data, json_file.name, "family")

            except Exception as e:
                logger.error(f"操作失败: {e}", exc_info=True)
                raise

        logger.info("✅ 家庭记忆导入完成")

    async def import_json_index_memories(self, conn):
        """导入JSON索引记忆"""
        logger.info("═══════════════════════════════════")
        logger.info("📋 导入JSON索引记忆")
        logger.info("═══════════════════════════════════")

        memory_storage_dir = self.data_dir / "memory_storage"
        if not memory_storage_dir.exists():
            logger.warning(f"⚠️ 记忆存储目录不存在: {memory_storage_dir}")
            return

        # 查找所有JSON索引文件
        index_files = list(memory_storage_dir.rglob("memory_index.json"))
        logger.info(f"📦 找到 {len(index_files)} 个索引文件")

        for index_file in index_files:
            try:
                with open(index_file, encoding="utf-8") as f:
                    index_data = json.load(f)

                # 处理索引中的记忆列表
                if "memories" in index_data:
                    for memory in index_data["memories"]:
                        await self.import_json_memory(
                            conn,
                            memory,
                            f"{index_file.parent.name}/{memory.get('memory_id', 'unknown')}",
                            "index",
                        )

            except Exception as e:
                logger.error(f"操作失败: {e}", exc_info=True)
                raise

        logger.info("✅ JSON索引记忆导入完成")

    async def import_json_memory(
        self, conn, memory: dict[str, Any], source_name: str, source_type: str
    ):
        """导入JSON记忆"""
        try:
            content = self.extract_content_from_json(memory)
            if not content or len(content) < 10:
                self.import_stats["total_skipped"] += 1
                return

            # 确定智能体
            agent_info = self.determine_agent_from_memory(memory, source_name)
            if not agent_info:
                self.import_stats["total_skipped"] += 1
                return

            # 确定记忆类型和层级
            memory_type = self.determine_memory_type_from_json(memory)
            memory_tier = "eternal" if source_type == "eternal" else "warm"

            # 提取标签
            tags = self.extract_tags_from_json(memory, source_type)

            # 提取重要性
            importance = self.extract_importance_from_json(memory)

            # 插入数据库
            await conn.execute(
                """
                INSERT INTO agent_memories (
                    memory_id,
                    agent_id,
                    agent_type,
                    content,
                    memory_type,
                    memory_tier,
                    importance,
                    access_count,
                    last_accessed,
                    created_at,
                    family_related,
                    work_related,
                    tags,
                    metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                ON CONFLICT (memory_id) DO NOTHING
            """,
                str(uuid.uuid4()),
                agent_info["agent_id"],
                agent_info["agent_type"],
                str(content)[:10000],  # 限制内容长度
                memory_type,
                memory_tier,
                importance,
                0,
                datetime.now(),
                datetime.now(),
                agent_info["family_related"],
                not agent_info["family_related"],
                tags,
                json.dumps(
                    {"source": source_type, "source_file": source_name, "original_data": memory},
                    ensure_ascii=False,
                ),
            )

            self.import_stats["total_imported"] += 1
            self.import_stats["total_processed"] += 1

            # 更新统计
            self.import_stats["by_source"][source_type] = (
                self.import_stats["by_source"].get(source_type, 0) + 1
            )
            agent = agent_info["name"]
            self.import_stats["by_agent"][agent] = self.import_stats["by_agent"].get(agent, 0) + 1

        except Exception as e:
            logger.error(f"操作失败: {e}", exc_info=True)
            raise

    def extract_content_from_json(self, memory: dict[str, Any]) -> str:
        """从JSON提取内容"""
        # 尝试多个字段
        for field in ["content", "message", "description", "title", "event"]:
            if memory.get(field):
                content = memory[field]
                if isinstance(content, str):
                    return content
                elif isinstance(content, dict):
                    return json.dumps(content, ensure_ascii=False)

        return ""

    def determine_agent_from_memory(
        self, memory: dict[str, Any], source_name: str
    ) -> dict[str, Any] | None:
        """从记忆确定智能体"""
        # 检查participants字段
        if "participants" in memory:
            participants = memory["participants"]
            creator = participants.get("creator", "") if isinstance(participants, dict) else ""

            if "xiaonuo" in creator.lower() or "小诺" in creator:
                return self.agent_mapping["xiaonuo"]
            elif "xiaona" in creator.lower() or "小娜" in creator:
                return self.agent_mapping["xiaona"]

        # 检查文件名
        if "xiaonuo" in source_name.lower():
            return self.agent_mapping["xiaonuo"]
        elif "xiaona" in source_name.lower():
            return self.agent_mapping["xiaona"]

        # 默认返回小诺
        return self.agent_mapping["xiaonuo"]

    def determine_memory_type_from_json(self, memory: dict[str, Any]) -> str:
        """从JSON确定记忆类型"""
        # 检查event_type
        if "event_type" in memory:
            event_type = memory["event_type"]
            if "family" in event_type or "greeting" in event_type:
                return "family"
            elif "work" in event_type or "experiment" in event_type:
                return "professional"

        # 检查category
        if "category" in memory:
            category = memory["category"]
            if "family" in category:
                return "family"
            elif "system" in category:
                return "knowledge"

        return "conversation"

    def extract_tags_from_json(self, memory: dict[str, Any], source_type: str) -> list[str]:
        """从JSON提取标签"""
        tags = [source_type]

        # 添加现有的tags
        if "tags" in memory and isinstance(memory["tags"], list):
            tags.extend(memory["tags"][:10])  # 限制标签数量

        # 添加event_type作为标签
        if "event_type" in memory:
            tags.append(memory["event_type"])

        # 添加category作为标签
        if "category" in memory:
            tags.append(memory["category"])

        # 添加wishes作为标签
        if "wishes" in memory and isinstance(memory["wishes"], list):
            tags.extend([f"愿望:{w}" for w in memory["wishes"][:5]])

        return list(set(tags))  # 去重

    def extract_importance_from_json(self, memory: dict[str, Any]) -> float:
        """从JSON提取重要性"""
        # 检查priority字段
        if "priority" in memory:
            priority = memory["priority"]
            if priority == "high":
                return 1.0
            elif priority == "medium":
                return 0.7
            elif priority == "low":
                return 0.4

        # 检查importance字段
        if "importance" in memory:
            return float(memory["importance"])

        # 根据source_type确定
        return 0.8  # 默认较高重要性

    def map_user_to_agent(self, user_id: str) -> dict[str, Any] | None:
        """映射用户ID到智能体"""
        user_id_lower = user_id.lower()

        if "xiaonuo" in user_id_lower or "小诺" in user_id:
            return self.agent_mapping["xiaonuo"]
        elif "xiaona" in user_id_lower or "小娜" in user_id:
            return self.agent_mapping["xiaona"]
        elif "athena" in user_id_lower:
            return self.agent_mapping["athena"]
        elif "xiaochen" in user_id_lower:
            return self.agent_mapping["xiaochen"]

        # 默认返回小诺
        return self.agent_mapping["xiaonuo"]

    def map_memory_type(self, memory_type: str) -> str:
        """映射记忆类型"""
        type_mapping = {
            "episodic": "conversation",
            "semantic": "knowledge",
            "procedural": "knowledge",
            "family": "family",
            "work": "professional",
        }
        return type_mapping.get(memory_type.lower(), "conversation")

    def determine_memory_tier(self, memory: dict[str, Any]) -> str:
        """确定记忆层级"""
        importance = memory.get("importance", 0.5)
        access_count = memory.get("access_count", 0)

        if importance >= 0.9:
            return "eternal"
        elif importance >= 0.7 or access_count > 10:
            return "warm"
        elif access_count > 5:
            return "cold"
        else:
            return "cold"

    def display_import_summary(self) -> Any:
        """显示导入统计"""
        logger.info("")
        logger.info("═══════════════════════════════════════════════════════════════")
        logger.info("📊 导入统计报告")
        logger.info("═══════════════════════════════════════════════════════════════")
        logger.info(f"总处理数: {self.import_stats['total_processed']}")
        logger.info(f"成功导入: {self.import_stats['total_imported']}")
        logger.info(f"跳过记录: {self.import_stats['total_skipped']}")
        logger.info(f"错误记录: {self.import_stats['total_errors']}")

        logger.info("")
        logger.info("📂 按来源分类:")
        for source, count in self.import_stats["by_source"].items():
            logger.info(f"  {source}: {count}条")

        logger.info("")
        logger.info("👥 按智能体分类:")
        for agent, count in self.import_stats["by_agent"].items():
            logger.info(f"  {agent}: {count}条")

        logger.info("═══════════════════════════════════════════════════════════════")


async def main():
    """主函数"""
    importer = PlatformMemoryImporter()
    await importer.import_all_memories()


# 入口点: @async_main装饰器已添加到main函数
