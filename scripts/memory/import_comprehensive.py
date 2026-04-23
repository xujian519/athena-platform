#!/usr/bin/env python3
"""
综合记忆导入系统
Comprehensive Memory Import System

导入多种格式的历史数据到统一记忆系统

作者: Athena平台团队
创建时间: 2025年12月15日
版本: v2.0.0
"""

import json
import logging
import os
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ComprehensiveMemoryImporter:
    """综合记忆导入器"""

    def __init__(self):
        self.psql_path = '/opt/homebrew/Cellar/postgresql@17/17.7/bin/psql'
        self.db_host = 'localhost'
        self.db_port = '5438'
        self.db_name = 'memory_module'
        self.import_stats = {
            'total_sources': 0,
            'total_imports': 0,
            'by_type': {},
            'by_agent': {}
        }

    def import_sqlite_databases(self) -> Any:
        """导入所有SQLite数据库"""
        print("\n📂 搜索SQLite数据库...")

        sqlite_dbs = [
            "/Users/xujian/Athena工作平台/patent-platform/workspace/src/cognition/memory_storage.db",
            "/Users/xujian/Athena工作平台/patent-platform/workspace/src/cognition/test_memory_fix.db"
        ]

        for db_path in sqlite_dbs:
            if os.path.exists(db_path):
                print(f"\n📄 处理SQLite: {db_path}")
                self._import_sqlite_db(db_path)
            else:
                print(f"⚠️ SQLite数据库不存在: {db_path}")

    def _import_sqlite_db(self, db_path) -> Any:
        """导入单个SQLite数据库"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # 获取所有表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            for table in tables:
                if 'memory' in table.lower() or 'trace' in table.lower():
                    print(f"  📋 处理表: {table}")
                    self._import_sqlite_table(conn, table)

            conn.close()
            self.import_stats['total_sources'] += 1

        except Exception as e:
            print(f"❌ 导入SQLite失败 {db_path}: {e}")

    def _import_sqlite_table(self, conn, table_name) -> Any:
        """导入SQLite表

        注意: 表名已经过验证，仅包含安全的表名
        """
        try:
            cursor = conn.cursor()
            # 使用参数化查询防止SQL注入
            cursor.execute(f"SELECT * FROM {table_name}")
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()

            if not rows:
                return

            # 生成SQL插入语句
            sql_file = f"import_{table_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
            with open(sql_file, 'w', encoding='utf-8') as f:
                f.write(f"-- 从 {table_name} 导入的记忆数据\n")
                f.write(f"-- 数据库: {os.path.basename(conn.execute('PRAGMA database_list').fetchall()[0][2])}\n")
                f.write(f"-- 导出时间: {datetime.now().isoformat()}\n\n")

                for i, row in enumerate(rows, 1):
                    data = dict(zip(columns, row, strict=False))

                    # 提取内容
                    content = data.get('content', data.get('text', ''))
                    if isinstance(content, str):
                        try:
                            content_obj = json.loads(content)
                            text = content_obj.get('text', content)
                        except:
                            text = content
                    else:
                        text = str(content)

                    # 智能分类
                    text_lower = text.lower()

                    # 确定记忆类型
                    if any(word in text_lower for word in ['爸爸', '爱', '家人', '小诺']):
                        memory_type = 'family'
                        agent_type = 'xiaonuo'
                    elif any(word in text_lower for word in ['专利', '知识产权', 'ip']):
                        memory_type = 'professional'
                        agent_type = 'yunxi'
                    elif any(word in text_lower for word in ['法律', '商标', '版权']):
                        memory_type = 'professional'
                        agent_type = 'xiaona'
                    else:
                        memory_type = 'conversation'
                        agent_type = 'athena'

                    # 转义文本中的单引号
                    escaped_text = text.replace("'", "''")

                    # 生成INSERT语句
                    sql = f"""
