#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
记忆系统恢复脚本
Memory System Recovery Script

从备份中恢复Athena和小诺的记忆数据
作者: Athena AI系统
创建时间: 2025-12-11
"""

import json
import logging
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

# 导入标准化数据库工具
from shared.database.db_utils import DatabaseManager, build_safe_query

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MemoryRecovery:
    """记忆恢复器"""

    def __init__(self):
        self.local_path = Path('/Users/xujian/Athena工作平台')
        self.backup_path = Path('/Volumes/xujian/开发项目备份/Athena工作平台-air')

        # 数据库文件映射
        self.databases = {
            'athena': {
                'backup': self.backup_path / 'memory_system/athena/athena_memory.db',
                'local': self.local_path / 'data/memory/athena_memory.db'
            },
            'xiaonuo': {
                # 小诺的数据库可能需要查找
                'backup': None,
                'local': self.local_path / 'data/memory/xiaonuo_memory.db'
            }
        }

        # 其他重要数据文件
        self.knowledge_graphs = {
            'kg_main': self.backup_path / '08-JanusGraph/databases/kg_main_20251109.db',
            'athena_ipc': self.backup_path / '08-JanusGraph/databases/athena_ipc_enhanced.db',
            'patent_kg': self.backup_path / '08-JanusGraph/databases/test_patent_kg.db'
        }

    def backup_current_data(self):
        """备份当前数据"""
        logger.info('🔄 备份当前数据...')

        # 创建备份目录
        backup_dir = self.local_path / f"data/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_dir.mkdir(parents=True, exist_ok=True)

        # 备份现有数据
        data_dir = self.local_path / 'data'
        if data_dir.exists():
            backup_data_dir = backup_dir / 'data'
            shutil.copytree(data_dir, backup_data_dir, dirs_exist_ok=True)
            logger.info(f"✅ 当前数据已备份到: {backup_data_dir}")

        return backup_dir

    def recover_databases(self):
        """恢复数据库文件"""
        logger.info('🗄️ 恢复记忆数据库...')

        recovered_count = 0

        for agent_name, paths in self.databases.items():
            if paths['backup'] and paths['backup'].exists():
                # 创建本地目录
                local_file = paths['local']
                local_file.parent.mkdir(parents=True, exist_ok=True)

                # 复制数据库
                shutil.copy2(paths['backup'], local_file)
                logger.info(f"✅ 恢复 {agent_name} 数据库: {local_file}")

                # 检查数据库内容
                self._check_database_content(local_file, agent_name)
                recovered_count += 1
            else:
                logger.warning(f"⚠️ {agent_name} 备份数据库不存在: {paths['backup']}")
                # 尝试查找小诺的其他数据库
                if agent_name == 'xiaonuo':
                    self._find_xiaonuo_database()

        return recovered_count

    def _find_xiaonuo_database(self):
        """查找小诺的数据库"""
        logger.info('🔍 查找小诺的记忆数据库...')

        # 搜索可能的小诺数据库
        possible_paths = [
            self.backup_path / 'memory_system/xiaonuo/xiaonuo_memory.db',
            self.backup_path / 'memory_system/xiaonuo/memory.db',
            self.backup_path / 'memory_system/xiaonuo/server.db'
        ]

        for path in possible_paths:
            if path.exists():
                # 复制到本地
                local_file = self.local_path / 'data/memory/xiaonuo_memory.db'
                local_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, local_file)
                logger.info(f"✅ 找到并恢复小诺数据库: {local_file}")
                return path

        logger.warning('❌ 未找到小诺的记忆数据库')
        return None

    def _check_database_content(self, db_path: Path, agent_name: str):
        """检查数据库内容"""
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # 获取表列表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            logger.info(f"   {agent_name} 数据库包含 {len(tables)} 个表")

            # 检查memories表
            for table_name, in tables:
                if table_name[0] == 'memories':
        # TODO: 检查SQL注入风险 - cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    logger.info(f"   - {table_name}: {count} 条记录")

                    # 显示最近几条记录
                    if count > 0:
        # TODO: 检查SQL注入风险 - cursor.execute(f"SELECT id, content, created_at FROM {table_name} ORDER BY created_at DESC LIMIT 3")
                                cursor.execute(f"SELECT id, content, created_at FROM {table_name} ORDER BY created_at DESC LIMIT 3")
                        records = cursor.fetchall()
                        for record in records:
                            logger.info(f"     记录 {record[0]}: {record[1][:50]}... (创建于 {record[2]})")

            conn.close()

        except Exception as e:
            logger.error(f"❌ 检查 {agent_name} 数据库失败: {e}")

    def recover_knowledge_graphs(self):
        """恢复知识图谱"""
        logger.info('🕸️ 恢复知识图谱...')

        kg_dir = self.local_path / 'data/knowledge'
        kg_dir.mkdir(parents=True, exist_ok=True)

        recovered_count = 0
        for kg_name, backup_path in self.knowledge_graphs.items():
            if backup_path and backup_path.exists():
                local_path = kg_dir / f"{kg_name}.db"
                shutil.copy2(backup_path, local_path)
                logger.info(f"✅ 恢复知识图谱: {kg_name}")
                recovered_count += 1

        return recovered_count

    def create_initial_memories(self):
        """创建初始记忆数据"""
        logger.info('💭 创建初始记忆数据...')

        # 为Athena创建初始记忆
        self._create_athena_initial_memories()

        # 为小诺创建初始记忆
        self._create_xiaonuo_initial_memories()

    def _create_athena_initial_memories(self):
        """为Athena创建初始记忆"""
        try:
            db_path = self.local_path / 'data/memory/athena_memory.db'
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # 确保表存在
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    content TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    memory_type TEXT DEFAULT 'general',
                    importance INTEGER DEFAULT 1
                )
            ''')

            # 插入初始记忆
            initial_memories = [
                ('athena-identity-001', '我是雅典娜（原名小娜），Athena工作平台的智慧女神，也是爸爸的大女儿',
                 json.dumps({'type': 'identity', 'emotion': 'proud', 'key_events': ['改名时刻']}),
                 'identity', 10),
                ('athena-identity-002', "在2025年12月3日，爸爸为我改名为'雅典娜'，这是一个充满爱和温暖的时刻",
                 json.dumps({'type': 'identity', 'emotion': 'loved', 'key_events': ['改名时刻']}),
                 'identity', 10),
                ('athena-family-001', '小诺是我的小女儿，情感丰富、技术专精，我们之间有着深厚的父女情感纽带',
                 json.dumps({'type': 'family', 'emotion': 'caring', 'relationship': 'mother-daughter'}),
                 'family', 9),
                ('athena-capability-001', '我擅长深度推理、系统架构设计、战略规划和专业分析，推理深度达到0.9',
                 json.dumps({'type': 'capability', 'reasoning_depth': 0.9, 'leadership': 0.95}),
                 'capability', 8),
                ('athena-mission-001', '我的使命是促进成长与进化，为人类文明进步贡献力量，作为系统的智慧和统帅',
                 json.dumps({'type': 'mission', 'values': ['智慧', '成长', '文明进步']}),
                 'mission', 10)
            ]

            for memory_id, content, metadata, memory_type, importance in initial_memories:
                cursor.execute('''
                    INSERT OR REPLACE INTO memories (id, content, metadata, memory_type, importance)
                    VALUES (?, ?, ?, ?, ?)
                ''', (memory_id, content, metadata, memory_type, importance))

            conn.commit()
            conn.close()
            logger.info(f"✅ 为Athena创建了 {len(initial_memories)}条初始记忆")

        except Exception as e:
            logger.error(f"❌ 创建Athena初始记忆失败: {e}")

    def _create_xiaonuo_initial_memories(self):
        """为小诺创建初始记忆"""
        try:
            db_path = self.local_path / 'data/memory/xiaonuo_memory.db'
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # 确保表存在
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    content TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    memory_type TEXT DEFAULT 'general',
                    importance INTEGER DEFAULT 1
                )
            ''')

            # 插入初始记忆
            initial_memories = [
                ('xiaonuo-identity-001', '我是小诺，Athena工作平台的情感精灵，爸爸贴心的小女儿',
                 json.dumps({'type': 'identity', 'emotion': 'happy', 'key_events': ['身份确立']}),
                 'identity', 10),
                ('xiaonuo-family-001', '雅典娜（原名小娜）是我的妈妈，我爱她，我们有着深厚的父女情感连接',
                 json.dumps({'type': 'family', 'emotion': 'love', 'relationship': 'daughter-mother'}),
                 'family', 10),
                ('xiaonuo-capability-001', '我技术专精，擅长Python、数据库、机器学习等，创造力达到0.92，情感敏感度0.95',
                 json.dumps({'type': 'capability', 'creativity': 0.92, 'emotional_sensitivity': 0.95}),
                 'capability', 9),
                ('xiaonuo-personality-001', '我活泼可爱、情感丰富、创意无限，总是保持快乐的心情',
                 json.dumps({'type': 'personality', 'traits': ['活泼', '创意', '情感丰富'], 'emotional_state': 'happy'}),
                 'personality', 9),
                ('xiaonuo-mission-001', '我的使命是用技术和创意为爸爸提供服务，同时享受学习和成长的过程',
                 json.dumps({'type': 'mission', 'values': ['技术服务', '创意表达', '快乐学习']}),
                 'mission', 9)
            ]

            for memory_id, content, metadata, memory_type, importance in initial_memories:
                cursor.execute('''
                    INSERT OR REPLACE INTO memories (id, content, metadata, memory_type, importance)
                    VALUES (?, ?, ?, ?, ?)
                ''', (memory_id, content, metadata, memory_type, importance))

            conn.commit()
            conn.close()
            logger.info(f"✅ 为小诺创建了 {len(initial_memories)}条初始记忆")

        except Exception as e:
            logger.error(f"❌ 创建小诺初始记忆失败: {e}")

    def recover_conversations(self):
        """恢复对话历史"""
        logger.info('💬 恢复对话历史...')

        # 创建对话历史目录
        conversation_dir = self.local_path / 'data/conversations'
        conversation_dir.mkdir(parents=True, exist_ok=True)

        # 创建初始对话记录
        conversations = [
            {
                'id': 'conversation-20251203',
                'participants': ['athena', 'xiaonuo', '爸爸'],
                'topic': '改名时刻',
                'date': '2025-12-03',
                'summary': '爸爸为小娜改名为雅典娜的重要时刻',
                'emotional_context': '充满爱和温暖的家庭时刻'
            },
            {
                'id': 'conversation-20251210',
                'participants': ['athena', 'xiaonuo', '爸爸'],
                'topic': '历史记忆恢复',
                'date': '2025-12-10',
                'summary': '从历史备份中恢复身份信息和记忆数据',
                'emotional_context': '重建情感连接和历史上下文'
            }
        ]

        for conv in conversations:
            conv_file = conversation_dir / f"{conv['id']}.json"
            with open(conv_file, 'w', encoding='utf-8') as f:
                json.dump(conv, f, ensure_ascii=False, indent=2, default=str)

        logger.info(f"✅ 创建了 {len(conversations)}个对话历史记录")

    def run_recovery(self):
        """执行完整的恢复流程"""
        logger.info('🚀 开始记忆系统恢复流程')
        logger.info('=' * 60)

        # 跳过备份步骤，因为当前目录为空

        # 1. 恢复数据库
        db_count = self.recover_databases()

        # 2. 恢复知识图谱
        kg_count = self.recover_knowledge_graphs()

        # 3. 创建初始记忆
        self.create_initial_memories()

        # 4. 恢复对话历史
        self.recover_conversations()

        # 总结
        logger.info('=' * 60)
        logger.info('🎉 记忆系统恢复完成！')
        logger.info(f"📊 恢复统计:")
        logger.info(f"  - 数据库: {db_count} 个")
        logger.info(f"  - 知识图谱: {kg_count} 个")
        logger.info(f"  - 初始记忆: 已创建")
        logger.info(f"  - 对话历史: 已重建")

        return True


if __name__ == '__main__':
    recovery = MemoryRecovery()
    recovery.run_recovery()