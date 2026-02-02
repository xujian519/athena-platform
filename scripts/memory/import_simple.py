#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的历史记忆导入
Simple Historical Memory Import

直接从SQLite导入到PostgreSQL

作者: Athena平台团队
创建时间: 2025年12月15日
"""

import sqlite3
from typing import Any, Dict, List, Optional, Tuple, Callable, Union
import json
import sys
from datetime import datetime
import uuid

# PostgreSQL连接
try:
    import asyncpg
except ImportError:
    print("请安装asyncpg: pip install asyncpg")
    sys.exit(1)

def export_sqlite_to_json() -> Any:
    """导出SQLite数据到JSON"""
    db_path = "/Users/xujian/Athena工作平台/patent-platform/workspace/src/cognition/memory_storage.db"

    print("📂 导出SQLite记忆数据...")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 查询所有记忆
    cursor.execute("SELECT * FROM memory_traces")
    columns = [description[0] for description in cursor.description]
    rows = cursor.fetchall()

    # 转换为JSON格式
    memories = []
    for row in rows:
        memory = dict(zip(columns, row))
        memories.append(memory)

    conn.close()

    # 保存为JSON
    with open('historical_memories.json', 'w', encoding='utf-8') as f:
        json.dump({
            'export_date': datetime.now().isoformat(),
            'total_memories': len(memories),
            'memories': memories
        }, f, ensure_ascii=False, indent=2)

    print(f"✅ 已导出 {len(memories)} 条记忆到 historical_memories.json")
    return memories

async def import_to_postgresql(memories):
    """导入到PostgreSQL"""
    print("\n💾 导入到PostgreSQL记忆系统...")

    # 连接PostgreSQL
    conn = await asyncpg.connect(
        host='localhost',
        port=5438,
        database='memory_module'
    )

    success_count = 0
    error_count = 0

    for memory in memories:
        try:
            # 解析内容
            content = memory.get('content', '')
            if isinstance(content, str):
                try:
                    content_dict = json.loads(content)
                    text = content_dict.get('text', content)
                except:
                    text = content
            else:
                text = str(content)

            # 确定记忆类型
            text_lower = text.lower()
            if any(word in text_lower for word in ['爸爸', '爱', '家人']):
                memory_type = 'family'
            elif any(word in text_lower for word in ['工作', '项目', '技术']):
                memory_type = 'professional'
            elif 'semantic' in str(memory.get('trace_type', '')):
                memory_type = 'knowledge'
            else:
                memory_type = 'conversation'

            # 插入到PostgreSQL
            await conn.execute("""
                INSERT INTO memory_items (
                    id, agent_id, agent_type, content, memory_type,
                    importance, emotional_weight, family_related, work_related,
                    tags, metadata, created_at, updated_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $12
                )
            """, (
                str(uuid.uuid4()),
                'historical_agent',
                'athena',
                text,
                memory_type,
                float(memory.get('importance', 0.5)),
                0.5,
                'family' in text_lower,
                True,
                ['历史导入'],
                json.dumps({
                    'source': 'sqlite_import',
                    'original_id': memory.get('id', ''),
                    'import_date': datetime.now().isoformat()
                }),
                datetime.now()
            ))

            success_count += 1

        except Exception as e:
            print(f"⚠️ 导入失败: {e}")
            error_count += 1

    print(f"\n📊 导入结果:")
    print(f"  成功: {success_count}")
    print(f"  失败: {error_count}")
    print(f"  成功率: {success_count/(success_count+error_count)*100:.1f}%")

    await conn.close()

def create_sqlite_import_script() -> Any:
    """创建SQL导入脚本"""
    sql_script = """
-- 历史记忆导入脚本
-- 从SQLite导出数据

-- 1. 导出记忆数据
.mode json
.once historical_memories.json
SELECT json_group_array(
    json_object(
        'id', id,
        'trace_type', trace_type,
        'content', content,
        'tags', tags,
        'importance', importance,
        'emotional_weight', emotional_weight,
        'access_count', access_count,
        'created_at', created_at,
        'updated_at', updated_at,
        'persistence', persistence,
        'status', status,
        'related_traces', related_traces,
        'metadata', metadata
    )
) FROM memory_traces;

-- 2. 查看数据量
SELECT COUNT(*) as total_memories FROM memory_traces;
"""

    with open('export_sqlite.sql', 'w', encoding='utf-8') as f:
        f.write(sql_script)

    print("✅ 已创建 export_sqlite.sql")

def main() -> None:
    """主函数"""
    print("🚀 历史记忆导入工具")
    print("=" * 60)

    # 创建导出脚本
    create_sqlite_import_script()

    # 导出SQLite数据
    memories = export_sqlite_to_json()

    # 询问是否导入到PostgreSQL
    response = input("\n是否导入到PostgreSQL记忆系统? (y/n): ")
    if response.lower() == 'y':
        # 使用asyncio运行导入
        import asyncio
        asyncio.run(import_to_postgresql(memories))

    print("\n✅ 历史记忆导出完成！")
    print("\n📁 生成的文件:")
    print("  - historical_memories.json (历史记忆数据)")
    print("  - export_sqlite.sql (SQLite导出脚本)")

    print("\n📋 下一步操作:")
    print("1. 确保PostgreSQL(5438)和Qdrant(6333)正在运行")
    print("2. 使用导入脚本将数据迁移到新系统")
    print("3. 测试记忆功能是否正常")

if __name__ == "__main__":
    main()