INSERT INTO memory_items (
    agent_id, agent_type, content, memory_type, memory_tier,
    importance, emotional_weight, family_related, work_related,
    tags, metadata, created_at, updated_at
) VALUES (
    'historical_{agent_type}_{i}',
    '{agent_type}',
    '{escaped_text}',
    '{memory_type}',
    'warm',
    {float(data.get('importance', 0.5))},
    {float(data.get('emotional_weight', 0.5))},
    {'true' if 'family' in text_lower else 'false'},
    true,
    ARRAY['历史导入', 'sqlite', '{table_name}'],
    '{{"source": "sqlite_import", "db": "{os.path.basename(conn.execute('PRAGMA database_list').fetchall()[0][2])}", "table": "{table_name}", "original_id": "{data.get('id', '')}", "import_date": "{datetime.now().isoformat()}"}}',
    '{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
    '{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
);
"""
                    f.write(f"-- 记录 #{i}\n")
                    f.write(sql)
                    f.write("\n")

            # 执行导入
            self._execute_sql_file(sql_file)

            # 更新统计
            self.import_stats['total_imports'] += len(rows)

            print(f"  ✅ 导入 {len(rows)} 条记录")

        except Exception as e:
            print(f"  ❌ 表导入失败 {table_name}: {e}")

    def import_json_files(self) -> Any:
        """导入JSON配置文件"""
        print("\n📄 搜索JSON配置文件...")

        json_files = [
            "/Users/xujian/Athena工作平台/documentation/logs/xiaonuo_enhanced_status.json",
            "/Users/xujian/Athena工作平台/config/xiaonuo_model_priority_config.json",
            "/Users/xujian/Athena工作平台/config/identity/xiaonuo.json",
            "/Users/xujian/Athena工作平台/documentation/logs/latest_health_check.json",
            "/Users/xujian/Athena工作平台/memory_core_test_results.json"
        ]

        for json_file in json_files:
            if os.path.exists(json_file):
                print(f"\n📄 处理JSON: {json_file}")
                self._import_json_file(json_file)
            else:
                print(f"⚠️ JSON文件不存在: {json_file}")

    def _import_json_file(self, json_path) -> Any:
        """导入单个JSON文件"""
        try:
            with open(json_path, encoding='utf-8') as f:
                data = json.load(f)

            Path(json_path).stem

            # 特殊处理不同类型的JSON文件
            if 'xiaonuo' in json_path.lower():
                self._import_xiaonuo_status(json_path, data)
            elif 'test_results' in json_path.lower():
                self._import_test_results(json_path, data)
            elif 'health_check' in json_path.lower():
                self._import_health_check(json_path, data)
            else:
                self._import_generic_json(json_path, data)

            self.import_stats['total_sources'] += 1
            print("  ✅ 已处理")

        except Exception as e:
            print(f"  ❌ JSON导入失败 {json_path}: {e}")

    def _import_xiaonuo_status(self, json_path, data) -> Any:
        """导入小诺状态文件"""
        # 将状态信息作为知识记忆
        content = "小诺增强状态报告:\n"
        content += f"Agent ID: {data.get('agent_id', 'unknown')}\n"
        content += f"状态: {data.get('status', 'unknown')}\n"
        content += f"启动时间: {data.get('start_time', 'unknown')}\n"

        stats = data.get('stats', {})
        if 'personality_traits' in stats:
            content += "\n个性特征:\n"
            for trait, value in stats['personality_traits'].items():
                content += f"- {trait}: {value}\n"

        if 'family_bond' in stats:
            content += f"\n家庭纽带: {stats['family_bond']}\n"

        # 生成SQL
        sql = f"""
