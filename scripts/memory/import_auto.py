#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动导入历史记忆
Auto Import Historical Memories

自动执行导入，无需用户交互

作者: Athena平台团队
创建时间: 2025年12月15日
"""

import sqlite3
import json
import sys
from datetime import datetime
import uuid
import asyncio
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 检查依赖
try:
    import asyncpg
except ImportError:
    print("❌ 缺少asyncpg，请安装: pip install asyncpg")
    sys.exit(1)

async def import_historical_memories():
    """导入历史记忆"""
    print("🚀 开始导入历史记忆...")
    print("=" * 60)

    # 1. 从SQLite导出数据
    db_path = "/Users/xujian/Athena工作平台/patent-platform/workspace/src/cognition/memory_storage.db"

    if not sys.platform == 'darwin':
        print("⚠️ 请确保在macOS系统上运行")

    print("\n📂 步骤1: 从SQLite导出数据...")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 查询所有记忆
        cursor.execute("SELECT * FROM memory_traces")
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        conn.close()

        print(f"✅ 找到 {len(rows)} 条历史记忆")

        # 转换数据
        memories = []
        for row in rows:
            memory = dict(zip(columns, row))

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

            memory['text'] = text
            memories.append(memory)

    except Exception as e:
        print(f"❌ SQLite导出失败: {e}")
        return

    # 2. 导入到PostgreSQL
    print("\n💾 步骤2: 导入到PostgreSQL记忆系统...")

    try:
        conn = await asyncpg.connect(
            host='localhost',
            port=5438,
            database='memory_module'
        )

        print("✅ PostgreSQL连接成功")

        success_count = 0
        error_count = 0

        # 插入每条记忆
        for memory in memories:
            try:
                text = memory['text']
                text_lower = text.lower()

                # 确定记忆类型
                if any(word in text_lower for word in ['爸爸', '爱', '家人', '小诺']):
                    memory_type = 'family'
                elif any(word in text_lower for word in ['工作', '项目', '技术', '开发']):
                    memory_type = 'professional'
                elif 'semantic' in str(memory.get('trace_type', '')):
                    memory_type = 'knowledge'
                else:
                    memory_type = 'conversation'

                # 确定智能体类型
                if any(word in text_lower for word in ['爸爸', '小诺', '女儿']):
                    agent_type = 'xiaonuo'
                elif any(word in text_lower for word in ['专利', '知识产权']):
                    agent_type = 'yunxi'
                else:
                    agent_type = 'athena'

                # 插入记录
                await conn.execute("""
                    INSERT INTO memory_items (
                        id, agent_id, agent_type, content, memory_type,
                        importance, emotional_weight, family_related, work_related,
                        tags, metadata, created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                """, (
                    str(uuid.uuid4()),
                    f"historical_{agent_type}",
                    agent_type,
                    text,
                    memory_type,
                    float(memory.get('importance', 0.5)),
                    0.5,
                    'family' in text_lower,
                    True,
                    ['历史导入', 'sqlite'],
                    json.dumps({
                        'source': 'sqlite_import',
                        'original_id': memory.get('id', ''),
                        'import_date': datetime.now().isoformat(),
                        'original_trace_type': memory.get('trace_type', '')
                    }),
                    datetime.now(),
                    datetime.now()
                ))

                success_count += 1

                # 进度显示
                if success_count % 10 == 0:
                    print(f"  已导入: {success_count}/{len(memories)}")

            except Exception as e:
                error_count += 1
                logger.error(f"导入失败: {e}")

        await conn.close()

        print(f"\n📊 导入结果:")
        print(f"  ✅ 成功: {success_count}")
        print(f"  ❌ 失败: {error_count}")
        print(f"  📈 成功率: {success_count/(success_count+error_count)*100:.1f}%")

    except Exception as e:
        print(f"❌ PostgreSQL导入失败: {e}")
        logger.error("PostgreSQL错误", exc_info=True)
        return

    # 3. 导出结果报告
    print("\n📋 步骤3: 生成导入报告...")

    report = {
        'import_date': datetime.now().isoformat(),
        'source': 'sqlite_memory_storage.db',
        'total_memories': len(memories),
        'successful_imports': success_count,
        'failed_imports': error_count,
        'success_rate': success_count/(success_count+error_count)*100,
        'target_system': 'PostgreSQL记忆系统(5438)'
    }

    with open('memory_import_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("✅ 报告已保存到: memory_import_report.json")

    # 4. 保存原始数据
    with open('historical_memories_backup.json', 'w', encoding='utf-8') as f:
        json.dump({
            'export_date': datetime.now().isoformat(),
            'total_count': len(memories),
            'memories': memories[:10]  # 只保存前10条作为样本
        }, f, ensure_ascii=False, indent=2)

    print("✅ 备份数据已保存到: historical_memories_backup.json")

    # 5. 总结
    print("\n" + "=" * 60)
    print("🎉 历史记忆导入完成！")
    print("\n📁 生成的文件:")
    print("  - memory_import_report.json (导入报告)")
    print("  - historical_memories_backup.json (数据备份)")
    print("\n📊 导入统计:")
    print(f"  - 总记忆数: {len(memories)}")
    print(f"  - 成功导入: {success_count}")
    print(f"  - 存储位置: PostgreSQL(memory_module@localhost:5438)")

    # 6. 验证导入
    print("\n🔍 步骤4: 验证导入结果...")

    try:
        conn = await asyncpg.connect(
            host='localhost',
            port=5438,
            database='memory_module'
        )

        # 查询导入的记忆数量
        count = await conn.fetchval(
            "SELECT COUNT(*) FROM memory_items WHERE metadata->>'source' = 'sqlite_import'"
        )

        print(f"✅ 验证成功: 找到 {count} 条导入的记忆")

        # 查询样本
        sample = await conn.fetchrow(
            "SELECT content, memory_type, agent_type FROM memory_items WHERE metadata->>'source' = 'sqlite_import' LIMIT 1"
        )

        if sample:
            print(f"\n📝 记忆样本:")
            print(f"  内容: {sample['content'][:50]}...")
            print(f"  类型: {sample['memory_type']}")
            print(f"  智能体: {sample['agent_type']}")

        await conn.close()

    except Exception as e:
        print(f"⚠️ 验证失败: {e}")

    print("\n✅ 所有历史记忆已成功导入到统一记忆系统！")

if __name__ == "__main__":
    # 运行导入
    asyncio.run(import_historical_memories())