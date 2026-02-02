#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
历史记忆导入系统
Historical Memory Import System

将平台的历史记忆数据导入到新的统一记忆系统中

作者: Athena平台团队
创建时间: 2025年12月15日
版本: v1.0.0
"""

import asyncio
import json
import sqlite3
import logging
import sys
from datetime import datetime
from pathlib import Path
import uuid
from typing import Dict, List, Any, Optional

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent.parent))

from core.memory.unified_agent_memory_system import (
    UnifiedAgentMemorySystem,
    AgentType,
    MemoryType,
    MemoryTier
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HistoricalMemoryImporter:
    """历史记忆导入器"""

    def __init__(self):
        self.memory_system = None
        self.import_stats = {
            'total_processed': 0,
            'successful_imports': 0,
            'failed_imports': 0,
            'by_agent': {},
            'by_type': {}
        }

    async def initialize(self):
        """初始化记忆系统"""
        print("\n🔄 初始化统一记忆系统...")
        self.memory_system = UnifiedAgentMemorySystem()
        await self.memory_system.initialize()
        print("✅ 记忆系统初始化成功")

    async def import_from_sqlite(self, db_path: str):
        """从SQLite数据库导入记忆"""
        print(f"\n📂 从SQLite导入记忆: {db_path}")

        try:
            # 连接SQLite数据库
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # 获取表结构
            cursor.execute("PRAGMA table_info(memory_traces)")
            columns = [row[1] for row in cursor.fetchall()]
            print(f"📊 发现列: {columns}")

            # 查询所有记忆
            cursor.execute("SELECT * FROM memory_traces")
            rows = cursor.fetchall()

            print(f"📝 找到 {len(rows)} 条历史记忆")

            # 导入每条记忆
            for row in rows:
                try:
                    await self._process_memory_row(row, columns)
                    self.import_stats['successful_imports'] += 1
                except Exception as e:
                    logger.error(f"导入记忆失败: {e}")
                    self.import_stats['failed_imports'] += 1

            conn.close()
            print(f"✅ SQLite导入完成")

        except Exception as e:
            print(f"❌ SQLite导入失败: {e}")
            logger.error("SQLite导入错误", exc_info=True)

    async def _process_memory_row(self, row: tuple, columns: List[str]):
        """处理单条记忆记录"""
        # 解析数据
        data = dict(zip(columns, row))

        # 提取内容
        content = data.get('content', '')
        if isinstance(content, str):
            try:
                content_dict = json.loads(content)
                text = content_dict.get('text', str(content))
            except:
                text = content
        else:
            text = str(content)

        # 确定记忆类型
        memory_type = self._determine_memory_type(data, text)

        # 确定智能体类型
        agent_type = self._determine_agent_type(data, text)

        # 计算重要性
        importance = float(data.get('importance', 0.5))

        # 创建记忆
        memory_id = await self.memory_system.store_memory(
            agent_id=f"historical_{agent_type.value}",
            agent_type=agent_type,
            content=text,
            memory_type=memory_type,
            importance=importance,
            emotional_weight=0.5,
            family_related=self._is_family_related(text),
            work_related=True,
            tags=self._extract_tags(text),
            metadata={
                'source': 'sqlite_import',
                'original_id': data.get('id', ''),
                'import_date': datetime.now().isoformat(),
                'raw_data': data
            },
            tier=self._determine_tier(importance),
            related_agents=[]
        )

        # 更新统计
        self.import_stats['total_processed'] += 1

        agent_name = agent_type.value
        self.import_stats['by_agent'][agent_name] = self.import_stats['by_agent'].get(agent_name, 0) + 1
        self.import_stats['by_type'][memory_type.value] = self.import_stats['by_type'].get(memory_type.value, 0) + 1

    def _determine_memory_type(self, data: Dict, text: str) -> MemoryType:
        """确定记忆类型"""
        text_lower = text.lower()

        if any(word in text_lower for word in ['爸爸', '爱', '家人', '家']):
            return MemoryType.FAMILY
        elif any(word in text_lower for word in ['工作', '项目', '技术', '开发']):
            return MemoryType.PROFESSIONAL
        elif any(word in text_lower for word in ['学习', '知识', '理解']):
            return MemoryType.LEARNING
        elif any(word in text_lower for word in ['想法', '灵感', '创意']):
            return MemoryType.REFLECTION
        elif 'semantic' in str(data.get('trace_type', '')):
            return MemoryType.KNOWLEDGE
        else:
            return MemoryType.CONVERSATION

    def _determine_agent_type(self, data: Dict, text: str) -> AgentType:
        """确定智能体类型"""
        text_lower = text.lower()

        # 根据内容关键词判断
        if any(word in text_lower for word in ['爸爸', '小诺', '女儿', '爱']):
            return AgentType.XIAONUO
        elif any(word in text_lower for word in ['法律', '专利', '商标', '版权']):
            return AgentType.XIAONA
        elif any(word in text_lower for word in ['专利', 'ip', '知识产权']):
            return AgentType.YUNXI
        elif any(word in text_lower for word in ['媒体', '运营', '内容', '推广']):
            return AgentType.XIAOCHEN
        else:
            # 默认归为Athena
            return AgentType.ATHENA

    def _determine_tier(self, importance: float) -> MemoryTier:
        """根据重要性确定记忆层级"""
        if importance >= 0.9:
            return MemoryTier.ETERNAL
        elif importance >= 0.7:
            return MemoryTier.HOT
        elif importance >= 0.5:
            return MemoryTier.WARM
        else:
            return MemoryTier.COLD

    def _is_family_related(self, text: str) -> bool:
        """判断是否与家庭相关"""
        family_keywords = ['爸爸', '妈妈', '爱', '家人', '家', '女儿']
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in family_keywords)

    def _extract_tags(self, text: str) -> List[str]:
        """提取标签"""
        tags = []
        text_lower = text.lower()

        # 通用标签
        if '测试' in text_lower:
            tags.append('测试')
        if '集成' in text_lower:
            tags.append('集成')
        if '系统' in text_lower:
            tags.append('系统')
        if '专利' in text_lower:
            tags.append('专利')
        if '学习' in text_lower:
            tags.append('学习')
        if '工作' in text_lower:
            tags.append('工作')

        return tags

    async def import_from_json_files(self, directory: str):
        """从JSON文件导入记忆"""
        print(f"\n📂 从JSON文件导入记忆: {directory}")

        import_path = Path(directory)
        json_files = list(import_path.glob("**/*.json"))

        print(f"📝 找到 {len(json_files)} 个JSON文件")

        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # 处理不同类型的JSON文件
                if 'identity' in data:
                    await self._process_identity_file(json_file, data)
                elif 'memories' in data:
                    await self._process_memories_file(json_file, data)
                else:
                    await self._process_generic_json(json_file, data)

            except Exception as e:
                logger.error(f"处理JSON文件失败 {json_file}: {e}")

    async def _process_identity_file(self, file_path: Path, data: Dict):
        """处理身份配置文件"""
        agent_name = data.get('identity', {}).get('name', 'unknown')

        # 将身份信息作为永恒记忆
        await self.memory_system.store_memory(
            agent_id=f"identity_{agent_name}",
            agent_type=AgentType.ATHENA,  # 默认类型
            content=json.dumps(data, ensure_ascii=False, indent=2),
            memory_type=MemoryType.KNOWLEDGE,
            importance=1.0,
            emotional_weight=0.8,
            tags=['身份', '配置', '导入'],
            metadata={
                'source': 'json_import',
                'file_path': str(file_path),
                'type': 'identity'
            },
            tier=MemoryTier.ETERNAL
        )

    async def _process_memories_file(self, file_path: Path, data: Dict):
        """处理包含记忆的JSON文件"""
        memories = data.get('memories', [])

        for memory_data in memories:
            try:
                await self.memory_system.store_memory(
                    agent_id=memory_data.get('agent_id', 'unknown'),
                    agent_type=self._get_agent_type_from_str(memory_data.get('agent_type', 'athena')),
                    content=memory_data.get('content', ''),
                    memory_type=self._get_memory_type_from_str(memory_data.get('type', 'conversation')),
                    importance=float(memory_data.get('importance', 0.5)),
                    tags=memory_data.get('tags', []),
                    metadata={
                        'source': 'json_import',
                        'file_path': str(file_path),
                        'import_date': datetime.now().isoformat()
                    }
                )
            except Exception as e:
                logger.error(f"导入记忆失败: {e}")

    async def _process_generic_json(self, file_path: Path, data: Any):
        """处理通用JSON文件"""
        # 将整个文件作为知识记忆
        await self.memory_system.store_memory(
            agent_id="json_import",
            agent_type=AgentType.ATHENA,
            content=f"导入的JSON文件: {file_path.name}\n\n{json.dumps(data, ensure_ascii=False, indent=2)[:1000]}...",
            memory_type=MemoryType.KNOWLEDGE,
            importance=0.6,
            tags=['json导入', file_path.stem],
            metadata={
                'source': 'json_import',
                'file_path': str(file_path),
                'file_size': len(str(data))
            }
        )

    def _get_agent_type_from_str(self, agent_type_str: str) -> AgentType:
        """从字符串获取智能体类型"""
        mapping = {
            'athena': AgentType.ATHENA,
            'xiaona': AgentType.XIAONA,
            'yunxi': AgentType.YUNXI,
            'xiaochen': AgentType.XIAOCHEN,
            'xiaonuo': AgentType.XIAONUO
        }
        return mapping.get(agent_type_str.lower(), AgentType.ATHENA)

    def _get_memory_type_from_str(self, memory_type_str: str) -> MemoryType:
        """从字符串获取记忆类型"""
        mapping = {
            'family': MemoryType.FAMILY,
            'professional': MemoryType.PROFESSIONAL,
            'learning': MemoryType.LEARNING,
            'reflection': MemoryType.REFLECTION,
            'conversation': MemoryType.CONVERSATION,
            'schedule': MemoryType.SCHEDULE,
            'preference': MemoryType.PREFERENCE,
            'knowledge': MemoryType.KNOWLEDGE
        }
        return mapping.get(memory_type_str.lower(), MemoryType.CONVERSATION)

    async def generate_import_report(self):
        """生成导入报告"""
        print("\n📊 生成导入报告...")

        report = {
            'import_date': datetime.now().isoformat(),
            'statistics': self.import_stats,
            'system_stats': await self.memory_system.get_system_stats(),
            'agent_breakdown': {}
        }

        # 获取各智能体的统计
        for agent_type in AgentType:
            stats = await self.memory_system.get_agent_stats(agent_type.value)
            report['agent_breakdown'][agent_type.value] = stats

        # 保存报告
        report_path = Path('historical_memory_import_report.json')
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"✅ 导入报告已保存到: {report_path}")

        # 打印总结
        print("\n📋 导入总结:")
        print(f"  - 总处理数: {self.import_stats['total_processed']}")
        print(f"  - 成功导入: {self.import_stats['successful_imports']}")
        print(f"  - 失败数: {self.import_stats['failed_imports']}")
        print(f"  - 成功率: {(self.import_stats['successful_imports']/max(self.import_stats['total_processed'], 1))*100:.1f}%")

    async def cleanup(self):
        """清理资源"""
        if self.memory_system:
            await self.memory_system.close()

# 主导入函数
async def main():
    """主导入函数"""
    print("\n🚀 启动历史记忆导入系统...")
    print("=" * 60)

    importer = HistoricalMemoryImporter()

    try:
        # 初始化
        await importer.initialize()

        # 导入SQLite数据库
        sqlite_db = "/Users/xujian/Athena工作平台/patent-platform/workspace/src/cognition/memory_storage.db"
        if Path(sqlite_db).exists():
            await importer.import_from_sqlite(sqlite_db)
        else:
            print(f"⚠️ SQLite数据库不存在: {sqlite_db}")

        # 导入JSON文件
        json_dir = "/Users/xujian/Athena工作平台/config"
        if Path(json_dir).exists():
            await importer.import_from_json_files(json_dir)

        # 生成报告
        await importer.generate_import_report()

        print("\n🎉 历史记忆导入完成！")

    except Exception as e:
        logger.error(f"导入过程中出现错误: {e}", exc_info=True)

    finally:
        await importer.cleanup()

if __name__ == "__main__":
    asyncio.run(main())