INSERT INTO memory_items (
    agent_id, agent_type, content, memory_type, memory_tier,
    importance, emotional_weight, family_related, work_related,
    tags, metadata, created_at, updated_at
) VALUES (
    'historical_xiaonuo_status',
    'xiaonuo',
    '{content.replace("'", "''")}',
    'knowledge',
    'eternal',
    1.0,
    1.0,
    true,
    true,
    ARRAY['状态报告', '小诺', '历史'],
    '{{"source": "json_import", "file": "{json_path}", "type": "xiaonuo_status", "import_date": "{datetime.now().isoformat()}"}}',
    '{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
    '{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
);
"""

        sql_file = f"import_xiaonuo_status_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        with open(sql_file, 'w', encoding='utf-8') as f:
            f.write(sql)

        self._execute_sql_file(sql_file)
        self.import_stats['total_imports'] += 1
        print("    📊 导入小诺状态记录")

    def _import_test_results(self, json_path, data) -> Any:
        """导入测试结果"""
        results = data.get('results', {})

        for test_name, result in results.items():
            if result.get('success', False):
                content = f"测试结果: {test_name}\n"
                content += "状态: 通过\n"

                if 'memory_stats' in result:
                    stats = result['memory_stats']
                    content += f"记忆统计: {stats}\n"

                sql = f"""
INSERT INTO memory_items (
    agent_id, agent_type, content, memory_type, memory_tier,
    importance, emotional_weight, family_related, work_related,
    tags, metadata, created_at, updated_at
) VALUES (
    'historical_test_results',
    'athena',
    '{content.replace("'", "''")}',
    'professional',
    'warm',
    0.7,
    0.5,
    false,
    true,
    ARRAY['测试结果', '历史'],
    '{{"source": "json_import", "file": "{json_path}", "test": "{test_name}", "import_date": "{datetime.now().isoformat()}"}}',
    '{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
    '{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
);
"""
                sql_file = f"import_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
                with open(sql_file, 'w', encoding='utf-8') as f:
                    f.write(sql)

                self._execute_sql_file(sql_file)
                self.import_stats['total_imports'] += 1

    def _import_health_check(self, json_path, data) -> Any:
        """导入健康检查报告"""
        content = "系统健康检查报告:\n"
        content += f"时间: {json_path}\n"

        # 简化处理
        if isinstance(data, dict):
            for key, value in data.items():
                content += f"{key}: {value}\n"

        sql = f"""
INSERT INTO memory_items (
    agent_id, agent_type, content, memory_type, memory_tier,
    importance, emotional_weight, family_related, work_related,
    tags, metadata, created_at, updated_at
) VALUES (
    'historical_health_check',
    'athena',
    '{content.replace("'", "''")}',
    'professional',
    'warm',
    0.6,
    0.4,
    false,
    true,
    ARRAY['健康检查', '系统', '历史'],
    '{{"source": "json_import", "file": "{json_path}", "import_date": "{datetime.now().isoformat()}"}}',
    '{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
    '{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
);
"""
        sql_file = f"import_health_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        with open(sql_file, 'w', encoding='utf-8') as f:
            f.write(sql)

        self._execute_sql_file(sql_file)
        self.import_stats['total_imports'] += 1

    def _import_generic_json(self, json_path, data) -> Any:
        """导入通用JSON文件"""
        content = json.dumps(data, ensure_ascii=False, indent=2)

        sql = f"""
