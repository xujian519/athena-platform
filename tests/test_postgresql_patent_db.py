#!/usr/bin/env python3
"""
测试PostgreSQL中国专利数据库连接和搜索功能
Test PostgreSQL Chinese Patent Database Connection and Search
"""

import logging
import sys

logger = logging.getLogger(__name__)
import os

sys.path.append(os.path.expanduser("~/Athena工作平台"))

import asyncio
import json
from datetime import datetime

import psycopg2
from psycopg2 import sql


class PostgreSQLPatentDBTester:
    """PostgreSQL专利数据库测试器"""

    def __init__(self):
        self.connection = None
        self.test_results = {
            'connection': False,
            'table_access': False,
            'search_functions': [],
            'sample_queries': [],
            'errors': []
        }

        # 数据库配置 - 从环境变量或配置文件获取
        self.db_config = {
            'host': os.getenv('PATENT_DB_HOST', 'localhost'),
            'port': os.getenv('PATENT_DB_PORT', '5432'),
            'database': os.getenv('PATENT_DB_NAME', 'patent_db'),
            'user': os.getenv('PATENT_DB_USER', 'postgres'),
            'password': os.getenv('PATENT_DB_PASSWORD', ''),
            # 添加PostgreSQL路径信息用于调试
            'pg_data_path': '/opt/homebrew/var/postgresql@17'
        }

    async def run_comprehensive_test(self):
        """运行全面的数据库测试"""
        print("🗄️ 测试PostgreSQL中国专利数据库")
        print("=" * 60)
        print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # 1. 测试基础连接
        await self.test_database_connection()

        # 2. 测试数据库结构
        await self.test_database_structure()

        # 3. 测试搜索功能
        await self.test_search_functions()

        # 4. 生成测试报告
        await self.generate_test_report()

    async def test_database_connection(self):
        """测试数据库连接"""
        print("1️⃣ 测试数据库连接")
        print("-" * 40)

        try:
            # 尝试连接数据库
            print(f"📡 正在连接 {self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}...")

            self.connection = psycopg2.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                database=self.db_config['database'],
                user=self.db_config['user'],
                password=self.db_config['password']
            )

            # 测试连接是否有效
            cursor = self.connection.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()

            print("✅ 数据库连接成功！")
            print(f"   PostgreSQL版本: {version[0]}")

            # 测试数据库权限
            cursor.execute("SELECT current_database(), current_user;")
            db_info = cursor.fetchone()
            print(f"   当前数据库: {db_info[0]}")
            print(f"   当前用户: {db_info[1]}")

            self.test_results['connection'] = True
            cursor.close()

        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            self.test_results['errors'].append(f"连接错误: {str(e)}")

        print()

    async def test_database_structure(self):
        """测试数据库结构"""
        if not self.connection:
            print("⚠️ 跳过数据库结构测试 - 连接未建立")
            return

        print("2️⃣ 测试数据库结构")
        print("-" * 40)

        try:
            cursor = self.connection.cursor()

            # 检查表是否存在
            print("📋 检查专利相关表...")

            # 常见的专利表名称
            patent_tables = [
                'patents',
                'patent_info',
                'chinese_patents',
                'patent_data',
                'patents_cn',
                'cn_patents'
            ]

            existing_tables = []
            for table in patent_tables:
                try:
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables
                            WHERE table_name = %s
                        );
                    """, (table,))
                    exists = cursor.fetchone()[0]
                    if exists:
                        existing_tables.append(table)
                        print(f"   ✅ 找到表: {table}")
                except Exception as e:                    # 记录异常但不中断流程
                    logger.debug(f"[test_postgresql_patent_db] Exception: {e}")

            if not existing_tables:
                # 查找所有表
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = 'public'
                    ORDER BY table_name;
                """)
                all_tables = [row[0] for row in cursor.fetchall()]
                print(f"   📝 数据库中的所有表: {', '.join(all_tables[:10])}")
                if len(all_tables) > 10:
                    print(f"      ... 还有 {len(all_tables) - 10} 个表")

            # 如果找到专利相关表，检查结构
            if existing_tables:
                main_table = existing_tables[0]
                print(f"\n🔍 检查表结构: {main_table}")

                cursor.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = %s
                    ORDER BY ordinal_position;
                """, (main_table,))

                columns = cursor.fetchall()
                print("   字段信息:")
                for col in columns[:10]:  # 只显示前10个字段
                    print(f"     • {col[0]}: {col[1]} ({'可空' if col[2] == 'YES' else '非空'})")

                # 检查记录数
                cursor.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(main_table)))
                count = cursor.fetchone()[0]
                print(f"   📊 记录总数: {count:,}")

                self.test_results['table_access'] = True
                self.test_results['main_table'] = main_table

            cursor.close()

        except Exception as e:
            print(f"❌ 数据库结构测试失败: {e}")
            self.test_results['errors'].append(f"结构错误: {str(e)}")

        print()

    async def test_search_functions(self):
        """测试搜索功能"""
        if not self.connection or not self.test_results.get('table_access'):
            print("⚠️ 跳过搜索功能测试 - 表访问不可用")
            return

        print("3️⃣ 测试搜索功能")
        print("-" * 40)

        main_table = self.test_results.get('main_table', 'patents')

        try:
            cursor = self.connection.cursor()

            # 测试1: 基础关键词搜索
            print("🔎 测试1: 基础关键词搜索")
            test_keywords = ['人工智能', '机器学习', '深度学习', 'AI', '算法']

            for keyword in test_keywords[:2]:  # 只测试前2个关键词
                try:
                    # 尝试构建搜索查询
                    search_query = sql.SQL("""
                        SELECT * FROM {}
                        WHERE patent_name ILIKE %s OR applicant ILIKE %s
                        LIMIT 5;
                    """).format(sql.Identifier(main_table))

                    cursor.execute(search_query, (f'%{keyword}%', f'%{keyword}%'))
                    results = cursor.fetchall()

                    print(f"   📝 搜索'{keyword}': 找到 {len(results)} 条结果")

                    if results:
                        self.test_results['search_functions'].append({
                            'type': 'keyword_search',
                            'keyword': keyword,
                            'results_count': len(results),
                            'success': True
                        })

                except Exception as e:
                    print(f"   ❌ 搜索'{keyword}'失败: {e}")

            # 测试2: 专利号搜索
            print("\n🔎 测试2: 专利号模式搜索")
            patent_patterns = ['CN%', 'ZL%', 'CN20%', 'CN10%']

            for pattern in patent_patterns[:2]:  # 只测试前2个模式
                try:
                    cursor.execute(sql.SQL("""
                        SELECT * FROM {}
                        WHERE application_number LIKE %s OR publication_number LIKE %s
                        LIMIT 3;
                    """).format(sql.Identifier(main_table)), (pattern, pattern))

                    results = cursor.fetchall()
                    print(f"   📝 专利号模式'{pattern}': 找到 {len(results)} 条结果")

                except Exception as e:
                    print(f"   ❌ 专利号搜索失败: {e}")

            # 测试3: 日期范围搜索
            print("\n🔎 测试3: 日期范围搜索")
            date_columns = ['application_date', 'publication_date', 'grant_date', 'create_date']

            for date_col in date_columns:
                try:
                    # 检查列是否存在
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.columns
                            WHERE table_name = %s AND column_name = %s
                        );
                    """, (main_table, date_col))

                    if cursor.fetchone()[0]:
                        cursor.execute(sql.SQL("""
                            SELECT COUNT(*) FROM {}
                            WHERE {} >= %s;
                        """).format(sql.Identifier(main_table), sql.Identifier(date_col)), ['2020-01-01'])
                        count = cursor.fetchone()[0]
                        print(f"   📅 {date_col}: 2020年后申请 {count:,} 件")
                        break

                except Exception:
                    continue

            # 测试4: 分类号搜索（简化版本，因为我们还不知道具体字段名）
            print("\n🔎 测试4: 申请人搜索")
            applicant_keywords = ['华为', '腾讯', '阿里巴巴', '小米']

            for keyword in applicant_keywords[:2]:  # 只测试前2个申请人
                try:
                    cursor.execute(sql.SQL("""
                        SELECT COUNT(*) FROM {}
                        WHERE applicant ILIKE %s;
                    """).format(sql.Identifier(main_table)), (f'%{keyword}%',))

                    count = cursor.fetchone()[0]
                    print(f"   🏢 {keyword}: {count:,} 件专利")

                except Exception as e:
                    print(f"   ⚠️ 申请人搜索失败: {e}")

            # 保存示例查询结果
            try:
                cursor.execute(sql.SQL("""
                    SELECT patent_name, application_number, application_date, patent_type
                    FROM {}
                    WHERE patent_name IS NOT NULL
                    LIMIT 3;
                """).format(sql.Identifier(main_table)))

                sample_results = cursor.fetchall()
                if sample_results:
                    self.test_results['sample_queries'] = [
                        {
                            'title': row[0],
                            'patent_number': row[1],
                            'date': str(row[2]) if row[2] else None,
                            'type': row[3]
                        }
                        for row in sample_results
                    ]

            except Exception as e:
                print(f"   ⚠️ 获取示例数据失败: {e}")

            cursor.close()

        except Exception as e:
            print(f"❌ 搜索功能测试失败: {e}")
            self.test_results['errors'].append(f"搜索错误: {str(e)}")

        print()

    async def test_advanced_features(self):
        """测试高级功能"""
        if not self.connection:
            return

        print("4️⃣ 测试高级功能")
        print("-" * 40)

        try:
            cursor = self.connection.cursor()

            # 测试全文搜索
            print("🔍 测试全文搜索功能...")
            try:
                cursor.execute("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'patents'
                    AND data_type IN ('text', 'varchar')
                    AND column_name LIKE '%search%' OR column_name LIKE '%vector%';
                """)

                search_columns = [row[0] for row in cursor.fetchall()]
                if search_columns:
                    print(f"   ✅ 发现搜索相关字段: {', '.join(search_columns)}")
                else:
                    print("   ℹ️ 未发现专门的搜索字段")

            except Exception:
                print("   ℹ️ 全文搜索检查跳过")

            # 测试索引
            print("\n📊 检查数据库索引...")
            try:
                cursor.execute("""
                    SELECT indexname, tablename
                    FROM pg_indexes
                    WHERE schemaname = 'public'
                    AND tablename LIKE '%patent%'
                    LIMIT 5;
                """)

                indexes = cursor.fetchall()
                if indexes:
                    print(f"   ✅ 发现 {len(indexes)} 个索引")
                    for idx in indexes:
                        print(f"     • {idx[0]} (表: {idx[1]})")
                else:
                    print("   ℹ️ 未发现专利相关索引")

            except Exception:
                print("   ℹ️ 索引检查跳过")

            cursor.close()

        except Exception as e:
            print(f"❌ 高级功能测试失败: {e}")

        print()

    async def generate_test_report(self):
        """生成测试报告"""
        print("📊 生成测试报告")
        print("=" * 60)

        # 计算成功率
        tests = ['connection', 'table_access']
        passed = sum(1 for test in tests if self.test_results.get(test, False))
        total = len(tests)
        success_rate = (passed / total) * 100 if total > 0 else 0

        print(f"\n✅ 基础功能测试结果: {passed}/{total} ({success_rate:.1f}%)")
        print(f"   • 数据库连接: {'✅' if self.test_results['connection'] else '❌'}")
        print(f"   • 表访问权限: {'✅' if self.test_results['table_access'] else '❌'}")

        if self.test_results['search_functions']:
            print(f"\n🔍 搜索功能测试: {len(self.test_results['search_functions'])} 项成功")
            for func in self.test_results['search_functions']:
                if func['success']:
                    print(f"   ✅ {func['type']}: '{func['keyword']}' ({func['results_count']} 结果)")

        if self.test_results['sample_queries']:
            print("\n📝 示例查询结果:")
            for i, sample in enumerate(self.test_results['sample_queries'][:3], 1):
                print(f"\n   示例 {i}:")
                print(f"   📋 标题: {sample['title']}")
                print(f"   🔢 专利号: {sample['patent_number']}")
                print(f"   📅 日期: {sample['date']}")
                if sample['abstract']:
                    print(f"   📄 摘要: {sample['abstract']}")

        if self.test_results['errors']:
            print(f"\n⚠️ 发现 {len(self.test_results['errors'])} 个问题:")
            for error in self.test_results['errors']:
                print(f"   • {error}")

        # 保存测试报告
        report = {
            'test_time': datetime.now().isoformat(),
            'database_config': {
                'host': self.db_config['host'],
                'port': self.db_config['port'],
                'database': self.db_config['database'],
                'user': self.db_config['user']
            },
            'test_results': self.test_results,
            'success_rate': success_rate
        }

        with open('/Users/xujian/postgresql_patent_db_test_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print("\n💾 测试报告已保存至: /Users/xujian/postgresql_patent_db_test_report.json")

        # 关闭连接
        if self.connection:
            self.connection.close()
            print("\n🔌 数据库连接已关闭")

    async def cleanup(self):
        """清理资源"""
        if self.connection:
            self.connection.close()

async def main():
    """主函数"""
    tester = PostgreSQLPatentDBTester()

    try:
        await tester.run_comprehensive_test()
        await tester.test_advanced_features()
    except KeyboardInterrupt:
        print("\n\n⏹️ 测试被用户中断")
    except Exception as e:
        print(f"\n\n💥 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