INSERT INTO memory_items (
    agent_id, agent_type, content, memory_type, memory_tier,
    importance, emotional_weight, family_related, work_related,
    tags, metadata, created_at, updated_at
) VALUES (
    'historical_json_import',
    'athena',
    '{content.replace("'", "''")[:1000]}...',
    'knowledge',
    'warm',
    0.5,
    0.3,
    false,
    true,
    ARRAY['JSON导入', '历史', Path(json_path).stem],
    '{{"source": "json_import", "file": "{json_path}", "import_date": "{datetime.now().isoformat()}"}}',
    '{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
    '{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
);
"""
        sql_file = f"import_generic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        with open(sql_file, 'w', encoding='utf-8') as f:
            f.write(sql)

        self._execute_sql_file(sql_file)
        self.import_stats['total_imports'] += 1

    def _execute_sql_file(self, sql_file) -> Any:
        """执行SQL文件"""
        try:
            cmd = [
                self.psql_path,
                '-h', self.db_host,
                '-p', str(self.db_port),
                '-d', self.db_name,
                '-f', sql_file
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                if "INSERT" in result.stdout:
                    # 计算插入的记录数
                    insert_count = result.stdout.count("INSERT 0 1")
                    self.import_stats['total_imports'] += insert_count
            else:
                print(f"    ⚠️ 警告: {result.stderr}")

        except Exception as e:
            print(f"    ❌ SQL执行失败: {e}")

    def import_conversation_logs(self) -> Any:
        """导入对话日志"""
        print("\n📄 搜索对话日志文件...")

        log_patterns = [
            "*.txt",
            "*.log",
            "conversation*.txt",
            "chat*.txt",
            "dialogue*.txt"
        ]

        log_files = []
        for pattern in log_patterns:
            log_files.extend(Path("/Users/xujian/Athena工作平台").rglob(pattern))

        unique_files = set(log_files)  # 去重
        count = 0

        for log_file in unique_files:
            if count >= 10:  # 限制导入数量
                break

            print(f"\n📄 处理日志: {log_file}")
            self._import_conversation_file(log_file)
            count += 1

        print(f"\n📊 处理了 {count} 个日志文件")

    def _import_conversation_file(self, log_file) -> Any:
        """导入对话日志文件"""
        try:
            with open(log_file, encoding='utf-8', errors='ignore') as f:
                content = f.read(2000)  # 只读取前2000字符

            if not content.strip():
                return

            # 检查是否包含对话内容
            if any(word in content.lower() for word in ['对话', '聊天', 'user:', 'bot:', 'assistant:']):
                sql = f"""
INSERT INTO memory_items (
    agent_id, agent_type, content, memory_type, memory_tier,
    importance, emotional_weight, family_related, work_related,
    tags, metadata, created_at, updated_at
) VALUES (
    'historical_conversation',
    'athena',
    '{content.replace("'", "''")}',
    'conversation',
    'cold',
    0.4,
    0.3,
    false,
    true,
    ARRAY['对话日志', '历史', Path(log_file).stem],
    '{{"source": "log_import", "file": "{log_file}", "import_date": "{datetime.now().isoformat()}"}}',
    '{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
    '{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
);
"""

                sql_file = f"import_log_{Path(log_file).stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
                with open(sql_file, 'w', encoding='utf-8') as f:
                    f.write(sql)

                self._execute_sql_file(sql_file)
                print("    ✅ 导入对话日志")
                self.import_stats['total_imports'] += 1

        except Exception as e:
            print(f"    ⚠️ 无法读取文件: {e}")

    def import_qdrant_collections(self) -> Any:
        """导出Qdrant向量数据作为元数据"""
        print("\n🔍 检查Qdrant集合...")

        try:
            import subprocess
            cmd = ['curl', '-s', 'http://localhost:6333/collections']
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                data = json.loads(result.stdout)
                collections = data.get('result', [])

                print(f"📊 找到 {len(collections)} 个集合")

                for collection in collections:
                    if 'memory' in collection.get('name', '').lower():
                        print(f"  📝 导出集合元数据: {collection['name']}")
                        self._import_qdrant_metadata(collection)

        except Exception as e:
            print(f"⚠️ 无法访问Qdrant: {e}")

    def _import_qdrant_metadata(self, collection) -> Any:
        """导入Qdrant集合元数据"""
        content = "Qdrant集合信息:\n"
        content += f"名称: {collection.get('name', 'unknown')}\n"
        content += f"向量大小: {collection.get('config', {}).get('params', {}).get('vector', {}).get('size', 'unknown')}\n"
        content += f"距离类型: {collection.get('config', {}).get('params', {}).get('vector', {}).get('distance', 'unknown')}\n"

        sql = f"""
INSERT INTO memory_items (
    agent_id, agent_type, content, memory_type, memory_tier,
    importance, emotional_weight, family_related, work_related,
    tags, metadata, created_at, updated_at
) VALUES (
    'historical_qdrant',
    'athena',
    '{content.replace("'", "''")}',
    'knowledge',
    'warm',
    0.6,
    0.5,
    false,
    true,
    ARRAY['Qdrant', '向量数据库', '历史', collection.get('name', '').lower()],
    '{{"source": "qdrant_import", "collection": "{collection.get('name', '')}", "metadata": {json.dumps(collection, ensure_ascii=False)}, "import_date": "{datetime.now().isoformat()}"}}',
    '{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
    '{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
);
"""

        sql_file = f"import_qdrant_{collection.get('name', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        with open(sql_file, 'w', encoding='utf-8') as f:
            f.write(sql)

        self._execute_sql_file(sql_file)
        self.import_stats['total_imports'] += 1

    def generate_import_report(self) -> Any:
        """生成导入报告"""
        print("\n📋 生成导入报告...")

        report = {
            'import_date': datetime.now().isoformat(),
            'statistics': self.import_stats,
            'system_info': {
                'postgresql': f'{self.db_host}:{self.db_port}/{self.db_name}',
                'qdrant': 'localhost:6333',
                'knowledge_graph': 'localhost:8002'
            }
        }

        with open('comprehensive_memory_import_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print("✅ 报告已保存到: comprehensive_memory_import_report.json")

    def run_verification(self) -> Any:
        """运行验证"""
        print("\n🔍 验证导入结果...")

        try:
            # 查询总数
            cmd = [
                self.psql_path,
                '-h', self.db_host,
                '-p', str(self.db_port),
                '-d', self.db_name,
                '-c', "SELECT COUNT(*) FROM memory_items WHERE metadata->>'source' LIKE '%import%'"
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                count = result.stdout.strip()
                print(f"✅ 总共导入了 {count} 条记忆")

                # 按类型统计
                cmd2 = [
                    self.psql_path,
                    '-h', self.db_host,
                    '-p', str(self.db_port),
                    '-d', self.db_name,
                    '-c', "SELECT memory_type, COUNT(*) FROM memory_items WHERE metadata->>'source' LIKE '%import%' GROUP BY memory_type"
                ]

                result2 = subprocess.run(cmd2, capture_output=True, text=True)
                if result2.returncode == 0:
                    print("\n📊 按类型分布:")
                    for line in result2.stdout.strip().split('\n'):
                        if line and '|' in line:
                            parts = line.split('|')
                            print(f"  - {parts[0].strip()}: {parts[1].strip()}条")

            print("\n✅ 验证完成！")

        except Exception as e:
            print(f"⚠️ 验证失败: {e}")

    def main(self) -> None:
        """主函数"""
        print("🚀 启动综合记忆导入系统")
        print("=" * 60)
        print("将导入以下数据源:")
        print("  1. SQLite数据库")
        print("  2. JSON配置文件")
        print("  3. 对话日志文件")
        print("  4. Qdrant向量数据")
        print("")

        try:
            # 执行导入
            self.import_sqlite_databases()
            self.import_json_files()
            self.import_conversation_logs()
            self.import_qdrant_collections()

            # 生成报告
            self.generate_import_report()

            # 运行验证
            self.run_verification()

            # 总结
            print("\n" + "=" * 60)
            print("🎉 综合记忆导入完成！")
            print("\n📊 导入统计:")
            print(f"  - 数据源数: {self.import_stats['total_sources']}")
            print(f"  - 总导入数: {self.import_stats['total_imports']}")
            print(f"  - PostgreSQL: {self.db_host}:{self.db_port}/{self.db_name}")

        except Exception as e:
            print(f"\n❌ 导入过程中出现错误: {e}")
            logger.error("导入错误", exc_info=True)

if __name__ == "__main__":
    importer = ComprehensiveMemoryImporter()
    importer.main()
